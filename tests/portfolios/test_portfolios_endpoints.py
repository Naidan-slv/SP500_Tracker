from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import Stock
from tests.conftest import make_verified_user


def create_portfolio(client: TestClient, auth_headers: dict, name: str = "Core") -> int:
    resp = client.post("/portfolios", json={"name": name}, headers=auth_headers)
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


class TestPortfoliosAuth:
    def test_list_requires_auth(self, client: TestClient):
        resp = client.get("/portfolios")
        assert resp.status_code == 401


class TestPortfolioCrud:
    def test_create_and_list_portfolio(self, client: TestClient, auth_headers: dict):
        create_portfolio(client, auth_headers, "Long-term")

        resp = client.get("/portfolios", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Long-term"
        assert body["items"][0]["holdings_count"] == 0

    def test_delete_portfolio(self, client: TestClient, auth_headers: dict):
        portfolio_id = create_portfolio(client, auth_headers, "Delete")

        delete_resp = client.delete(f"/portfolios/{portfolio_id}", headers=auth_headers)
        assert delete_resp.status_code == 200

        list_resp = client.get("/portfolios", headers=auth_headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 0

    def test_cannot_access_other_users_portfolio(self, client: TestClient):
        owner = make_verified_user(client, "owner_port@example.com")
        owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}
        intruder = make_verified_user(client, "intruder_port@example.com")
        intruder_headers = {"Authorization": f"Bearer {intruder['access_token']}"}

        portfolio_id = create_portfolio(client, owner_headers, "Private")

        resp = client.delete(f"/portfolios/{portfolio_id}", headers=intruder_headers)
        assert resp.status_code == 404


class TestPortfolioHoldings:
    def test_add_and_list_holdings(self, client: TestClient, auth_headers: dict, db_session: Session):
        seed_stocks(db_session)
        portfolio_id = create_portfolio(client, auth_headers)

        add_resp = client.post(
            f"/portfolios/{portfolio_id}/holdings",
            json={"ticker": "aapl", "quantity": 10, "avg_cost": 100},
            headers=auth_headers,
        )
        assert add_resp.status_code == 201
        assert add_resp.json()["ticker"] == "AAPL"
        assert add_resp.json()["company_name"] == "Apple Inc."
        assert add_resp.json()["quantity"] == 10
        assert add_resp.json()["avg_cost"] == 100

        list_resp = client.get(f"/portfolios/{portfolio_id}/holdings", headers=auth_headers)
        assert list_resp.status_code == 200
        body = list_resp.json()
        assert body["total"] == 1
        assert body["items"][0]["ticker"] == "AAPL"
        assert body["items"][0]["company_name"] == "Apple Inc."

    def test_add_invalid_ticker_returns_404(self, client: TestClient, auth_headers: dict):
        portfolio_id = create_portfolio(client, auth_headers)

        resp = client.post(
            f"/portfolios/{portfolio_id}/holdings",
            json={"ticker": "NOTREAL", "quantity": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_add_holding_accepts_company_name_input(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
    ):
        seed_stocks(db_session)
        portfolio_id = create_portfolio(client, auth_headers)

        resp = client.post(
            f"/portfolios/{portfolio_id}/holdings",
            json={"ticker": "Microsoft", "quantity": 2},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["ticker"] == "MSFT"

    def test_add_holding_accepts_company_name_with_missing_db_name(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
    ):
        db_session.add(Stock(ticker="AAPL", company_name=None))
        db_session.commit()
        portfolio_id = create_portfolio(client, auth_headers)

        resp = client.post(
            f"/portfolios/{portfolio_id}/holdings",
            json={"ticker": "Apple", "quantity": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["ticker"] == "AAPL"
        assert resp.json()["company_name"] == "Apple Inc."

    def test_add_duplicate_ticker_returns_409(self, client: TestClient, auth_headers: dict, db_session: Session):
        seed_stocks(db_session)
        portfolio_id = create_portfolio(client, auth_headers)

        first = client.post(
            f"/portfolios/{portfolio_id}/holdings",
            json={"ticker": "MSFT", "quantity": 5},
            headers=auth_headers,
        )
        assert first.status_code == 201

        second = client.post(
            f"/portfolios/{portfolio_id}/holdings",
            json={"ticker": "MSFT", "quantity": 7},
            headers=auth_headers,
        )
        assert second.status_code == 409

    def test_remove_holding(self, client: TestClient, auth_headers: dict, db_session: Session):
        seed_stocks(db_session)
        portfolio_id = create_portfolio(client, auth_headers)

        client.post(
            f"/portfolios/{portfolio_id}/holdings",
            json={"ticker": "AAPL", "quantity": 3},
            headers=auth_headers,
        )

        remove_resp = client.delete(f"/portfolios/{portfolio_id}/holdings/AAPL", headers=auth_headers)
        assert remove_resp.status_code == 200

        list_resp = client.get(f"/portfolios/{portfolio_id}/holdings", headers=auth_headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 0

    def test_remove_missing_holding_returns_404(self, client: TestClient, auth_headers: dict):
        portfolio_id = create_portfolio(client, auth_headers)
        resp = client.delete(f"/portfolios/{portfolio_id}/holdings/MSFT", headers=auth_headers)
        assert resp.status_code == 404

    def test_invalid_quantity_validation(self, client: TestClient, auth_headers: dict, db_session: Session):
        seed_stocks(db_session)
        portfolio_id = create_portfolio(client, auth_headers)

        resp = client.post(
            f"/portfolios/{portfolio_id}/holdings",
            json={"ticker": "AAPL", "quantity": 0},
            headers=auth_headers,
        )
        assert resp.status_code == 422
