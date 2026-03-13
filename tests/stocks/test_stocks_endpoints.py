from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import Stock, StockPrice
from app.api.routes import stocks as stocks_routes


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

    def test_list_stocks_search_uses_provider_symbol_fallback(
        self,
        client: TestClient,
        db_session: Session,
        monkeypatch,
    ):
        seed_stock_data(db_session)

        monkeypatch.setattr(stocks_routes, "_search_yahoo_tickers", lambda _search: ["MSFT"])
        async def fake_fetch_company_profile(_ticker: str):
            return None, None

        monkeypatch.setattr(stocks_routes, "_fetch_company_profile", fake_fetch_company_profile)

        resp = client.get("/stocks?search=windows-maker")
        assert resp.status_code == 200
        body = resp.json()

        assert body["total"] == 1
        assert body["items"][0]["ticker"] == "MSFT"

    def test_list_stocks_search_uses_company_override_when_names_missing(
        self,
        client: TestClient,
        db_session: Session,
    ):
        db_session.add(Stock(ticker="AAPL", company_name=None))
        db_session.commit()

        resp = client.get("/stocks?search=apple")
        assert resp.status_code == 200
        body = resp.json()

        assert body["total"] == 1
        assert body["items"][0]["ticker"] == "AAPL"
        assert body["items"][0]["company_name"] == "Apple Inc."


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


class TestStockNews:
    def test_news_unknown_ticker_returns_404(self, client: TestClient):
        resp = client.get("/stocks/ZZZZ/news")
        assert resp.status_code == 404

    def test_news_returns_filtered_items_for_timeframe(
        self,
        client: TestClient,
        db_session: Session,
        monkeypatch,
    ):
        seed_stock_data(db_session)
        stocks_routes._NEWS_CACHE.clear()

        now = datetime.now(timezone.utc)

        def fake_fetch_google_news_items(ticker: str, company_name: str | None, limit: int, timeframe_value: str = "1w"):
            return [
                stocks_routes.StockNewsItem(
                    title="Apple launches new AI features",
                    url="https://example.com/news/apple-ai",
                    source="Example News",
                    published_at=now - timedelta(days=2),
                ),
                stocks_routes.StockNewsItem(
                    title="Apple long-term retrospective",
                    url="https://example.com/news/apple-history",
                    source="Example News",
                    published_at=now - timedelta(days=45),
                ),
            ], None

        monkeypatch.setattr(stocks_routes, "_fetch_google_news_items", fake_fetch_google_news_items)

        resp = client.get("/stocks/AAPL/news?timeframe=1w&limit=10")
        assert resp.status_code == 200
        body = resp.json()

        assert body["ticker"] == "AAPL"
        assert body["company_name"] == "Apple Inc."
        assert body["timeframe"] == "1w"
        assert body["total"] == 1
        assert len(body["items"]) == 1
        assert body["items"][0]["title"] == "Apple launches new AI features"

    def test_news_includes_provider_error_when_source_unavailable(
        self,
        client: TestClient,
        db_session: Session,
        monkeypatch,
    ):
        seed_stock_data(db_session)
        stocks_routes._NEWS_CACHE.clear()

        def fake_fetch_google_news_items(ticker: str, company_name: str | None, limit: int, timeframe_value: str = "1w"):
            return [], "News provider unavailable"

        monkeypatch.setattr(stocks_routes, "_fetch_google_news_items", fake_fetch_google_news_items)

        resp = client.get("/stocks/AAPL/news?timeframe=1m&limit=5")
        assert resp.status_code == 200
        body = resp.json()

        assert body["provider"] == "google_news_rss"
        assert body["provider_error"] == "News provider unavailable"
        assert body["items"] == []


class TestStockLive:
    def test_live_unknown_ticker_returns_404(self, client: TestClient):
        stocks_routes._LIVE_CACHE.clear()
        resp = client.get("/stocks/ZZZZ/live")
        assert resp.status_code == 404

    def test_live_returns_intraday_points(
        self,
        client: TestClient,
        db_session: Session,
        monkeypatch,
    ):
        stocks_routes._LIVE_CACHE.clear()
        seed_stock_data(db_session)

        def fake_fetch_yahoo_live_points(ticker: str, data_range, interval):
            return [
                stocks_routes.StockLivePoint(
                    timestamp=datetime(2024, 1, 10, 14, 30, tzinfo=timezone.utc),
                    open=188.2,
                    high=189.4,
                    low=187.9,
                    close=189.1,
                    volume=120_000,
                ),
                stocks_routes.StockLivePoint(
                    timestamp=datetime(2024, 1, 10, 14, 35, tzinfo=timezone.utc),
                    open=189.1,
                    high=189.6,
                    low=188.9,
                    close=189.3,
                    volume=132_000,
                ),
            ], None

        monkeypatch.setattr(stocks_routes, "_fetch_yahoo_live_points", fake_fetch_yahoo_live_points)

        resp = client.get("/stocks/AAPL/live?range=1d&interval=5m")
        assert resp.status_code == 200
        body = resp.json()

        assert body["ticker"] == "AAPL"
        assert body["range"] == "1d"
        assert body["interval"] == "5m"
        assert body["provider"] == "yahoo_chart"
        assert body["total"] == 2
        assert body["latest_close"] == 189.3
        assert len(body["items"]) == 2

    def test_live_prefers_finnhub_when_available(
        self,
        client: TestClient,
        db_session: Session,
        monkeypatch,
    ):
        stocks_routes._LIVE_CACHE.clear()
        seed_stock_data(db_session)

        monkeypatch.setattr(stocks_routes, "_can_use_finnhub_live", lambda: True)

        def fake_fetch_finnhub_live_points(ticker: str, data_range, interval):
            return [
                stocks_routes.StockLivePoint(
                    timestamp=datetime(2024, 1, 10, 14, 30, tzinfo=timezone.utc),
                    open=188.2,
                    high=189.4,
                    low=187.9,
                    close=189.1,
                    volume=120_000,
                ),
            ], None

        monkeypatch.setattr(stocks_routes, "_fetch_finnhub_live_points", fake_fetch_finnhub_live_points)
        monkeypatch.setattr(stocks_routes, "_fetch_yahoo_live_points", lambda *_args, **_kwargs: ([], "should not be called"))

        resp = client.get("/stocks/AAPL/live?range=1d&interval=5m")
        assert resp.status_code == 200
        body = resp.json()

        assert body["provider"] == "finnhub_candle"
        assert body["total"] == 1
        assert body["latest_close"] == 189.1

    def test_live_includes_provider_error(
        self,
        client: TestClient,
        db_session: Session,
        monkeypatch,
    ):
        stocks_routes._LIVE_CACHE.clear()
        seed_stock_data(db_session)

        def fake_fetch_yahoo_live_points(ticker: str, data_range, interval):
            return [], "Live market provider unavailable"

        monkeypatch.setattr(stocks_routes, "_fetch_yahoo_live_points", fake_fetch_yahoo_live_points)

        resp = client.get("/stocks/AAPL/live?range=5d&interval=15m")
        assert resp.status_code == 200
        body = resp.json()

        assert body["range"] == "5d"
        assert body["interval"] == "15m"
        assert body["provider_error"] == "Live market provider unavailable"
        assert body["items"] == []
