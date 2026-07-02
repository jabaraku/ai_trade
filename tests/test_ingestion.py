from pathlib import Path

import pandas as pd

from app.services.ingestion import ingest_watchlist


class FakeProvider:
    def fetch_daily_prices(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        if symbol == "BAD":
            raise ValueError("simulated provider failure")
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
    def insert_price_bars(self, df: pd.DataFrame) -> int:
        return len(df)


def test_ingest_watchlist_continues_after_symbol_failure(tmp_path: Path):
    watchlist = tmp_path / "watchlist.txt"
    watchlist.write_text("AAPL\nBAD\nMSFT\n", encoding="utf-8")

    result = ingest_watchlist(
        watchlist_path=watchlist,
        period="1y",
        provider=FakeProvider(),
        db=FakeDb(),
        continue_on_error=True,
    )

    assert result.attempted == 3
    assert result.succeeded == 2
    assert result.failed == 1
    assert [item.symbol for item in result.results] == ["AAPL", "BAD", "MSFT"]
    assert result.results[1].status == "failed"
    assert "simulated provider failure" in result.results[1].error
