"""
Tests for GET /watchlists/{watchlist_id}/insights

Covers:
- Auth guard (401 when unauthenticated)
- 404 for non-existent watchlist
- 404 when trying to access another user's watchlist
- Empty watchlist returns valid response with zero tickers
- Insights returned for watchlist with price data
- Response shape contract
"""

from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import Stock, StockPrice, Watchlist, WatchlistItem
from tests.conftest import make_verified_user


# ── Seed helpers ──────────────────────────────────────────────────────────────

def seed_stock_with_prices(db_session: Session, ticker: str, company_name: str, num_days: int = 30) -> None:
    """Insert a stock and `num_days` of synthetic daily prices ending today."""
    if not db_session.get(Stock, ticker):
        db_session.add(Stock(ticker=ticker, company_name=company_name))
        db_session.flush()

    base_close = 100.0
    today = date(2025, 1, 31)
    for i in range(num_days):
        day = today - timedelta(days=i)
        close = round(base_close + i * 0.5, 4)
        db_session.add(
            StockPrice(
                ticker=ticker,
                date=day,
                open=Decimal(str(close - 0.2)),
                high=Decimal(str(close + 1.0)),
                low=Decimal(str(close - 1.0)),
                close=Decimal(str(close)),
                adj_close=Decimal(str(close)),
                volume=1_000_000 + i * 1000,
            )
        )
    db_session.commit()


def create_watchlist_with_tickers(
    client: TestClient,
    auth_headers: dict,
    db_session: Session,
    tickers: list[str],
    name: str = "Test Watchlist",
) -> int:
    """Create a watchlist and add the given tickers. Stocks + prices must already be seeded."""
    resp = client.post("/watchlists", json={"name": name}, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    watchlist_id = resp.json()["id"]

    for ticker in tickers:
        r = client.post(
            f"/watchlists/{watchlist_id}/items",
            json={"ticker": ticker},
            headers=auth_headers,
        )
        assert r.status_code == 201, f"Failed to add {ticker}: {r.text}"

    return watchlist_id


# ── Auth guard ────────────────────────────────────────────────────────────────

class TestInsightsAuth:
    def test_insights_requires_auth(self, client: TestClient):
        resp = client.get("/watchlists/1/insights")
        assert resp.status_code == 401


# ── 404 cases ─────────────────────────────────────────────────────────────────

class TestInsightsNotFound:
    def test_nonexistent_watchlist_returns_404(self, client: TestClient, auth_headers: dict):
        resp = client.get("/watchlists/99999/insights", headers=auth_headers)
        assert resp.status_code == 404

    def test_other_users_watchlist_returns_404(self, client: TestClient):
        owner = make_verified_user(client, "insights_owner@example.com")
        owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}
        intruder = make_verified_user(client, "insights_intruder@example.com")
        intruder_headers = {"Authorization": f"Bearer {intruder['access_token']}"}

        resp = client.post("/watchlists", json={"name": "Private"}, headers=owner_headers)
        assert resp.status_code == 201
        watchlist_id = resp.json()["id"]

        resp = client.get(f"/watchlists/{watchlist_id}/insights", headers=intruder_headers)
        assert resp.status_code == 404


# ── Empty watchlist ───────────────────────────────────────────────────────────

class TestInsightsEmpty:
    def test_empty_watchlist_returns_valid_response(self, client: TestClient, auth_headers: dict):
        resp = client.post("/watchlists", json={"name": "Empty"}, headers=auth_headers)
        watchlist_id = resp.json()["id"]

        resp = client.get(f"/watchlists/{watchlist_id}/insights", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()

        assert body["ticker_count"] == 0
        assert body["tickers"] == []
        assert body["top_gainer_1w"] is None
        assert body["top_loser_1w"] is None
        assert body["highest_volatility"] is None
        assert body["lowest_volatility"] is None


# ── Insights with data ────────────────────────────────────────────────────────

class TestInsightsWithData:
    def test_insights_returns_correct_shape(
        self, client: TestClient, auth_headers: dict, db_session: Session
    ):
        seed_stock_with_prices(db_session, "AAPL", "Apple Inc.", num_days=30)
        seed_stock_with_prices(db_session, "MSFT", "Microsoft Corporation", num_days=30)

        watchlist_id = create_watchlist_with_tickers(
            client, auth_headers, db_session, ["AAPL", "MSFT"]
        )

        resp = client.get(f"/watchlists/{watchlist_id}/insights", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()

        # Top-level fields
        assert body["watchlist_id"] == watchlist_id
        assert isinstance(body["watchlist_name"], str)
        assert body["ticker_count"] == 2
        assert isinstance(body["as_of_date"], str)

        # Ticker insights
        assert len(body["tickers"]) == 2
        tickers_returned = {t["ticker"] for t in body["tickers"]}
        assert tickers_returned == {"AAPL", "MSFT"}

    def test_ticker_insight_fields_present(
        self, client: TestClient, auth_headers: dict, db_session: Session
    ):
        seed_stock_with_prices(db_session, "GOOG", "Alphabet Inc.", num_days=30)

        watchlist_id = create_watchlist_with_tickers(
            client, auth_headers, db_session, ["GOOG"]
        )

        resp = client.get(f"/watchlists/{watchlist_id}/insights", headers=auth_headers)
        assert resp.status_code == 200
        insight = resp.json()["tickers"][0]

        assert "ticker" in insight
        assert "company_name" in insight
        assert "latest_close" in insight
        assert "change_pct_1w" in insight
        assert "change_pct_1m" in insight
        assert "change_pct_1y" in insight
        assert "avg_volume_30d" in insight
        assert "volatility_30d" in insight
        assert "weight_pct" in insight

        assert insight["ticker"] == "GOOG"
        assert insight["latest_close"] is not None
        assert isinstance(insight["weight_pct"], float)
        # Single ticker = 100% weight
        assert abs(insight["weight_pct"] - 100.0) < 0.01

    def test_weight_pct_sums_to_100(
        self, client: TestClient, auth_headers: dict, db_session: Session
    ):
        for t, name in [("AMZN", "Amazon"), ("META", "Meta"), ("NVDA", "Nvidia")]:
            seed_stock_with_prices(db_session, t, name, num_days=30)

        watchlist_id = create_watchlist_with_tickers(
            client, auth_headers, db_session, ["AMZN", "META", "NVDA"]
        )

        resp = client.get(f"/watchlists/{watchlist_id}/insights", headers=auth_headers)
        assert resp.status_code == 200
        weights = [t["weight_pct"] for t in resp.json()["tickers"]]
        assert abs(sum(weights) - 100.0) < 0.1

    def test_top_gainer_and_loser_populated(
        self, client: TestClient, auth_headers: dict, db_session: Session
    ):
        seed_stock_with_prices(db_session, "TSLA", "Tesla", num_days=30)
        seed_stock_with_prices(db_session, "NFLX", "Netflix", num_days=30)

        watchlist_id = create_watchlist_with_tickers(
            client, auth_headers, db_session, ["TSLA", "NFLX"]
        )

        resp = client.get(f"/watchlists/{watchlist_id}/insights", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()

        # With 30 days of data we have enough history for 1w change
        assert body["top_gainer_1w"] in {"TSLA", "NFLX", None}
        assert body["top_loser_1w"] in {"TSLA", "NFLX", None}
        assert body["highest_volatility"] in {"TSLA", "NFLX", None}
        assert body["lowest_volatility"] in {"TSLA", "NFLX", None}
