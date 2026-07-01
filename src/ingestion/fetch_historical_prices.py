from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
import yfinance as yf
from loguru import logger

from src.utils.config_loader import load_yaml_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "etf_symbols.yml"
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze" / "yahoo_finance"
LOG_DIR = PROJECT_ROOT / "logs"


def setup_logger() -> None:
    """
    Store ingestion logs in logs/ingestion.log.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.add(LOG_DIR / "ingestion.log", rotation="1 MB", retention="7 days")


def normalize_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    yfinance can sometimes return MultiIndex columns.
    This function standardizes column names.
    """
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


def fetch_symbol_history(symbol: str, start_date: str, batch_id: str) -> pd.DataFrame:
    """
    Fetch historical daily OHLCV prices for one ETF symbol.
    """
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
    df["source_provider"] = "yahoo_finance"
    df["load_type"] = "historical"
    df["batch_id"] = batch_id
    df["ingested_at_utc"] = datetime.now(timezone.utc).isoformat()

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

    missing_columns = [col for col in expected_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing columns for {symbol}: {missing_columns}")

    return df[expected_columns]


def save_to_bronze(df: pd.DataFrame, symbol: str) -> None:
    """
    Save ETF data to the local Bronze layer as CSV.

    Bronze rule:
    - Keep the data close to source format.
    - Add ingestion metadata.
    - Do not calculate business metrics here.
    """
    output_dir = BRONZE_DIR / f"symbol={symbol}" / "load_type=historical"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "prices.csv"

    df.to_csv(output_path, index=False)

    logger.success(f"Saved {len(df)} rows for {symbol} to {output_path}")


def main() -> None:
    setup_logger()

    config = load_yaml_config(CONFIG_PATH)

    symbols = config["symbols"]
    start_date = config["source"]["start_date"]
    batch_id = str(uuid4())

    logger.info(f"Starting historical ingestion batch_id={batch_id}")
    logger.info(f"ETF symbols: {symbols}")

    successful_symbols = []
    failed_symbols = []

    for symbol in symbols:
        try:
            df = fetch_symbol_history(
                symbol=symbol,
                start_date=start_date,
                batch_id=batch_id,
            )

            if not df.empty:
                save_to_bronze(df=df, symbol=symbol)
                successful_symbols.append(symbol)
            else:
                failed_symbols.append(symbol)

        except Exception as error:
            logger.exception(f"Failed to process {symbol}: {error}")
            failed_symbols.append(symbol)

    logger.info(f"Successful symbols: {successful_symbols}")
    logger.info(f"Failed symbols: {failed_symbols}")
    logger.success("Historical ingestion finished")


if __name__ == "__main__":
    main()