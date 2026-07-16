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
- Git /GitHub

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
---

## Bronze Layer

The Bronze layer contains raw ETF price data fetched from Yahoo Finance.

The local Bronze files are saved as CSV files under:

```text
data/bronze/yahoo_finance/
```

A combined CSV file is created for dbt seed loading:

```text
data/bronze/yahoo_finance_upload/etf_prices_historical.csv
```

In Databricks, the Bronze table is:

```text
bronze.etf_prices_raw
```

---

## Silver Layer

The Silver layer cleans and standardizes the raw ETF price data.

Main Silver model:

```text
silver.etf_prices_cleaned
```

Silver layer work includes:

- Renaming columns
- Filtering invalid rows
- Keeping required price fields
- Calculating previous adjusted closing price
- Calculating daily return
- Calculating daily return percentage

The Silver table keeps this grain:

```text
one row per ETF per trading day
```

---

## Gold Layer

The Gold layer contains business-ready analytical marts.

Current Gold marts:

```text
gold.etf_long_term_performance
gold.etf_month_by_month_performance
gold.etf_risk_summary
gold.etf_monthly_market_summary
gold.etf_alert_candidates
```

### `etf_long_term_performance`

Compares each ETF from its first available trading date to the latest available trading date.

Main metrics:

- Start date
- End date
- First adjusted closing price
- Latest adjusted closing price
- Total return
- Total return percentage

---

### `etf_month_by_month_performance`

Calculates ETF performance month by month.

Main metrics:

- First trading date of the month
- Last trading date of the month
- First adjusted closing price
- Last adjusted closing price
- Monthly return
- Monthly return percentage
- Trading days count

---

### `etf_risk_summary`

Summarizes risk and return behavior for each ETF.

Main metrics:

- Total months count
- Positive months count
- Negative months count
- Average monthly return percentage
- Monthly volatility percentage
- Positive month ratio percentage
- Return-to-risk score

---

### `etf_monthly_market_summary`

Summarizes overall ETF market behavior by month.

Main metrics:

- Total ETFs count
- Positive ETFs count
- Negative ETFs count
- Average monthly return percentage
- Best-performing ETF
- Worst-performing ETF
- Positive ETF ratio percentage

---

### `etf_alert_candidates`

Identifies ETF months with strong positive or negative movement.

Current alert rules:

| Monthly Return | Alert Type | Severity |
|---:|---|---|
| >= 8% | STRONG_GAIN | HIGH |
| <= -8% | SHARP_DROP | HIGH |
| >= 4% | POSITIVE_MOMENTUM | MEDIUM |
| <= -4% | NEGATIVE_MOMENTUM | MEDIUM |

This mart is currently used for analysis only. It will later support alerting.

---

## How to Run the Pipeline

Run these commands from the project root.

### 1. Fetch ETF data

```powershell
python -m src.ingestion.fetch_historical_prices
```

### 2. Validate local Bronze files

```powershell
python -m src.ingestion.check_bronze_files
```

### 3. Create combined upload file

```powershell
python -m src.ingestion.create_databricks_upload_file
```

### 4. Copy combined CSV into dbt seeds

```powershell
Copy-Item `
  data\bronze\yahoo_finance_upload\etf_prices_historical.csv `
  etf_intelligence_pipeline\seeds\etf_prices_raw.csv `
  -Force
```

### 5. Move into dbt project

```powershell
cd etf_intelligence_pipeline
```

### 6. Refresh Bronze seed table

```powershell
dbt seed --full-refresh --select etf_prices_raw
```

### 7. Build Silver and Gold models

```powershell
dbt run --select silver gold
```

### 8. Run tests

```powershell
dbt test --select silver gold
```

---

## Useful Validation Queries

### Check Silver row counts and date ranges

```sql
SELECT
    symbol,
    COUNT(*) AS row_count,
    MIN(price_date) AS first_date,
    MAX(price_date) AS latest_date
FROM silver.etf_prices_cleaned
GROUP BY symbol
ORDER BY symbol;
```

### Check Gold long-term performance

```sql
SELECT
    symbol,
    start_date,
    end_date,
    ROUND(total_return_pct, 2) AS total_return_pct
FROM gold.etf_long_term_performance
ORDER BY total_return_pct DESC;
```

### Check alert distribution

```sql
SELECT
    alert_type,
    alert_severity,
    COUNT(*) AS alert_count
FROM gold.etf_alert_candidates
GROUP BY alert_type, alert_severity
ORDER BY alert_severity, alert_count DESC;
```
---

## Current Milestone

The current version of the project has completed the batch pipeline from Yahoo Finance ingestion to Databricks Silver and Gold marts.

The next development phase is building a Streamlit dashboard using the Gold tables.

---
