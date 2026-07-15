# ETF Market Intelligence Pipeline

This is a Data Engineering portfolio project that ingests ETF market data, loads it into Databricks, and transforms it through Bronze, Silver, and Gold layers using dbt.

The project currently focuses on building a reliable batch pipeline for ETF price analytics using the Medallion Architecture.

---

## Current Project Status

Completed:

- Historical ETF data ingestion from Yahoo Finance using Python
- Local Bronze CSV file generation
- Combined upload file creation for Databricks
- Bronze table loading in Databricks using dbt seed
- Silver cleaned model using dbt
- Gold analytical marts using dbt
- dbt tests for Silver and Gold models
- Data refreshed to the latest available trading date
- ETF universe expanded from 8 ETFs to 20 global USD-listed ETFs
- Project pushed to GitHub on the `main` branch

Next:

- Build Streamlit dashboard from Gold tables
- Add daily incremental ingestion
- Add AWS-based automation and alerts later

---

## Tech Stack

- Python
- yfinance
- pandas
- CSV files
- Databricks
- dbt Core
- dbt-databricks
- Medallion Architecture
- Git / GitHub

---

## ETF Universe

The project currently tracks 20 USD-listed ETFs:

```text
VOO
SPY
QQQ
VGT
VT
VXUS
BND
GLD
VEA
VWO
BNDX
ACWI
EFA
IEMG
EWJ
MCHI
INDA
EWG
EWU
EWZ
```

The ETF symbols are stored in:

```text
config/etf_symbols.yml
```

ETF metadata is stored in:

```text
config/etf_metadata.yml
```

---

## Project Structure

```text
daily_etf_market_intelligence_pipeline/
│
├── config/
│   ├── etf_symbols.yml
│   └── etf_metadata.yml
│
├── data/
│   └── bronze/
│
├── src/
│   ├── ingestion/
│   │   ├── fetch_historical_prices.py
│   │   ├── check_bronze_files.py
│   │   └── create_databricks_upload_file.py
│   │
│   └── utils/
│       └── config_loader.py
│
├── etf_intelligence_pipeline/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── bronze/
│   │   ├── silver/
│   │   └── gold/
│   ├── seeds/
│   └── tests/
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Pipeline Flow

```text
Yahoo Finance
    ↓
Python ingestion scripts
    ↓
Local Bronze CSV files
    ↓
Combined upload CSV
    ↓
dbt seed into Databricks Bronze
    ↓
dbt Silver model
    ↓
dbt Gold marts
```

