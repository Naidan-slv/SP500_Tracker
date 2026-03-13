from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.connection import engine
from app.database.models import Stock, StockPrice

CSV_PATH = Path("/Users/naidansalvador/CodingProjects/SP500_Tracker/data/processed/top_companies_20y_daily_clean.csv")
PRICE_CHUNK_SIZE = 5000


def chunk_rows(rows: list[dict], size: int):
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


def load_clean_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Clean CSV not found: {path}")

    df = pd.read_csv(path)
    required_columns = {"date", "ticker", "open", "high", "low", "close", "adj_close", "volume"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in clean CSV: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="raise").dt.date
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()

    numeric_columns = ["open", "high", "low", "close", "adj_close", "volume"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="raise")

    df["volume"] = df["volume"].round().astype("int64")

    duplicate_pairs = int(df.duplicated(subset=["ticker", "date"]).sum())
    if duplicate_pairs:
        raise ValueError(f"CSV has duplicate (ticker, date) rows: {duplicate_pairs}")

    return df


def upsert_stocks(connection, tickers: list[str]) -> int:
    stock_rows = [{"ticker": ticker, "company_name": None} for ticker in tickers]
    stmt = insert(Stock.__table__).values(stock_rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=["ticker"])
    connection.execute(stmt)
    return len(stock_rows)


def upsert_prices(connection, df: pd.DataFrame) -> int:
    total_rows = len(df)
    inserted_total = 0

    for index, start in enumerate(range(0, total_rows, PRICE_CHUNK_SIZE), start=1):
        batch_df = df.iloc[start : start + PRICE_CHUNK_SIZE]
        batch = batch_df.to_dict(orient="records")
        stmt = insert(StockPrice.__table__).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker", "date"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "adj_close": stmt.excluded.adj_close,
                "volume": stmt.excluded.volume,
            },
        )
        connection.execute(stmt)
        inserted_total += len(batch)
        print(f"Processed chunk {index}: {inserted_total:,}/{total_rows:,} rows")

    return inserted_total


def print_post_ingestion_summary(connection) -> None:
    stocks_count = connection.execute(text("SELECT COUNT(*) FROM stocks")).scalar_one()
    prices_count = connection.execute(text("SELECT COUNT(*) FROM stock_prices")).scalar_one()

    min_date, max_date = connection.execute(
        text("SELECT MIN(date), MAX(date) FROM stock_prices")
    ).one()

    print("\n=== Post-Ingestion Summary ===")
    print(f"stocks rows: {stocks_count:,}")
    print(f"stock_prices rows: {prices_count:,}")
    print(f"stock_prices date range: {min_date} -> {max_date}")


def main() -> None:
    print(f"Reading cleaned CSV from: {CSV_PATH}")
    df = load_clean_csv(CSV_PATH)

    unique_tickers = sorted(df["ticker"].unique().tolist())
    print(f"CSV rows: {len(df):,}")
    print(f"Unique tickers: {len(unique_tickers):,}")

    with engine.begin() as connection:
        stock_rows = upsert_stocks(connection, unique_tickers)
        print(f"Upserted stocks: {stock_rows:,}")

        price_rows = upsert_prices(connection, df)
        print(f"Upserted stock_prices rows (processed): {price_rows:,}")

        print_post_ingestion_summary(connection)


if __name__ == "__main__":
    main()
