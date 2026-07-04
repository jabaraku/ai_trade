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

1. Enter a ticker in the sidebar **Ticker symbol** field.
2. Select an ingestion period.
3. Click **Ingest ticker**.

### Watchlist

1. Edit `config/watchlist.txt` if needed.
2. Select an ingestion period.
3. Click **Ingest default watchlist**.

The watchlist parser accepts blank lines and comments.

## Analyze tab

The Analyze tab uses the ticker from the sidebar **Ticker symbol** field. It does not have its own ticker text box.

1. Enter a ticker in the sidebar **Ticker symbol** field.
2. Open the **Ingest** tab.
3. Click **Ingest ticker** to fetch and store local data.
4. Open the **Analyze** tab.
5. The JSON report and candlestick chart display that same ticker.

If the Analyze tab says no data was found, verify the sidebar ticker, go back to **Ingest**, and click **Ingest ticker**.

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

The chart calculates SMA overlays before trimming to the selected duration, then displays only the selected duration. This lets long overlays such as SMA 200 appear on shorter views when enough older local history exists.

### SMA overlay color key

The chart shows these SMA overlays in the Plotly legend titled **Color key**:

| Overlay | Meaning |
|---|---|
| SMA 20 | Approximate one-month average on daily candles, or 20 bars on the selected timeframe. |
| SMA 50 | Intermediate trend average. |
| SMA 200 | Long-term trend average. |

For Weekly candles, SMA 20 means 20 weekly closes. For Monthly candles, SMA 20 means 20 monthly closes.

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
