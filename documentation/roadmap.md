# Roadmap

## Current milestone

The project now has a working local research foundation:

- ingestion,
- local storage,
- dashboard,
- Analyze refresh,
- candlestick controls,
- feature engineering,
- documentation.

## Next recommended milestones

### 1. Persist engineered features

Currently features are generated on demand. Next, create a `features_daily` table and store computed features for each symbol/date.

### 2. Dataset builder for XGBoost

Create a dataset builder that combines many symbols, excludes leakage columns, and creates training/validation/test periods.

### 3. First XGBoost classifier

Target:

```text
target_up_5d
```

Output:

```text
probability that 5-day future return is positive
```

### 4. Walk-forward validation

Add time-aware validation. Avoid random train/test splits.

### 5. Backtesting module

Simulate rules based on model probability thresholds, transaction costs, and position sizing.

### 6. Risk engine

Add deterministic risk calculations:

- max position size,
- max dollar risk,
- stop distance,
- ATR-based risk,
- portfolio exposure.

### 7. RAG for research documents

Add document ingestion for:

- SEC filings,
- earnings transcripts,
- investor presentations,
- strategy notes.

### 8. Options analytics

Add options chain ingestion, Greeks, implied volatility, open interest, and strategy templates.

### 9. Paper trading log

Track research recommendations and outcomes without placing live trades.

### 10. Production hardening

Add:

- automated scheduled ingestion,
- richer logging,
- data quality dashboards,
- model versioning,
- experiment tracking,
- Docker packaging.
