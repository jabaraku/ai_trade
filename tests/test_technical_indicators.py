from __future__ import annotations

import pandas as pd
import pytest

from app.features.technical_indicators import (
    add_price_features,
    add_supervised_targets,
    build_feature_frame,
    calculate_atr,
    calculate_rsi,
    latest_complete_feature_row,
)


def make_price_frame(rows: int = 260) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    base = pd.Series(range(rows), dtype="float") + 100
    close = base + (base % 7) * 0.15
    open_ = close - 0.25
    high = close + 1.00
    low = close - 1.25
    volume = 1_000_000 + (base.astype(int) * 1000)
    return pd.DataFrame(
        {
            "symbol": "TEST",
            "trade_date": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "adj_close": close,
            "volume": volume,
            "provider": "unit-test",
        }
    )


def test_add_price_features_creates_expected_columns():
    df = make_price_frame()
    featured = add_price_features(df)

    expected_columns = {
        "return_1d",
        "return_5d",
        "return_21d",
        "log_return_1d",
        "sma_20",
        "sma_50",
        "sma_200",
        "ema_12",
        "ema_26",
        "macd_line",
        "macd_signal",
        "macd_histogram",
        "rsi_14",
        "atr_14",
        "atr_14_pct",
        "rolling_vol_20d_annualized",
        "volume_ratio_20",
        "dollar_volume",
    }
    assert expected_columns.issubset(featured.columns)
    assert len(featured) == len(df)


def test_feature_values_are_reasonable_after_warmup():
    featured = add_price_features(make_price_frame())
    row = featured.dropna(subset=["sma_50", "rsi_14", "atr_14"]).iloc[-1]

    assert row["sma_20"] > 0
    assert row["sma_50"] > 0
    assert 0 <= row["rsi_14"] <= 100
    assert row["atr_14"] > 0
    assert row["volume_ratio_20"] > 0


def test_calculate_rsi_bounds_output():
    close = pd.Series([100, 101, 102, 101, 103, 104, 103, 105, 106, 107, 106, 108, 109, 110, 111, 110, 112])
    rsi = calculate_rsi(close, window=14)
    non_null = rsi.dropna()
    assert not non_null.empty
    assert (non_null >= 0).all()
    assert (non_null <= 100).all()


def test_calculate_atr_returns_positive_values_after_warmup():
    df = make_price_frame(60)
    atr = calculate_atr(df, window=14)
    assert atr.dropna().iloc[-1] > 0


def test_supervised_targets_are_future_looking_labels():
    featured = add_price_features(make_price_frame(80))
    with_targets = add_supervised_targets(featured)

    assert "future_return_1d" in with_targets.columns
    assert "target_up_1d" in with_targets.columns
    expected_first_future_return = with_targets.loc[1, "close"] / with_targets.loc[0, "close"] - 1
    assert with_targets.loc[0, "future_return_1d"] == pytest.approx(expected_first_future_return)


def test_build_feature_frame_excludes_targets_by_default():
    featured = build_feature_frame(make_price_frame(80))
    assert "target_up_1d" not in featured.columns

    featured_with_targets = build_feature_frame(make_price_frame(80), include_targets=True)
    assert "target_up_1d" in featured_with_targets.columns


def test_latest_complete_feature_row_requires_enough_history():
    featured = build_feature_frame(make_price_frame(20))
    with pytest.raises(ValueError, match="Not enough data"):
        latest_complete_feature_row(featured, minimum_history_days=50)


def test_missing_ohlcv_columns_raise_clear_error():
    df = make_price_frame().drop(columns=["volume"])
    with pytest.raises(ValueError, match="Missing required OHLCV"):
        add_price_features(df)
