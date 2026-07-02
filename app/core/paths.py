from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if it does not exist and return it as a Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
