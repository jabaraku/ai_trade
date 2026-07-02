# Troubleshooting

## PowerShell says the script is not digitally signed

Run with bypass:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_project.ps1
```

Or unblock scripts:

```powershell
Get-ChildItem .\scripts\*.ps1 | Unblock-File
```

## `python` command not found

Try:

```powershell
py -3.11 --version
```

or reinstall Python 3.11 and ensure it is on PATH.

## Virtual environment not active

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

## `No data found for AAPL`

Ingest data first:

```bash
python -m app.main ingest-price AAPL --period 1y
```

Or use the dashboard Ingest tab's **Ingest ticker** button.

## Dashboard opens but chart is empty

Possible causes:

- The symbol has not been ingested.
- The selected duration requires more history than you stored.
- The data provider returned no rows.

Fix:

```bash
python -m app.main ingest-price AAPL --period 5y
```

## Gemma explanation fails

Check Ollama:

```bash
python -m app.main doctor
```

Make sure Ollama is installed, running, and the model name in `.env` exists locally.

## `ModuleNotFoundError: app`

Run from the project root and install editable mode:

```bash
pip install -e ".[dev]"
```

## Patch fails to apply

Your local files may differ from the version the patch was created against. Use the full upgraded ZIP instead, or apply the patch to a clean copy of the prior version.

## yfinance request fails

Possible causes:

- internet issue,
- invalid ticker,
- temporary Yahoo Finance response problem,
- rate limiting,
- delisted or unsupported symbol.

Try another symbol such as `AAPL` or wait and retry.


## Streamlit session-state error after changing symbols

The current dashboard avoids the previous `analyze_symbol_input` issue by using a single shared widget key, `active_symbol_input`, from the Ingest tab. The Analyze tab does not mutate widget-backed session state. If you customize the dashboard and see a session-state error, do not assign to a widget key after the widget has been instantiated.
