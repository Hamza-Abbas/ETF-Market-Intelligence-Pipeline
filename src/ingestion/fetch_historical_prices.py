import inspect
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
import yfinance as yf
from loguru import logger
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DateType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from src.utils.config_loader import load_yaml_config


def resolve_project_root() -> Path:
    """Locate the project root even when __file__ is not set.

    Databricks Python script tasks run from a Git source execute the
    file through exec() without setting __file__, so fall back to the
    compiled code object's filename in that case instead.
    """

    try:
        script_path = Path(__file__).resolve()
    except NameError:
        script_path = Path(inspect.getfile(inspect.currentframe())).resolve()

    return script_path.parents[2]


PROJECT_ROOT = resolve_project_root()

CONFIG_PATH = PROJECT_ROOT / "config" / "etf_symbols.yml"

# Git source checkouts in Databricks are read only, so anything this
# script writes locally has to live outside PROJECT_ROOT. /tmp is
# normal writable disk on the cluster node.
LOCAL_SCRATCH_DIR = Path("/tmp/etf_intelligence_pipeline")

BRONZE_DIR = (
    LOCAL_SCRATCH_DIR
    / "data"
    / "bronze"
    / "yahoo_finance"
)

LOG_DIR = LOCAL_SCRATCH_DIR / "logs"

BRONZE_CATALOG = "etf_market_intelligence"
BRONZE_SCHEMA = "bronze"
BRONZE_TABLE = "etf_prices_raw"

MERGE_COLUMNS = [
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

BRONZE_SCHEMA_STRUCT = StructType(
    [
        StructField("symbol", StringType(), False),
        StructField("price_date", DateType(), False),
        StructField("open", DoubleType(), False),
        StructField("high", DoubleType(), False),
        StructField("low", DoubleType(), False),
        StructField("close", DoubleType(), False),
        StructField("adjusted_close", DoubleType(), False),
        StructField("volume", LongType(), False),
        StructField("source_provider", StringType(), False),
        StructField("load_type", StringType(), False),
        StructField("batch_id", StringType(), False),
        StructField("ingested_at_utc", TimestampType(), False),
    ]
)


def setup_logger() -> None:
    """Store ingestion logs on the cluster's local scratch disk."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.add(LOG_DIR / "ingestion.log", rotation="1 MB", retention="7 days")


def normalize_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """yfinance can sometimes return MultiIndex columns. Standardize them."""

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    df = df.reset_index()

    df.columns = [
        str(col)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace(".", "")
        for col in df.columns
    ]

    return df


def fetch_symbol_history(
    symbol: str,
    start_date: str,
    batch_id: str,
    ingested_at_utc: str,
    source_provider: str,
) -> pd.DataFrame:
    """Fetch the full daily OHLCV history for one ETF symbol."""

    logger.info(f"Fetching historical data for {symbol} from {start_date}")

    df = yf.download(
        tickers=symbol,
        start=start_date,
        progress=False,
        auto_adjust=False,
    )

    if df.empty:
        logger.warning(f"No data returned for {symbol}")
        return pd.DataFrame()

    df = normalize_yfinance_columns(df)

    df = df.rename(
        columns={
            "date": "price_date",
            "adj_close": "adjusted_close",
        }
    )

    df["symbol"] = symbol
    df["source_provider"] = source_provider
    df["load_type"] = "historical"
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
        column for column in expected_columns if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing columns for {symbol}: {missing_columns}")

    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date

    df["volume"] = pd.to_numeric(df["volume"], errors="raise").astype("int64")

    return df[expected_columns]


def save_local_bronze_copy(df: pd.DataFrame, symbol: str) -> None:
    """Preserve the extracted history on the cluster's local disk.

    This is scratch space for debugging a single run, not a persistent
    audit trail: /tmp on an ephemeral job cluster does not survive past
    the run.
    """

    output_dir = BRONZE_DIR / f"symbol={symbol}" / "load_type=historical"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "prices.csv"
    df.to_csv(output_path, index=False)

    logger.success(f"Saved {len(df)} rows for {symbol} to {output_path}")


def merge_into_bronze(df: pd.DataFrame, spark: SparkSession) -> None:
    """Merge the full historical batch straight into the Bronze Delta table.

    Runs on the Databricks cluster's own Spark session, no external
    connection details needed. Safe to run at any time: it matches on
    symbol and price_date, so running it again never creates duplicates.
    That makes it usable as a backfill or recovery tool if the daily
    incremental job ever fails or misses a run.
    """

    target_table = f"{BRONZE_CATALOG}.{BRONZE_SCHEMA}.{BRONZE_TABLE}"

    typed_df = df[MERGE_COLUMNS].copy()
    typed_df["ingested_at_utc"] = pd.to_datetime(typed_df["ingested_at_utc"])

    spark_df = spark.createDataFrame(typed_df, schema=BRONZE_SCHEMA_STRUCT)
    spark_df.createOrReplaceTempView("historical_landing")

    logger.info(f"Merging {df.shape[0]} rows into {target_table}")

    spark.sql(
        f"""
        MERGE INTO {target_table} AS target
        USING historical_landing AS source
        ON target.symbol = source.symbol
           AND target.price_date = source.price_date
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
    )

    logger.success(f"Merged {df.shape[0]} rows into {target_table}")


def main() -> None:
    setup_logger()

    spark = SparkSession.builder.getOrCreate()

    config = load_yaml_config(CONFIG_PATH)

    symbols = config["symbols"]
    start_date = config["source"]["start_date"]
    source_provider = config["source"]["name"]

    batch_id = str(uuid4())
    ingested_at_utc = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )

    logger.info(f"Starting historical batch: {batch_id}")
    logger.info(f"Symbols: {len(symbols)}, start date: {start_date}")

    dataframes = []
    successful_symbols = []
    failed_symbols = []

    for symbol in symbols:
        try:
            symbol_df = fetch_symbol_history(
                symbol=symbol,
                start_date=start_date,
                batch_id=batch_id,
                ingested_at_utc=ingested_at_utc,
                source_provider=source_provider,
            )

            if symbol_df.empty:
                failed_symbols.append(symbol)
                continue

            save_local_bronze_copy(df=symbol_df, symbol=symbol)
            dataframes.append(symbol_df)
            successful_symbols.append(symbol)

        except Exception as error:
            logger.exception(f"Failed to process {symbol}: {error}")
            failed_symbols.append(symbol)

    if not dataframes:
        raise RuntimeError("No historical data was fetched for any symbol.")

    combined_df = pd.concat(dataframes, ignore_index=True)

    duplicate_count = combined_df.duplicated(
        subset=["symbol", "price_date"]
    ).sum()

    if duplicate_count > 0:
        raise ValueError(
            f"Historical batch contains {duplicate_count} duplicate keys"
        )

    merge_into_bronze(combined_df, spark)

    print("\nHistorical batch merged into Bronze successfully")
    print(f"Batch ID: {batch_id}")
    print(f"Rows: {len(combined_df)}")
    print(f"Successful symbols ({len(successful_symbols)}): {successful_symbols}")
    print(f"Failed symbols ({len(failed_symbols)}): {failed_symbols}")
    print(
        "Date range: "
        f"{combined_df['price_date'].min()} -> "
        f"{combined_df['price_date'].max()}"
    )
    print(f"Bronze table: {BRONZE_CATALOG}.{BRONZE_SCHEMA}.{BRONZE_TABLE}")


if __name__ == "__main__":
    main()