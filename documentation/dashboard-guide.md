# Dashboard Guide

Start the dashboard and open:

```text
http://localhost:8501
```

The dashboard has four tabs.

## Overview tab

Shows symbols currently stored in the local DuckDB database.

Use this to confirm:

- which tickers have data,
- how many rows exist,
- first available date,
- latest available date,
- provider name.

## Ingest tab

Use this to pull local price history from yfinance.

### Single symbol

1. Enter a ticker in the sidebar's **Ingest tab ticker** field.
2. Select an ingestion period.
3. Click **Ingest ticker**.

### Watchlist

1. Edit `config/watchlist.txt` if needed.
2. Select an ingestion period.
3. Click **Ingest default watchlist**.

The watchlist parser accepts blank lines and comments.

## Analyze tab

The Analyze tab is symbol-driven.

1. Enter a ticker symbol in the Symbol text box.
2. Click **Refresh**.
3. The app fetches fresh yfinance data for that symbol.
4. The app stores the refreshed data in DuckDB.
5. The JSON report updates.
6. The candlestick chart updates.

### Chart timeframe controls

Top-right buttons:

- Daily
- Weekly
- Monthly

Daily uses stored daily OHLC candles. Weekly and Monthly aggregate the local daily data.

### Chart duration controls

Bottom-left buttons:

- 3M
- 6M
- 1Y
- 3Y
- 5Y

The duration filter is applied before display, so the selected timeframe/duration combination controls the exact chart shown.

Examples:

| Selection | Meaning |
|---|---|
| Daily + 3M | Daily candles over the latest 3 months of local data. |
| Weekly + 6M | Weekly OHLC candles over the latest 6 months of local data. |
| Monthly + 5Y | Monthly OHLC candles over the latest 5 years of local data. |

### JSON quick report

The report is deterministic. It is built from locally stored data and engineered features.

It currently contains sections such as:

- `price_action`
- `trend`
- `momentum_volatility`
- `volume_liquidity`
- `data_notes`

## Config tab

Shows runtime configuration and watchlist contents.

Use it when debugging:

- database path,
- Ollama URL,
- model name,
- watchlist path,
- environment settings.

## Gemma explanation

Enable **Use Gemma explanation** in the sidebar if you want the local LLM to explain the JSON report. Gemma should be treated as an explanation layer, not as a source of guaranteed trading decisions.
