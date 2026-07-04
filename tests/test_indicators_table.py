from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.db.duckdb_client import DuckDBClient
from app.services.indicators import (
    build_indicator_frame,
    calculate_and_store_indicators,
    normalize_indicator_duration,
)


def make_price_frame(rows: int = 2600) -> pd.DataFrame:
    dates = pd.date_range("2016-01-01", periods=rows, freq="B")
    close = pd.Series(range(rows), dtype="float") * 0.05 + 100
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


def test_schema_has_indicators_table_and_columns():
    schema = Path("app/db/schema.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS indicators" in schema
    assert "sma_200 DOUBLE" in schema
    assert "macd_histogram DOUBLE" in schema
    assert "PRIMARY KEY (symbol, trade_date)" in schema


def test_duration_validation_caps_at_five_years():
    assert normalize_indicator_duration(" 5Y ") == "5y"
    with pytest.raises(ValueError, match="maximum calculation duration is 5y"):
        normalize_indicator_duration("10y")


def test_build_indicator_frame_calculates_full_history_then_filters_to_duration():
    prices = make_price_frame()

    indicators = build_indicator_frame("aapl", prices, "5y")

    latest_date = pd.to_datetime(prices["trade_date"]).max()
    cutoff = latest_date - pd.DateOffset(years=5)
    assert pd.to_datetime(indicators["trade_date"]).min() >= cutoff
    assert pd.to_datetime(indicators["trade_date"]).max() == latest_date
    assert len(indicators) < len(prices)
    assert set(["sma_20", "sma_50", "sma_200", "rsi_14", "atr_14"]).issubset(indicators.columns)
    assert indicators["source_row_count"].iloc[0] == len(prices)
    assert indicators["calculation_duration"].iloc[0] == "5y"


def test_calculate_and_store_indicators_persists_rows_to_duckdb(tmp_path: Path):
    db = DuckDBClient(tmp_path / "test.duckdb")
    db.init_schema()
    prices = make_price_frame()
    db.insert_price_bars(prices)

    result = calculate_and_store_indicators("AAPL", "5y", db)
    stored = db.fetch_indicators("AAPL")

    assert result.symbol == "AAPL"
    assert result.duration == "5y"
    assert result.source_rows == len(prices)
    assert result.rows_stored == len(stored)
    assert len(stored) < len(prices)
    assert stored["sma_200"].notna().any()


def test_main_exposes_calculate_command():
    text = Path("app/main.py").read_text(encoding="utf-8")
    assert '@app.command("calculate")' in text
    assert "python -m app.main calculate AAPL 5y" in text
    assert '@app.command("list-indicators")' in text
