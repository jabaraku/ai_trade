import json
import logging
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.table import Table

from app.analysis.quick_report import build_gemma_prompt, build_quick_report
from app.features.technical_indicators import build_feature_frame
from app.core.config import load_settings_or_raise
from app.core.logging import configure_logging
from app.core.watchlist import normalize_symbol
from app.data.providers.yfinance_provider import YFinanceProvider
from app.db.duckdb_client import DuckDBClient
from app.llm.ollama_client import OllamaClient, OllamaGenerationOptions
from app.services.ingestion import ingest_one_symbol, ingest_watchlist
from app.services.indicators import calculate_and_store_indicators
from app.tools.duckdb_context import (
    DuckDBGemmaContextOptions,
    build_duckdb_context,
    build_gemma_db_prompt,
)

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
    print(f"Default watchlist: {settings.default_watchlist_path}")
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
    """Download and store daily price history for one symbol."""
    settings = bootstrap()
    provider = YFinanceProvider()
    db = DuckDBClient(settings.db_path)
    db.init_schema()

    selected_period = period or settings.default_price_period
    result = ingest_one_symbol(symbol=symbol, period=selected_period, provider=provider, db=db)
    print(f"[green]Stored {result.rows_stored} rows for {result.symbol}.[/green]")


@app.command("ingest-watchlist")
def ingest_watchlist_command(
    watchlist: Optional[Path] = typer.Option(
        None,
        "--watchlist",
        "-w",
        help="Path to a text file containing one ticker per line.",
    ),
    period: Optional[str] = typer.Option(None, help="Example: 1y, 5y, 10y"),
    stop_on_error: bool = typer.Option(
        False,
        help="Stop the whole batch if one symbol fails. Default continues and reports failures.",
    ),
):
    """Download and store daily price history for every symbol in the watchlist."""
    settings = bootstrap()
    provider = YFinanceProvider()
    db = DuckDBClient(settings.db_path)
    db.init_schema()

    selected_watchlist = watchlist or settings.default_watchlist_path
    selected_period = period or settings.default_price_period
    result = ingest_watchlist(
        watchlist_path=selected_watchlist,
        period=selected_period,
        provider=provider,
        db=db,
        continue_on_error=not stop_on_error,
    )

    table = Table(title=f"Watchlist ingestion: {result.watchlist_path}")
    table.add_column("Symbol", style="bold")
    table.add_column("Status")
    table.add_column("Rows", justify="right")
    table.add_column("Error")

    for item in result.results:
        status = "[green]success[/green]" if item.status == "success" else "[red]failed[/red]"
        table.add_row(item.symbol, status, str(item.rows_stored), item.error or "")

    print(table)
    print(
        f"[bold]Attempted:[/bold] {result.attempted} | "
        f"[green]Succeeded:[/green] {result.succeeded} | "
        f"[red]Failed:[/red] {result.failed}"
    )


@app.command("list-symbols")
def list_symbols():
    """Show which symbols already exist in the local DuckDB price_bars table."""
    settings = bootstrap()
    db = DuckDBClient(settings.db_path)
    db.init_schema()
    df = db.fetch_symbol_summary()

    if df.empty:
        print("[yellow]No price data found yet. Run ingest-price or ingest-watchlist first.[/yellow]")
        return

    table = Table(title="Local price data")
    table.add_column("Symbol", style="bold")
    table.add_column("Rows", justify="right")
    table.add_column("First date")
    table.add_column("Latest date")
    table.add_column("Provider")

    for row in df.to_dict("records"):
        table.add_row(
            row["symbol"],
            str(row["rows"]),
            str(row["first_date"]),
            str(row["latest_date"]),
            row["provider"],
        )
    print(table)


@app.command("features")
def features_command(
    symbol: str,
    tail: int = typer.Option(5, help="Number of latest feature rows to display."),
    include_targets: bool = typer.Option(
        False,
        help="Include future-looking target columns for ML dataset inspection only.",
    ),
    output: str = typer.Option("table", "--output", "-o", help="table or json"),
):
    """Generate the first feature-engineering dataset for one symbol."""
    settings = bootstrap()
    db = DuckDBClient(settings.db_path)
    normalized_symbol = normalize_symbol(symbol)
    price_df = db.fetch_price_bars(normalized_symbol)
    if price_df.empty:
        raise typer.BadParameter(
            f"No data found for {normalized_symbol}. Run: python -m app.main ingest-price {normalized_symbol}"
        )

    feature_df = build_feature_frame(price_df, include_targets=include_targets)
    latest = feature_df.tail(tail)

    if output.lower() == "json":
        print(latest.to_json(orient="records", date_format="iso", indent=2))
        return
    if output.lower() != "table":
        raise typer.BadParameter("--output must be either table or json")

    columns = [
        "trade_date",
        "close",
        "return_1d",
        "return_5d",
        "sma_20",
        "sma_50",
        "rsi_14",
        "atr_14",
        "volume_ratio_20",
    ]
    if include_targets:
        columns.extend(["future_return_1d", "target_up_1d"])

    table = Table(title=f"Latest engineered features: {normalized_symbol}")
    for column in columns:
        table.add_column(column)

    for row in latest[columns].to_dict("records"):
        values = []
        for column in columns:
            value = row[column]
            if hasattr(value, "date") and column == "trade_date":
                values.append(str(value.date()))
            elif isinstance(value, float):
                values.append("" if value != value else f"{value:.6f}")
            else:
                values.append("" if value is None else str(value))
        table.add_row(*values)
    print(table)


@app.command("calculate")
def calculate_indicators_command(symbol: str, duration: str):
    """Manually calculate and persist daily technical indicators for one symbol.

    Example: python -m app.main calculate AAPL 5y
    """
    settings = bootstrap()
    db = DuckDBClient(settings.db_path)
    db.init_schema()

    result = calculate_and_store_indicators(symbol=symbol, duration=duration, db=db)
    print(
        f"[green]Stored {result.rows_stored} indicator rows for {result.symbol} "
        f"({result.duration}).[/green]"
    )
    print(f"Source price rows: {result.source_rows}")
    print(f"Indicator date range: {result.first_trade_date} to {result.latest_trade_date}")


@app.command("calculate-indicators")
def calculate_indicators_alias(symbol: str, duration: str):
    """Alias for calculate, kept explicit for readability."""
    calculate_indicators_command(symbol, duration)


@app.command("list-indicators")
def list_indicators():
    """Show which symbols already have persisted indicator rows."""
    settings = bootstrap()
    db = DuckDBClient(settings.db_path)
    db.init_schema()
    df = db.fetch_indicator_summary()

    if df.empty:
        print("[yellow]No indicator data found yet. Run: python -m app.main calculate AAPL 5y[/yellow]")
        return

    table = Table(title="Local indicator data")
    table.add_column("Symbol", style="bold")
    table.add_column("Rows", justify="right")
    table.add_column("First date")
    table.add_column("Latest date")
    table.add_column("Latest duration")
    table.add_column("Latest calculated at")

    for row in df.to_dict("records"):
        table.add_row(
            row["symbol"],
            str(row["rows"]),
            str(row["first_date"]),
            str(row["latest_date"]),
            str(row["latest_duration"]),
            str(row["latest_calculated_at"]),
        )
    print(table)


@app.command("db-context")
def db_context_command(
    symbol: str,
    rows: int = typer.Option(5, "--rows", "-r", help="Number of latest rows to include, max 25."),
):
    """Print the controlled DuckDB context that can be sent to Gemma.

    Example: python -m app.main db-context AAPL --rows 5
    """
    settings = bootstrap()
    db = DuckDBClient(settings.db_path)
    db.init_schema()
    context = build_duckdb_context(
        db=db,
        symbol=symbol,
        options=DuckDBGemmaContextOptions(row_limit=rows),
    )
    print(json.dumps(context, indent=2, default=str))


@app.command("gemma-db")
def gemma_db_command(
    symbol: str,
    question: str = typer.Argument(
        "Summarize the latest price and indicator rows from DuckDB.",
        help="Question Gemma should answer using controlled DuckDB context.",
    ),
    rows: int = typer.Option(5, "--rows", "-r", help="Number of latest DB rows to include, max 25."),
):
    """Ask local Gemma a question using safe, read-only DuckDB context.

    Gemma never receives direct SQL access. Python extracts approved table rows
    from price_bars and indicators, then sends that compact context to Ollama.

    Example:
        python -m app.main gemma-db AAPL "What does the indicators table say about trend?"
    """
    settings = bootstrap()
    db = DuckDBClient(settings.db_path)
    db.init_schema()
    context = build_duckdb_context(
        db=db,
        symbol=symbol,
        options=DuckDBGemmaContextOptions(row_limit=rows),
    )

    ollama = OllamaClient(
        settings.ollama_base_url,
        settings.ollama_model,
        settings.ollama_timeout_seconds,
        options=OllamaGenerationOptions(
            num_predict=settings.ollama_num_predict,
            num_ctx=settings.ollama_num_ctx,
            keep_alive=settings.ollama_keep_alive,
        ),
    )
    prompt = build_gemma_db_prompt(symbol=symbol, question=question, db_context=context)
    print("[bold]Gemma database-context analysis[/bold]\n")
    print(ollama.generate(prompt))


@app.command()
def analyze(symbol: str, use_gemma: bool = typer.Option(False, help="Ask local Gemma to explain report.")):
    """Build a deterministic first-pass analysis report."""
    settings = bootstrap()
    db = DuckDBClient(settings.db_path)
    normalized_symbol = normalize_symbol(symbol)
    price_df = db.fetch_price_bars(normalized_symbol)
    if price_df.empty:
        raise typer.BadParameter(
            f"No data found for {normalized_symbol}. Run: python -m app.main ingest-price {normalized_symbol}"
        )

    report = build_quick_report(normalized_symbol, price_df)
    print(json.dumps(report, indent=2))

    if use_gemma:
        ollama = OllamaClient(
            settings.ollama_base_url,
            settings.ollama_model,
            settings.ollama_timeout_seconds,
            options=OllamaGenerationOptions(
                num_predict=settings.ollama_num_predict,
                num_ctx=settings.ollama_num_ctx,
                keep_alive=settings.ollama_keep_alive,
            ),
        )
        db_context = build_duckdb_context(
            db=db,
            symbol=normalized_symbol,
            options=DuckDBGemmaContextOptions(row_limit=5),
        )
        prompt = build_gemma_prompt(report, db_context=db_context)
        print("\n[bold]Gemma analysis[/bold]\n")
        print(ollama.generate(prompt))


if __name__ == "__main__":
    app()
