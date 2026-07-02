import logging
import sys
from pathlib import Path

from app.core.paths import ensure_dir


def configure_logging(level: str = "INFO", log_dir: str | Path = "logs") -> None:
    """Configure console and file logging with a consistent format."""
    ensure_dir(log_dir)
    log_file = Path(log_dir) / "app.log"

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    root.addHandler(console_handler)
    root.addHandler(file_handler)
