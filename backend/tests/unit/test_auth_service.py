"""Unit tests for AuthService — no HTTP, no real DB required."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.core.security import hash_password, verify_password, decode_token
from app.modules.auth.service import AuthService
from app.modules.users.models import User


def _make_user(email: str = "test@example.com", active: bool = True) -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        full_name="Test User",
        hashed_password=hash_password("Password1"),
        is_active=active,
    )


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        pw = "Password1"
        hashed = hash_password(pw)
        assert hashed != pw

    def test_verify_correct_password(self):
        pw = "Password1"
        assert verify_password(pw, hash_password(pw)) is True

    def test_reject_wrong_password(self):
        assert verify_password("Wrong1", hash_password("Password1")) is False


class TestAuthServiceLogin:
    def test_login_returns_tokens(self, db):
        user = _make_user()
        db.add(user)
        db.commit()

        service = AuthService(db)
        result = service.login("test@example.com", "Password1")

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"

    def test_login_wrong_password_raises(self, db):
        from fastapi import HTTPException

        user = _make_user()
        db.add(user)
        db.commit()

        service = AuthService(db)
        with pytest.raises(HTTPException) as exc_info:
            service.login("test@example.com", "WrongPassword1")
        assert exc_info.value.status_code == 401

    def test_login_inactive_user_raises(self, db):
        from fastapi import HTTPException

        user = _make_user(active=False)
        db.add(user)
        db.commit()

        service = AuthService(db)
        with pytest.raises(HTTPException) as exc_info:
            service.login("test@example.com", "Password1")
        assert exc_info.value.status_code == 401

    def test_login_nonexistent_user_raises(self, db):
        from fastapi import HTTPException

        service = AuthService(db)
        with pytest.raises(HTTPException) as exc_info:
            service.login("nobody@example.com", "Password1")
        assert exc_info.value.status_code == 401

    def test_access_token_contains_user_id(self, db):
        user = _make_user()
        db.add(user)
        db.commit()

        service = AuthService(db)
        result = service.login("test@example.com", "Password1")

        payload = decode_token(result.access_token)
        assert payload["sub"] == str(user.id)
        assert payload["type"] == "access"

    def test_refresh_token_type(self, db):
        user = _make_user()
        db.add(user)
        db.commit()

        service = AuthService(db)
        result = service.login("test@example.com", "Password1")
        payload = decode_token(result.refresh_token)
        assert payload["type"] == "refresh"


class TestAuthServiceRefresh:
    def test_refresh_returns_new_tokens(self, db):
        user = _make_user()
        db.add(user)
        db.commit()

        service = AuthService(db)
        tokens = service.login("test@example.com", "Password1")
        new_tokens = service.refresh(tokens.refresh_token)

        assert new_tokens.access_token
        assert new_tokens.access_token != tokens.access_token

    def test_refresh_with_access_token_raises(self, db):
        from fastapi import HTTPException

        user = _make_user()
        db.add(user)
        db.commit()

        service = AuthService(db)
        tokens = service.login("test@example.com", "Password1")

        with pytest.raises(HTTPException) as exc_info:
            service.refresh(tokens.access_token)  # Wrong token type
        assert exc_info.value.status_code == 401

    def test_refresh_with_garbage_raises(self, db):
        from fastapi import HTTPException

        service = AuthService(db)
        with pytest.raises(HTTPException):
            service.refresh("not.a.valid.jwt")
