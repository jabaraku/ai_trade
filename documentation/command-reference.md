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
