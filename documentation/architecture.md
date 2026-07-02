# Architecture

## High-level architecture

```text
                      User
                       |
                       v
              Streamlit Dashboard
                       |
          +------------+------------+
          |                         |
     Ingestion UI                Analyze UI
          |                         |
          v                         v
   YFinanceProvider          DuckDB local store
          |                         |
          v                         v
       yfinance              Feature engine
                                    |
                                    v
                              Quick report JSON
                                    |
                     +--------------+--------------+
                     |                             |
              Candlestick chart              Optional Gemma
                                                via Ollama
```

## Main code modules

| Module | Responsibility |
|---|---|
| `app/main.py` | Typer CLI entry point. |
| `app/core/config.py` | Loads settings from `.env` and defaults. |
| `app/core/watchlist.py` | Normalizes tickers and parses watchlist files. |
| `app/data/providers/base.py` | Provider interface for market data. |
| `app/data/providers/yfinance_provider.py` | Prototype provider using `yfinance`. |
| `app/db/duckdb_client.py` | Database client for DuckDB reads/writes. |
| `app/db/schema.sql` | Database schema. |
| `app/services/ingestion.py` | Reusable single-symbol and watchlist ingestion workflows. |
| `app/features/technical_indicators.py` | Feature engineering and indicator calculations. |
| `app/analysis/quick_report.py` | Converts features into deterministic JSON report. |
| `app/llm/ollama_client.py` | Sends prompts to local Ollama/Gemma. |
| `app/dashboard/streamlit_app.py` | Streamlit dashboard UI. |
| `app/dashboard/charts.py` | Candlestick chart construction and OHLC resampling. |
| `app/dashboard/analyze_actions.py` | Analyze tab Refresh action. |

## Service boundaries

The current app is a local monolith, but it is organized as if it could later become services:

- data provider service
- database service
- feature engineering service
- analysis service
- LLM service
- dashboard/API service

This makes the code easier to test and easier to replace later. For example, `YFinanceProvider` can later be replaced with Polygon, Alpaca, Tradier, Databento, Interactive Brokers, or another market data source without rewriting the dashboard.

## Data flow for Analyze Refresh

When the user enters a symbol in the Analyze tab and clicks **Refresh**:

1. `streamlit_app.py` reads the text input.
2. `refresh_symbol_data()` normalizes the ticker.
3. `YFinanceProvider` fetches price bars.
4. `DuckDBClient` stores the rows.
5. The active Analyze symbol is updated in Streamlit session state.
6. `build_quick_report()` rebuilds the JSON report.
7. `build_candlestick_figure()` rebuilds the chart.
8. If enabled, Gemma receives the updated report.

## Data flow for feature engineering

```text
price_bars table
    |
    v
fetch_price_bars(symbol)
    |
    v
build_feature_frame(price_df)
    |
    v
latest_complete_feature_row(feature_df)
    |
    v
build_quick_report(symbol, price_df)
```

## Production-readiness principles already used

- Configuration is centralized.
- Database access is isolated.
- Market data provider is abstracted.
- Feature engineering is deterministic and testable.
- Future-looking targets are excluded by default.
- Dashboard actions reuse service functions rather than duplicating business logic.
- Tests cover watchlist parsing, schema, ingestion workflows, charts, refresh actions, and feature engineering.
