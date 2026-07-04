"""Manual technical indicator calculation and persistence service.

This service intentionally calculates indicators only when the user asks for it.
It reads historical OHLCV rows from ``price_bars``, calculates deterministic
technical features, filters the output to a requested daily duration, and stores
those rows in the ``indicators`` table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import pandas as pd

from app.core.watchlist import normalize_symbol
from app.db.duckdb_client import DuckDBClient
from app.features.technical_indicators import build_feature_frame

SUPPORTED_INDICATOR_DURATIONS: Final[dict[str, pd.DateOffset]] = {
    "3m": pd.DateOffset(months=3),
    "6m": pd.DateOffset(months=6),
    "1y": pd.DateOffset(years=1),
    "3y": pd.DateOffset(years=3),
    "5y": pd.DateOffset(years=5),
}

INDICATOR_VALUE_COLUMNS: Final[list[str]] = [
    "return_1d",
    "return_5d",
    "return_21d",
    "log_return_1d",
    "daily_range_pct",
    "open_to_close_pct",
    "close_position_in_day_range",
    "sma_5",
    "sma_10",
    "sma_20",
    "sma_50",
    "sma_200",
    "close_vs_sma_5",
    "close_vs_sma_10",
    "close_vs_sma_20",
    "close_vs_sma_50",
    "close_vs_sma_200",
    "ema_12",
    "ema_26",
    "macd_line",
    "macd_signal",
    "macd_histogram",
    "rsi_14",
    "true_range",
    "atr_14",
    "atr_14_pct",
    "rolling_vol_20d",
    "rolling_vol_20d_annualized",
    "volume_sma_20",
    "volume_ratio_20",
    "dollar_volume",
    "dollar_volume_sma_20",
]


@dataclass(frozen=True)
class IndicatorCalculationResult:
    """Summary of one manual indicator calculation run."""

    symbol: str
    duration: str
    source_rows: int
    rows_stored: int
    first_trade_date: str
    latest_trade_date: str


def normalize_indicator_duration(duration: str) -> str:
    """Normalize and validate supported indicator durations.

    The table is intentionally capped at five years per calculation so the local
    database stays small while still supporting long-window features such as
    SMA-200.
    """
    normalized = duration.strip().lower()
    if normalized not in SUPPORTED_INDICATOR_DURATIONS:
        supported = ", ".join(SUPPORTED_INDICATOR_DURATIONS)
        raise ValueError(
            f"Unsupported indicator duration '{duration}'. Supported values: {supported}. "
            "The maximum calculation duration is 5y."
        )
    return normalized


def build_indicator_frame(symbol: str, price_df: pd.DataFrame, duration: str) -> pd.DataFrame:
    """Build indicator rows for one symbol and one duration.

    Indicators are calculated on the full available historical price frame first.
    Only after calculation do we filter to the requested output duration. This
    preserves long-window indicators, e.g. SMA-200, when more history exists than
    the requested display/storage period.
    """
    normalized_symbol = normalize_symbol(symbol)
    normalized_duration = normalize_indicator_duration(duration)

    if price_df.empty:
        raise ValueError(f"No price data found for {normalized_symbol}.")

    feature_df = build_feature_frame(price_df, include_targets=False)
    feature_df["trade_date"] = pd.to_datetime(feature_df["trade_date"])
    feature_df = feature_df.sort_values("trade_date").reset_index(drop=True)

    latest_trade_date = feature_df["trade_date"].max()
    cutoff_date = latest_trade_date - SUPPORTED_INDICATOR_DURATIONS[normalized_duration]
    output = feature_df.loc[feature_df["trade_date"] >= cutoff_date].copy()

    if output.empty:
        raise ValueError(
            f"No rows available for {normalized_symbol} after applying duration {normalized_duration}."
        )

    output["symbol"] = normalized_symbol
    output["calculation_duration"] = normalized_duration
    output["source_row_count"] = len(price_df)

    columns = ["symbol", "trade_date", "calculation_duration", "source_row_count"] + INDICATOR_VALUE_COLUMNS
    return output[columns].reset_index(drop=True)


def calculate_and_store_indicators(
    symbol: str,
    duration: str,
    db: DuckDBClient,
) -> IndicatorCalculationResult:
    """Calculate indicator rows for a ticker and persist them to DuckDB."""
    normalized_symbol = normalize_symbol(symbol)
    normalized_duration = normalize_indicator_duration(duration)

    price_df = db.fetch_price_bars(normalized_symbol)
    if price_df.empty:
        raise ValueError(
            f"No price data found for {normalized_symbol}. "
            f"Run: python -m app.main ingest-price {normalized_symbol} --period 5y"
        )

    indicator_df = build_indicator_frame(normalized_symbol, price_df, normalized_duration)
    rows_stored = db.upsert_indicators(indicator_df)

    return IndicatorCalculationResult(
        symbol=normalized_symbol,
        duration=normalized_duration,
        source_rows=len(price_df),
        rows_stored=rows_stored,
        first_trade_date=str(pd.to_datetime(indicator_df["trade_date"].min()).date()),
        latest_trade_date=str(pd.to_datetime(indicator_df["trade_date"].max()).date()),
    )
