import json
import logging
from typing import Optional

import typer
from rich import print

from app.analysis.quick_report import build_gemma_prompt, build_quick_report
from app.core.config import load_settings_or_raise
from app.core.logging import configure_logging
from app.data.providers.yfinance_provider import YFinanceProvider
from app.db.duckdb_client import DuckDBClient
from app.llm.ollama_client import OllamaClient

app = typer.Typer(help="AI Trading Research Platform command line interface.")
logger = logging.getLogger(__name__)


def bootstrap():
    settings = load_settings_or_raise()
    configure_logging(settings.log_level)
    return settings


@app.command()
def doctor():
    """Check local configuration and basic service availability."""
    settings = bootstrap()
    print("[bold]Configuration loaded successfully.[/bold]")
    print(f"Environment: {settings.app_env}")
    print(f"Database path: {settings.db_path}")
    print(f"Ollama URL: {settings.ollama_base_url}")
    print(f"Ollama model: {settings.ollama_model}")

    ollama = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    if ollama.healthcheck():
        print("[green]Ollama reachable.[/green]")
    else:
        print("[yellow]Ollama not reachable. Install/start Ollama before LLM analysis.[/yellow]")


@app.command("init-db")
def init_db():
    """Initialize the local DuckDB schema."""
    settings = bootstrap()
    db = DuckDBClient(settings.db_path)
    db.init_schema()
    print(f"[green]Initialized database:[/green] {settings.db_path}")


@app.command("ingest-price")
def ingest_price(symbol: str, period: Optional[str] = typer.Option(None, help="Example: 1y, 5y, 10y")):
    """Download and store daily price history for a symbol."""
    settings = bootstrap()
    provider = YFinanceProvider()
    db = DuckDBClient(settings.db_path)
    db.init_schema()

    selected_period = period or settings.default_price_period
    df = provider.fetch_daily_prices(symbol, period=selected_period)
    inserted = db.insert_price_bars(df)
    print(f"[green]Stored {inserted} rows for {symbol.upper()}.[/green]")


@app.command()
def analyze(symbol: str, use_gemma: bool = typer.Option(False, help="Ask local Gemma to explain report.")):
    """Build a deterministic first-pass analysis report."""
    settings = bootstrap()
    db = DuckDBClient(settings.db_path)
    price_df = db.fetch_price_bars(symbol)
    if price_df.empty:
        raise typer.BadParameter(
            f"No data found for {symbol.upper()}. Run: python -m app.main ingest-price {symbol.upper()}"
        )

    report = build_quick_report(symbol, price_df)
    print(json.dumps(report, indent=2))

    if use_gemma:
        ollama = OllamaClient(
            settings.ollama_base_url,
            settings.ollama_model,
            settings.ollama_timeout_seconds,
        )
        prompt = build_gemma_prompt(report)
        print("\n[bold]Gemma analysis[/bold]\n")
        print(ollama.generate(prompt))


if __name__ == "__main__":
    app()
