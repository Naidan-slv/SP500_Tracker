from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import Stock
from tests.conftest import make_verified_user


def create_watchlist(client: TestClient, auth_headers: dict, name: str = "Tech") -> int:
    resp = client.post("/watchlists", json={"name": name}, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def seed_stocks(db_session: Session) -> None:
    db_session.add_all(
        [
            Stock(ticker="AAPL", company_name="Apple Inc."),
            Stock(ticker="MSFT", company_name="Microsoft Corporation"),
        ]
    )
    db_session.commit()


class TestWatchlistsAuth:
    def test_list_requires_auth(self, client: TestClient):
        resp = client.get("/watchlists")
        assert resp.status_code == 401


class TestWatchlistCrud:
    def test_create_and_list_watchlist(self, client: TestClient, auth_headers: dict):
        create_watchlist(client, auth_headers, "My Watchlist")

        resp = client.get("/watchlists", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "My Watchlist"
        assert body["items"][0]["items_count"] == 0

    def test_delete_watchlist(self, client: TestClient, auth_headers: dict):
        watchlist_id = create_watchlist(client, auth_headers, "Delete Me")

        delete_resp = client.delete(f"/watchlists/{watchlist_id}", headers=auth_headers)
        assert delete_resp.status_code == 200

        list_resp = client.get("/watchlists", headers=auth_headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 0

    def test_cannot_access_other_users_watchlist(self, client: TestClient):
        owner = make_verified_user(client, "owner_watch@example.com")
        owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}
        intruder = make_verified_user(client, "intruder_watch@example.com")
        intruder_headers = {"Authorization": f"Bearer {intruder['access_token']}"}

        watchlist_id = create_watchlist(client, owner_headers, "Private")

        resp = client.delete(f"/watchlists/{watchlist_id}", headers=intruder_headers)
        assert resp.status_code == 404


class TestWatchlistItems:
    def test_add_and_list_watchlist_item(self, client: TestClient, auth_headers: dict, db_session: Session):
        seed_stocks(db_session)
        watchlist_id = create_watchlist(client, auth_headers)

        add_resp = client.post(
            f"/watchlists/{watchlist_id}/items",
            json={"ticker": "aapl"},
            headers=auth_headers,
        )
        assert add_resp.status_code == 201
        assert add_resp.json()["ticker"] == "AAPL"

        list_resp = client.get(f"/watchlists/{watchlist_id}/items", headers=auth_headers)
        assert list_resp.status_code == 200
        body = list_resp.json()
        assert body["total"] == 1
        assert body["items"][0]["ticker"] == "AAPL"

    def test_add_invalid_ticker_returns_404(self, client: TestClient, auth_headers: dict):
        watchlist_id = create_watchlist(client, auth_headers)

        resp = client.post(
            f"/watchlists/{watchlist_id}/items",
            json={"ticker": "NOTREAL"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_add_duplicate_ticker_returns_409(self, client: TestClient, auth_headers: dict, db_session: Session):
        seed_stocks(db_session)
        watchlist_id = create_watchlist(client, auth_headers)

        first = client.post(
            f"/watchlists/{watchlist_id}/items",
            json={"ticker": "MSFT"},
            headers=auth_headers,
        )
        assert first.status_code == 201

        second = client.post(
            f"/watchlists/{watchlist_id}/items",
            json={"ticker": "MSFT"},
            headers=auth_headers,
        )
        assert second.status_code == 409

    def test_remove_watchlist_item(self, client: TestClient, auth_headers: dict, db_session: Session):
        seed_stocks(db_session)
        watchlist_id = create_watchlist(client, auth_headers)

        client.post(
            f"/watchlists/{watchlist_id}/items",
            json={"ticker": "AAPL"},
            headers=auth_headers,
        )

        remove_resp = client.delete(f"/watchlists/{watchlist_id}/items/AAPL", headers=auth_headers)
        assert remove_resp.status_code == 200

        list_resp = client.get(f"/watchlists/{watchlist_id}/items", headers=auth_headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 0

    def test_remove_missing_item_returns_404(self, client: TestClient, auth_headers: dict):
        watchlist_id = create_watchlist(client, auth_headers)
        resp = client.delete(f"/watchlists/{watchlist_id}/items/MSFT", headers=auth_headers)
        assert resp.status_code == 404
