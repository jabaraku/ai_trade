from pathlib import Path
from typing import Iterable

import duckdb
import pandas as pd

from app.core.paths import ensure_dir


class DuckDBClient:
    """Small wrapper around DuckDB for local analytical storage."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        ensure_dir(self.db_path.parent)

    def connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def init_schema(self, schema_path: str | Path = "app/db/schema.sql") -> None:
        schema_sql = Path(schema_path).read_text(encoding="utf-8")
        with self.connect() as con:
            con.execute(schema_sql)

    def insert_price_bars(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        required = {
            "symbol",
            "trade_date",
            "open",
            "high",
            "low",
            "close",
            "adj_close",
            "volume",
            "provider",
        }
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"Missing required price columns: {sorted(missing)}")

        rows_before = len(df)
        with self.connect() as con:
            con.register("incoming_price_bars", df)
            con.execute(
                """
                INSERT OR REPLACE INTO price_bars
                SELECT
                    symbol,
                    trade_date,
                    open,
                    high,
                    low,
                    close,
                    adj_close,
                    volume,
                    provider,
                    CURRENT_TIMESTAMP AS ingested_at
                FROM incoming_price_bars
                """
            )
        return rows_before

    def fetch_price_bars(self, symbol: str) -> pd.DataFrame:
        with self.connect() as con:
            return con.execute(
                """
                SELECT *
                FROM price_bars
                WHERE symbol = ?
                ORDER BY trade_date
                """,
                [symbol.upper()],
            ).df()


    def fetch_symbol_summary(self) -> pd.DataFrame:
        """Return one row per locally stored symbol/provider pair."""
        with self.connect() as con:
            return con.execute(
                """
                SELECT
                    symbol,
                    provider,
                    COUNT(*) AS rows,
                    MIN(trade_date) AS first_date,
                    MAX(trade_date) AS latest_date
                FROM price_bars
                GROUP BY symbol, provider
                ORDER BY symbol, provider
                """
            ).df()


    def upsert_indicators(self, df: pd.DataFrame) -> int:
        """Insert or replace calculated technical indicator rows."""
        if df.empty:
            return 0
        required = {"symbol", "trade_date", "calculation_duration", "source_row_count"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"Missing required indicator columns: {sorted(missing)}")

        with self.connect() as con:
            con.register("incoming_indicators", df)
            con.execute(
                """
                INSERT OR REPLACE INTO indicators (
                    symbol, trade_date, calculation_duration, source_row_count, calculated_at,
                    return_1d, return_5d, return_21d, log_return_1d, daily_range_pct,
                    open_to_close_pct, close_position_in_day_range,
                    sma_5, sma_10, sma_20, sma_50, sma_200,
                    close_vs_sma_5, close_vs_sma_10, close_vs_sma_20, close_vs_sma_50, close_vs_sma_200,
                    ema_12, ema_26, macd_line, macd_signal, macd_histogram,
                    rsi_14, true_range, atr_14, atr_14_pct, rolling_vol_20d, rolling_vol_20d_annualized,
                    volume_sma_20, volume_ratio_20, dollar_volume, dollar_volume_sma_20
                )
                SELECT
                    symbol, trade_date, calculation_duration, source_row_count, CURRENT_TIMESTAMP AS calculated_at,
                    return_1d, return_5d, return_21d, log_return_1d, daily_range_pct,
                    open_to_close_pct, close_position_in_day_range,
                    sma_5, sma_10, sma_20, sma_50, sma_200,
                    close_vs_sma_5, close_vs_sma_10, close_vs_sma_20, close_vs_sma_50, close_vs_sma_200,
                    ema_12, ema_26, macd_line, macd_signal, macd_histogram,
                    rsi_14, true_range, atr_14, atr_14_pct, rolling_vol_20d, rolling_vol_20d_annualized,
                    volume_sma_20, volume_ratio_20, dollar_volume, dollar_volume_sma_20
                FROM incoming_indicators
                """
            )
        return len(df)

    def fetch_indicator_summary(self) -> pd.DataFrame:
        """Return one row per symbol already stored in the indicators table."""
        with self.connect() as con:
            return con.execute(
                """
                SELECT
                    symbol,
                    COUNT(*) AS rows,
                    MIN(trade_date) AS first_date,
                    MAX(trade_date) AS latest_date,
                    MAX(calculation_duration) AS latest_duration,
                    MAX(calculated_at) AS latest_calculated_at
                FROM indicators
                GROUP BY symbol
                ORDER BY symbol
                """
            ).df()

    def fetch_indicators(self, symbol: str) -> pd.DataFrame:
        """Fetch stored indicator rows for one symbol."""
        with self.connect() as con:
            return con.execute(
                """
                SELECT *
                FROM indicators
                WHERE symbol = ?
                ORDER BY trade_date
                """,
                [symbol.upper()],
            ).df()


    def fetch_price_summary(self, symbol: str) -> pd.DataFrame:
        """Return price_bars coverage for one symbol."""
        with self.connect() as con:
            return con.execute(
                """
                SELECT
                    symbol,
                    provider,
                    COUNT(*) AS rows,
                    MIN(trade_date) AS first_date,
                    MAX(trade_date) AS latest_date,
                    MIN(close) AS min_close,
                    MAX(close) AS max_close,
                    AVG(close) AS avg_close
                FROM price_bars
                WHERE symbol = ?
                GROUP BY symbol, provider
                ORDER BY provider
                """,
                [symbol.upper()],
            ).df()

    def fetch_latest_price_bars(self, symbol: str, limit: int = 5) -> pd.DataFrame:
        """Return latest price_bars rows for one symbol in descending date order."""
        safe_limit = max(1, min(int(limit), 100))
        with self.connect() as con:
            return con.execute(
                """
                SELECT *
                FROM price_bars
                WHERE symbol = ?
                ORDER BY trade_date DESC
                LIMIT ?
                """,
                [symbol.upper(), safe_limit],
            ).df()

    def fetch_indicator_symbol_summary(self, symbol: str) -> pd.DataFrame:
        """Return indicators coverage for one symbol."""
        with self.connect() as con:
            return con.execute(
                """
                SELECT
                    symbol,
                    COUNT(*) AS rows,
                    MIN(trade_date) AS first_date,
                    MAX(trade_date) AS latest_date,
                    MAX(calculation_duration) AS latest_duration,
                    MAX(calculated_at) AS latest_calculated_at
                FROM indicators
                WHERE symbol = ?
                GROUP BY symbol
                """,
                [symbol.upper()],
            ).df()

    def fetch_latest_indicators(self, symbol: str, limit: int = 5) -> pd.DataFrame:
        """Return latest persisted indicator rows for one symbol in descending date order."""
        safe_limit = max(1, min(int(limit), 100))
        with self.connect() as con:
            return con.execute(
                """
                SELECT *
                FROM indicators
                WHERE symbol = ?
                ORDER BY trade_date DESC
                LIMIT ?
                """,
                [symbol.upper(), safe_limit],
            ).df()

    def execute(self, sql: str, parameters: Iterable | None = None) -> None:
        with self.connect() as con:
            con.execute(sql, parameters or [])
