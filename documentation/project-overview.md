# Project Overview

## Product vision

The goal is to build a local AI trading research platform using two complementary components:

- **XGBoost** for structured numeric modeling from historical market features.
- **Gemma through Ollama** for natural-language explanation, summarization, critique, and research assistance.

The system should behave like a research terminal, not like a blind autonomous trading bot. The platform should help answer questions such as:

- What does the recent price action look like?
- Which indicators are stretched, improving, weakening, or neutral?
- What does a deterministic quick report say about a symbol?
- What does a local LLM explanation say, given the structured report?
- What data exists locally and how fresh is it?

## Current capabilities

The current repository includes:

- single-symbol ingestion: `python -m app.main ingest-price AAPL --period 1y`
- watchlist ingestion: `python -m app.main ingest-watchlist --period 1y`
- local symbol summary: `python -m app.main list-symbols`
- deterministic analysis: `python -m app.main analyze AAPL`
- feature preview: `python -m app.main features AAPL --tail 5`
- optional Gemma explanation: `python -m app.main analyze AAPL --use-gemma`
- Streamlit dashboard with Overview, Ingest, Analyze, and Config tabs
- Shared Ingest tab ticker that drives the Analyze tab chart and JSON report
- candlestick charts with duration and timeframe controls
- local start/stop/status scripts

## Explicit non-goals in this phase

This phase does **not** attempt to:

- place live trades,
- connect to a brokerage account,
- guarantee predictions,
- train XGBoost yet,
- fine-tune Gemma,
- ingest real-time tick-level data,
- ingest full options chains,
- perform portfolio optimization.

Those are later phases.

## Why this project is structured this way

A trading AI system should not make every decision inside an LLM prompt. The safer and more maintainable design is:

```text
Market data -> Feature engineering -> Quant model -> Risk layer -> LLM explanation -> Human decision
```

In the current phase, we have the first pieces of that pipeline:

```text
yfinance -> DuckDB -> feature engine -> quick report -> candlestick chart -> optional Gemma explanation
```

## Recommended use

Use this project to learn and validate the system design. Treat every output as research material. Never use a generated explanation as a standalone reason to buy, sell, or hold any financial instrument.
