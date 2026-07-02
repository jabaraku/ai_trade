from app.features.basic_features import add_basic_price_features


def build_quick_report(symbol: str, price_df) -> dict:
    """Build a simple deterministic report before ML and LLM layers are added."""
    featured = add_basic_price_features(price_df)
    latest = featured.dropna().tail(1)
    if latest.empty:
        raise ValueError("Not enough data to build a report. Ingest more history.")

    row = latest.iloc[0]
    return {
        "symbol": symbol.upper(),
        "trade_date": str(row["trade_date"]),
        "close": round(float(row["close"]), 4),
        "return_1d_pct": round(float(row["return_1d"] * 100), 3),
        "return_5d_pct": round(float(row["return_5d"] * 100), 3),
        "sma_20": round(float(row["sma_20"]), 4),
        "sma_50": round(float(row["sma_50"]), 4),
        "close_vs_sma_20_pct": round(float(row["close_vs_sma_20"] * 100), 3),
        "close_vs_sma_50_pct": round(float(row["close_vs_sma_50"] * 100), 3),
    }


def build_gemma_prompt(report: dict) -> str:
    return f"""
You are a cautious trading research assistant. You do not give financial advice.
You explain market data in plain English and highlight uncertainty.

Analyze this deterministic price report:

{report}

Return:
1. A neutral summary.
2. Bullish considerations.
3. Bearish considerations.
4. What data is missing before making any trading decision.
5. A reminder that this is research only.
""".strip()
