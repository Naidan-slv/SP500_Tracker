from pathlib import Path

import kagglehub
import pandas as pd


def main() -> None:
    dataset_ref = "ibrahimshahrukh/top-50-companies-dataset"
    print(f"Downloading dataset: {dataset_ref}")
    dataset_path = Path(kagglehub.dataset_download(dataset_ref))
    print(f"Local dataset path: {dataset_path}")

    files = sorted([p for p in dataset_path.rglob("*") if p.is_file()])
    if not files:
        raise RuntimeError("No files found in downloaded dataset folder.")

    print("\nFiles found:")
    for file_path in files:
        print(f"- {file_path.name}")

    csv_files = [p for p in files if p.suffix.lower() == ".csv"]
    if not csv_files:
        raise RuntimeError("No CSV files found in dataset.")

    target_csv = csv_files[0]
    print(f"\nPreviewing CSV: {target_csv.name}")

    df = pd.read_csv(target_csv)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {list(df.columns)}")

    print("\nFirst 5 rows:")
    print(df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
