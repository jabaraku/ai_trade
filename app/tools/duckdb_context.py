"""Safe DuckDB context extraction for Gemma.

Gemma should not receive raw database access or arbitrary SQL execution rights.
Instead, Python extracts approved read-only slices from DuckDB and sends a compact
JSON context to the model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.core.watchlist import normalize_symbol
from app.db.duckdb_client import DuckDBClient


DEFAULT_ROW_LIMIT = 5
MAX_ROW_LIMIT = 25

PRICE_COLUMNS_FOR_LLM = [
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
    "provider",
]

INDICATOR_COLUMNS_FOR_LLM = [
    "trade_date",
    "calculation_duration",
    "return_1d",
    "return_5d",
    "return_21d",
    "daily_range_pct",
    "open_to_close_pct",
    "sma_20",
    "sma_50",
    "sma_200",
    "close_vs_sma_20",
    "close_vs_sma_50",
    "close_vs_sma_200",
    "macd_line",
    "macd_signal",
    "macd_histogram",
    "rsi_14",
    "atr_14",
    "atr_14_pct",
    "rolling_vol_20d_annualized",
    "volume_ratio_20",
    "dollar_volume",
]


@dataclass(frozen=True)
class DuckDBGemmaContextOptions:
    """Options for how much database context is shared with Gemma."""

    row_limit: int = DEFAULT_ROW_LIMIT
    include_price_rows: bool = True
    include_indicator_rows: bool = True

    def safe_row_limit(self) -> int:
        """Clamp row limit so prompts do not become too large."""
        return max(1, min(int(self.row_limit), MAX_ROW_LIMIT))


def _json_safe(value: Any) -> Any:
    """Convert pandas/numpy/date values into JSON-safe Python values."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            return value
    return value


def _records_for_llm(df: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    """Return compact JSON-safe records for selected columns that exist."""
    if df.empty:
        return []
    available = [column for column in columns if column in df.columns]
    if not available:
        return []
    records = []
    for row in df[available].to_dict("records"):
        records.append({key: _json_safe(value) for key, value in row.items()})
    return records


def _first_record(df: pd.DataFrame) -> dict[str, Any] | None:
    if df.empty:
        return None
    row = df.iloc[0].to_dict()
    return {key: _json_safe(value) for key, value in row.items()}


def build_duckdb_context(
    db: DuckDBClient,
    symbol: str,
    options: DuckDBGemmaContextOptions | None = None,
) -> dict[str, Any]:
    """Build a safe read-only database context for Gemma.

    The returned object intentionally includes table names, row counts, date
    coverage, and a small tail of rows. It never gives Gemma SQL execution
    capability.
    """
    opts = options or DuckDBGemmaContextOptions()
    row_limit = opts.safe_row_limit()
    normalized_symbol = normalize_symbol(symbol)

    price_summary = db.fetch_price_summary(normalized_symbol)
    indicator_summary = db.fetch_indicator_symbol_summary(normalized_symbol)

    context: dict[str, Any] = {
        "symbol": normalized_symbol,
        "database_access_mode": "read-only summarized context prepared by Python",
        "important_rules_for_gemma": [
            "You cannot directly query DuckDB.",
            "Use only the database context included in this prompt.",
            "Do not invent rows, timeframes, dates, indicators, or future outcomes.",
            "Do not treat future target columns as available trading information.",
        ],
        "available_tables": {
            "price_bars": {
                "description": "Daily OHLCV market data ingested from the configured provider.",
                "summary_for_symbol": _first_record(price_summary),
            },
            "indicators": {
                "description": "Persisted daily deterministic technical indicators calculated from price_bars.",
                "summary_for_symbol": _first_record(indicator_summary),
            },
        },
    }

    if opts.include_price_rows:
        latest_price_rows = db.fetch_latest_price_bars(normalized_symbol, row_limit)
        context["latest_price_bars"] = _records_for_llm(latest_price_rows, PRICE_COLUMNS_FOR_LLM)

    if opts.include_indicator_rows:
        latest_indicator_rows = db.fetch_latest_indicators(normalized_symbol, row_limit)
        context["latest_indicator_rows"] = _records_for_llm(
            latest_indicator_rows,
            INDICATOR_COLUMNS_FOR_LLM,
        )

    context["notes"] = [
        f"Row samples are capped at {row_limit} latest rows to keep local Gemma fast.",
        "If indicator rows are empty, run: python -m app.main calculate <SYMBOL> 5y",
        "This database context is for research explanation only and is not financial advice.",
    ]
    return context


def build_gemma_db_prompt(symbol: str, question: str, db_context: dict[str, Any]) -> str:
    """Create a strict prompt for Gemma using controlled DuckDB context."""
    return f"""
You are a cautious trading research assistant. You do not give financial advice.

You are being given a controlled, read-only DuckDB context prepared by Python.
You cannot query the database directly. You must not invent missing data.

Rules:
1. Use only the DuckDB context included below.
2. If the context does not contain enough data, say exactly what is missing.
3. Do not infer a timeframe unless it appears in the table summaries or rows.
4. Do not claim to know future price movement.
5. Do not recommend buying, selling, calls, or puts.
6. Treat this as research-only analysis.

User question for {normalize_symbol(symbol)}:
{question}

DuckDB context:
{db_context}

Return:
1. Direct answer based only on the provided context.
2. Relevant facts from price_bars.
3. Relevant facts from indicators.
4. What is missing or uncertain.
5. Research-only reminder.
""".strip()
