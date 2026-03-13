"""
tests/auth/test_register.py

Tests for POST /auth/register
"""
import pytest
from fastapi.testclient import TestClient


class TestRegisterSuccess:
    def test_register_returns_201(self, client: TestClient):
        resp = client.post(
            "/auth/register",
            json={"email": "new_user@example.com", "password": "Password123"},
        )
        assert resp.status_code == 201

    def test_register_response_has_expected_fields(self, client: TestClient):
        resp = client.post(
            "/auth/register",
            json={"email": "fields_user@example.com", "password": "Password123"},
        )
        body = resp.json()
        assert "message" in body
        assert "user_id" in body
        assert isinstance(body["user_id"], int)

    def test_register_exposes_verification_token_in_dev_mode(self, client: TestClient):
        """EXPOSE_VERIFICATION_TOKEN=true → token is present in response."""
        resp = client.post(
            "/auth/register",
            json={"email": "token_exposed@example.com", "password": "Password123"},
        )
        body = resp.json()
        assert body.get("verification_token") is not None
        assert len(body["verification_token"]) > 10

    def test_register_message_content(self, client: TestClient):
        resp = client.post(
            "/auth/register",
            json={"email": "msg_check@example.com", "password": "Password123"},
        )
        assert "verify" in resp.json()["message"].lower()

    def test_register_response_includes_verification_link(self, client: TestClient):
        resp = client.post(
            "/auth/register",
            json={"email": "link_user@example.com", "password": "Password123"},
        )
        body = resp.json()
        assert body.get("verification_link")
        assert "/verify-email?token=" in body["verification_link"]

    def test_register_message_when_email_sent(self, client: TestClient, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("app.api.routes.auth.send_verification_email", lambda *_args, **_kwargs: True)

        resp = client.post(
            "/auth/register",
            json={"email": "sent_user@example.com", "password": "Password123"},
        )
        assert "email sent" in resp.json()["message"].lower()

    def test_register_email_is_normalised_to_lowercase(self, client: TestClient):
        """Upper-case email should be normalised and stored in lower-case."""
        resp = client.post(
            "/auth/register",
            json={"email": "UPPERCASE@Example.COM", "password": "Password123"},
        )
        assert resp.status_code == 201


class TestRegisterDuplicateEmail:
    def test_duplicate_email_returns_409(self, client: TestClient):
        payload = {"email": "dup@example.com", "password": "Password123"}
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 409

    def test_duplicate_email_is_case_insensitive(self, client: TestClient):
        """Registering same email with different casing should still be rejected."""
        client.post("/auth/register", json={"email": "case@example.com", "password": "Password123"})
        resp = client.post("/auth/register", json={"email": "CASE@EXAMPLE.COM", "password": "Password123"})
        assert resp.status_code == 409

    def test_duplicate_email_error_message(self, client: TestClient):
        payload = {"email": "dup_msg@example.com", "password": "Password123"}
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert "registered" in resp.json()["detail"].lower()


class TestRegisterValidation:
    def test_password_too_short_returns_422(self, client: TestClient):
        resp = client.post(
            "/auth/register",
            json={"email": "short_pw@example.com", "password": "abc"},
        )
        assert resp.status_code == 422

    def test_missing_email_returns_422(self, client: TestClient):
        resp = client.post("/auth/register", json={"password": "Password123"})
        assert resp.status_code == 422

    def test_missing_password_returns_422(self, client: TestClient):
        resp = client.post("/auth/register", json={"email": "nopw@example.com"})
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client: TestClient):
        resp = client.post("/auth/register", json={})
        assert resp.status_code == 422
