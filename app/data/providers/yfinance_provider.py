import pandas as pd
import yfinance as yf

from app.data.providers.base import MarketDataProvider


class YFinanceProvider(MarketDataProvider):
    provider_name = "yfinance"

    def fetch_daily_prices(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        symbol = symbol.upper().strip()
        raw = yf.download(symbol, period=period, interval="1d", auto_adjust=False, progress=False)
        if raw.empty:
            raise ValueError(f"No price data returned for symbol: {symbol}")

        # yfinance can return multi-index columns in some situations. Normalize them.
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = [col[0] for col in raw.columns]

        df = raw.reset_index().rename(
            columns={
                "Date": "trade_date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )
        df["symbol"] = symbol
        df["provider"] = self.provider_name
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

        expected = [
            "symbol",
            "trade_date",
            "open",
            "high",
            "low",
            "close",
            "adj_close",
            "volume",
            "provider",
        ]
        return df[expected]
