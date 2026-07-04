from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.db.duckdb_client import DuckDBClient
from app.services.indicators import calculate_and_store_indicators
from app.tools.duckdb_context import (
    DuckDBGemmaContextOptions,
    build_duckdb_context,
    build_gemma_db_prompt,
)


def make_price_frame(rows: int = 260) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = pd.Series(range(rows), dtype="float") * 0.25 + 100
    return pd.DataFrame(
        {
            "symbol": "AAPL",
            "trade_date": dates.date,
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "adj_close": close,
            "volume": 1_000_000,
            "provider": "unit-test",
        }
    )


def test_build_duckdb_context_includes_price_and_indicator_summaries(tmp_path: Path):
    db = DuckDBClient(tmp_path / "test.duckdb")
    db.init_schema()
    db.insert_price_bars(make_price_frame())
    calculate_and_store_indicators("AAPL", "1y", db)

    context = build_duckdb_context(db, "aapl", DuckDBGemmaContextOptions(row_limit=3))

    assert context["symbol"] == "AAPL"
    assert context["database_access_mode"] == "read-only summarized context prepared by Python"
    assert context["available_tables"]["price_bars"]["summary_for_symbol"]["rows"] == 260
    assert context["available_tables"]["indicators"]["summary_for_symbol"]["rows"] > 0
    assert len(context["latest_price_bars"]) == 3
    assert len(context["latest_indicator_rows"]) == 3
    assert "rsi_14" in context["latest_indicator_rows"][0]


def test_duckdb_context_caps_row_limit(tmp_path: Path):
    db = DuckDBClient(tmp_path / "test.duckdb")
    db.init_schema()
    db.insert_price_bars(make_price_frame())

    context = build_duckdb_context(db, "AAPL", DuckDBGemmaContextOptions(row_limit=500))

    assert len(context["latest_price_bars"]) == 25


def test_build_gemma_db_prompt_is_strict():
    context = {
        "symbol": "AAPL",
        "latest_price_bars": [],
        "latest_indicator_rows": [],
    }
    prompt = build_gemma_db_prompt(
        "AAPL",
        "What does the indicators table say?",
        context,
    )

    assert "You cannot query the database directly" in prompt
    assert "Do not invent" in prompt
    assert "DuckDB context" in prompt
    assert "What does the indicators table say?" in prompt


def test_main_exposes_database_context_commands():
    text = Path("app/main.py").read_text(encoding="utf-8")
    assert '@app.command("db-context")' in text
    assert '@app.command("gemma-db")' in text
