# AI Trading Research Platform - Volume 1 Starter

This repository is the foundation for a local AI trading research platform using:

- Gemma through Ollama for natural-language analysis
- XGBoost for structured numerical prediction
- DuckDB for local analytical storage
- yfinance for prototype market data ingestion
- Streamlit for the local dashboard

This starter is intentionally paper-trading/research only. It does **not** place live trades.

## Project documentation

A comprehensive navigable documentation section now lives in:

```text
documentation/
```

Start here:

- [Documentation main page](documentation/index.md)
- [Setup guide](documentation/setup-guide.md)
- [Command reference](documentation/command-reference.md)
- [Dashboard guide](documentation/dashboard-guide.md)
- [Feature engineering](documentation/feature-engineering.md)
- [Indicator reference](documentation/indicators.md)

The [Indicator Reference](documentation/indicators.md) explains every engineered feature currently produced by `app/features/technical_indicators.py`, including returns, moving averages, MACD, RSI, ATR, volatility, volume/liquidity features, and future target labels.



## What changed in the shared Analyze symbol upgrade

The dashboard now uses one shared ticker field in the **sidebar**. Enter a ticker such as `MSFT`, `NVDA`, `SOXL`, or `SPY` in the sidebar **Ticker symbol** field, open **Ingest**, click **Ingest ticker**, then open **Analyze**. The Analyze page automatically uses that same sidebar ticker for the JSON quick report and candlestick chart.

The Analyze tab no longer has its own symbol text box or Refresh button. This prevents Streamlit session-state conflicts and keeps the dashboard behavior simple: one active ticker drives both ingestion and analysis.

## What changed in the chart controls upgrade

The Analyze tab candlestick chart now has interactive button arrays:

- **Top-right timeframe buttons:** `Daily`, `Weekly`, `Monthly`
- **Bottom-left duration buttons:** `3M`, `6M`, `1Y`, `3Y`, `5Y`

The chart uses locally stored daily OHLCV data and recalculates the displayed candles based on the selected combination.
For example, `Weekly + 6M` shows weekly OHLC candles over the latest six months of locally stored data.
`Monthly + 5Y` shows monthly OHLC candles over the latest five years of locally stored data.

## What changed in the SMA overlay upgrade

The Analyze tab candlestick chart now overlays the medium- and long-term simple moving averages:

- `SMA 20`
- `SMA 50`
- `SMA 200`

The chart includes a built-in **Color key** legend so each SMA line is visually identifiable. The SMA calculation follows the selected candle timeframe: on `Daily`, SMA 20 means 20 daily candles; on `Weekly`, SMA 20 means 20 weekly candles; on `Monthly`, SMA 20 means 20 monthly candles. SMA values are calculated before the selected duration is trimmed, so long overlays such as SMA 200 can still appear on shorter views like `3M` when enough older local history exists.

## What changed in the watchlist upgrade

You can now ingest multiple symbols from a watchlist file instead of running one command per ticker.

New files:

```text
config/watchlist.txt
app/core/watchlist.py
app/services/__init__.py
app/services/ingestion.py
tests/test_watchlist.py
tests/test_ingestion.py
```

Updated files:

```text
.env.example
Makefile
README.md
app/core/config.py
app/db/duckdb_client.py
app/main.py
```

## Quick start on Windows PowerShell

```powershell
cd ai-trading-platform
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
copy .env.example .env
python -m app.main doctor
python -m app.main init-db
python -m app.main ingest-price AAPL --period 1y
python -m app.main analyze AAPL
```

## Quick start on macOS/Linux

```bash
cd ai-trading-platform
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
python -m app.main doctor
python -m app.main init-db
python -m app.main ingest-price AAPL --period 1y
python -m app.main analyze AAPL
```

## Single-symbol ingestion

Use this when you only want one ticker:

```bash
python -m app.main ingest-price AAPL --period 1y
```

This fetches daily OHLCV price bars for AAPL from Yahoo Finance through `yfinance` and stores them locally in DuckDB.

## Watchlist ingestion

The default watchlist lives here:

```text
config/watchlist.txt
```

Default contents:

```text
AAPL
MSFT
NVDA
TSLA
AMZN
META
GOOGL
AMD
SPY
QQQ
```

Run this command to ingest every symbol in the file:

```bash
python -m app.main ingest-watchlist --period 1y
```

You can also point to a different watchlist:

```bash
python -m app.main ingest-watchlist --watchlist config/my_watchlist.txt --period 5y
```

The watchlist file supports:

- one ticker per line
- blank lines
- full-line comments starting with `#`
- inline comments after a ticker
- duplicate tickers, which are ignored after the first occurrence

Example:

```text
# Core watchlist
AAPL
MSFT
NVDA
SPY  # S&P 500 ETF
AAPL # duplicate ignored
```

By default, if one ticker fails, the batch continues and reports the failure at the end. To stop the whole batch on the first error:

```bash
python -m app.main ingest-watchlist --period 1y --stop-on-error
```

## See which symbols are already stored locally

```bash
python -m app.main list-symbols
```

This prints a table with symbol, row count, first date, latest date, and provider.

## Analyze a symbol

After ingestion:

```bash
python -m app.main analyze AAPL
```

With local Gemma explanation:

```bash
python -m app.main analyze AAPL --use-gemma
```

## Useful Makefile shortcuts

```bash
make doctor
make init-db
make ingest-aapl
make ingest-watchlist
make list-symbols
make analyze-aapl
make test
```

On Windows without `make`, run the equivalent `python -m app.main ...` commands directly.



## Start, stop, and status commands

The project now includes a small local control layer for long-running services.

### Windows PowerShell

Start the local components:

```powershell
.\scripts\start_project.ps1
```

This command will:

1. initialize the DuckDB schema,
2. start Ollama if it is installed and not already listening on port `11434`,
3. start the Streamlit dashboard on port `8501`, and
4. write service logs under `logs/` and tracked process IDs under `.runtime/pids/`.

Then open:

```text
http://localhost:8501
```

The dashboard uses the **sidebar → Ticker symbol** field as the single shared active symbol. Enter a ticker there, open Ingest, click **Ingest ticker**, then open Analyze to view the JSON quick report and chart for that symbol. The chart displays red/green candlesticks using locally stored OHLC data. Green candles represent sessions where close is above open. Red candles represent sessions where close is below open. It also overlays SMA 20, SMA 50, and SMA 200 lines with a Color key legend. Use the top-right chart controls to switch between daily, weekly, and monthly candles. Use the bottom-left controls to switch between 3M, 6M, 1Y, 3Y, and 5Y durations.

Check status:

```powershell
.\scripts\status_project.ps1
```

Stop tracked components:

```powershell
.\scripts\stop_project.ps1
```

Optional start flags:

```powershell
.\scripts\start_project.ps1 -IngestWatchlist -Period 1y
.\scripts\start_project.ps1 -SkipOllama
.\scripts\start_project.ps1 -SkipDashboard
.\scripts\start_project.ps1 -NoInitDb
```

Optional stop flags:

```powershell
.\scripts\stop_project.ps1 -ForceByPort
.\scripts\stop_project.ps1 -StopExternalOllama
```

`-StopExternalOllama` is intentionally optional because Ollama may be shared by other local projects.

### macOS/Linux

```bash
./scripts/start_project.sh
./scripts/status_project.sh
./scripts/stop_project.sh
```

Optional environment variables:

```bash
INGEST_WATCHLIST=1 PERIOD=1y ./scripts/start_project.sh
SKIP_OLLAMA=1 ./scripts/start_project.sh
SKIP_DASHBOARD=1 ./scripts/start_project.sh
NO_INIT_DB=1 ./scripts/start_project.sh
```

### Makefile shortcuts

On Windows with `make` available:

```bash
make start
make status
make stop
make dashboard
```

Without `make`, use the PowerShell scripts directly.

## Local LLM check

Install Ollama, then run one of these:

```bash
ollama pull gemma3:1b
ollama run gemma3:1b
```

On CPU-only laptops, start with `gemma3:1b`. If Gemma still runs hot or feels stuck, lower `OLLAMA_NUM_PREDICT` to `200`, keep `OLLAMA_NUM_CTX` around `2048`, and turn off Gemma in the dashboard when you only need the deterministic JSON report.

## Project philosophy

This project separates responsibilities:

- Quantitative models produce probabilities and measurable signals.
- Gemma explains, critiques, and summarizes evidence.
- The risk engine constrains what the system is allowed to recommend.
- Backtesting and paper trading decide whether ideas survive.

## Important data-source note

This foundation uses `yfinance` for prototyping and education. It is useful for local development, historical research, and early backtesting, but it should not be treated as a production-grade live market-data feed. A later volume should add a provider interface for paid/reliable feeds such as Polygon, Alpaca, Interactive Brokers, Tradier, or Databento depending on the target use case.

## Point 18 — First Feature Engineering Module

This upgrade adds the first real feature-engineering layer under:

```text
app/features/technical_indicators.py
```

It converts stored OHLCV price bars into reusable model-ready features. These are deterministic technical features, not predictions.

### What features are created

Price action:

- `return_1d`
- `return_5d`
- `return_21d`
- `log_return_1d`
- `daily_range_pct`
- `open_to_close_pct`
- `close_position_in_day_range`

Trend:

- `sma_5`
- `sma_10`
- `sma_20`
- `sma_50`
- `sma_200`
- `close_vs_sma_5`
- `close_vs_sma_10`
- `close_vs_sma_20`
- `close_vs_sma_50`
- `close_vs_sma_200`
- `ema_12`
- `ema_26`
- `macd_line`
- `macd_signal`
- `macd_histogram`

Momentum and volatility:

- `rsi_14`
- `true_range`
- `atr_14`
- `atr_14_pct`
- `rolling_vol_20d`
- `rolling_vol_20d_annualized`

Volume and liquidity:

- `volume_sma_20`
- `volume_ratio_20`
- `dollar_volume`
- `dollar_volume_sma_20`

Optional future-looking labels for later XGBoost training:

- `future_return_1d`
- `future_return_5d`
- `target_up_1d`
- `target_up_5d`

Important: future-looking target columns are excluded by default and should never be used as model input features. They are labels only.

### Generate features from the command line

First make sure you have data:

```powershell
python -m app.main ingest-price AAPL --period 5y
```

Then generate the latest feature rows:

```powershell
python -m app.main features AAPL --tail 5
```

Get the feature rows as JSON:

```powershell
python -m app.main features AAPL --tail 5 --output json
```

Inspect future target labels for ML dataset development:

```powershell
python -m app.main features AAPL --tail 5 --include-targets
```

### Analyze report now uses engineered features

The existing command:

```powershell
python -m app.main analyze AAPL
```

now returns a richer structured JSON report with:

- price action
- trend
- momentum and volatility
- volume and liquidity
- data notes explaining that this is not yet an XGBoost prediction

The Analyze page in Streamlit also updates because it uses the same quick-report function.

### Makefile shortcut

```bash
make features-aapl
```

### Design rule

Feature engineering must never mix inputs and labels. The feature frame uses only present and historical data by default. Future-looking columns are created only when `include_targets=True`, and those columns are for supervised training labels only.

## Persisting calculated indicators

You can now create a dedicated DuckDB table called `indicators` that stores daily calculated technical indicator values for a ticker.

This is separate from the temporary feature preview command. The `features` command calculates features and prints them. The `calculate` command calculates features and stores them.

### Example: calculate last 5 years of indicators

First ingest enough price history:

```powershell
python -m app.main ingest-price AAPL --period 10y
```

Then manually calculate and persist indicators for the last 5 years:

```powershell
python -m app.main calculate AAPL 5y
```

You can also use the explicit alias:

```powershell
python -m app.main calculate-indicators AAPL 5y
```

Supported durations are:

```text
3m, 6m, 1y, 3y, 5y
```

The maximum persisted calculation duration is intentionally capped at `5y`. If your `price_bars` table contains 10 years of AAPL data, the system calculates indicators using the full available price history first, then stores only the last 5 years of daily indicator rows in the `indicators` table. This preserves long-window indicators such as `sma_200` while keeping the indicator table bounded.

List stored indicator coverage:

```powershell
python -m app.main list-indicators
```

Query the table directly:

```sql
SELECT symbol, COUNT(*) AS rows, MIN(trade_date), MAX(trade_date)
FROM indicators
GROUP BY symbol;
```


## Gemma with DuckDB context

Gemma does not directly query DuckDB. The app now provides a safe Python tool
layer that extracts approved read-only context from `price_bars` and
`indicators`, then sends that compact context to Ollama/Gemma.

Preview the exact database context:

```powershell
python -m app.main db-context AAPL --rows 5
```

Ask Gemma a database-aware question:

```powershell
python -m app.main gemma-db AAPL "What do the latest indicator rows say about trend and momentum?"
```

Recommended sequence:

```powershell
python -m app.main ingest-price AAPL --period 10y
python -m app.main calculate AAPL 5y
python -m app.main db-context AAPL --rows 5
python -m app.main gemma-db AAPL "Explain the latest DuckDB indicators in plain English."
```
