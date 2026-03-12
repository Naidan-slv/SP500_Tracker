from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import Stock, StockPrice


def seed_chart_data(db_session: Session) -> None:
    db_session.add(Stock(ticker="AAPL", company_name="Apple Inc."))
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


def test_end_to_end_user_journey(client: TestClient, db_session: Session):
    seed_chart_data(db_session)

    register = client.post(
        "/auth/register",
        json={"email": "e2e_user@example.com", "password": "Password123"},
    )
    assert register.status_code == 201
    verification_token = register.json()["verification_token"]

    verify = client.post("/auth/verify-email", json={"token": verification_token})
    assert verify.status_code == 200

    login = client.post(
        "/auth/login",
        json={"email": "e2e_user@example.com", "password": "Password123"},
    )
    assert login.status_code == 200
    access_token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "e2e_user@example.com"

    create_watchlist = client.post("/watchlists", json={"name": "My Watchlist"}, headers=headers)
    assert create_watchlist.status_code == 201
    watchlist_id = create_watchlist.json()["id"]

    add_watch_item = client.post(
        f"/watchlists/{watchlist_id}/items",
        json={"ticker": "AAPL"},
        headers=headers,
    )
    assert add_watch_item.status_code == 201

    list_watch_items = client.get(f"/watchlists/{watchlist_id}/items", headers=headers)
    assert list_watch_items.status_code == 200
    assert list_watch_items.json()["total"] == 1

    create_portfolio = client.post("/portfolios", json={"name": "Core Portfolio"}, headers=headers)
    assert create_portfolio.status_code == 201
    portfolio_id = create_portfolio.json()["id"]

    add_holding = client.post(
        f"/portfolios/{portfolio_id}/holdings",
        json={"ticker": "AAPL", "quantity": 5, "avg_cost": 100},
        headers=headers,
    )
    assert add_holding.status_code == 201

    holdings = client.get(f"/portfolios/{portfolio_id}/holdings", headers=headers)
    assert holdings.status_code == 200
    assert holdings.json()["total"] == 1

    discover = client.get("/stocks?search=aapl&limit=10&offset=0")
    assert discover.status_code == 200
    assert discover.json()["total"] >= 1

    history = client.get("/stocks/AAPL/history?timeframe=max&limit=100&offset=0")
    assert history.status_code == 200
    history_body = history.json()
    assert history_body["ticker"] == "AAPL"
    assert history_body["total"] == 2
    assert len(history_body["items"]) == 2
