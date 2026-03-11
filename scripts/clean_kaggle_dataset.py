from pathlib import Path

import kagglehub
import pandas as pd

REQUIRED_COLUMNS = ["Date", "Ticker", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
RENAME_MAP = {
    "Date": "date",
    "Ticker": "ticker",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
    "Volume": "volume",
}


def load_latest_csv(dataset_ref: str) -> Path:
    dataset_path = Path(kagglehub.dataset_download(dataset_ref))
    csv_files = sorted([p for p in dataset_path.rglob("*.csv") if p.is_file()])
    if not csv_files:
        raise RuntimeError("No CSV files found in Kaggle dataset download.")
    return csv_files[0]


def validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def cleanse(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    report: dict[str, int | str | float] = {}

    report["input_rows"] = len(df)
    validate_columns(df)

    df = df[REQUIRED_COLUMNS].copy()
    df = df.rename(columns=RENAME_MAP)

    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    invalid_date_rows = int(df["date"].isna().sum())
    if invalid_date_rows:
        df = df.dropna(subset=["date"])

    numeric_cols = ["open", "high", "low", "close", "adj_close", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    null_close_rows = int(df["close"].isna().sum())
    if null_close_rows:
        df = df.dropna(subset=["close"])

    duplicate_key_rows = int(df.duplicated(subset=["ticker", "date"]).sum())
    if duplicate_key_rows:
        df = df.drop_duplicates(subset=["ticker", "date"], keep="last")

    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    df["date"] = df["date"].dt.date

    report["invalid_date_rows_dropped"] = invalid_date_rows
    report["null_close_rows_dropped"] = null_close_rows
    report["duplicate_ticker_date_rows_dropped"] = duplicate_key_rows
    report["output_rows"] = len(df)
    report["unique_tickers"] = int(df["ticker"].nunique())
    report["date_min"] = str(df["date"].min())
    report["date_max"] = str(df["date"].max())

    return df, report


def print_quality_report(report: dict) -> None:
    print("\n=== Data Quality Report ===")
    print(f"Input rows: {report['input_rows']:,}")
    print(f"Invalid date rows dropped: {report['invalid_date_rows_dropped']:,}")
    print(f"Null close rows dropped: {report['null_close_rows_dropped']:,}")
    print(f"Duplicate (ticker,date) rows dropped: {report['duplicate_ticker_date_rows_dropped']:,}")
    print(f"Output rows: {report['output_rows']:,}")
    print(f"Unique tickers: {report['unique_tickers']:,}")
    print(f"Date range: {report['date_min']} -> {report['date_max']}")


def main() -> None:
    dataset_ref = "ibrahimshahrukh/top-50-companies-dataset"
    source_csv = load_latest_csv(dataset_ref)

    print(f"Source CSV: {source_csv}")
    raw_df = pd.read_csv(source_csv)
    clean_df, report = cleanse(raw_df)

    output_dir = Path("/Users/naidansalvador/CodingProjects/SP500_Tracker/data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "top_companies_20y_daily_clean.csv"

    clean_df.to_csv(output_csv, index=False)

    print_quality_report(report)
    print(f"\nCleaned CSV written to: {output_csv}")
    print("\nSample cleaned rows:")
    print(clean_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
