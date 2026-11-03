"""Integration tests for document endpoints."""

import io
import uuid
from unittest.mock import patch

import pytest


def _fake_pdf() -> bytes:
    """Minimal valid-looking PDF bytes for upload tests."""
    return b"%PDF-1.4 fake pdf content for testing purposes only"


class TestDocumentUpload:
    def test_upload_requires_auth(self, client):
        response = client.post("/api/v1/documents/")
        assert response.status_code == 401

    def test_upload_pdf_success(self, client, auth_headers):
        with patch("app.modules.documents.service.DocumentService._process_document"):
            with patch("app.shared.storage.LocalStorage.save") as mock_save:
                mock_save.return_value = "/fake/path/doc.pdf"
                response = client.post(
                    "/api/v1/documents/",
                    headers=auth_headers,
                    files={"file": ("test.pdf", io.BytesIO(_fake_pdf()), "application/pdf")},
                )
        assert response.status_code == 201
        data = response.json()
        assert data["original_name"] == "test.pdf"
        assert data["status"] == "pending"

    def test_upload_non_pdf_rejected(self, client, auth_headers):
        response = client.post(
            "/api/v1/documents/",
            headers=auth_headers,
            files={"file": ("doc.txt", io.BytesIO(b"text content"), "text/plain")},
        )
        assert response.status_code == 422

    def test_upload_requires_file(self, client, auth_headers):
        response = client.post("/api/v1/documents/", headers=auth_headers)
        assert response.status_code == 422


class TestDocumentListing:
    def test_list_documents_empty(self, client, auth_headers):
        response = client.get("/api/v1/documents/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_documents_requires_auth(self, client):
        response = client.get("/api/v1/documents/")
        assert response.status_code == 401


class TestDocumentIsolation:
    """Ensure users cannot access each other's documents."""

    def test_cannot_access_other_users_document(self, client, db):
        from app.modules.users.models import User
        from app.modules.documents.models import Document, DocumentStatus
        from app.core.security import hash_password

        # Create second user and a document belonging to them
        other_user = User(
            id=uuid.uuid4(),
            email="other@example.com",
            full_name="Other User",
            hashed_password=hash_password("Password1"),
            is_active=True,
        )
        db.add(other_user)
        db.commit()

        other_doc = Document(
            id=uuid.uuid4(),
            user_id=other_user.id,
            filename="other.pdf",
            original_name="other.pdf",
            file_path="/fake/other.pdf",
            status=DocumentStatus.COMPLETED,
        )
        db.add(other_doc)
        db.commit()

        # Login as test_user and try to access other user's doc
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "Password1"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = client.get(f"/api/v1/documents/{other_doc.id}", headers=headers)
        assert response.status_code == 404  # Not found, not forbidden (don't leak existence)
