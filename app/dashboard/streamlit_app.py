from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from app.analysis.quick_report import build_gemma_prompt, build_quick_report
from app.dashboard.charts import DURATION_OPTIONS, TIMEFRAME_OPTIONS, build_candlestick_figure
from app.core.config import load_settings_or_raise
from app.core.watchlist import load_watchlist, normalize_symbol
from app.data.providers.yfinance_provider import YFinanceProvider
from app.db.duckdb_client import DuckDBClient
from app.llm.ollama_client import OllamaClient
from app.services.ingestion import ingest_one_symbol, ingest_watchlist


st.set_page_config(page_title="AI Trading Research Platform", page_icon="📈", layout="wide")


def get_runtime_objects():
    settings = load_settings_or_raise()
    db = DuckDBClient(settings.db_path)
    db.init_schema()
    return settings, db


def render_symbol_summary(db: DuckDBClient) -> None:
    summary = db.fetch_symbol_summary()
    if summary.empty:
        st.info("No local price data yet. Ingest a ticker or your watchlist to begin.")
        return
    st.dataframe(summary, use_container_width=True, hide_index=True)


def render_button_array(
    label: str,
    options: list[str],
    state_key: str,
    default: str,
    *,
    align_label: str | None = None,
) -> str:
    """Render compact button-style choices backed by Streamlit session state."""
    if state_key not in st.session_state:
        st.session_state[state_key] = default

    if align_label:
        st.caption(align_label)
    else:
        st.caption(label)

    cols = st.columns(len(options), gap="small")
    for option, col in zip(options, cols, strict=True):
        selected = st.session_state[state_key] == option
        button_type = "primary" if selected else "secondary"
        if col.button(
            option,
            key=f"{state_key}_{option}",
            type=button_type,
            use_container_width=True,
        ):
            st.session_state[state_key] = option
            st.rerun()
    return str(st.session_state[state_key])


def render_analysis(symbol: str, db: DuckDBClient, use_gemma: bool) -> None:
    normalized = normalize_symbol(symbol)
    prices = db.fetch_price_bars(normalized)
    if prices.empty:
        st.warning(f"No data found for {normalized}. Ingest it first.")
        return

    report = build_quick_report(normalized, prices)
    st.subheader(f"Quick report: {normalized}")
    st.json(report)

    timeframe_key = f"{normalized}_chart_timeframe"
    duration_key = f"{normalized}_chart_duration"

    _, timeframe_col = st.columns([3, 2])
    with timeframe_col:
        selected_timeframe = render_button_array(
            label="Timeframe",
            options=list(TIMEFRAME_OPTIONS.keys()),
            state_key=timeframe_key,
            default="Daily",
            align_label="Timeframe",
        )

    selected_duration = str(st.session_state.get(duration_key, "1Y"))
    st.plotly_chart(
        build_candlestick_figure(
            prices=prices,
            symbol=normalized,
            timeframe=selected_timeframe,
            duration=selected_duration,
        ),
        use_container_width=True,
        config={"displayModeBar": True, "scrollZoom": True},
    )

    duration_col, _ = st.columns([3, 4])
    with duration_col:
        render_button_array(
            label="Duration",
            options=list(DURATION_OPTIONS.keys()),
            state_key=duration_key,
            default="1Y",
            align_label="Duration",
        )

    if use_gemma:
        settings, _ = get_runtime_objects()
        ollama = OllamaClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        )
        if not ollama.healthcheck():
            st.error("Ollama is not reachable. Start Ollama or run scripts/start_project.ps1.")
            return
        with st.spinner("Asking Gemma for a cautious research explanation..."):
            st.markdown(ollama.generate(build_gemma_prompt(report)))


def main() -> None:
    settings, db = get_runtime_objects()

    st.title("AI Trading Research Platform")
    st.caption("Volume 1 local dashboard — research only, no live trading.")

    with st.sidebar:
        st.header("Controls")
        period = st.selectbox("Ingestion period", ["6mo", "1y", "2y", "5y", "10y"], index=1)
        use_gemma = st.checkbox("Use Gemma explanation", value=False)
        st.divider()
        st.write("Database")
        st.code(str(settings.db_path), language="text")
        st.write("Watchlist")
        st.code(str(settings.default_watchlist_path), language="text")

    tab_overview, tab_ingest, tab_analyze, tab_config = st.tabs(
        ["Overview", "Ingest", "Analyze", "Config"]
    )

    with tab_overview:
        st.subheader("Stored symbols")
        render_symbol_summary(db)

    with tab_ingest:
        st.subheader("Ingest data")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Single symbol")
            if "active_symbol_input" not in st.session_state:
                st.session_state["active_symbol_input"] = "AAPL"
            st.text_input(
                "Ticker symbol",
                key="active_symbol_input",
                placeholder="AAPL",
                help=(
                    "This is the dashboard's shared symbol. The Analyze tab chart "
                    "and JSON report use this same ticker."
                ),
            )
            active_symbol = normalize_symbol(
                str(st.session_state.get("active_symbol_input", "AAPL"))
            )
            if st.button("Ingest ticker", type="primary"):
                provider = YFinanceProvider()
                with st.spinner(f"Ingesting {active_symbol} from yfinance..."):
                    result = ingest_one_symbol(
                        symbol=active_symbol,
                        period=period,
                        provider=provider,
                        db=db,
                    )
                st.success(f"Stored {result.rows_stored} rows for {result.symbol}.")
        with col2:
            st.write("Watchlist")
            if st.button("Ingest default watchlist"):
                provider = YFinanceProvider()
                with st.spinner("Ingesting watchlist from yfinance..."):
                    result = ingest_watchlist(
                        watchlist_path=settings.default_watchlist_path,
                        period=period,
                        provider=provider,
                        db=db,
                        continue_on_error=True,
                    )
                st.write(
                    {
                        "attempted": result.attempted,
                        "succeeded": result.succeeded,
                        "failed": result.failed,
                    }
                )
                st.dataframe([item.__dict__ for item in result.results], use_container_width=True)

    with tab_analyze:
        st.subheader("Analyze symbol")
        if "active_symbol_input" not in st.session_state:
            st.session_state["active_symbol_input"] = "AAPL"

        active_symbol = normalize_symbol(
            str(st.session_state.get("active_symbol_input", "AAPL"))
        )
        st.caption(
            "Analyze uses the ticker from the Ingest tab's **Ticker symbol** field. "
            "To change the chart symbol, update that field on the Ingest tab and ingest the ticker."
        )
        st.info(f"Current analyze symbol: {active_symbol}")

        render_analysis(active_symbol, db, use_gemma)

    with tab_config:
        st.subheader("Runtime configuration")
        safe_settings = settings.model_dump()
        st.code(json.dumps(safe_settings, indent=2, default=str), language="json")
        st.subheader("Default watchlist contents")
        path = Path(settings.default_watchlist_path)
        if path.exists():
            st.code("\n".join(load_watchlist(path)), language="text")
        else:
            st.warning(f"Watchlist file not found: {path}")


if __name__ == "__main__":
    main()
