"""Integration tests for auth endpoints."""

import pytest


class TestRegister:
    def test_register_success(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "Password1",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, test_user):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "testuser@example.com",  # Already exists
                "full_name": "Duplicate",
                "password": "Password1",
            },
        )
        assert response.status_code == 409

    def test_register_weak_password(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "full_name": "Weak",
                "password": "password",  # No uppercase or digit
            },
        )
        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "full_name": "Test",
                "password": "Password1",
            },
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client, test_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "Password1"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "WrongPass1"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "Password1"},
        )
        assert response.status_code == 401


class TestProtectedRoute:
    def test_get_me_without_token(self, client):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_get_me_with_valid_token(self, client, auth_headers):
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"

    def test_get_me_with_invalid_token(self, client):
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401


class TestRefresh:
    def test_refresh_returns_new_access_token(self, client, test_user):
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "Password1"},
        )
        refresh_token = login.json()["refresh_token"]

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_with_access_token_fails(self, client, test_user):
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "Password1"},
        )
        access_token = login.json()["access_token"]

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},  # Wrong type
        )
        assert response.status_code == 401
