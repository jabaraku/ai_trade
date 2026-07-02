# Testing and Quality

## Run tests

```bash
pytest -q
```

## Compile check

```bash
python -m compileall app tests -q
```

## Ruff linting

If `ruff` is installed:

```bash
ruff check .
```

## Current test coverage themes

The current tests validate:

- settings loading,
- database schema initialization,
- watchlist parsing,
- single-symbol ingestion workflow,
- watchlist ingestion workflow,
- start/stop/status script existence,
- candlestick chart construction,
- chart timeframe/duration behavior,
- Analyze tab symbol refresh behavior,
- feature engineering calculations,
- quick report feature sections,
- documentation page existence and local links.

## Quality rules for future code

1. Keep business logic outside Streamlit UI when possible.
2. Keep provider-specific code inside `app/data/providers/`.
3. Keep database logic inside `app/db/`.
4. Keep deterministic numeric calculations inside `app/features/`.
5. Do not let Gemma invent raw data.
6. Avoid future-looking data leakage in model features.
7. Add tests for every feature that changes behavior.
8. Prefer small functions with clear inputs and outputs.

## Model quality rules for later XGBoost work

When training begins, the project should add tests/checks for:

- chronological splits,
- no target leakage,
- no random row-level train/test split for time series,
- calibration checks,
- backtest assumptions,
- benchmark comparison,
- stable saved model artifacts.
