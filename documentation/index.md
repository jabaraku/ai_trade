# AI Trading Research Platform Documentation

Welcome to the project documentation for the **AI Trading Research Platform**. This documentation is meant to be read directly from the repository. Every page is plain Markdown, so it works in VS Code, GitHub, or any Markdown viewer.

> Research-only safety rule: this project is an AI-assisted research terminal. It does not place live trades, does not manage money, and does not remove your responsibility to verify data, assumptions, risk, and suitability.

## What this project does today

The current project can:

1. ingest daily OHLCV price bars from Yahoo Finance through `yfinance`,
2. store local market history in DuckDB,
3. ingest one symbol or a watchlist,
4. compute a first production-style feature engineering set,
5. render a Streamlit dashboard,
6. show red/green candlestick charts,
7. switch chart timeframe between Daily, Weekly, and Monthly,
8. switch chart duration between 3M, 6M, 1Y, 3Y, and 5Y,
9. refresh the Analyze tab from a typed symbol,
10. generate a deterministic JSON quick report,
11. optionally send that JSON report to local Gemma through Ollama for a cautious explanation.

## Documentation map

Start here, then move page by page:

| Page | Purpose |
|---|---|
| [Project Overview](project-overview.md) | Product vision, current capabilities, and non-goals. |
| [Architecture](architecture.md) | System components and how data moves through the app. |
| [Setup Guide](setup-guide.md) | Exact setup steps for Windows and macOS/Linux. |
| [Command Reference](command-reference.md) | CLI commands and Makefile shortcuts. |
| [Dashboard Guide](dashboard-guide.md) | How to use Overview, Ingest, Analyze, and Config tabs. |
| [Data Pipeline](data-pipeline.md) | Where data comes from, where it is stored, and refresh behavior. |
| [Feature Engineering](feature-engineering.md) | How raw OHLCV data becomes model-ready features. |
| [Indicator Reference](indicators.md) | Detailed description of every current indicator/feature. |
| [Gemma and Ollama](gemma-ollama.md) | How local LLM analysis fits into the project. |
| [Operations Runbook](operations-runbook.md) | Start, stop, status, logs, and common admin tasks. |
| [Testing and Quality](testing-quality.md) | Test strategy, commands, and validation expectations. |
| [Troubleshooting](troubleshooting.md) | Common errors and fixes. |
| [Roadmap](roadmap.md) | What to build next. |
| [Glossary](glossary.md) | Trading, ML, and engineering terms. |

## Suggested reading order

1. Read [Project Overview](project-overview.md).
2. Read [Architecture](architecture.md).
3. Follow [Setup Guide](setup-guide.md).
4. Run commands from [Command Reference](command-reference.md).
5. Use the app with [Dashboard Guide](dashboard-guide.md).
6. Study [Feature Engineering](feature-engineering.md) and [Indicator Reference](indicators.md).

## Repository areas that matter most

```text
app/
  analysis/       deterministic JSON quick report logic
  core/           settings, paths, logging, watchlist parsing
  dashboard/      Streamlit UI and charting
  data/           market data provider interfaces
  db/             DuckDB client and schema
  features/       feature engineering and indicators
  llm/            Ollama/Gemma client
  services/       reusable business workflows such as ingestion
config/           watchlist and project configuration inputs
data/             local DuckDB database and data folders
documentation/    project docs you are reading now
scripts/          start/stop/status scripts
models/           future saved ML models
tests/            unit and integration-style tests
```

## Current safety boundary

The project is intentionally limited to research and analysis. Any future brokerage integration must be added behind explicit paper-trading safeguards before live execution is even considered.
