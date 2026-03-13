"""
tests/auth/test_resend_verification.py

Tests for POST /auth/resend-verification
"""
from fastapi.testclient import TestClient


class TestResendVerificationSuccess:
    def test_unverified_user_can_resend(self, client: TestClient):
        client.post(
            "/auth/register",
            json={"email": "resend_ok@example.com", "password": "Password123"},
        )

        resp = client.post(
            "/auth/resend-verification",
            json={"email": "resend_ok@example.com"},
        )
        assert resp.status_code == 200

    def test_resend_success_message(self, client: TestClient, monkeypatch):
        monkeypatch.setattr("app.api.routes.auth.send_verification_email", lambda *_args, **_kwargs: True)

        client.post(
            "/auth/register",
            json={"email": "resend_msg@example.com", "password": "Password123"},
        )

        resp = client.post(
            "/auth/resend-verification",
            json={"email": "resend_msg@example.com"},
        )
        assert "resent" in resp.json()["message"].lower()


class TestResendVerificationFailures:
    def test_missing_email_returns_422(self, client: TestClient):
        resp = client.post("/auth/resend-verification", json={})
        assert resp.status_code == 422

    def test_unknown_user_returns_400(self, client: TestClient):
        resp = client.post(
            "/auth/resend-verification",
            json={"email": "unknown_user@example.com"},
        )
        assert resp.status_code == 400

    def test_verified_user_returns_400(self, client: TestClient):
        reg = client.post(
            "/auth/register",
            json={"email": "already_verified@example.com", "password": "Password123"},
        )
        token = reg.json()["verification_token"]
        client.post("/auth/verify-email", json={"token": token})

        resp = client.post(
            "/auth/resend-verification",
            json={"email": "already_verified@example.com"},
        )
        assert resp.status_code == 400
        assert "already verified" in resp.json()["detail"].lower()
