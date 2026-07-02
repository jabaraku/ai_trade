from __future__ import annotations

import pandas as pd

from app.analysis.quick_report import build_quick_report


def make_price_frame(rows: int = 260) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = pd.Series(range(rows), dtype="float") + 100
    return pd.DataFrame(
        {
            "symbol": "AAPL",
            "trade_date": dates,
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "adj_close": close,
            "volume": 1_000_000,
            "provider": "unit-test",
        }
    )


def test_quick_report_uses_feature_sections():
    report = build_quick_report("aapl", make_price_frame())

    assert report["symbol"] == "AAPL"
    assert "price_action" in report
    assert "trend" in report
    assert "momentum_volatility" in report
    assert "volume_liquidity" in report
    assert report["trend"]["sma_20"] is not None
    assert report["momentum_volatility"]["rsi_14"] is not None
    assert report["data_notes"][1] == "No XGBoost prediction is being made yet."
