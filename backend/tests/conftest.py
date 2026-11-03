"""
Pytest configuration and shared fixtures.
Uses an in-memory SQLite database for speed (no Docker required).
Gemini API calls are always mocked.
"""

import os
import uuid
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set test env vars BEFORE importing the app
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-32chars")
os.environ.setdefault("GEMINI_API_KEY", "fake-api-key-for-tests")

from app.core.database import Base, get_db
from app.main import app
from app.modules.users.models import User
from app.core.security import hash_password

# We need SQLite-compatible imports; pgvector won't work in SQLite.
# So we patch the Vector column for tests.


@pytest.fixture(scope="session")
def engine():
    """In-memory SQLite engine for the test session."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Patch Vector type for SQLite compatibility
    with patch("pgvector.sqlalchemy.Vector", return_value=None):
        from app.core.database import Base
        # Re-import all models to register them
        import app.modules.users.models  # noqa
        import app.modules.documents.models  # noqa
        import app.modules.conversations.models  # noqa

        # Skip RAG model (uses Vector) — tested separately with mocks
        Base.metadata.create_all(bind=_engine)
    return _engine


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    """Transactional test session — rolled back after each test."""
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db: Session) -> Generator:
    """FastAPI TestClient with db dependency override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """A pre-created active user for auth tests."""
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        full_name="Test User",
        hashed_password=hash_password("Password1"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user) -> dict:
    """Authorization headers for the test_user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "Password1"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_gemini_embed():
    """Mock Gemini embedding calls."""
    with patch("app.integrations.gemini.embeddings.embed_texts") as mock:
        mock.return_value = [[0.1] * 768]
        yield mock


@pytest.fixture
def mock_gemini_generate():
    """Mock Gemini generation calls."""
    with patch("app.integrations.gemini.generation.generate_answer") as mock:
        from app.integrations.gemini.generation import GenerationResult
        mock.return_value = GenerationResult(
            answer="This is a mocked answer from the document.",
            model="gemini-1.5-flash",
        )
        yield mock
