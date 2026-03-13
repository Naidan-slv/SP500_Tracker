"""
tests/auth/test_login.py

Tests for POST /auth/login
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import make_verified_user


class TestLoginSuccess:
    def test_login_returns_200(self, client: TestClient):
        make_verified_user(client, "login_ok@example.com")
        resp = client.post(
            "/auth/login",
            json={"email": "login_ok@example.com", "password": "Password123"},
        )
        assert resp.status_code == 200

    def test_login_returns_access_token(self, client: TestClient):
        make_verified_user(client, "token_check@example.com")
        resp = client.post(
            "/auth/login",
            json={"email": "token_check@example.com", "password": "Password123"},
        )
        body = resp.json()
        assert "access_token" in body
        assert len(body["access_token"]) > 20

    def test_login_token_type_is_bearer(self, client: TestClient):
        make_verified_user(client, "token_type@example.com")
        resp = client.post(
            "/auth/login",
            json={"email": "token_type@example.com", "password": "Password123"},
        )
        assert resp.json()["token_type"] == "bearer"

    def test_login_response_contains_user_object(self, client: TestClient):
        make_verified_user(client, "user_obj@example.com")
        resp = client.post(
            "/auth/login",
            json={"email": "user_obj@example.com", "password": "Password123"},
        )
        user = resp.json().get("user")
        assert user is not None
        assert user["email"] == "user_obj@example.com"
        assert user["is_email_verified"] is True
        assert user["is_active"] is True

    def test_login_user_id_is_integer(self, client: TestClient):
        make_verified_user(client, "user_id_check@example.com")
        resp = client.post(
            "/auth/login",
            json={"email": "user_id_check@example.com", "password": "Password123"},
        )
        assert isinstance(resp.json()["user"]["id"], int)


class TestLoginFailures:
    def test_wrong_password_returns_401(self, client: TestClient):
        make_verified_user(client, "wrong_pw@example.com")
        resp = client.post(
            "/auth/login",
            json={"email": "wrong_pw@example.com", "password": "WrongPassword!"},
        )
        assert resp.status_code == 401

    def test_nonexistent_email_returns_401(self, client: TestClient):
        resp = client.post(
            "/auth/login",
            json={"email": "ghost@example.com", "password": "Password123"},
        )
        assert resp.status_code == 401

    def test_missing_email_returns_422(self, client: TestClient):
        resp = client.post("/auth/login", json={"password": "Password123"})
        assert resp.status_code == 422

    def test_missing_password_returns_422(self, client: TestClient):
        resp = client.post("/auth/login", json={"email": "someone@example.com"})
        assert resp.status_code == 422
