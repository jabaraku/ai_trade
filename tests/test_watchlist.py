from pathlib import Path

import pytest

from app.core.watchlist import load_watchlist, normalize_symbol


def test_normalize_symbol_uppercases_and_strips():
    assert normalize_symbol(" aapl ") == "AAPL"
    assert normalize_symbol("brk-b") == "BRK-B"
    assert normalize_symbol("7203.t") == "7203.T"


def test_normalize_symbol_rejects_blank():
    with pytest.raises(ValueError, match="blank"):
        normalize_symbol("   ")


def test_load_watchlist_ignores_comments_blanks_and_duplicates(tmp_path: Path):
    path = tmp_path / "watchlist.txt"
    path.write_text(
        """
        # Core tech
        aapl
        MSFT

        AAPL  # duplicate should be ignored
        spy
        """,
        encoding="utf-8",
    )

    assert load_watchlist(path) == ["AAPL", "MSFT", "SPY"]


def test_load_watchlist_requires_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_watchlist(tmp_path / "missing.txt")
