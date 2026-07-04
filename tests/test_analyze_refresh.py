from pathlib import Path

import pandas as pd
import pytest

from app.dashboard.analyze_actions import refresh_symbol_data


class FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def fetch_daily_prices(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        self.calls.append((symbol, period))
        return pd.DataFrame(
            {
                "symbol": [symbol],
                "trade_date": [pd.Timestamp("2026-01-02").date()],
                "open": [100.0],
                "high": [101.0],
                "low": [99.0],
                "close": [100.5],
                "adj_close": [100.5],
                "volume": [1_000_000],
                "provider": ["fake"],
            }
        )


class FakeDb:
    def __init__(self) -> None:
        self.rows_stored = 0

    def insert_price_bars(self, df: pd.DataFrame) -> int:
        self.rows_stored += len(df)
        return len(df)


def test_refresh_symbol_data_normalizes_and_stores():
    provider = FakeProvider()

    db = FakeDb()
    refreshed = refresh_symbol_data(
        symbol=" msft ",
        period="1y",
        db=db,
        provider_factory=lambda: provider,
    )

    assert refreshed == "MSFT"
    assert provider.calls == [("MSFT", "1y")]
    assert db.rows_stored == 1


def test_refresh_symbol_data_rejects_blank_symbol():
    with pytest.raises(ValueError, match="Ticker symbol cannot be blank"):
        refresh_symbol_data(symbol=" ", period="1y", db=FakeDb(), provider_factory=FakeProvider)


def test_analyze_tab_uses_sidebar_symbol_instead_of_own_text_box():
    text = Path("app/dashboard/streamlit_app.py").read_text(encoding="utf-8")
    assert 'with st.sidebar:' in text
    assert '"Ticker symbol"' in text
    assert 'key="active_symbol_input"' in text
    assert 'Uses the sidebar **Ticker symbol** field.' in text
    assert 'Analyze uses the shared **Ticker symbol** field from the sidebar.' in text
    assert 'render_analysis(active_symbol, db, use_gemma)' in text
    assert 'analyze_symbol_input' not in text
    assert 'st.button("Refresh"' not in text
