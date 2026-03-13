from datetime import datetime, timezone
from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app


def main() -> None:
    client = TestClient(app)
    unique_email = f"auth_test_{datetime.now(timezone.utc).timestamp()}@example.com"
    password = "StrongPass123"

    register_resp = client.post(
        "/auth/register",
        json={"email": unique_email, "password": password},
    )
    print("register_status", register_resp.status_code)
    print("register_body", register_resp.json())

    login_resp = client.post(
        "/auth/login",
        json={"email": unique_email, "password": password},
    )
    print("login_status", login_resp.status_code)
    print("login_body", login_resp.json())

    access_token = login_resp.json()["access_token"]

    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    print("me_status", me_resp.status_code)
    print("me_body", me_resp.json())


if __name__ == "__main__":
    main()
