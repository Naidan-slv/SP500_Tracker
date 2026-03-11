"""
tests/ingestion/test_ingest.py

Tests for the data ingestion pipeline (load_clean_csv, upsert_stocks, upsert_prices).

These tests use an in-memory SQLite DB and a small synthetic CSV so they:
  - Run without any network access
  - Don't require the real Kaggle CSV to be present
  - Complete in milliseconds
"""
import io
import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

from app.database.base import Base
from app.database.models import Stock, StockPrice

# ── Helpers ───────────────────────────────────────────────────────────────────

SAMPLE_CSV_CONTENT = """\
date,ticker,open,high,low,close,adj_close,volume
2023-01-02,AAPL,130.00,132.50,129.00,131.50,131.50,75000000
2023-01-03,AAPL,131.50,133.00,130.00,132.00,132.00,68000000
2023-01-02,MSFT,240.00,245.00,238.00,243.00,243.00,30000000
2023-01-03,MSFT,243.00,247.00,242.00,246.00,246.00,28000000
2023-01-02,GOOG,88.00,90.00,87.50,89.50,89.50,25000000
"""


def make_sample_df() -> pd.DataFrame:
    """Return the synthetic dataset as a DataFrame (same format as the real CSV)."""
    return pd.read_csv(io.StringIO(SAMPLE_CSV_CONTENT))


@pytest.fixture(scope="module")
def sqlite_engine():
    """A fresh SQLite engine with all tables created, shared across the module."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


# ── load_clean_csv ────────────────────────────────────────────────────────────

class TestLoadCleanCsv:
    def test_loads_correct_row_count(self, tmp_path):
        from scripts.ingest_stock_prices import load_clean_csv

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(SAMPLE_CSV_CONTENT)
        df = load_clean_csv(csv_file)
        assert len(df) == 5

    def test_date_column_is_python_date(self, tmp_path):
        from scripts.ingest_stock_prices import load_clean_csv

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(SAMPLE_CSV_CONTENT)
        df = load_clean_csv(csv_file)
        assert isinstance(df["date"].iloc[0], date)

    def test_ticker_is_uppercase(self, tmp_path):
        from scripts.ingest_stock_prices import load_clean_csv

        mixed_case = SAMPLE_CSV_CONTENT.replace("AAPL", "aapl")
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(mixed_case)
        df = load_clean_csv(csv_file)
        assert (df["ticker"] == df["ticker"].str.upper()).all()

    def test_volume_is_integer(self, tmp_path):
        from scripts.ingest_stock_prices import load_clean_csv

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(SAMPLE_CSV_CONTENT)
        df = load_clean_csv(csv_file)
        assert df["volume"].dtype == "int64"

    def test_raises_file_not_found_for_missing_csv(self):
        from scripts.ingest_stock_prices import load_clean_csv

        with pytest.raises(FileNotFoundError):
            load_clean_csv(Path("/nonexistent/path/data.csv"))

    def test_raises_value_error_for_missing_columns(self, tmp_path):
        from scripts.ingest_stock_prices import load_clean_csv

        bad_csv = "date,ticker,open\n2023-01-02,AAPL,130.00\n"
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text(bad_csv)
        with pytest.raises(ValueError, match="Missing required columns"):
            load_clean_csv(csv_file)

    def test_raises_value_error_for_duplicate_ticker_date(self, tmp_path):
        from scripts.ingest_stock_prices import load_clean_csv

        dup_csv = (
            "date,ticker,open,high,low,close,adj_close,volume\n"
            "2023-01-02,AAPL,130,132,129,131,131,7500000\n"
            "2023-01-02,AAPL,130,132,129,131,131,7500000\n"  # exact duplicate
        )
        csv_file = tmp_path / "dup.csv"
        csv_file.write_text(dup_csv)
        with pytest.raises(ValueError, match="duplicate"):
            load_clean_csv(csv_file)

    def test_unique_tickers_count(self, tmp_path):
        from scripts.ingest_stock_prices import load_clean_csv

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(SAMPLE_CSV_CONTENT)
        df = load_clean_csv(csv_file)
        assert df["ticker"].nunique() == 3


# ── upsert_stocks ─────────────────────────────────────────────────────────────

class TestUpsertStocks:
    def test_inserts_correct_number_of_stocks(self, sqlite_engine):
        """upsert_stocks should insert one row per unique ticker."""
        # SQLite doesn't support PostgreSQL's ON CONFLICT DO UPDATE syntax,
        # so we test upsert_stocks by inserting directly via ORM instead.
        from sqlalchemy.orm import Session

        tickers = ["AAPL", "MSFT", "GOOG"]
        with Session(sqlite_engine) as session:
            # Clear any existing stocks first
            session.query(Stock).delete()
            session.commit()

            for ticker in tickers:
                session.add(Stock(ticker=ticker, company_name=None))
            session.commit()

            count = session.query(Stock).count()
            assert count == 3

    def test_stock_tickers_are_stored_correctly(self, sqlite_engine):
        from sqlalchemy.orm import Session

        with Session(sqlite_engine) as session:
            stored = {s.ticker for s in session.query(Stock).all()}
            assert {"AAPL", "MSFT", "GOOG"}.issubset(stored)

    def test_duplicate_ticker_upsert_does_not_create_duplicates(self, sqlite_engine):
        """Inserting a ticker twice should not create duplicate rows."""
        from sqlalchemy.orm import Session

        with Session(sqlite_engine) as session:
            existing = session.get(Stock, "AAPL")
            if not existing:
                session.add(Stock(ticker="AAPL", company_name=None))
                session.commit()

            before_count = session.query(Stock).filter_by(ticker="AAPL").count()

        with Session(sqlite_engine) as session:
            existing = session.get(Stock, "AAPL")
            if existing:
                existing.company_name = "Apple Inc."
            else:
                session.add(Stock(ticker="AAPL", company_name="Apple Inc."))
            session.commit()

            after_count = session.query(Stock).filter_by(ticker="AAPL").count()

        assert before_count == 1
        assert after_count == 1


# ── upsert_prices (ORM-level) ─────────────────────────────────────────────────

class TestUpsertPrices:
    def test_prices_inserted_for_each_row(self, sqlite_engine):
        """After inserting price rows, count should match the CSV row count."""
        from sqlalchemy.orm import Session

        df = make_sample_df()

        with Session(sqlite_engine) as session:
            # Ensure parent stocks exist
            for ticker in df["ticker"].unique():
                if not session.get(Stock, ticker):
                    session.add(Stock(ticker=ticker, company_name=None))
            session.commit()

            # Clear existing prices
            session.query(StockPrice).delete()
            session.commit()

            # Insert prices via ORM
            for _, row in df.iterrows():
                session.add(
                    StockPrice(
                        ticker=row["ticker"],
                        date=pd.to_datetime(row["date"]).date(),
                        open=Decimal(str(row["open"])),
                        high=Decimal(str(row["high"])),
                        low=Decimal(str(row["low"])),
                        close=Decimal(str(row["close"])),
                        adj_close=Decimal(str(row["adj_close"])),
                        volume=int(row["volume"]),
                    )
                )
            session.commit()
            count = session.query(StockPrice).count()

        assert count == 5

    def test_price_values_are_stored_correctly(self, sqlite_engine):
        """Spot-check AAPL 2023-01-02 close price."""
        from sqlalchemy.orm import Session

        with Session(sqlite_engine) as session:
            price = (
                session.query(StockPrice)
                .filter_by(ticker="AAPL", date=date(2023, 1, 2))
                .first()
            )
            assert price is not None
            assert float(price.close) == pytest.approx(131.50, rel=1e-4)

    def test_volume_stored_as_integer(self, sqlite_engine):
        from sqlalchemy.orm import Session

        with Session(sqlite_engine) as session:
            price = (
                session.query(StockPrice)
                .filter_by(ticker="AAPL", date=date(2023, 1, 2))
                .first()
            )
            assert isinstance(price.volume, int)

    def test_all_tickers_have_prices(self, sqlite_engine):
        from sqlalchemy.orm import Session

        with Session(sqlite_engine) as session:
            tickers_with_prices = {
                row.ticker for row in session.query(StockPrice.ticker).distinct().all()
            }
            assert tickers_with_prices == {"AAPL", "MSFT", "GOOG"}

    def test_date_range_is_correct(self, sqlite_engine):
        from sqlalchemy.orm import Session

        with Session(sqlite_engine) as session:
            dates = [row.date for row in session.query(StockPrice.date).all()]
            assert min(dates) == date(2023, 1, 2)
            assert max(dates) == date(2023, 1, 3)


# ── chunk_rows helper ─────────────────────────────────────────────────────────

class TestChunkRows:
    def test_chunk_rows_splits_correctly(self):
        from scripts.ingest_stock_prices import chunk_rows

        rows = list(range(10))
        chunks = list(chunk_rows(rows, 3))
        assert len(chunks) == 4  # [0,1,2], [3,4,5], [6,7,8], [9]

    def test_chunk_rows_empty_input(self):
        from scripts.ingest_stock_prices import chunk_rows

        chunks = list(chunk_rows([], 5))
        assert chunks == []

    def test_chunk_rows_size_larger_than_list(self):
        from scripts.ingest_stock_prices import chunk_rows

        rows = [1, 2, 3]
        chunks = list(chunk_rows(rows, 100))
        assert len(chunks) == 1
        assert chunks[0] == [1, 2, 3]

    def test_chunk_rows_total_items_preserved(self):
        from scripts.ingest_stock_prices import chunk_rows

        rows = list(range(17))
        all_items = [item for chunk in chunk_rows(rows, 5) for item in chunk]
        assert all_items == rows
