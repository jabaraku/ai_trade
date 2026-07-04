# Command Reference

All commands should be run from the project root while the virtual environment is active.

## Check environment

```bash
python -m app.main doctor
```

Checks configuration and Ollama availability.

## Initialize database

```bash
python -m app.main init-db
```

Creates the DuckDB schema if needed.

## Ingest one symbol

```bash
python -m app.main ingest-price AAPL --period 1y
```

Common periods:

```text
6mo
1y
2y
5y
10y
```

## Ingest the default watchlist

```bash
python -m app.main ingest-watchlist --period 1y
```

Default watchlist path:

```text
config/watchlist.txt
```

## Ingest a custom watchlist

```bash
python -m app.main ingest-watchlist --watchlist config/my_watchlist.txt --period 5y
```

## Stop watchlist ingestion on first failure

```bash
python -m app.main ingest-watchlist --period 1y --stop-on-error
```

## List locally stored symbols

```bash
python -m app.main list-symbols
```

Shows symbol, number of stored rows, first date, latest date, and data provider.

## Analyze a symbol

```bash
python -m app.main analyze AAPL
```

## Analyze with Gemma

```bash
python -m app.main analyze AAPL --use-gemma
```

Requires Ollama to be running and a Gemma model to be available locally.

## Generate feature preview

```bash
python -m app.main features AAPL --tail 5
```

JSON output:

```bash
python -m app.main features AAPL --tail 5 --output json
```

Include future-looking targets for dataset development:

```bash
python -m app.main features AAPL --tail 5 --include-targets
```

Do not use target columns as model input features.

## Start/status/stop

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_project.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\status_project.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\stop_project.ps1
```

macOS/Linux:

```bash
bash scripts/start_project.sh
bash scripts/status_project.sh
bash scripts/stop_project.sh
```

## Makefile shortcuts

```bash
make doctor
make init-db
make ingest-aapl
make ingest-watchlist
make list-symbols
make analyze-aapl
make features-aapl
make dashboard
make start
make status
make stop
make test
```

On Windows, if `make` is not installed, use the equivalent Python or PowerShell commands directly.

## Calculate and persist technical indicators

The `calculate` command manually calculates daily technical indicators for one ticker and stores them in the DuckDB `indicators` table.

```bash
python -m app.main calculate AAPL 5y
```

Alias:

```bash
python -m app.main calculate-indicators AAPL 5y
```

Supported durations:

```text
3m
6m
1y
3y
5y
```

The maximum duration is `5y`. If more price history exists in `price_bars`, the feature engine calculates indicators using all available history first, then persists only the requested duration. This helps long-window indicators such as `sma_200` remain accurate.

List persisted indicator coverage:

```bash
python -m app.main list-indicators
```

## DuckDB context for Gemma

Gemma does not get direct SQL access. The application extracts a small, approved,
read-only context from DuckDB and sends that context to Ollama/Gemma.

Preview the exact context that would be sent to Gemma:

```powershell
python -m app.main db-context AAPL --rows 5
```

Ask Gemma a question using controlled DuckDB context:

```powershell
python -m app.main gemma-db AAPL "What do the latest indicator rows say about trend and momentum?"
```

The context includes:

- `price_bars` summary for the symbol
- latest `price_bars` rows
- `indicators` summary for the symbol
- latest `indicators` rows

The row sample is capped to protect the CPU and keep local Gemma responsive.
