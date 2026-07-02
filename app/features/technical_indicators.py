"""Technical feature engineering for OHLCV price bars.

This module intentionally avoids model-specific logic. It converts raw daily price
bars into reusable numeric features that can later feed reports, dashboards,
backtests, and XGBoost training datasets.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

REQUIRED_OHLCV_COLUMNS = {"trade_date", "open", "high", "low", "close", "volume"}


def _validate_price_frame(price_df: pd.DataFrame) -> None:
    missing = REQUIRED_OHLCV_COLUMNS.difference(price_df.columns)
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {sorted(missing)}")


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide while avoiding infinite values from zero denominators."""
    result = numerator / denominator.replace(0, np.nan)
    return result.replace([np.inf, -np.inf], np.nan)


def calculate_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Calculate Relative Strength Index using Wilder-style smoothing.

    RSI ranges from 0 to 100. Many traders loosely treat values above 70 as
    overbought and values below 30 as oversold, but those thresholds are context
    dependent and should not be used as standalone signals.
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    rs = _safe_divide(avg_gain, avg_loss)
    rsi = 100 - (100 / (1 + rs))

    # When average loss is exactly zero after the warmup window, RSI is 100.
    # When both gain and loss are zero, there is no directional movement, so 50
    # is a neutral value.
    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100)
    rsi = rsi.mask((avg_loss == 0) & (avg_gain == 0), 50)
    return rsi.clip(lower=0, upper=100)


def calculate_true_range(df: pd.DataFrame) -> pd.Series:
    """Calculate true range for each row of OHLC data."""
    high_low = df["high"] - df["low"]
    high_prev_close = (df["high"] - df["close"].shift(1)).abs()
    low_prev_close = (df["low"] - df["close"].shift(1)).abs()
    return pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)


def calculate_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Calculate Average True Range using Wilder-style smoothing."""
    true_range = calculate_true_range(df)
    return true_range.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def add_price_features(price_df: pd.DataFrame) -> pd.DataFrame:
    """Add first-pass deterministic features to a raw OHLCV dataframe.

    The function returns a new dataframe and does not mutate the input.
    All features are calculated using current and historical data only, so the
    resulting frame is safe to use for analysis and model input features. Future
    targets are created separately by ``add_supervised_targets``.
    """
    _validate_price_frame(price_df)

    df = price_df.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.sort_values("trade_date").reset_index(drop=True)

    # Basic price action
    df["return_1d"] = df["close"].pct_change()
    df["return_5d"] = df["close"].pct_change(5)
    df["return_21d"] = df["close"].pct_change(21)
    df["log_return_1d"] = np.log(_safe_divide(df["close"], df["close"].shift(1)))
    df["daily_range_pct"] = _safe_divide(df["high"] - df["low"], df["close"])
    df["open_to_close_pct"] = _safe_divide(df["close"] - df["open"], df["open"])
    df["close_position_in_day_range"] = _safe_divide(df["close"] - df["low"], df["high"] - df["low"])

    # Trend features
    for window in (5, 10, 20, 50, 200):
        df[f"sma_{window}"] = df["close"].rolling(window).mean()
        df[f"close_vs_sma_{window}"] = _safe_divide(df["close"], df[f"sma_{window}"]) - 1

    for span in (12, 26):
        df[f"ema_{span}"] = df["close"].ewm(span=span, adjust=False).mean()

    df["macd_line"] = df["ema_12"] - df["ema_26"]
    df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean()
    df["macd_histogram"] = df["macd_line"] - df["macd_signal"]

    # Momentum and volatility features
    df["rsi_14"] = calculate_rsi(df["close"], window=14)
    df["true_range"] = calculate_true_range(df)
    df["atr_14"] = calculate_atr(df, window=14)
    df["atr_14_pct"] = _safe_divide(df["atr_14"], df["close"])
    df["rolling_vol_20d"] = df["return_1d"].rolling(20).std()
    df["rolling_vol_20d_annualized"] = df["rolling_vol_20d"] * math.sqrt(252)

    # Volume and liquidity features
    df["volume_sma_20"] = df["volume"].rolling(20).mean()
    df["volume_ratio_20"] = _safe_divide(df["volume"], df["volume_sma_20"])
    df["dollar_volume"] = df["close"] * df["volume"]
    df["dollar_volume_sma_20"] = df["dollar_volume"].rolling(20).mean()

    return df.replace([np.inf, -np.inf], np.nan)


def add_supervised_targets(feature_df: pd.DataFrame) -> pd.DataFrame:
    """Add future-looking labels for later XGBoost training.

    These columns are targets/labels only. Do not use them as input features
    when training a model, because they intentionally use future data.
    """
    if "close" not in feature_df.columns:
        raise ValueError("Missing required column: close")

    df = feature_df.copy()
    df["future_return_1d"] = df["close"].shift(-1) / df["close"] - 1
    df["future_return_5d"] = df["close"].shift(-5) / df["close"] - 1
    df["target_up_1d"] = (df["future_return_1d"] > 0).astype("Int64")
    df["target_up_5d"] = (df["future_return_5d"] > 0).astype("Int64")
    return df


def build_feature_frame(price_df: pd.DataFrame, include_targets: bool = False) -> pd.DataFrame:
    """Create the standard feature frame used throughout the project."""
    featured = add_price_features(price_df)
    if include_targets:
        featured = add_supervised_targets(featured)
    return featured


def latest_complete_feature_row(feature_df: pd.DataFrame, minimum_history_days: int = 50) -> pd.Series:
    """Return the latest row with enough non-null features for analysis.

    ``minimum_history_days`` defaults to 50 because the current quick report
    relies on SMA-50. Later model training can choose a higher threshold such as
    200 when long-window indicators are required.
    """
    if len(feature_df) < minimum_history_days:
        raise ValueError(
            f"Not enough data to build features. Need at least {minimum_history_days} rows, "
            f"found {len(feature_df)}."
        )

    candidates = feature_df.dropna(subset=["return_1d", "sma_20", "sma_50", "rsi_14", "atr_14"])
    if candidates.empty:
        raise ValueError("Feature calculation produced no complete rows. Ingest more history.")
    return candidates.tail(1).iloc[0]
