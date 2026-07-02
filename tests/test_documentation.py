from pathlib import Path
import re


DOC_ROOT = Path("documentation")

REQUIRED_PAGES = [
    "index.md",
    "project-overview.md",
    "architecture.md",
    "setup-guide.md",
    "command-reference.md",
    "dashboard-guide.md",
    "data-pipeline.md",
    "feature-engineering.md",
    "indicators.md",
    "gemma-ollama.md",
    "operations-runbook.md",
    "testing-quality.md",
    "troubleshooting.md",
    "roadmap.md",
    "glossary.md",
]

REQUIRED_INDICATOR_TERMS = [
    "return_1d",
    "return_5d",
    "return_21d",
    "log_return_1d",
    "daily_range_pct",
    "open_to_close_pct",
    "close_position_in_day_range",
    "sma_5",
    "sma_10",
    "sma_20",
    "sma_50",
    "sma_200",
    "close_vs_sma_5",
    "close_vs_sma_10",
    "close_vs_sma_20",
    "close_vs_sma_50",
    "close_vs_sma_200",
    "ema_12",
    "ema_26",
    "macd_line",
    "macd_signal",
    "macd_histogram",
    "rsi_14",
    "true_range",
    "atr_14",
    "atr_14_pct",
    "rolling_vol_20d",
    "rolling_vol_20d_annualized",
    "volume_sma_20",
    "volume_ratio_20",
    "dollar_volume",
    "dollar_volume_sma_20",
    "future_return_1d",
    "future_return_5d",
    "target_up_1d",
    "target_up_5d",
]


def test_documentation_pages_exist():
    for page in REQUIRED_PAGES:
        assert (DOC_ROOT / page).exists(), f"Missing documentation page: {page}"


def test_documentation_index_links_to_indicator_reference():
    index = (DOC_ROOT / "index.md").read_text(encoding="utf-8")
    assert "[Indicator Reference](indicators.md)" in index


def test_indicator_reference_mentions_all_current_feature_columns():
    indicators = (DOC_ROOT / "indicators.md").read_text(encoding="utf-8")
    missing = [term for term in REQUIRED_INDICATOR_TERMS if term not in indicators]
    assert not missing, f"Missing indicator docs for: {missing}"


def test_local_markdown_links_resolve():
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)")
    for page in DOC_ROOT.glob("*.md"):
        content = page.read_text(encoding="utf-8")
        for target in pattern.findall(content):
            if target.startswith(("http://", "https://")):
                continue
            resolved = (page.parent / target).resolve()
            assert resolved.exists(), f"Broken link in {page}: {target}"
