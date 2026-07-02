from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go


BULLISH_CANDLE_COLOR = "#16a34a"
BEARISH_CANDLE_COLOR = "#dc2626"

TIMEFRAME_OPTIONS: dict[str, str] = {
    "Daily": "D",
    "Weekly": "W-FRI",
    "Monthly": "ME",
}

DURATION_OPTIONS: dict[str, pd.DateOffset | None] = {
    "3M": pd.DateOffset(months=3),
    "6M": pd.DateOffset(months=6),
    "1Y": pd.DateOffset(years=1),
    "3Y": pd.DateOffset(years=3),
    "5Y": pd.DateOffset(years=5),
}


@dataclass(frozen=True)
class ChartSelection:
    """User-selected chart controls from the Analyze tab."""

    timeframe: str = "Daily"
    duration: str = "1Y"


def normalize_timeframe(timeframe: str) -> str:
    normalized = timeframe.strip().title()
    if normalized not in TIMEFRAME_OPTIONS:
        raise ValueError(
            f"Unsupported timeframe '{timeframe}'. "
            f"Expected one of: {', '.join(TIMEFRAME_OPTIONS)}"
        )
    return normalized


def normalize_duration(duration: str) -> str:
    normalized = duration.strip().upper()
    if normalized not in DURATION_OPTIONS:
        raise ValueError(
            f"Unsupported duration '{duration}'. "
            f"Expected one of: {', '.join(DURATION_OPTIONS)}"
        )
    return normalized


def prepare_candlestick_data(
    prices: pd.DataFrame,
    timeframe: str = "Daily",
    duration: str = "1Y",
) -> pd.DataFrame:
    """Filter local daily bars by duration and aggregate them to the selected timeframe.

    The source data is expected to contain daily OHLCV bars. Duration is measured backward
    from the latest locally stored trade date for the symbol, not from today's calendar date.
    This makes the chart deterministic when the database is not freshly updated.
    """
    if prices.empty:
        return prices.copy()

    normalized_timeframe = normalize_timeframe(timeframe)
    normalized_duration = normalize_duration(duration)

    required_columns = {"trade_date", "open", "high", "low", "close", "volume"}
    missing = required_columns.difference(prices.columns)
    if missing:
        raise ValueError(f"Missing required chart columns: {sorted(missing)}")

    data = prices.copy()
    data["trade_date"] = pd.to_datetime(data["trade_date"])
    data = data.sort_values("trade_date")

    latest_date = data["trade_date"].max()
    duration_offset = DURATION_OPTIONS[normalized_duration]
    if duration_offset is not None:
        start_date = latest_date - duration_offset
        data = data[data["trade_date"] >= start_date]

    if data.empty or normalized_timeframe == "Daily":
        return data.reset_index(drop=True)

    rule = TIMEFRAME_OPTIONS[normalized_timeframe]
    aggregated = (
        data.set_index("trade_date")
        .resample(rule)
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
    return aggregated


def build_candlestick_figure(
    prices: pd.DataFrame,
    symbol: str,
    timeframe: str = "Daily",
    duration: str = "1Y",
) -> go.Figure:
    """Build a red/green candlestick chart from local OHLCV price bars."""
    normalized_timeframe = normalize_timeframe(timeframe)
    normalized_duration = normalize_duration(duration)
    chart_data = prepare_candlestick_data(prices, normalized_timeframe, normalized_duration)

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=chart_data["trade_date"],
                open=chart_data["open"],
                high=chart_data["high"],
                low=chart_data["low"],
                close=chart_data["close"],
                increasing_line_color=BULLISH_CANDLE_COLOR,
                increasing_fillcolor=BULLISH_CANDLE_COLOR,
                decreasing_line_color=BEARISH_CANDLE_COLOR,
                decreasing_fillcolor=BEARISH_CANDLE_COLOR,
                name=symbol.upper(),
            )
        ]
    )
    title = f"{symbol.upper()} {normalized_timeframe.lower()} candlestick chart · {normalized_duration}"
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=560,
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    return fig
