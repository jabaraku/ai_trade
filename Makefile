.PHONY: doctor init-db test lint format ingest-aapl ingest-watchlist list-symbols analyze-aapl features-aapl start stop status dashboard

doctor:
	python -m app.main doctor

init-db:
	python -m app.main init-db

test:
	pytest

lint:
	ruff check .

format:
	ruff check . --fix

ingest-aapl:
	python -m app.main ingest-price AAPL --period 1y

ingest-watchlist:
	python -m app.main ingest-watchlist --period 1y

list-symbols:
	python -m app.main list-symbols

analyze-aapl:
	python -m app.main analyze AAPL

features-aapl:
	python -m app.main features AAPL --tail 5


start:
	powershell -ExecutionPolicy Bypass -File scripts/start_project.ps1

stop:
	powershell -ExecutionPolicy Bypass -File scripts/stop_project.ps1

status:
	powershell -ExecutionPolicy Bypass -File scripts/status_project.ps1

dashboard:
	python -m streamlit run app/dashboard/streamlit_app.py --server.port 8501
