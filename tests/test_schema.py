from pathlib import Path


def test_schema_file_exists():
    assert Path("app/db/schema.sql").exists()


def test_schema_has_price_bars_table():
    schema = Path("app/db/schema.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS price_bars" in schema
