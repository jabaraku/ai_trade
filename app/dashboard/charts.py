from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go


BULLISH_CANDLE_COLOR = "#16a34a"
BEARISH_CANDLE_COLOR = "#dc2626"

SMA_WINDOWS: tuple[int, ...] = (20, 50, 200)
SMA_LINE_COLORS: dict[int, str] = {
    20: "#7c3aed",
    50: "#db2777",
    200: "#64748b",
}

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


def _add_sma_overlay_columns(chart_data: pd.DataFrame) -> pd.DataFrame:
    """Add SMA overlay columns calculated on the displayed candle timeframe.

    The function expects the data to already be sorted and resampled to the selected
    candle timeframe. For example, SMA 20 means 20 daily candles on Daily,
    20 weekly candles on Weekly, and 20 monthly candles on Monthly.
    """
    data = chart_data.copy()
    for window in SMA_WINDOWS:
        data[f"sma_{window}"] = data["close"].rolling(window=window, min_periods=window).mean()
    return data


def _filter_by_duration(chart_data: pd.DataFrame, duration: str) -> pd.DataFrame:
    """Filter chart data backward from the latest locally stored bar date."""
    if chart_data.empty:
        return chart_data.reset_index(drop=True)

    normalized_duration = normalize_duration(duration)
    latest_date = chart_data["trade_date"].max()
    duration_offset = DURATION_OPTIONS[normalized_duration]
    if duration_offset is None:
        return chart_data.reset_index(drop=True)

    start_date = latest_date - duration_offset
    return chart_data[chart_data["trade_date"] >= start_date].reset_index(drop=True)


def prepare_candlestick_data(
    prices: pd.DataFrame,
    timeframe: str = "Daily",
    duration: str = "1Y",
) -> pd.DataFrame:
    """Prepare OHLCV candles plus SMA overlays for the selected chart controls.

    The source data is expected to contain daily OHLCV bars. Data is first sorted,
    then aggregated to the selected timeframe, then SMA overlays are calculated,
    and only then is the selected duration applied. Calculating SMAs before the
    duration trim allows long overlays such as SMA 200 to appear on a 3M chart
    when enough older local history exists.
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

    if normalized_timeframe != "Daily":
        rule = TIMEFRAME_OPTIONS[normalized_timeframe]
        data = (
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

    data = _add_sma_overlay_columns(data)
    return _filter_by_duration(data, normalized_duration)


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

    fig = go.Figure()
    fig.add_trace(
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
            name=f"{symbol.upper()} candles",
        )
    )

    for window in SMA_WINDOWS:
        column_name = f"sma_{window}"
        fig.add_trace(
            go.Scatter(
                x=chart_data["trade_date"],
                y=chart_data[column_name],
                mode="lines",
                name=f"SMA {window}",
                line={"color": SMA_LINE_COLORS[window], "width": 1.6},
                hovertemplate=(
                    f"SMA {window}<br>"
                    "Date=%{x|%Y-%m-%d}<br>"
                    "Value=%{y:.2f}<extra></extra>"
                ),
            )
        )
    title = f"{symbol.upper()} {normalized_timeframe.lower()} candlestick chart · {normalized_duration}"
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=560,
        margin={"l": 20, "r": 20, "t": 70, "b": 20},
        legend={
            "title": {"text": "Color key"},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        hovermode="x unified",
    )
    return fig
