from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from app.core.watchlist import load_watchlist, normalize_symbol

if TYPE_CHECKING:
    import pandas as pd


class PriceBarStore(Protocol):
    def insert_price_bars(self, df: "pd.DataFrame") -> int: ...


class DailyPriceProvider(Protocol):
    def fetch_daily_prices(self, symbol: str, period: str = "5y") -> "pd.DataFrame": ...

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SymbolIngestionResult:
    symbol: str
    rows_stored: int
    status: str
    error: str | None = None


@dataclass(frozen=True)
class WatchlistIngestionResult:
    watchlist_path: Path
    period: str
    attempted: int
    succeeded: int
    failed: int
    results: list[SymbolIngestionResult] = field(default_factory=list)


def ingest_one_symbol(
    *,
    symbol: str,
    period: str,
    provider: DailyPriceProvider,
    db: PriceBarStore,
) -> SymbolIngestionResult:
    """Fetch and store daily bars for a single symbol."""
    normalized = normalize_symbol(symbol)
    logger.info("Starting price ingestion", extra={"symbol": normalized, "period": period})
    df = provider.fetch_daily_prices(normalized, period=period)
    rows = db.insert_price_bars(df)
    logger.info("Finished price ingestion", extra={"symbol": normalized, "rows": rows})
    return SymbolIngestionResult(symbol=normalized, rows_stored=rows, status="success")


def ingest_watchlist(
    *,
    watchlist_path: str | Path,
    period: str,
    provider: DailyPriceProvider,
    db: PriceBarStore,
    continue_on_error: bool = True,
) -> WatchlistIngestionResult:
    """Fetch and store daily bars for every symbol in a watchlist file."""
    resolved_path = Path(watchlist_path)
    symbols = load_watchlist(resolved_path)
    results: list[SymbolIngestionResult] = []

    for symbol in symbols:
        try:
            result = ingest_one_symbol(symbol=symbol, period=period, provider=provider, db=db)
        except Exception as exc:  # noqa: BLE001 - batch ingestion should capture per-symbol failures.
            logger.exception("Price ingestion failed", extra={"symbol": symbol})
            result = SymbolIngestionResult(
                symbol=symbol,
                rows_stored=0,
                status="failed",
                error=str(exc),
            )
            results.append(result)
            if not continue_on_error:
                raise
        else:
            results.append(result)

    succeeded = sum(1 for item in results if item.status == "success")
    failed = len(results) - succeeded
    return WatchlistIngestionResult(
        watchlist_path=resolved_path,
        period=period,
        attempted=len(symbols),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )
