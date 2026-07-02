from pathlib import Path


def test_project_control_scripts_exist():
    expected = [
        "scripts/start_project.ps1",
        "scripts/stop_project.ps1",
        "scripts/status_project.ps1",
        "scripts/start_project.sh",
        "scripts/stop_project.sh",
        "scripts/status_project.sh",
    ]
    for path in expected:
        assert Path(path).exists(), f"Missing {path}"


def test_streamlit_dashboard_entrypoint_exists():
    dashboard = Path("app/dashboard/streamlit_app.py")
    assert dashboard.exists()
    text = dashboard.read_text(encoding="utf-8")
    assert "AI Trading Research Platform" in text
    assert "ingest_watchlist" in text
    assert "build_quick_report" in text
