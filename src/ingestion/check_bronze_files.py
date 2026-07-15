from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze" / "yahoo_finance"


def main() -> None:
    files = list(BRONZE_DIR.glob("symbol=*/load_type=historical/prices.csv"))

    if not files:
        raise FileNotFoundError("No Bronze CSV files found.")

    for file in sorted(files):
        df = pd.read_csv(file)

        symbol = df["symbol"].iloc[0]
        row_count = len(df)
        min_date = df["price_date"].min()
        max_date = df["price_date"].max()

        duplicate_count = df.duplicated(subset=["symbol", "price_date"]).sum()

        print(
            f"{symbol}: {row_count} rows | "
            f"{min_date} -> {max_date} | "
            f"duplicates: {duplicate_count}"
        )


if __name__ == "__main__":
    main()