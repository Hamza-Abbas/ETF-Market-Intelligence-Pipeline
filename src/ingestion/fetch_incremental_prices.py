from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
import yfinance as yf
from loguru import logger

from src.utils.config_loader import load_yaml_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = PROJECT_ROOT / "config" / "etf_symbols.yml"

BRONZE_DIR = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "yahoo_finance"
)

LANDING_SEED_PATH = (
    PROJECT_ROOT
    / "etf_intelligence_pipeline"
    / "seeds"
    / "etf_prices_incremental.csv"
)

LOG_DIR = PROJECT_ROOT / "logs"


def setup_logger() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger.add(
        LOG_DIR / "ingestion.log",
        rotation="1 MB",
        retention="7 days",
    )


def normalize_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize the columns returned by yfinance."""

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [column[0] for column in df.columns]

    df = df.reset_index()

    df.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace(".", "")
        for column in df.columns
    ]

    return df


def fetch_latest_price(
    symbol: str,
    batch_id: str,
    ingested_at_utc: str,
    source_provider: str,
) -> pd.DataFrame:
    """Fetch only the newest available daily price for one ETF."""

    logger.info(f"Fetching latest daily price for {symbol}")

    df = yf.download(
        tickers=symbol,
        period="1d",
        interval="1d",
        progress=False,
        auto_adjust=False,
        threads=False,
    )

    if df.empty:
        raise ValueError(f"No daily data returned for {symbol}")

    df = normalize_yfinance_columns(df)

    df = df.rename(
        columns={
            "date": "price_date",
            "adj_close": "adjusted_close",
        }
    )

    # Defensive step: keep exactly the newest record.
    df = df.tail(1).copy()

    df["symbol"] = symbol
    df["source_provider"] = source_provider
    df["load_type"] = "incremental"
    df["batch_id"] = batch_id
    df["ingested_at_utc"] = ingested_at_utc

    expected_columns = [
        "symbol",
        "price_date",
        "open",
        "high",
        "low",
        "close",
        "adjusted_close",
        "volume",
        "source_provider",
        "load_type",
        "batch_id",
        "ingested_at_utc",
    ]

    missing_columns = [
        column
        for column in expected_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns for {symbol}: {missing_columns}"
        )

    df["price_date"] = pd.to_datetime(
        df["price_date"]
    ).dt.date

    required_columns = [
        "price_date",
        "open",
        "high",
        "low",
        "close",
        "adjusted_close",
        "volume",
    ]

    if df[required_columns].isnull().any().any():
        raise ValueError(
            f"Null values found in the latest record for {symbol}"
        )

    df["volume"] = pd.to_numeric(
        df["volume"],
        errors="raise",
    ).astype("int64")

    return df[expected_columns]


def save_local_bronze_copy(
    df: pd.DataFrame,
    symbol: str,
) -> None:
    """Preserve the extracted daily record locally."""

    price_date = str(df["price_date"].iloc[0])

    output_directory = (
        BRONZE_DIR
        / f"symbol={symbol}"
        / "load_type=incremental"
        / f"price_date={price_date}"
    )

    output_directory.mkdir(parents=True, exist_ok=True)

    output_path = output_directory / "prices.csv"
    df.to_csv(output_path, index=False)

    logger.success(f"Saved {symbol} daily record to {output_path}")


def main() -> None:
    setup_logger()

    config = load_yaml_config(CONFIG_PATH)

    symbols = config["symbols"]
    source_provider = config["source"]["name"]

    batch_id = str(uuid4())

    ingested_at_utc = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )

    logger.info(f"Starting incremental batch: {batch_id}")
    logger.info(f"Expected symbols: {len(symbols)}")

    dataframes = []
    failed_symbols = []

    for symbol in symbols:
        try:
            symbol_df = fetch_latest_price(
                symbol=symbol,
                batch_id=batch_id,
                ingested_at_utc=ingested_at_utc,
                source_provider=source_provider,
            )

            save_local_bronze_copy(
                df=symbol_df,
                symbol=symbol,
            )

            dataframes.append(symbol_df)

        except Exception as error:
            logger.exception(
                f"Latest-day extraction failed for {symbol}: {error}"
            )
            failed_symbols.append(symbol)

    if failed_symbols:
        raise RuntimeError(
            "The landing seed was not updated because these symbols "
            f"failed: {failed_symbols}"
        )

    combined_df = pd.concat(
        dataframes,
        ignore_index=True,
    )

    duplicate_count = combined_df.duplicated(
        subset=["symbol", "price_date"]
    ).sum()

    if duplicate_count > 0:
        raise ValueError(
            f"Landing batch contains {duplicate_count} duplicate keys"
        )

    if combined_df["symbol"].nunique() != len(symbols):
        raise ValueError(
            "The landing batch does not contain every configured ETF"
        )

    combined_df = combined_df.sort_values(
        ["symbol", "price_date"]
    )

    LANDING_SEED_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined_df.to_csv(
        LANDING_SEED_PATH,
        index=False,
    )

    print("\nLatest-day landing batch created successfully")
    print(f"Batch ID: {batch_id}")
    print(f"Rows: {len(combined_df)}")
    print(f"Symbols: {combined_df['symbol'].nunique()}")
    print(
        "Date range: "
        f"{combined_df['price_date'].min()} -> "
        f"{combined_df['price_date'].max()}"
    )
    print(f"Duplicate business keys: {duplicate_count}")
    print(f"Landing seed: {LANDING_SEED_PATH}")


if __name__ == "__main__":
    main()