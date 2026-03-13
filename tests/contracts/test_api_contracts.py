from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import Stock, StockPrice


def seed_stock_data(db_session: Session) -> None:
    db_session.add_all(
        [
            Stock(ticker="AAPL", company_name="Apple Inc."),
            Stock(ticker="MSFT", company_name="Microsoft Corporation"),
        ]
    )
    db_session.add_all(
        [
            StockPrice(
                ticker="AAPL",
                date=date(2024, 1, 1),
                open=Decimal("100.00"),
                high=Decimal("110.00"),
                low=Decimal("95.00"),
                close=Decimal("105.00"),
                adj_close=Decimal("105.00"),
                volume=1_000_000,
            ),
            StockPrice(
                ticker="AAPL",
                date=date(2024, 1, 2),
                open=Decimal("105.00"),
                high=Decimal("112.00"),
                low=Decimal("102.00"),
                close=Decimal("111.00"),
                adj_close=Decimal("111.00"),
                volume=1_200_000,
            ),
        ]
    )
    db_session.commit()


class TestAuthContract:
    def test_register_response_contract(self, client: TestClient):
        resp = client.post(
            "/auth/register",
            json={"email": "contract_reg@example.com", "password": "Password123"},
        )
        assert resp.status_code == 201
        body = resp.json()

        assert set(body.keys()) >= {"message", "user_id"}
        assert isinstance(body["message"], str)
        assert isinstance(body["user_id"], int)

    def test_login_response_contract(self, client: TestClient):
        register = client.post(
            "/auth/register",
            json={"email": "contract_login@example.com", "password": "Password123"},
        )
        token = register.json()["verification_token"]
        client.post("/auth/verify-email", json={"token": token})

        resp = client.post(
            "/auth/login",
            json={"email": "contract_login@example.com", "password": "Password123"},
        )
        assert resp.status_code == 200
        body = resp.json()

        assert set(body.keys()) == {"access_token", "token_type", "user"}
        assert isinstance(body["access_token"], str)
        assert body["token_type"] == "bearer"
        assert set(body["user"].keys()) == {
            "id",
            "email",
            "is_email_verified",
            "is_active",
            "created_at",
        }


class TestStocksContract:
    def test_stocks_discover_contract(self, client: TestClient, db_session: Session):
        seed_stock_data(db_session)

        resp = client.get("/stocks?limit=10&offset=0")
        assert resp.status_code == 200
        body = resp.json()

        assert set(body.keys()) == {"total", "limit", "offset", "items"}
        assert isinstance(body["total"], int)
        assert isinstance(body["limit"], int)
        assert isinstance(body["offset"], int)
        assert isinstance(body["items"], list)
        assert set(body["items"][0].keys()) == {"ticker", "company_name", "logo_url"}

    def test_stock_history_contract(self, client: TestClient, db_session: Session):
        seed_stock_data(db_session)

        resp = client.get("/stocks/AAPL/history?limit=10&offset=0")
        assert resp.status_code == 200
        body = resp.json()

        assert set(body.keys()) == {
            "ticker",
            "company_name",
            "logo_url",
            "timeframe",
            "start_date",
            "end_date",
            "total",
            "limit",
            "offset",
            "items",
        }
        assert isinstance(body["items"], list)
        point = body["items"][0]
        assert set(point.keys()) == {"date", "open", "high", "low", "close", "adj_close", "volume"}


class TestUserResourceContracts:
    def test_watchlist_list_contract(self, client: TestClient):
        reg = client.post(
            "/auth/register",
            json={"email": "contract_watch@example.com", "password": "Password123"},
        )
        client.post("/auth/verify-email", json={"token": reg.json()["verification_token"]})
        login = client.post(
            "/auth/login",
            json={"email": "contract_watch@example.com", "password": "Password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        client.post("/watchlists", json={"name": "Tech"}, headers=headers)
        resp = client.get("/watchlists", headers=headers)
        assert resp.status_code == 200
        body = resp.json()

        assert set(body.keys()) == {"total", "limit", "offset", "items"}
        assert set(body["items"][0].keys()) == {"id", "name", "created_at", "items_count"}

    def test_watchlist_items_contract_includes_company_name(
        self,
        client: TestClient,
        db_session: Session,
    ):
        seed_stock_data(db_session)

        reg = client.post(
            "/auth/register",
            json={"email": "contract_watch_items@example.com", "password": "Password123"},
        )
        client.post("/auth/verify-email", json={"token": reg.json()["verification_token"]})
        login = client.post(
            "/auth/login",
            json={"email": "contract_watch_items@example.com", "password": "Password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        watchlist_id = client.post("/watchlists", json={"name": "Tech"}, headers=headers).json()["id"]
        client.post(f"/watchlists/{watchlist_id}/items", json={"ticker": "AAPL"}, headers=headers)

        resp = client.get(f"/watchlists/{watchlist_id}/items", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert set(body["items"][0].keys()) == {"id", "ticker", "company_name", "added_at"}

    def test_portfolio_list_contract(self, client: TestClient):
        reg = client.post(
            "/auth/register",
            json={"email": "contract_port@example.com", "password": "Password123"},
        )
        client.post("/auth/verify-email", json={"token": reg.json()["verification_token"]})
        login = client.post(
            "/auth/login",
            json={"email": "contract_port@example.com", "password": "Password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        client.post("/portfolios", json={"name": "Long-term"}, headers=headers)
        resp = client.get("/portfolios", headers=headers)
        assert resp.status_code == 200
        body = resp.json()

        assert set(body.keys()) == {"total", "limit", "offset", "items"}
        assert set(body["items"][0].keys()) == {"id", "name", "created_at", "holdings_count"}

    def test_portfolio_holdings_contract_includes_company_name(
        self,
        client: TestClient,
        db_session: Session,
    ):
        seed_stock_data(db_session)

        reg = client.post(
            "/auth/register",
            json={"email": "contract_port_holdings@example.com", "password": "Password123"},
        )
        client.post("/auth/verify-email", json={"token": reg.json()["verification_token"]})
        login = client.post(
            "/auth/login",
            json={"email": "contract_port_holdings@example.com", "password": "Password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        portfolio_id = client.post("/portfolios", json={"name": "Core"}, headers=headers).json()["id"]
        client.post(
            f"/portfolios/{portfolio_id}/holdings",
            json={"ticker": "AAPL", "quantity": 2},
            headers=headers,
        )

        resp = client.get(f"/portfolios/{portfolio_id}/holdings", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert set(body["items"][0].keys()) == {
            "id",
            "ticker",
            "company_name",
            "quantity",
            "avg_cost",
        }
