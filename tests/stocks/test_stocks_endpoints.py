from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import Stock, StockPrice


def seed_stock_data(db_session: Session) -> None:
    stocks = [
        Stock(ticker="AAPL", company_name="Apple Inc."),
        Stock(ticker="MSFT", company_name="Microsoft Corporation"),
        Stock(ticker="TSLA", company_name="Tesla Inc."),
        Stock(ticker="EMPTY", company_name="No Prices Ltd"),
    ]
    db_session.add_all(stocks)

    prices = [
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
        StockPrice(
            ticker="AAPL",
            date=date(2024, 1, 3),
            open=Decimal("111.00"),
            high=Decimal("115.00"),
            low=Decimal("109.00"),
            close=Decimal("113.00"),
            adj_close=Decimal("113.00"),
            volume=1_400_000,
        ),
        StockPrice(
            ticker="MSFT",
            date=date(2024, 1, 1),
            open=Decimal("300.00"),
            high=Decimal("310.00"),
            low=Decimal("298.00"),
            close=Decimal("307.00"),
            adj_close=Decimal("307.00"),
            volume=900_000,
        ),
        StockPrice(
            ticker="MSFT",
            date=date(2024, 1, 10),
            open=Decimal("307.00"),
            high=Decimal("315.00"),
            low=Decimal("305.00"),
            close=Decimal("313.00"),
            adj_close=Decimal("313.00"),
            volume=950_000,
        ),
    ]
    db_session.add_all(prices)
    db_session.commit()


class TestStocksDiscover:
    def test_list_stocks_returns_paginated_items(self, client: TestClient, db_session: Session):
        seed_stock_data(db_session)

        resp = client.get("/stocks?limit=2&offset=0")
        assert resp.status_code == 200
        body = resp.json()

        assert body["total"] == 4
        assert body["limit"] == 2
        assert body["offset"] == 0
        assert len(body["items"]) == 2

    def test_list_stocks_supports_search(self, client: TestClient, db_session: Session):
        seed_stock_data(db_session)

        resp = client.get("/stocks?search=tesla")
        assert resp.status_code == 200
        body = resp.json()

        assert body["total"] == 1
        assert body["items"][0]["ticker"] == "TSLA"


class TestStockHistory:
    def test_history_returns_points_for_known_ticker(self, client: TestClient, db_session: Session):
        seed_stock_data(db_session)

        resp = client.get("/stocks/AAPL/history")
        assert resp.status_code == 200
        body = resp.json()

        assert body["ticker"] == "AAPL"
        assert body["total"] == 3
        assert len(body["items"]) == 3
        assert body["items"][0]["date"] == "2024-01-01"
        assert body["items"][-1]["date"] == "2024-01-03"

    def test_history_unknown_ticker_returns_404(self, client: TestClient):
        resp = client.get("/stocks/ZZZZ/history")
        assert resp.status_code == 404

    def test_history_rejects_invalid_date_range(self, client: TestClient, db_session: Session):
        seed_stock_data(db_session)

        resp = client.get("/stocks/AAPL/history?start_date=2024-01-10&end_date=2024-01-01")
        assert resp.status_code == 422

    def test_history_supports_limit_and_offset(self, client: TestClient, db_session: Session):
        seed_stock_data(db_session)

        resp = client.get("/stocks/AAPL/history?limit=1&offset=1")
        assert resp.status_code == 200
        body = resp.json()

        assert body["total"] == 3
        assert len(body["items"]) == 1
        assert body["items"][0]["date"] == "2024-01-02"

    def test_history_supports_timeframe(self, client: TestClient, db_session: Session):
        seed_stock_data(db_session)

        resp = client.get("/stocks/MSFT/history?timeframe=1w")
        assert resp.status_code == 200
        body = resp.json()

        assert body["ticker"] == "MSFT"
        assert body["timeframe"] == "1w"
        assert body["start_date"] == "2024-01-03"
        assert body["end_date"] == "2024-01-10"
        assert len(body["items"]) == 1
        assert body["items"][0]["date"] == "2024-01-10"

    def test_history_rejects_timeframe_with_explicit_dates(self, client: TestClient, db_session: Session):
        seed_stock_data(db_session)

        resp = client.get("/stocks/AAPL/history?timeframe=1m&start_date=2024-01-01")
        assert resp.status_code == 422

    def test_history_returns_empty_items_for_ticker_without_prices(self, client: TestClient, db_session: Session):
        seed_stock_data(db_session)

        resp = client.get("/stocks/EMPTY/history")
        assert resp.status_code == 200
        body = resp.json()

        assert body["ticker"] == "EMPTY"
        assert body["total"] == 0
        assert body["items"] == []
