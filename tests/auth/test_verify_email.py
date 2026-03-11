"""
tests/auth/test_verify_email.py

Tests for POST /auth/verify-email
"""
import pytest
from fastapi.testclient import TestClient


class TestVerifyEmailSuccess:
    def test_valid_token_returns_200(self, client: TestClient):
        reg = client.post(
            "/auth/register",
            json={"email": "verify_ok@example.com", "password": "Password123"},
        )
        token = reg.json()["verification_token"]
        resp = client.post("/auth/verify-email", json={"token": token})
        assert resp.status_code == 200

    def test_verify_response_message(self, client: TestClient):
        reg = client.post(
            "/auth/register",
            json={"email": "verify_msg@example.com", "password": "Password123"},
        )
        token = reg.json()["verification_token"]
        resp = client.post("/auth/verify-email", json={"token": token})
        assert "verified" in resp.json()["message"].lower()

    def test_user_is_marked_verified_after_verification(self, client: TestClient, verified_user: dict):
        """The /auth/me endpoint should show is_email_verified=True after full flow."""
        headers = {"Authorization": f"Bearer {verified_user['access_token']}"}
        me = client.get("/auth/me", headers=headers)
        assert me.json()["is_email_verified"] is True


class TestVerifyEmailFailures:
    def test_wrong_token_returns_400(self, client: TestClient):
        resp = client.post("/auth/verify-email", json={"token": "this-is-not-a-real-token"})
        assert resp.status_code == 400

    def test_already_used_token_returns_400(self, client: TestClient):
        """Using the same token twice should be rejected."""
        reg = client.post(
            "/auth/register",
            json={"email": "reuse_token@example.com", "password": "Password123"},
        )
        token = reg.json()["verification_token"]
        client.post("/auth/verify-email", json={"token": token})
        # Second use
        resp = client.post("/auth/verify-email", json={"token": token})
        assert resp.status_code == 400

    def test_already_used_token_error_message(self, client: TestClient):
        reg = client.post(
            "/auth/register",
            json={"email": "reuse_msg@example.com", "password": "Password123"},
        )
        token = reg.json()["verification_token"]
        client.post("/auth/verify-email", json={"token": token})
        resp = client.post("/auth/verify-email", json={"token": token})
        assert "already used" in resp.json()["detail"].lower()

    def test_missing_token_field_returns_422(self, client: TestClient):
        resp = client.post("/auth/verify-email", json={})
        assert resp.status_code == 422

    def test_empty_token_string_returns_400(self, client: TestClient):
        resp = client.post("/auth/verify-email", json={"token": ""})
        # Service will treat empty string as invalid token
        assert resp.status_code == 400
