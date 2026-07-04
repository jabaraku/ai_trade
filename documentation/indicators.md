# Indicator Reference

This page documents every engineered feature currently created by:

```text
app/features/technical_indicators.py
```

The indicators are deterministic features created from local OHLCV price bars. They are not trading signals by themselves. They become useful when combined with risk rules, backtesting, model validation, and human review.

## Reading conventions

- **Close** means the daily closing price.
- **Return** means percentage change unless otherwise stated.
- **Warmup** means the minimum historical rows needed before the value becomes reliable.
- **Model use** means why this feature may be useful for future XGBoost training.

---

## Basic price action features

### `return_1d`

One-day close-to-close percentage return.

Formula:

```text
close_today / close_yesterday - 1
```

Interpretation:

- Positive means price closed higher than the prior trading day.
- Negative means price closed lower than the prior trading day.

Model use:

- Short-term momentum or reversal input.
- Base input for volatility features.

Caveat:

- A single daily return is noisy and should not be used alone.

### `return_5d`

Five-trading-day close-to-close percentage return.

Approximate meaning: one trading week of price movement.

Model use:

- Captures short swing-trading momentum.
- Useful for comparing recent momentum against longer-term trend.

### `return_21d`

Twenty-one-trading-day close-to-close percentage return.

Approximate meaning: one trading month of price movement.

Model use:

- Captures monthly momentum.
- Helps identify whether a stock is extended or weak relative to the last month.

### `log_return_1d`

Natural log of daily close-to-close price ratio.

Formula:

```text
ln(close_today / close_yesterday)
```

Interpretation:

- Similar to daily return for small moves.
- Often preferred in quantitative finance because log returns add more cleanly over time.

Model use:

- Useful for volatility calculations and future statistical modeling.

### `daily_range_pct`

Daily high-low range as a percentage of close.

Formula:

```text
(high - low) / close
```

Interpretation:

- Larger values indicate wider intraday movement.
- Can be a proxy for daily realized volatility.

Model use:

- Helps identify high-volatility sessions and regime changes.

### `open_to_close_pct`

Intraday move from open to close.

Formula:

```text
(close - open) / open
```

Interpretation:

- Positive: stock closed above its open.
- Negative: stock closed below its open.

Model use:

- Helps distinguish gap-driven moves from intraday buying/selling pressure.

### `close_position_in_day_range`

Where the close sits inside the day’s high-low range.

Formula:

```text
(close - low) / (high - low)
```

Interpretation:

- Near `1`: close was near the high of the day.
- Near `0`: close was near the low of the day.
- Near `0.5`: close was around the middle of the range.

Model use:

- Can capture session strength or weakness.

Caveat:

- If high equals low, the denominator is zero and the feature is set to null.

---

## Simple moving average features

### `sma_5`

Five-day simple moving average of close.

Interpretation:

- Very short-term average price.
- Reacts quickly to price changes.

### `sma_10`

Ten-day simple moving average of close.

Interpretation:

- Short-term trend proxy.

### `sma_20`

Twenty-day simple moving average of close.

Interpretation:

- Roughly one trading month.
- Often used to judge short/intermediate trend.

### `sma_50`

Fifty-day simple moving average of close.

Interpretation:

- Intermediate trend proxy.
- Many traders watch price relative to the 50-day average.

### `sma_200`

Two-hundred-day simple moving average of close.

Interpretation:

- Long-term trend proxy.
- Often used to classify broad bullish/bearish trend context.

Model use for all SMA values:

- Helps the model understand trend at multiple horizons.
- Useful when combined with `close_vs_sma_*` features.

Dashboard chart use:

- The Analyze tab overlays `SMA 20`, `SMA 50`, and `SMA 200` directly on the candlestick chart. `SMA 5` and `SMA 10` remain engineered features for modeling and JSON analysis, but they are intentionally not shown on the chart to reduce visual clutter.
- The chart legend is labeled **Color key** so each SMA line can be identified visually.
- SMA periods are calculated on the selected candle timeframe. For example, Weekly + SMA 20 means 20 weekly closes, not 20 daily closes.

Caveat:

- Moving averages lag price because they summarize historical data.

---

## Close-versus-moving-average features

These features normalize price distance from each SMA.

Formula:

```text
close / sma_window - 1
```

### `close_vs_sma_5`

Distance of close from the 5-day SMA.

### `close_vs_sma_10`

Distance of close from the 10-day SMA.

### `close_vs_sma_20`

Distance of close from the 20-day SMA.

### `close_vs_sma_50`

Distance of close from the 50-day SMA.

### `close_vs_sma_200`

Distance of close from the 200-day SMA.

Interpretation:

- Positive: close is above the moving average.
- Negative: close is below the moving average.
- Large positive values can indicate strength or overextension.
- Large negative values can indicate weakness or potential mean-reversion context.

Model use:

- Better than raw SMA values for cross-symbol modeling because the feature is normalized.

---

## Exponential moving average and MACD features

### `ema_12`

Twelve-period exponential moving average of close.

Interpretation:

- Fast-moving trend estimate.
- Reacts more quickly than a simple moving average.

### `ema_26`

Twenty-six-period exponential moving average of close.

Interpretation:

- Slower trend estimate.

### `macd_line`

Difference between the fast and slow EMAs.

Formula:

```text
ema_12 - ema_26
```

Interpretation:

- Positive: shorter-term trend is above longer-term trend.
- Negative: shorter-term trend is below longer-term trend.

### `macd_signal`

Nine-period exponential moving average of `macd_line`.

Interpretation:

- Smooths the MACD line.

### `macd_histogram`

Difference between MACD line and MACD signal.

Formula:

```text
macd_line - macd_signal
```

Interpretation:

- Positive histogram: MACD line is above signal line.
- Negative histogram: MACD line is below signal line.
- Increasing histogram can indicate improving momentum.
- Decreasing histogram can indicate fading momentum.

Model use:

- MACD features help represent momentum shifts and trend acceleration/deceleration.

Caveat:

- MACD can whipsaw in sideways markets.

---

## Momentum and volatility features

### `rsi_14`

Fourteen-period Relative Strength Index using Wilder-style smoothing.

Range:

```text
0 to 100
```

Common interpretation:

- Above 70: often described as overbought.
- Below 30: often described as oversold.
- Around 50: neutral.

Model use:

- Captures recent average gains versus recent average losses.
- Useful for momentum and mean-reversion research.

Caveat:

- RSI can remain high during strong uptrends and low during strong downtrends. Do not treat thresholds as automatic buy/sell rules.

### `true_range`

The largest of:

```text
high - low
abs(high - previous_close)
abs(low - previous_close)
```

Interpretation:

- Captures daily movement including overnight gaps.

Model use:

- Building block for ATR.

### `atr_14`

Fourteen-period Average True Range using Wilder-style smoothing.

Interpretation:

- Average absolute price movement over recent sessions.
- Higher ATR means larger price swings.

Model use:

- Useful for volatility-aware position sizing and expected move context.

Caveat:

- ATR is expressed in price units, so it is less comparable across symbols unless normalized.

### `atr_14_pct`

ATR normalized by close.

Formula:

```text
atr_14 / close
```

Interpretation:

- ATR as a percentage of price.
- More comparable across different symbols than raw ATR.

Model use:

- Helps compare volatility across stocks with different price levels.

### `rolling_vol_20d`

Twenty-day rolling standard deviation of daily returns.

Interpretation:

- Recent realized volatility.

Model use:

- Helps model changing market regimes and risk.

### `rolling_vol_20d_annualized`

Annualized version of 20-day rolling volatility.

Formula:

```text
rolling_vol_20d * sqrt(252)
```

Interpretation:

- Converts daily realized volatility into an approximate annualized number.

Caveat:

- Annualization assumes 252 trading days and stable volatility, which is only an approximation.

---

## Volume and liquidity features

### `volume_sma_20`

Twenty-day simple moving average of volume.

Interpretation:

- Recent average trading activity.

### `volume_ratio_20`

Current volume divided by 20-day average volume.

Formula:

```text
volume / volume_sma_20
```

Interpretation:

- Above 1: higher than recent average volume.
- Below 1: lower than recent average volume.

Model use:

- Helps detect unusual participation or low-liquidity conditions.

### `dollar_volume`

Close price multiplied by volume.

Formula:

```text
close * volume
```

Interpretation:

- Approximate dollar value traded during the session.

Model use:

- Liquidity proxy.

### `dollar_volume_sma_20`

Twenty-day moving average of dollar volume.

Interpretation:

- Smoothed liquidity estimate.

Model use:

- Helps filter out low-liquidity names in later strategy research.

---

## Future supervised targets

Targets are created only when `include_targets=True`.

These columns intentionally use future data and must never be used as model inputs.

### `future_return_1d`

Next-day future return.

Formula:

```text
close_next_day / close_today - 1
```

Use:

- Regression label or source for classification target.

### `future_return_5d`

Five-trading-day future return.

Formula:

```text
close_5_days_forward / close_today - 1
```

Use:

- Swing-trading horizon label.

### `target_up_1d`

Binary label indicating whether `future_return_1d` is positive.

Values:

```text
1 = next day return is positive
0 = next day return is not positive
```

### `target_up_5d`

Binary label indicating whether `future_return_5d` is positive.

Values:

```text
1 = next 5-day return is positive
0 = next 5-day return is not positive
```

## Important modeling warning

The target columns are labels, not features. A correct XGBoost training dataset must exclude:

```text
future_return_1d
future_return_5d
target_up_1d
target_up_5d
```

from the input feature matrix.

## Practical interpretation summary

| Category | What it tells you |
|---|---|
| Returns | Recent direction and magnitude. |
| Daily range | Intraday volatility. |
| Close position | Whether the session closed strong or weak. |
| SMAs | Trend across multiple horizons. |
| Close vs SMA | Normalized trend/extension. |
| EMAs/MACD | Momentum shifts. |
| RSI | Relative strength of gains vs losses. |
| ATR | Absolute volatility. |
| ATR percent | Comparable volatility across symbols. |
| Rolling vol | Realized volatility regime. |
| Volume ratio | Unusual activity. |
| Dollar volume | Liquidity. |
| Targets | Future labels for ML training only. |

## Persisted indicator rows

The indicator values documented above can now be written to the DuckDB `indicators` table by running:

```powershell
python -m app.main calculate AAPL 5y
```

The table stores one row per symbol and trade date for the requested duration. Supported durations are `3m`, `6m`, `1y`, `3y`, and `5y`. The maximum persisted duration is `5y`.

Future-looking labels such as `future_return_1d`, `future_return_5d`, `target_up_1d`, and `target_up_5d` are intentionally not stored in this table. Those labels belong in a later supervised machine-learning dataset, not in the current live-style indicator table.
