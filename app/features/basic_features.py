import pandas as pd

from app.features.technical_indicators import build_feature_frame


def add_basic_price_features(price_df: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible wrapper for the first feature-engineering module."""
    return build_feature_frame(price_df, include_targets=False)
