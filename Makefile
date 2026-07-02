.PHONY: doctor init-db test lint format ingest-aapl analyze-aapl

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

analyze-aapl:
	python -m app.main analyze AAPL
