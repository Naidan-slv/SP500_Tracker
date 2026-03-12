"""
Shared test fixtures for the SP500 Tracker test suite.

All tests use an in-memory SQLite database so they are:
  - Fast (no network round-trips)
  - Isolated (each test session starts clean)
  - Safe (never touch the real Supabase database)

The real DATABASE_URL from .env is completely bypassed here.
"""
import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ── Make sure the project root is on sys.path ────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set a dummy DATABASE_URL before any app import so config doesn't raise
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("EXPOSE_VERIFICATION_TOKEN", "true")

from sqlalchemy import Integer as SAInteger
from sqlalchemy import BigInteger
from app.database.base import Base  # noqa: E402
from app.database.dependencies import get_db  # noqa: E402
from app.main import app  # noqa: E402

# ── In-memory SQLite engine (shared connection so all sessions see same data) ─
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False, autocommit=False)


def _patch_bigint_for_sqlite(metadata):
    """
    SQLite does not support BigInteger autoincrement PKs via RETURNING.
    Replace BigInteger columns with Integer so SQLite's rowid mechanism works.
    """
    for table in metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, BigInteger):
                col.type = SAInteger()


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all tables once for the entire test session."""
    _patch_bigint_for_sqlite(Base.metadata)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def db_session(create_test_tables) -> Generator[Session, None, None]:
    """
    Provide a transactional DB session per test.
    Everything is rolled back after each test so tests don't bleed into each other.
    """
    connection = TEST_ENGINE.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient that uses the in-memory DB session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Reusable helpers ──────────────────────────────────────────────────────────

def register_user(client: TestClient, email: str, password: str = "Password123") -> dict:
    """POST /auth/register and return the response body."""
    resp = client.post("/auth/register", json={"email": email, "password": password})
    return resp


def get_verification_token(client: TestClient, email: str, password: str = "Password123") -> str:
    """Register a new user and return the raw verification token."""
    resp = register_user(client, email, password)
    assert resp.status_code == 201, resp.text
    return resp.json()["verification_token"]


def make_verified_user(client: TestClient, email: str, password: str = "Password123") -> dict:
    """Register + verify a user, return login response body."""
    token = get_verification_token(client, email, password)
    client.post("/auth/verify-email", json={"token": token})
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture()
def verified_user(client: TestClient) -> dict:
    """Fixture: a fully registered + verified + logged-in user."""
    return make_verified_user(client, "fixture_user@example.com")


@pytest.fixture()
def auth_headers(verified_user: dict) -> dict:
    """Fixture: Bearer token headers for an authenticated user."""
    return {"Authorization": f"Bearer {verified_user['access_token']}"}
