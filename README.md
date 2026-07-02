# AI Trading Research Platform - Volume 1 Starter

This repository is the foundation for a local AI trading research platform using:

- Gemma through Ollama for natural-language analysis
- XGBoost for structured numerical prediction
- DuckDB for local analytical storage
- yfinance for prototype market data ingestion
- Streamlit for the later dashboard

This starter is intentionally paper-trading/research only. It does not place live trades.

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

## Local LLM check

Install Ollama, then run one of these:

```bash
ollama pull gemma3:4b
ollama run gemma3:4b
```

If your machine struggles, use the smallest Gemma model available in your Ollama library.

## Project philosophy

This project separates responsibilities:

- Quantitative models produce probabilities and measurable signals.
- Gemma explains, critiques, and summarizes evidence.
- The risk engine constrains what the system is allowed to recommend.
- Backtesting and paper trading decide whether ideas survive.
