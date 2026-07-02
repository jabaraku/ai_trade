# Setup Guide

## Prerequisites

Install:

- Python 3.11
- Git for Windows or Git on macOS/Linux
- VS Code or another editor
- Optional: Ollama, if you want Gemma explanations

## Windows PowerShell setup

From the folder where you extracted the project:

```powershell
cd C:\Users\Administrator\Documents\trading\ai_trading_platform_volume1_starter\ai_trading_platform_volume1_starter
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
copy .env.example .env
python -m app.main doctor
python -m app.main init-db
```

If PowerShell blocks scripts because they are not signed, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_project.ps1
```

Or unblock the local scripts:

```powershell
Get-ChildItem .\scripts\*.ps1 | Unblock-File
```

## macOS/Linux setup

```bash
cd ai_trading_platform_volume1_starter
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
python -m app.main doctor
python -m app.main init-db
```

## First data load

```bash
python -m app.main ingest-price AAPL --period 1y
python -m app.main analyze AAPL
python -m app.main features AAPL --tail 5
```

## Start the dashboard

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_project.ps1
```

macOS/Linux:

```bash
bash scripts/start_project.sh
```

Then open:

```text
http://localhost:8501
```

## Stop the dashboard and local project processes

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_project.ps1
```

macOS/Linux:

```bash
bash scripts/stop_project.sh
```

## Verify setup

Run:

```bash
python -m app.main doctor
python -m compileall app tests -q
pytest -q
```

All tests should pass before you begin adding new features.
