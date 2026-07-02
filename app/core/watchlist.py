from __future__ import annotations

import re
from pathlib import Path

_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,14}$")


def normalize_symbol(value: str) -> str:
    """Normalize a user-provided ticker symbol.

    This intentionally stays provider-neutral. yfinance supports many symbols
    beyond U.S. equities, including ETFs and symbols with suffixes such as
    BRK-B or international forms like 7203.T.
    """
    symbol = value.strip().upper()
    if not symbol:
        raise ValueError("Ticker symbol cannot be blank.")
    if not _SYMBOL_PATTERN.match(symbol):
        raise ValueError(
            f"Invalid ticker symbol {value!r}. Use one symbol per line, e.g. AAPL, SPY, BRK-B."
        )
    return symbol


def load_watchlist(path: str | Path) -> list[str]:
    """Load unique ticker symbols from a text watchlist file.

    Supported format:
    - one symbol per line
    - blank lines ignored
    - lines starting with # ignored
    - inline comments allowed after #
    - duplicates removed while preserving file order
    """
    watchlist_path = Path(path)
    if not watchlist_path.exists():
        raise FileNotFoundError(
            f"Watchlist file not found: {watchlist_path}. "
            "Create it or pass --watchlist path/to/watchlist.txt."
        )

    symbols: list[str] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(watchlist_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Allow comments after a symbol: AAPL  # Apple
        candidate = line.split("#", maxsplit=1)[0].strip()
        symbol = normalize_symbol(candidate)
        if symbol not in seen:
            seen.add(symbol)
            symbols.append(symbol)

    if not symbols:
        raise ValueError(f"Watchlist file contains no valid symbols: {watchlist_path}")
    return symbols
