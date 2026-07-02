# Operations Runbook

## Start project

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_project.ps1
```

macOS/Linux:

```bash
bash scripts/start_project.sh
```

## Start and ingest watchlist

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_project.ps1 -IngestWatchlist -Period 1y
```

## Check status

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\status_project.ps1
```

macOS/Linux:

```bash
bash scripts/status_project.sh
```

## Stop project

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_project.ps1
```

macOS/Linux:

```bash
bash scripts/stop_project.sh
```

## Stop by port when needed

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_project.ps1 -ForceByPort
```

## Stop external Ollama only when intended

Ollama may be shared by other projects. The stop script does not kill an external Ollama process unless you request it.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_project.ps1 -StopExternalOllama
```

## Logs

Check:

```text
logs/
```

Runtime process IDs are tracked under:

```text
.runtime/pids/
```

## Database backup

The local database usually lives at:

```text
data/trading_platform.duckdb
```

To back it up, stop the dashboard first, then copy the file:

```powershell
copy data\trading_platform.duckdb data\trading_platform_backup.duckdb
```

## Recommended daily research workflow

```bash
python -m app.main init-db
python -m app.main ingest-watchlist --period 1y
python -m app.main list-symbols
python -m app.main analyze AAPL
python -m app.main features AAPL --tail 5
```

Then use the dashboard for visual inspection.
