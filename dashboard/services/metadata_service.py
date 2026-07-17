from pathlib import Path

import pandas as pd
import streamlit as st
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_PATH = PROJECT_ROOT / "config" / "etf_metadata.yml"


@st.cache_data(show_spinner=False)
def load_etf_metadata() -> pd.DataFrame:
    """
    Load ETF reference data used to convert ticker symbols into
    business-friendly names and classifications.
    """
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"ETF metadata file was not found: {METADATA_PATH}"
        )

    with METADATA_PATH.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    records = config.get("etfs", [])

    if not records:
        raise ValueError("No ETF records were found in etf_metadata.yml.")

    metadata = pd.DataFrame(records)

    required_columns = {
        "symbol",
        "name",
        "asset_class",
        "region",
        "category",
    }

    missing_columns = required_columns.difference(metadata.columns)

    if missing_columns:
        raise ValueError(
            "ETF metadata is missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    metadata["symbol"] = (
        metadata["symbol"].astype(str).str.strip().str.upper()
    )

    if metadata["symbol"].duplicated().any():
        duplicated_symbols = (
            metadata.loc[
                metadata["symbol"].duplicated(keep=False),
                "symbol",
            ]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            "Duplicate ETF metadata symbols found: "
            + ", ".join(duplicated_symbols)
        )

    metadata["etf_label"] = (
        metadata["name"] + " (" + metadata["symbol"] + ")"
    )

    return metadata.sort_values("symbol").reset_index(drop=True)
