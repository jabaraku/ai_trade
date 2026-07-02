from abc import ABC, abstractmethod

import pandas as pd


class MarketDataProvider(ABC):
    """Contract for all market data providers."""

    provider_name: str

    @abstractmethod
    def fetch_daily_prices(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        """Fetch daily OHLCV data for a symbol."""
