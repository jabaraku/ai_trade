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

    def execute(self, sql: str, parameters: Iterable | None = None) -> None:
        with self.connect() as con:
            con.execute(sql, parameters or [])
