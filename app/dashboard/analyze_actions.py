from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

from app.core.watchlist import normalize_symbol
from app.services.ingestion import ingest_one_symbol

if TYPE_CHECKING:
    import pandas as pd


class AnalyzePriceBarStore(Protocol):
    def insert_price_bars(self, df: "pd.DataFrame") -> int: ...


class AnalyzeDailyPriceProvider(Protocol):
    def fetch_daily_prices(self, symbol: str, period: str = "5y") -> "pd.DataFrame": ...


def refresh_symbol_data(
    *,
    symbol: str,
    period: str,
    db: AnalyzePriceBarStore,
    provider_factory: Callable[[], AnalyzeDailyPriceProvider] | None = None,
) -> str:
    """Fetch fresh local price data for a user-entered Analyze tab symbol.

    Returns the normalized symbol that should become the active Analyze tab symbol.
    The yfinance provider is imported lazily so unit tests can run without optional
    runtime data-provider dependencies already installed in the test environment.
    """
    normalized = normalize_symbol(symbol)
    if provider_factory is None:
        from app.data.providers.yfinance_provider import YFinanceProvider

        provider_factory = YFinanceProvider

    provider = provider_factory()
    result = ingest_one_symbol(
        symbol=normalized,
        period=period,
        provider=provider,
        db=db,
    )
    if result.status != "success":
        raise RuntimeError(result.error or f"Refresh failed for {normalized}.")
    return normalized
