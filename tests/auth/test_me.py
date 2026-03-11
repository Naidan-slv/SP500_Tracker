"""
tests/auth/test_me.py

Tests for GET /auth/me  (JWT-protected route)
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import make_verified_user


class TestMeSuccess:
    def test_me_returns_200_with_valid_token(self, client: TestClient, auth_headers: dict):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200

    def test_me_returns_correct_email(self, client: TestClient):
        data = make_verified_user(client, "me_email@example.com")
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        resp = client.get("/auth/me", headers=headers)
        assert resp.json()["email"] == "me_email@example.com"

    def test_me_returns_all_expected_fields(self, client: TestClient, auth_headers: dict):
        body = client.get("/auth/me", headers=auth_headers).json()
        for field in ("id", "email", "is_email_verified", "is_active", "created_at"):
            assert field in body, f"Missing field: {field}"

    def test_me_is_email_verified_true(self, client: TestClient, auth_headers: dict):
        body = client.get("/auth/me", headers=auth_headers).json()
        assert body["is_email_verified"] is True

    def test_me_is_active_true(self, client: TestClient, auth_headers: dict):
        body = client.get("/auth/me", headers=auth_headers).json()
        assert body["is_active"] is True

    def test_me_id_is_positive_integer(self, client: TestClient, auth_headers: dict):
        body = client.get("/auth/me", headers=auth_headers).json()
        assert isinstance(body["id"], int)
        assert body["id"] > 0


class TestMeFailures:
    def test_no_token_returns_401(self, client: TestClient):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client: TestClient):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer this.is.garbage"})
        assert resp.status_code == 401

    def test_malformed_bearer_header_returns_401(self, client: TestClient):
        resp = client.get("/auth/me", headers={"Authorization": "NotBearer sometoken"})
        assert resp.status_code == 401

    def test_empty_bearer_token_returns_401(self, client: TestClient):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer "})
        assert resp.status_code == 401
