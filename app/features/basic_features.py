import pandas as pd


def add_basic_price_features(price_df: pd.DataFrame) -> pd.DataFrame:
    """Add first-pass price features for analysis and future modeling."""
    df = price_df.copy().sort_values("trade_date")
    df["return_1d"] = df["close"].pct_change()
    df["return_5d"] = df["close"].pct_change(5)
    df["sma_20"] = df["close"].rolling(20).mean()
    df["sma_50"] = df["close"].rolling(50).mean()
    df["volume_sma_20"] = df["volume"].rolling(20).mean()
    df["close_vs_sma_20"] = df["close"] / df["sma_20"] - 1
    df["close_vs_sma_50"] = df["close"] / df["sma_50"] - 1
    return df
