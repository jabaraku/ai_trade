from __future__ import annotations

import pandas as pd
import pytest

from app.dashboard.charts import (
    BULLISH_CANDLE_COLOR,
    BEARISH_CANDLE_COLOR,
    build_candlestick_figure,
    normalize_duration,
    normalize_timeframe,
    prepare_candlestick_data,
)


def _sample_daily_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": pd.to_datetime(
                [
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                    "2024-01-08",
                    "2024-01-09",
                ]
            ),
            "open": [100.0, 105.0, 104.0, 107.0, 108.0, 109.0],
            "high": [110.0, 106.0, 108.0, 111.0, 112.0, 113.0],
            "low": [99.0, 95.0, 101.0, 103.0, 106.0, 107.0],
            "close": [108.0, 96.0, 107.0, 110.0, 109.0, 112.0],
            "volume": [1000, 1200, 1300, 1400, 1500, 1600],
        }
    )


def test_build_candlestick_figure_uses_ohlc_and_red_green_colors():
    prices = _sample_daily_prices().head(2)

    fig = build_candlestick_figure(prices, "AAPL")

    assert len(fig.data) == 1
    candle = fig.data[0]
    assert candle.type == "candlestick"
    assert list(candle.open) == [100.0, 105.0]
    assert list(candle.high) == [110.0, 106.0]
    assert list(candle.low) == [99.0, 95.0]
    assert list(candle.close) == [108.0, 96.0]
    assert candle.increasing.line.color == BULLISH_CANDLE_COLOR
    assert candle.decreasing.line.color == BEARISH_CANDLE_COLOR


def test_prepare_candlestick_data_returns_daily_rows_for_daily_timeframe():
    prices = _sample_daily_prices()

    chart_data = prepare_candlestick_data(prices, timeframe="Daily", duration="1Y")

    assert len(chart_data) == len(prices)
    assert list(chart_data["close"]) == list(prices["close"])


def test_prepare_candlestick_data_aggregates_weekly_ohlcv():
    prices = _sample_daily_prices()

    chart_data = prepare_candlestick_data(prices, timeframe="Weekly", duration="1Y")

    assert len(chart_data) == 2
    first_week = chart_data.iloc[0]
    assert first_week["open"] == 100.0
    assert first_week["high"] == 111.0
    assert first_week["low"] == 95.0
    assert first_week["close"] == 110.0
    assert first_week["volume"] == 4900


def test_prepare_candlestick_data_aggregates_monthly_ohlcv():
    prices = _sample_daily_prices()

    chart_data = prepare_candlestick_data(prices, timeframe="Monthly", duration="1Y")

    assert len(chart_data) == 1
    month = chart_data.iloc[0]
    assert month["open"] == 100.0
    assert month["high"] == 113.0
    assert month["low"] == 95.0
    assert month["close"] == 112.0
    assert month["volume"] == 8000


def test_prepare_candlestick_data_filters_to_selected_duration_from_latest_local_date():
    prices = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(["2020-01-01", "2023-01-01", "2024-01-01"]),
            "open": [10.0, 20.0, 30.0],
            "high": [11.0, 21.0, 31.0],
            "low": [9.0, 19.0, 29.0],
            "close": [10.5, 20.5, 30.5],
            "volume": [100, 200, 300],
        }
    )

    chart_data = prepare_candlestick_data(prices, timeframe="Daily", duration="1Y")

    assert list(chart_data["trade_date"]) == [
        pd.Timestamp("2023-01-01"),
        pd.Timestamp("2024-01-01"),
    ]


def test_normalizers_reject_unsupported_values():
    with pytest.raises(ValueError):
        normalize_timeframe("hourly")
    with pytest.raises(ValueError):
        normalize_duration("2Y")
