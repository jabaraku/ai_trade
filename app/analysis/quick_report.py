from __future__ import annotations

import math
from typing import Any

from app.features.technical_indicators import build_feature_frame, latest_complete_feature_row


def _round_optional(value: Any, digits: int = 4):
    if value is None:
        return None
    try:
        if math.isnan(float(value)):
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return value


def build_quick_report(symbol: str, price_df) -> dict:
    """Build a deterministic feature-based report before ML and LLM layers are added."""
    featured = build_feature_frame(price_df)
    row = latest_complete_feature_row(featured, minimum_history_days=50)

    return {
        "symbol": symbol.upper(),
        "trade_date": str(row["trade_date"].date() if hasattr(row["trade_date"], "date") else row["trade_date"]),
        "close": _round_optional(row["close"], 4),
        "price_action": {
            "return_1d_pct": _round_optional(row["return_1d"] * 100, 3),
            "return_5d_pct": _round_optional(row["return_5d"] * 100, 3),
            "return_21d_pct": _round_optional(row["return_21d"] * 100, 3),
            "daily_range_pct": _round_optional(row["daily_range_pct"] * 100, 3),
            "open_to_close_pct": _round_optional(row["open_to_close_pct"] * 100, 3),
        },
        "trend": {
            "sma_20": _round_optional(row["sma_20"], 4),
            "sma_50": _round_optional(row["sma_50"], 4),
            "sma_200": _round_optional(row["sma_200"], 4),
            "close_vs_sma_20_pct": _round_optional(row["close_vs_sma_20"] * 100, 3),
            "close_vs_sma_50_pct": _round_optional(row["close_vs_sma_50"] * 100, 3),
            "close_vs_sma_200_pct": _round_optional(row["close_vs_sma_200"] * 100, 3),
            "macd_line": _round_optional(row["macd_line"], 4),
            "macd_signal": _round_optional(row["macd_signal"], 4),
            "macd_histogram": _round_optional(row["macd_histogram"], 4),
        },
        "momentum_volatility": {
            "rsi_14": _round_optional(row["rsi_14"], 2),
            "atr_14": _round_optional(row["atr_14"], 4),
            "atr_14_pct": _round_optional(row["atr_14_pct"] * 100, 3),
            "rolling_vol_20d_annualized_pct": _round_optional(
                row["rolling_vol_20d_annualized"] * 100, 3
            ),
        },
        "volume_liquidity": {
            "volume": int(row["volume"]),
            "volume_sma_20": _round_optional(row["volume_sma_20"], 0),
            "volume_ratio_20": _round_optional(row["volume_ratio_20"], 3),
            "dollar_volume": _round_optional(row["dollar_volume"], 0),
            "dollar_volume_sma_20": _round_optional(row["dollar_volume_sma_20"], 0),
        },
        "data_notes": [
            "This report uses deterministic technical features only.",
            "No XGBoost prediction is being made yet.",
            "Future-looking target columns are excluded from this report to avoid look-ahead bias.",
        ],
    }


def build_gemma_prompt(report: dict, db_context: dict | None = None) -> str:
    """Build the cautious Gemma prompt for deterministic report explanation.

    When db_context is provided, Gemma receives a compact read-only extract from
    DuckDB. Gemma still cannot query the database directly.
    """
    context_block = ""
    if db_context is not None:
        context_block = f"""

Controlled DuckDB context prepared by Python:
{db_context}

Important database-context rules:
- You cannot query DuckDB directly.
- Use only the report and context included in this prompt.
- Do not invent dates, rows, timeframes, or future outcomes.
"""

    return f"""
You are a cautious trading research assistant. You do not give financial advice.
You explain market data in plain English and highlight uncertainty.

Analyze this deterministic feature report:

{report}{context_block}

Return:
1. A neutral summary.
2. Bullish considerations.
3. Bearish considerations.
4. What data is missing before making any trading decision.
5. A reminder that this is research only.
""".strip()
