# ETF Market Intelligence Pipeline

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![dbt](https://img.shields.io/badge/dbt%20Core-1.12-FF694B?logo=dbt&logoColor=white)](https://www.getdbt.com/)
[![Databricks](https://img.shields.io/badge/Databricks-Delta%20Lake-FF3621?logo=databricks&logoColor=white)](https://www.databricks.com/)
![Status](https://img.shields.io/badge/Project%20Status-Complete-2EA44F)

An automated cloud data platform that turns daily ETF market data into trusted, decision-ready analytics. The pipeline tracks **20 USD-listed ETFs** from 2015 onward, ingests the latest prices with Python and Spark, transforms them through a Bronze–Silver–Gold Medallion Architecture with dbt, validates the data with automated tests, and refreshes a published Databricks dashboard.

The ETF universe covers US equities, international and emerging markets, technology, bonds, and commodities.

> **Project status: Complete.** A scheduled three-task Databricks Job performs daily ingestion, builds and tests the Silver and Gold layers, and refreshes the dashboard without requiring a local machine or manual intervention.

## What the Project Delivers

- A fully automated daily pipeline for **20 ETFs**.
- Historical market coverage from **2015 onward**.
- Idempotent Delta Lake merges that prevent duplicate `(symbol, price_date)` records.
- **6 dbt models**, **82 data-quality tests**, and **5 Gold analytical marts**.
- A three-page dashboard for rolling market performance, configurable ETF comparisons, and historical seasonality.
- Version-controlled Python, dbt, and Databricks dashboard definitions for reproducibility.

## Project Snapshot

Operational status as of **30 July 2026**:

| Metric | Value |
| --- | ---: |
| ETFs tracked | 20 |
| Historical coverage | From 2015-01-02 |
| Latest automated price date validated | 2026-07-30 |
| Duplicate `(symbol, price_date)` keys | 0 |
| dbt models | 6 |
| dbt data tests | 82 |
| Gold analytical marts | 5 |
| Databricks Job tasks | 3 |
| Dashboard pages | 3 |
| Storage format | Delta |

The row count and latest date increase as new trading data is ingested.

## Why This Project Matters

This project demonstrates an end-to-end Data Engineering workflow rather than only a dashboard or a collection of SQL queries:

- Configuration-driven Python ingestion for a 20-ETF universe.
- Separate historical bootstrap and daily incremental ingestion paths.
- Idempotent Spark `MERGE` logic that prevents duplicate daily records.
- Cloud execution without requiring a local machine to remain online.
- Git-backed Python and dbt code used by Databricks Jobs.
- Bronze, Silver, and Gold layers implemented on Delta tables.
- dbt transformations, source definitions, data tests, and custom SQL tests.
- Task dependencies that stop downstream processing after upstream failure.
- A published Databricks dashboard refreshed automatically after Gold models finish.
- Dynamic data-freshness indicators and parameterized ETF comparisons.
- An exported `.lvdash.json` dashboard definition stored in Git for reproducibility.

## Architecture

```mermaid
flowchart LR
    A[Yahoo Finance] --> B[Databricks Job<br/>Python + Spark ingestion]
    B --> C[(Bronze Delta<br/>etf_prices_raw)]
    C --> D[dbt build]
    D --> E[(Silver Delta<br/>clean daily prices)]
    E --> F[(Gold marts<br/>performance and seasonality)]
    F --> G[Databricks SQL Warehouse]
    G --> H[Published Databricks Dashboard]
    D -->|on success| I[Dashboard refresh task]
    I --> H
```

## Ingestion Design

### Historical Bootstrap

`fetch_historical_prices.py` downloads the historical daily OHLCV data for each configured ETF from 2015 onward and loads it into Bronze through an idempotent Spark merge.

```text
Yahoo Finance historical download
        → pandas batch
        → Spark DataFrame
        → temporary view
        → MERGE INTO bronze.etf_prices_raw
```

The script can also serve as a recovery or backfill mechanism because rerunning the same dates updates matching keys rather than inserting duplicates.

### Daily Incremental Load

The scheduled incremental task retrieves the newest daily records and merges them directly into Bronze.

```text
Latest daily ETF records
        → pandas batch
        → Spark DataFrame
        → MERGE on symbol + price_date
        → dbt Silver and Gold build
        → dashboard refresh
```

`bronze.etf_prices_raw` is declared as a dbt source because it is populated by the ingestion task rather than built as a dbt model.

## Daily Orchestration

One Databricks Job, `etf_daily_pipeline`, manages the complete dependency chain:

| Order | Task | Type | Responsibility | Status |
| ---: | --- | --- | --- | --- |
| 1 | `fetch_incremental_prices` | Python script from Git | Fetch the latest records for all 20 ETFs and merge them into Bronze | Live |
| 2 | `build_silver_gold` | dbt task | Run Silver and Gold transformations and tests after ingestion succeeds | Live |
| 3 | `refresh_etf_dashboard` | Dashboard task | Refresh the published dashboard after the dbt task succeeds | Live |

```mermaid
flowchart LR
    A[fetch_incremental_prices] --> B[build_silver_gold]
    B --> C[refresh_etf_dashboard]
```

The job runs in Databricks, so the pipeline does not depend on a personal laptop or a local scheduler.

## Medallion Architecture

| Layer | Purpose | Main output |
| --- | --- | --- |
| Bronze | Preserve source values and ingestion metadata at daily ETF grain | `bronze.etf_prices_raw` |
| Silver | Clean, standardize, validate, and calculate daily price movements | `silver.etf_prices_cleaned` |
| Gold | Publish business-ready performance, market, risk, and alert datasets | Five analytical marts |
| Serving | Query curated Gold data and deliver interactive analytics | Databricks SQL + Dashboard |

### Bronze Layer

The Bronze table stores source market fields and operational metadata:

```text
symbol, price_date, open, high, low, close, adjusted_close, volume,
source_provider, load_type, batch_id, ingested_at_utc
```

**Grain:** one row per ETF per trading date.

### Silver Layer

`silver.etf_prices_cleaned`:

- Standardizes source field names.
- Filters records missing mandatory values.
- Rejects invalid price ranges where `high < low`.
- Calculates previous adjusted close.
- Calculates daily return and daily return percentage.
- Adds five-day comparison fields.
- Preserves ingestion lineage and batch metadata.

### Gold Analytical Marts

| Model | Grain | Business purpose |
| --- | --- | --- |
| `etf_long_term_performance` | One row per ETF | First and latest prices and total return since 2015 |
| `etf_month_by_month_performance` | One row per ETF per month | Monthly return and trading-period metrics |
| `etf_monthly_market_summary` | One row per month | Market breadth, average return, leaders, and laggards |
| `etf_risk_summary` | One row per ETF | Volatility, positive-month ratio, and return-to-risk metrics |
| `etf_alert_candidates` | One row per qualifying ETF/month | Strong gains, sharp drops, and momentum signals |

Alert thresholds:

| Monthly return | Alert type | Severity |
| ---: | --- | :---: |
| `>= 8%` | `STRONG_GAIN` | High |
| `<= -8%` | `SHARP_DROP` | High |
| `>= 4%` | `POSITIVE_MOMENTUM` | Medium |
| `<= -4%` | `NEGATIVE_MOMENTUM` | Medium |

The published dashboard focuses on current performance, configurable comparison, and seasonality. The risk and alert marts remain available in the analytical layer for technical exploration but are intentionally not exposed in the final dashboard navigation.

## Databricks Financial Dashboard

The native Databricks AI/BI dashboard is published and refreshed automatically as the final task in the daily pipeline.

### 1. Overview

The landing page provides a rolling **30-calendar-day market snapshot** through the latest available trading date:

- Average 30-day return across all tracked ETFs.
- Percentage of ETFs with a positive 30-day return.
- Best and worst 30-day performers.
- Complete ETF return ranking using a red–yellow–green diverging scale.
- Dynamic data-freshness banner showing the latest market date and ETF count.

The 30-day calculation uses adjusted closing prices and selects the nearest available trading date on or before the 30-day start date.

![ETF Market Intelligence Overview](docs/dashboard/overview.png)

### 2. Performance & Comparison

The performance page supports:

- Dynamic horizons: `1D`, `1W`, `1M`, `3M`, `6M`, `YTD`, `1Y`, `3Y`, `5Y`, and `MAX`.
- ETF return ranking for the selected horizon.
- Multi-select ETF comparison.
- Daily normalized growth from a common starting value of 100.
- Calculations extending through the latest available trading date.

`1D` compares the two latest trading sessions. `1W` compares the latest close with the close five trading sessions earlier. Longer horizons use daily adjusted closing prices from the Silver layer.

![ETF Performance and Comparison](docs/dashboard/performance-comparison.png)

### 3. Seasonality

The seasonality page provides:

- Dynamically calculated highest-average calendar month.
- Lowest-average calendar month.
- Most frequently positive calendar month.
- ETF-by-month average-return heatmap.
- Historical data from January 2015 onward.
- Current month-to-date observations, clearly disclosed in the page banner and footer.

Because the page includes current month-to-date data, the leading calendar month can change after each successful daily refresh.

![ETF Seasonality](docs/dashboard/seasonality.png)

### Request Access to the Live Dashboard

The published dashboard is hosted inside a private Databricks account, so it is not available through a fully public link. Read-only access can be granted on request.

#### Request access through LinkedIn

1. Open my [LinkedIn profile](https://www.linkedin.com/in/hamza-abbas-data-engineer/).
2. Send a short message requesting access to the **ETF Market Intelligence Dashboard**.
3. Include the email address you want to use for Databricks.
4. I will add that email to my Databricks account or workspace and grant **Can View** access to the published dashboard.
5. Accept the Databricks invitation and sign in with the same email address.


Dashboard access is read-only. Viewers can open the published dashboard, change filters, compare ETFs, and interact with the visualizations, but they cannot edit the dashboard, queries, or underlying datasets.

#### Create a Databricks Free Edition account

A Databricks Free Edition account is useful for exploring the platform independently. To create one:

1. Open the official [Databricks Free Edition signup page](https://login.databricks.com/).
2. Choose a signup method and register with an email address.
3. Complete email verification and sign in.
4. Databricks will create a separate Free Edition workspace for your personal use.

> **Important:** Creating your own Free Edition workspace does not automatically provide access to this dashboard. Access to this project still requires an invitation to my Databricks account and explicit **Can View** permission. Use the same email address in your LinkedIn request so the invitation can be matched correctly.

The dashboard is published with shared data permissions, so approved viewers do not need separate access to the underlying Silver and Gold tables or the SQL compute used by the dashboard.

Official references:

- [Sign up for Databricks Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition)

### Dashboard as Code

The exported Databricks dashboard definition is versioned here:

```text
databricks/dashboards/etf_market_intelligence.lvdash.json
```

The export contains dashboard pages, SQL datasets, parameters, filters, widget layouts, conditional formatting, and saved defaults. This keeps the analytical interface reviewable in Git alongside the ingestion and transformation code. It does not contain the underlying market data or Databricks credentials.

## ETF Universe

| Symbol | ETF |
| --- | --- |
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

Symbols are maintained in `config/etf_symbols.yml`. ETF names and classifications are maintained in `config/etf_metadata.yml`.

## Repository Structure

```text
daily_etf_market_intelligence_pipeline/
├── config/
│   ├── etf_symbols.yml
│   └── etf_metadata.yml
├── databricks/
│   └── dashboards/
│       └── etf_market_intelligence.lvdash.json
├── docs/
│   └── dashboard/
│       ├── overview.png
│       ├── performance-comparison.png
│       └── seasonality.png
├── etf_intelligence_pipeline/
│   ├── dbt_project.yml
│   ├── macros/
│   ├── models/
│   │   ├── bronze/
│   │   │   └── schema.yml
│   │   ├── silver/
│   │   └── gold/
│   └── tests/
├── src/
│   ├── ingestion/
│   │   ├── fetch_historical_prices.py
│   │   ├── fetch_incremental_prices.py
│   │   ├── check_bronze_files.py
│   │   └── create_databricks_upload_file.py
│   └── utils/
│       └── config_loader.py
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

Generated data, local environments, logs, dbt build artifacts, and credentials are excluded from version control.

## Local Setup

The scheduled pipeline executes in Databricks. Local setup is mainly used for developing and validating dbt models.

### Prerequisites

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Git
- Databricks workspace and SQL Warehouse
- dbt Core and `dbt-databricks`

### 1. Clone and install

```powershell
git clone https://github.com/Hamza-Abbas/ETF-Market-Intelligence-Pipeline.git
cd ETF-Market-Intelligence-Pipeline
uv sync
```

### 2. Configure dbt

Store the Databricks connection in `%USERPROFILE%\.dbt\profiles.yml`. Do not commit access tokens or connection secrets.

Validate the connection:

```powershell
cd etf_intelligence_pipeline
dbt debug
cd ..
```

## Running the Pipeline

### Automated cloud workflow

The scheduled `etf_daily_pipeline` Databricks Job handles ingestion, transformation, testing, and dashboard refresh automatically.

Check the Databricks Job run history to inspect task status, duration, and failures.

### Local dbt development

```powershell
cd .\etf_intelligence_pipeline
dbt build --select silver gold
cd ..
```

The Spark ingestion scripts are intended to run as Databricks Job tasks rather than as a local production scheduler.

## Data Quality

The project uses **82 dbt data tests** and custom SQL checks covering:

- Mandatory fields.
- Unique `(symbol, price_date)` grain.
- Valid OHLC price relationships.
- Stable grains through Silver and Gold.
- Complete configured ETF batches.
- Null handling in analytical metrics.
- Source-to-model consistency.

Bronze validation:

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT symbol) AS total_symbols,
    MIN(price_date) AS earliest_date,
    MAX(price_date) AS latest_date
FROM etf_market_intelligence.bronze.etf_prices_raw;
```

Duplicate-key validation:

```sql
SELECT
    symbol,
    price_date,
    COUNT(*) AS row_count
FROM etf_market_intelligence.bronze.etf_prices_raw
GROUP BY symbol, price_date
HAVING COUNT(*) > 1;
```

## Security

The following are excluded from Git:

- `.env`
- `%USERPROFILE%\.dbt\profiles.yml`
- `.venv/`
- Logs
- dbt `target/`
- `dbt_packages/`
- Generated local market-data files
- Databricks access tokens

Before every push:

```powershell
git status --short
git diff
git diff --cached
```

## Project Status

| Capability | Status |
| --- | --- |
| Historical ingestion for 20 ETFs | Complete |
| Bronze Delta baseline and daily incremental growth | Complete |
| Silver transformation layer | Complete |
| Five Gold analytical marts | Complete |
| dbt tests on Silver and Gold | Complete |
| Full ETF metadata and classifications | Complete |
| Idempotent Spark incremental ingestion | Complete |
| Git-backed Databricks Job execution | Complete |
| Daily cloud schedule | Complete |
| Published three-page Databricks dashboard | Complete |
| Automated dashboard refresh task | Complete |
| Dashboard definition exported to Git | Complete |
| **Overall project** | **Complete** |

## Project Completion

The project is considered **finished at its current scope**.

Delivered components:

- Historical and daily incremental ETF ingestion.
- Idempotent Spark merges into Databricks Bronze.
- Bronze, Silver, and Gold Medallion Architecture.
- dbt models, sources, tests, and analytical marts.
- Scheduled three-task Databricks workflow.
- Published three-page financial dashboard.
- Automated dashboard refresh after successful transformations.
- Dashboard screenshots and version-controlled `.lvdash.json` definition.
- Security, documentation, and reproducibility guidance.

There is no active roadmap for additional development. Future changes may be added later as optional extensions, but they are not required for this project to be considered complete.

## Author

**Hamza Abbas** — Aspiring Data Engineer focused on Python, SQL, dbt, Databricks, Snowflake, cloud data platforms, and Analytics Engineering.

- [LinkedIn](https://www.linkedin.com/in/hamza-abbas-data-engineer/)
- [GitHub](https://github.com/Hamza-Abbas)

## Disclaimer

This project is built for educational and Data Engineering portfolio purposes. It is not financial advice, investment research, or a recommendation to buy or sell any security.
