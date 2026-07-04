# Data Pipeline

## Current data source

The current prototype market data source is `yfinance`, which downloads data from Yahoo Finance.

The provider implementation is:

```text
app/data/providers/yfinance_provider.py
```

The important flow is:

```text
Ticker symbol -> YFinanceProvider -> yfinance -> OHLCV DataFrame -> DuckDB price_bars table
```

## What data is stored

The local database stores daily price bars in the `price_bars` table.

Current columns include:

| Column | Meaning |
|---|---|
| `symbol` | Normalized ticker symbol. |
| `trade_date` | Trading date. |
| `open` | Opening price. |
| `high` | Session high. |
| `low` | Session low. |
| `close` | Closing price. |
| `adj_close` | Adjusted close when available. |
| `volume` | Reported volume. |
| `provider` | Data provider name, currently `yfinance`. |
| `ingested_at` | Timestamp when row was ingested. |

## Where the database lives

Default path:

```text
data/trading_platform.duckdb
```

You can confirm this with:

```bash
python -m app.main doctor
```

or in the dashboard Config tab.

## Ingestion behavior

Data is pulled only when you run an ingestion command or click **Ingest ticker** / **Ingest default watchlist** in the dashboard.

The system does not automatically refresh data in the background yet.

## Important limitations

`yfinance` is suitable for prototyping, education, and research. It should not be treated as a final production-grade live trading data source.

Current limitations:

- no official service-level agreement,
- possible delays or missing fields,
- not designed for high-frequency use,
- not a direct broker/exchange data feed,
- not ideal for real-time options analytics.

## Future provider abstraction

Because data access is isolated behind a provider class, later volumes can add additional providers such as:

- Polygon
- Alpaca
- Tradier
- Interactive Brokers
- Databento
- broker-specific APIs

The goal is to keep the rest of the system stable while swapping or adding data sources.

## Persisted indicators table

The project now includes a separate `indicators` table for persisted daily technical indicators.

The intended workflow is:

```text
price_bars -> feature engine -> indicators
```

The `price_bars` table remains the raw-ish source of historical OHLCV data. The `indicators` table is a derived table that is rebuilt manually when the user runs a calculation command.

Example:

```powershell
python -m app.main ingest-price AAPL --period 10y
python -m app.main calculate AAPL 5y
```

If 10 years of AAPL data exists locally, the indicator calculation uses the full available price history to compute rolling windows, then stores only the last 5 years of daily indicator rows. The maximum stored duration is capped at 5 years.

The `indicators` table includes deterministic technical values such as returns, moving averages, MACD, RSI, ATR, volatility, and liquidity features. It does not include future-looking target columns.
