# Daily ETF Market Intelligence Pipeline

This project is an end-to-end Data Engineering portfolio project that ingests ETF market data, stores it in a Bronze layer, transforms it using Medallion Architecture, and later powers dashboards and email alerts.

## Phase 1: Historical Bulk Ingestion

In Phase 1, historical ETF price data is fetched from Yahoo Finance using `yfinance` and stored locally as Bronze CSV files.

## ETFs

- VOO
- SPY
- QQQ
- VGT
- VT
- VXUS
- BND
- GLD

## Current Bronze Layer

Data is stored in:

```text
data/bronze/yahoo_finance/symbol=<ETF_SYMBOL>/load_type=historical/prices.csv