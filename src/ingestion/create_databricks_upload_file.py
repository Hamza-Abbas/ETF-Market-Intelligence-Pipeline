from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_SOURCE_DIR = PROJECT_ROOT / "data" / "bronze" / "yahoo_finance"
UPLOAD_DIR = PROJECT_ROOT / "data" / "bronze" / "yahoo_finance_upload"


def main() -> None:
    files = sorted(
        BRONZE_SOURCE_DIR.glob("symbol=*/load_type=historical/prices.csv")
    )

    if not files:
        raise FileNotFoundError("No historical Bronze CSV files found.")

    dataframes = []

    for file in files:
        df = pd.read_csv(file)
        dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True)

    duplicate_count = combined_df.duplicated(
        subset=["symbol", "price_date"]
    ).sum()

    print(f"Combined rows: {len(combined_df)}")
    print(f"Symbols: {sorted(combined_df['symbol'].unique())}")
    print(f"Duplicate symbol + price_date rows: {duplicate_count}")
    print(f"Date range: {combined_df['price_date'].min()} -> {combined_df['price_date'].max()}")

    if duplicate_count > 0:
        raise ValueError("Duplicates found in combined upload file.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    output_path = UPLOAD_DIR / "etf_prices_historical.csv"
    combined_df.to_csv(output_path, index=False)

    print(f"Saved upload file to: {output_path}")


if __name__ == "__main__":
    main()