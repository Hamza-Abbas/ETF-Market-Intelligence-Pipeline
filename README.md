# ETF Market Intelligence Pipeline

> **Project status: In progress**
>
> The historical batch pipeline, Databricks Medallion layers, dbt models/tests, and Streamlit dashboard are working. Daily incremental ingestion, orchestration, alert delivery, and public deployment are still under development.

A Data Engineering portfolio project that collects ETF market data from Yahoo Finance, processes it through Bronze, Silver, and Gold layers in Databricks using dbt, and serves analytics through an interactive Streamlit dashboard.

The project currently tracks **20 USD-listed ETFs** across US, global, international, emerging-market, bond, technology, and commodity exposures.

---

## Current Progress

| Component | Status |
|---|---|
| Historical ETF ingestion with Python and `yfinance` | Complete |
| Local partitioned Bronze CSV files | Complete |
| Combined historical upload file | Complete |
| Databricks Bronze table | Complete |
| dbt Silver cleaning and daily return calculations | Complete |
| dbt Gold analytical marts | Complete |
| dbt data-quality tests | Complete |
| ETF universe expanded to 20 ETFs | Complete |
| Streamlit dashboard connected directly to Databricks Gold | Complete |
| ETF metadata and business-friendly names | Complete |
| Daily incremental ingestion | **Planned** |
| Databricks Bronze `MERGE` / upsert process | **Planned** |
| Scheduled pipeline execution | **Planned** |
| AWS EventBridge and Lambda automation | **Planned** |
| AWS SNS alert delivery | **Planned** |
| Public dashboard deployment | **Planned** |

---

## Architecture

### Current working architecture

```text
Yahoo Finance
      ↓
Python historical ingestion
      ↓
Local Bronze CSV files
      ↓
Combined dbt seed file
      ↓
Databricks Bronze
      ↓
dbt Silver
      ↓
dbt Gold marts
      ↓
Databricks SQL Warehouse
      ↓
Streamlit + Plotly dashboard
```

### Target architecture

```text
Yahoo Finance
      ↓
Daily incremental Python ingestion
      ↓
Databricks Bronze MERGE
      ↓
dbt Silver and Gold
      ↓
dbt tests and freshness checks
      ↓
Streamlit dashboard
      ↓
AWS SNS alerts

Scheduled by AWS EventBridge / Lambda
```

The dashboard is live relative to the most recent successful pipeline and dbt refresh. It is not a real-time exchange-price feed.

---

## Tech Stack

### Data ingestion

- Python
- `yfinance`
- pandas
- Loguru
- YAML configuration
- CSV-based local Bronze storage

### Data platform and transformation

- Databricks Free Edition
- Databricks SQL Warehouse
- dbt Core
- `dbt-databricks`
- SQL
- Medallion Architecture

### Dashboard

- Streamlit
- Plotly
- Databricks SQL Connector
- Cached Databricks queries
- Secure Streamlit secrets

### Development

- `uv`
- Git
- GitHub
- VS Code

### Planned automation

- AWS Lambda
- AWS EventBridge
- AWS SNS

---

## ETF Universe

| Symbol | ETF |
|---|---|
| VOO | Vanguard S&P 500 ETF |
| SPY | SPDR S&P 500 ETF Trust |
| QQQ | Invesco QQQ Trust |
| VGT | Vanguard Information Technology ETF |
| VT | Vanguard Total World Stock ETF |
| VXUS | Vanguard Total International Stock ETF |
| BND | Vanguard Total Bond Market ETF |
| GLD | SPDR Gold Shares |
| VEA | Vanguard FTSE Developed Markets ETF |
| VWO | Vanguard FTSE Emerging Markets ETF |
| BNDX | Vanguard Total International Bond ETF |
| ACWI | iShares MSCI ACWI ETF |
| EFA | iShares MSCI EAFE ETF |
| IEMG | iShares Core MSCI Emerging Markets ETF |
| EWJ | iShares MSCI Japan ETF |
| MCHI | iShares MSCI China ETF |
| INDA | iShares MSCI India ETF |
| EWG | iShares MSCI Germany ETF |
| EWU | iShares MSCI United Kingdom ETF |
| EWZ | iShares MSCI Brazil ETF |

Symbols are configured in:

```text
config/etf_symbols.yml
```

ETF names and classifications are maintained in:

```text
config/etf_metadata.yml
```

---

## Project Structure

```text
daily_etf_market_intelligence_pipeline/
│
├── .streamlit/
│   └── secrets.toml                 # Local only; never commit
│
├── config/
│   ├── etf_symbols.yml
│   └── etf_metadata.yml
│
├── dashboard/
│   ├── app.py
│   └── services/
│       ├── __init__.py
│       ├── databricks_service.py
│       └── metadata_service.py
│
├── data/
│   └── bronze/
│       └── yahoo_finance/
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
│   ├── tests/
│   └── macros/
│
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Medallion Architecture

### Bronze

The Bronze layer preserves raw historical ETF price data fetched from Yahoo Finance.

Local files are stored under:

```text
data/bronze/yahoo_finance/
```

The combined historical file is written to:

```text
data/bronze/yahoo_finance_upload/etf_prices_historical.csv
```

Databricks table:

```text
etf_market_intelligence.bronze.etf_prices_raw
```

Main fields include:

- ETF symbol
- Trading date
- Open, high, low, and close
- Adjusted close
- Trading volume
- Source provider
- Load type
- Batch ID
- Ingestion timestamp

### Silver

Silver model:

```text
etf_market_intelligence.silver.etf_prices_cleaned
```

The Silver layer:

- standardizes column names;
- removes unusable records;
- validates required price fields;
- checks that daily high is not below daily low;
- calculates the previous adjusted closing price;
- calculates daily return and daily return percentage;
- calculates a five-trading-day comparison value;
- keeps one row per ETF per trading day.

### Gold

Current Gold marts:

```text
etf_market_intelligence.gold.etf_long_term_performance
etf_market_intelligence.gold.etf_month_by_month_performance
etf_market_intelligence.gold.etf_monthly_market_summary
etf_market_intelligence.gold.etf_risk_summary
etf_market_intelligence.gold.etf_alert_candidates
```

#### `etf_long_term_performance`

One row per ETF with:

- first and latest trading dates;
- first and latest adjusted closing prices;
- total price return;
- total return percentage.

#### `etf_month_by_month_performance`

One row per ETF and month with:

- first and last trading dates;
- first and last adjusted closing prices;
- monthly return;
- monthly return percentage;
- trading-day count.

#### `etf_monthly_market_summary`

One row per month with:

- number of tracked ETFs;
- positive, negative, and flat ETF counts;
- average monthly return;
- best and worst monthly returns;
- best-performing ETF.

#### `etf_risk_summary`

One row per ETF with:

- total, positive, negative, and flat month counts;
- average monthly return;
- best and worst month;
- monthly volatility;
- positive-month ratio.

#### `etf_alert_candidates`

Identifies historically significant monthly movements for future alert delivery.

Current alert categories include:

| Condition | Alert type | Severity |
|---:|---|---|
| Monthly return `>= 8%` | `STRONG_GAIN` | High |
| Monthly return `<= -8%` | `SHARP_DROP` | High |
| Monthly return `>= 4%` | `POSITIVE_MOMENTUM` | Medium |
| Monthly return `<= -4%` | `NEGATIVE_MOMENTUM` | Medium |

The mart currently supports analysis in Streamlit. Sending notifications through AWS SNS is planned.

---

## Streamlit Dashboard

The dashboard queries the Databricks Gold tables directly through the Databricks SQL Connector.

Current pages:

### Overview

- ETF coverage
- Latest trading date
- Latest market month
- Monthly leader
- Best long-term performer
- Lowest monthly volatility
- Long-term performance ranking
- Market breadth
- Risk-return overview

### ETF Explorer

- Business-friendly ETF name and ticker selection
- Monthly adjusted closing-price history
- Monthly returns
- Normalized growth of `$100`
- Monthly return heatmap
- Downloadable monthly history

### Risk & Return

- Monthly return versus volatility
- Positive-month ratio
- Cross-ETF comparison
- Volatility ranking
- Detailed risk summary

### Market History

- Monthly average, best, and worst ETF returns
- Positive and negative market breadth
- Monthly winner leaderboard
- Downloadable market history

### Alerts

- Alert-severity and alert-type filters
- Historical ETF alert distribution
- Latest alert records
- Downloadable alert data

The dashboard uses a reusable query service, five-minute result caching, and a metadata service that converts ticker symbols into complete ETF names.

---

## Local Setup

### Prerequisites

- Python 3.11 or newer
- `uv`
- Git
- A Databricks workspace and SQL warehouse
- A Databricks personal access token with only the required SQL/BI permissions

### 1. Clone the repository

```powershell
git clone <YOUR_REPOSITORY_URL>
cd daily_etf_market_intelligence_pipeline
```

### 2. Recreate the Python environment

```powershell
uv sync
```

The environment is reproducible from:

```text
pyproject.toml
uv.lock
```

Do not commit `.venv`.

### 3. Configure Databricks secrets

Create:

```text
.streamlit/secrets.toml
```

Use this structure:

```toml
[databricks]
server_hostname = "YOUR_SERVER_HOSTNAME"
http_path = "/sql/1.0/warehouses/YOUR_WAREHOUSE_ID"
access_token = "YOUR_ACCESS_TOKEN"
catalog = "etf_market_intelligence"
schema = "gold"
```

Never commit this file. It must be listed in `.gitignore`.

### 4. Validate dbt connectivity

```powershell
cd etf_intelligence_pipeline
uv run dbt debug
cd ..
```

### 5. Run the dashboard

```powershell
uv run streamlit run dashboard/app.py
```

Local URL:

```text
http://localhost:8501
```

Stop the dashboard with:

```text
Ctrl + C
```

---

## Rebuild the Historical Pipeline

Run from the repository root unless stated otherwise.

### 1. Fetch historical ETF prices

```powershell
uv run python -m src.ingestion.fetch_historical_prices
```

### 2. Validate local Bronze files

```powershell
uv run python -m src.ingestion.check_bronze_files
```

### 3. Create the combined upload file

```powershell
uv run python -m src.ingestion.create_databricks_upload_file
```

### 4. Copy the combined file into the dbt seed directory

```powershell
Copy-Item `
  data\bronze\yahoo_finance_upload\etf_prices_historical.csv `
  etf_intelligence_pipeline\seeds\etf_prices_raw.csv `
  -Force
```

### 5. Load Bronze and rebuild the analytical layers

```powershell
cd etf_intelligence_pipeline

uv run dbt seed --full-refresh --select etf_prices_raw
uv run dbt run --select silver gold
uv run dbt test --select silver gold
```

Return to the root:

```powershell
cd ..
```

After a successful dbt refresh, use **Refresh from Databricks** in the Streamlit sidebar.

---

## Data Quality

The project uses dbt tests and validation queries to protect important assumptions, including:

- required symbols and trading dates are not null;
- required OHLCV fields are present;
- ETF/date records are unique where expected;
- invalid daily price ranges are rejected;
- Silver and Gold models return expected grains;
- custom business-rule tests pass.

Example validation query:

```sql
SELECT
    symbol,
    COUNT(*) AS row_count,
    MIN(price_date) AS first_date,
    MAX(price_date) AS latest_date
FROM etf_market_intelligence.silver.etf_prices_cleaned
GROUP BY symbol
ORDER BY symbol;
```

---

## Security

The following files must not be committed:

```text
.streamlit/secrets.toml
.venv/
logs/
```

Before pushing changes, verify:

```powershell
git check-ignore -v .streamlit/secrets.toml
git status
```

The dashboard token is used only for querying the Databricks SQL warehouse and should follow the principle of least privilege.

---

## Roadmap

### Next phase: daily incremental ingestion

- determine the latest loaded date for each ETF;
- fetch only missing trading days;
- label each ingestion run with a batch ID;
- keep historical and incremental loads auditable;
- prevent duplicates using `symbol + price_date`;
- replace recurring full seed refreshes with a scalable Bronze load and `MERGE`.

### Automation

- schedule ingestion using AWS EventBridge;
- run the ingestion and transformation workflow using AWS Lambda or an appropriate lightweight runner;
- execute dbt models and tests after each successful load;
- record pipeline status and freshness.

### Alert delivery

- use `etf_alert_candidates` as the source for alert decisions;
- publish strong gains, sharp drops, and other selected conditions through AWS SNS;
- avoid duplicate notifications for previously processed ETF/month events.

### Dashboard and deployment

- add daily-grain price and volume charts;
- add drawdown and annualized risk metrics;
- add pipeline-health and freshness views;
- deploy the Streamlit dashboard publicly;
- add dashboard and dbt-lineage screenshots to this README.

---

## Portfolio Purpose

This project demonstrates:

- Python-based ingestion;
- configuration-driven ETF processing;
- Databricks and Medallion Architecture;
- modular dbt transformations;
- data-quality testing;
- analytics-ready Gold modeling;
- secure SQL connectivity;
- Streamlit and Plotly dashboard development;
- separation of ingestion, transformation, and presentation responsibilities;
- a clear path toward incremental processing and cloud automation.

---

## Disclaimer

This project is built for educational and Data Engineering portfolio purposes. It is not financial advice, investment research, or a recommendation to buy or sell any security.