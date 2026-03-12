"""
Tests for GET /stocks/{ticker} (stock detail / summary card)

Covers:
- 404 for unknown ticker
- Response shape contract
- Correct field types and values
- Case-insensitive ticker normalisation
"""

from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import Stock, StockPrice


# ── Seed helpers ──────────────────────────────────────────────────────────────

def seed_stock_with_prices(
    db_session: Session,
    ticker: str,
    company_name: str,
    num_days: int = 30,
) -> None:
    """Insert a stock and `num_days` of ascending daily close prices."""
    if not db_session.get(Stock, ticker):
        db_session.add(Stock(ticker=ticker, company_name=company_name))
        db_session.flush()

    base_close = 150.0
    today = date(2025, 6, 30)
    for i in range(num_days):
        day = today - timedelta(days=i)
        close = round(base_close + i * 1.0, 4)
        db_session.add(
            StockPrice(
                ticker=ticker,
                date=day,
                open=Decimal(str(close - 0.5)),
                high=Decimal(str(close + 2.0)),
                low=Decimal(str(close - 2.0)),
                close=Decimal(str(close)),
                adj_close=Decimal(str(close)),
                volume=5_000_000 + i * 1000,
            )
        )
    db_session.commit()


# ── Not found ─────────────────────────────────────────────────────────────────

class TestStockDetailNotFound:
    def test_unknown_ticker_returns_404(self, client: TestClient):
        resp = client.get("/stocks/ZZZZ")
        assert resp.status_code == 404

    def test_404_detail_message_contains_ticker(self, client: TestClient):
        resp = client.get("/stocks/FAKECO")
        assert resp.status_code == 404
        assert "FAKECO" in resp.json()["detail"]


# ── Response shape ────────────────────────────────────────────────────────────

class TestStockDetailShape:
    def test_response_contains_all_expected_fields(
        self, client: TestClient, db_session: Session
    ):
        seed_stock_with_prices(db_session, "DETL", "Detail Corp", num_days=30)

        resp = client.get("/stocks/DETL")
        assert resp.status_code == 200
        body = resp.json()

        required_fields = {
            "ticker",
            "company_name",
            "latest_date",
            "latest_close",
            "latest_open",
            "latest_volume",
            "change_pct_1d",
            "change_pct_1w",
            "change_pct_1m",
            "change_pct_1y",
            "week_52_high",
            "week_52_low",
            "avg_volume_30d",
        }
        assert required_fields.issubset(body.keys())

    def test_ticker_normalised_to_uppercase(self, client: TestClient, db_session: Session):
        seed_stock_with_prices(db_session, "NORM", "Normalise Corp", num_days=10)

        resp = client.get("/stocks/norm")
        assert resp.status_code == 200
        assert resp.json()["ticker"] == "NORM"


# ── Field values ──────────────────────────────────────────────────────────────

class TestStockDetailValues:
    def test_latest_close_is_numeric(self, client: TestClient, db_session: Session):
        seed_stock_with_prices(db_session, "VAL1", "Values Co", num_days=30)

        resp = client.get("/stocks/VAL1")
        assert resp.status_code == 200
        body = resp.json()

        assert isinstance(body["latest_close"], float)
        assert body["latest_close"] > 0

    def test_52_week_high_geq_low(self, client: TestClient, db_session: Session):
        seed_stock_with_prices(db_session, "HL52", "52W HL Corp", num_days=60)

        resp = client.get("/stocks/HL52")
        assert resp.status_code == 200
        body = resp.json()

        assert body["week_52_high"] is not None
        assert body["week_52_low"] is not None
        assert body["week_52_high"] >= body["week_52_low"]

    def test_avg_volume_30d_is_positive(self, client: TestClient, db_session: Session):
        seed_stock_with_prices(db_session, "VOL2", "Volume Corp", num_days=30)

        resp = client.get("/stocks/VOL2")
        assert resp.status_code == 200
        assert resp.json()["avg_volume_30d"] > 0

    def test_no_price_data_returns_nulls(self, client: TestClient, db_session: Session):
        """A ticker with no price rows should return 200 with null numeric fields."""
        if not db_session.get(Stock, "EMPTY"):
            db_session.add(Stock(ticker="EMPTY", company_name="Empty Corp"))
            db_session.commit()

        resp = client.get("/stocks/EMPTY")
        assert resp.status_code == 200
        body = resp.json()

        assert body["ticker"] == "EMPTY"
        assert body["latest_close"] is None
        assert body["week_52_high"] is None
        assert body["week_52_low"] is None

    def test_1d_change_pct_is_float_or_null(self, client: TestClient, db_session: Session):
        seed_stock_with_prices(db_session, "CHG1", "Change Corp", num_days=5)

        resp = client.get("/stocks/CHG1")
        assert resp.status_code == 200
        body = resp.json()

        val = body["change_pct_1d"]
        assert val is None or isinstance(val, float)

    def test_1y_change_pct_null_when_insufficient_history(
        self, client: TestClient, db_session: Session
    ):
        """With only 30 days of data there is no 1-year comparison price."""
        seed_stock_with_prices(db_session, "HIST", "History Corp", num_days=30)

        resp = client.get("/stocks/HIST")
        assert resp.status_code == 200
        assert resp.json()["change_pct_1y"] is None
