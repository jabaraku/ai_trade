from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["local", "test", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    data_dir: Path = Path("data")
    db_path: Path = Path("data/trading_platform.duckdb")

    market_data_provider: Literal["yfinance"] = "yfinance"
    default_price_period: str = "5y"
    default_price_interval: str = "1d"
    default_watchlist_path: Path = Path("config/watchlist.txt")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    ollama_timeout_seconds: int = Field(default=120, ge=5, le=600)

    enable_live_trading: bool = False
    enable_paper_trading: bool = False
    max_position_risk_pct: float = Field(default=1.0, gt=0, le=5)

    def validate_safety(self) -> None:
        """Fail fast if live trading is accidentally enabled in this foundation project."""
        if self.enable_live_trading:
            raise ValueError(
                "ENABLE_LIVE_TRADING=true is not allowed in Volume 1. "
                "This foundation is research/paper-trading only."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_safety()
    return settings


def load_settings_or_raise() -> Settings:
    try:
        return get_settings()
    except ValidationError as exc:
        raise RuntimeError(f"Invalid application configuration: {exc}") from exc
