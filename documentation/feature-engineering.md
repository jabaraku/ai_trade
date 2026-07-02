# Feature Engineering

## Purpose

Feature engineering converts raw market data into numeric inputs that are useful for analysis, reports, backtests, and eventually XGBoost models.

Raw OHLCV data looks like:

```text
open, high, low, close, volume
```

The feature engine turns it into:

```text
returns, moving averages, volatility, momentum, volume/liquidity features, and optional future labels
```

## Main file

```text
app/features/technical_indicators.py
```

## Main functions

| Function | Purpose |
|---|---|
| `build_feature_frame(price_df, include_targets=False)` | Main entry point. Adds features and optionally targets. |
| `add_price_features(price_df)` | Adds current/historical features only. Safe for analysis/model inputs. |
| `add_supervised_targets(feature_df)` | Adds future-looking labels for later ML training. |
| `calculate_rsi(close, window=14)` | Computes RSI. |
| `calculate_true_range(df)` | Computes true range. |
| `calculate_atr(df, window=14)` | Computes ATR. |
| `latest_complete_feature_row(feature_df, minimum_history_days=50)` | Returns latest row with enough complete indicator history. |

## Input requirements

The feature engine requires these columns:

```text
trade_date
open
high
low
close
volume
```

If any are missing, the system raises a clear error.

## Feature categories

See [Indicator Reference](indicators.md) for full descriptions.

Current categories:

1. Basic price action
2. Trend
3. MACD
4. Momentum
5. Volatility
6. Volume and liquidity
7. Future supervised targets

## No look-ahead bias by default

The core feature set uses only current and historical data. Future targets are only added when explicitly requested:

```bash
python -m app.main features AAPL --include-targets
```

Target columns are useful for model training labels, but they must never be used as model input features.

## Warmup periods

Some features need historical rows before they become valid.

Examples:

| Feature | Warmup idea |
|---|---|
| `sma_20` | Needs 20 rows. |
| `sma_50` | Needs 50 rows. |
| `sma_200` | Needs 200 rows. |
| `rsi_14` | Needs about 14 rows. |
| `atr_14` | Needs about 14 rows. |
| `rolling_vol_20d` | Needs 20 returns. |

For serious model training, ingest at least 5 years of history when possible.

## Command-line usage

```bash
python -m app.main ingest-price AAPL --period 5y
python -m app.main features AAPL --tail 5
```

JSON:

```bash
python -m app.main features AAPL --tail 5 --output json
```

## How the quick report uses features

The quick report calls the feature engine and then extracts the latest complete row. It summarizes:

- price action,
- trend relative to moving averages,
- RSI and MACD,
- ATR and volatility,
- volume ratio and dollar volume,
- data coverage.

## How XGBoost will use this later

In a later volume, the XGBoost dataset builder should:

1. build feature frames for many symbols,
2. include supervised targets,
3. drop target columns from model inputs,
4. split chronologically,
5. train and validate on out-of-sample periods,
6. calibrate probability outputs,
7. store model artifacts under `models/`.
