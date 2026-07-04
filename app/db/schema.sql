CREATE TABLE IF NOT EXISTS price_bars (
    symbol TEXT NOT NULL,
    trade_date DATE NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    adj_close DOUBLE,
    volume BIGINT,
    provider TEXT NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, trade_date, provider)
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    run_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_name TEXT,
    probability_up DOUBLE,
    recommendation TEXT,
    explanation TEXT,
    raw_payload JSON
);

CREATE TABLE IF NOT EXISTS system_events (
    event_id TEXT PRIMARY KEY,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSON
);

CREATE TABLE IF NOT EXISTS indicators (
    symbol TEXT NOT NULL,
    trade_date DATE NOT NULL,
    calculation_duration TEXT NOT NULL,
    source_row_count BIGINT NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    return_1d DOUBLE,
    return_5d DOUBLE,
    return_21d DOUBLE,
    log_return_1d DOUBLE,
    daily_range_pct DOUBLE,
    open_to_close_pct DOUBLE,
    close_position_in_day_range DOUBLE,

    sma_5 DOUBLE,
    sma_10 DOUBLE,
    sma_20 DOUBLE,
    sma_50 DOUBLE,
    sma_200 DOUBLE,
    close_vs_sma_5 DOUBLE,
    close_vs_sma_10 DOUBLE,
    close_vs_sma_20 DOUBLE,
    close_vs_sma_50 DOUBLE,
    close_vs_sma_200 DOUBLE,

    ema_12 DOUBLE,
    ema_26 DOUBLE,
    macd_line DOUBLE,
    macd_signal DOUBLE,
    macd_histogram DOUBLE,

    rsi_14 DOUBLE,
    true_range DOUBLE,
    atr_14 DOUBLE,
    atr_14_pct DOUBLE,
    rolling_vol_20d DOUBLE,
    rolling_vol_20d_annualized DOUBLE,

    volume_sma_20 DOUBLE,
    volume_ratio_20 DOUBLE,
    dollar_volume DOUBLE,
    dollar_volume_sma_20 DOUBLE,

    PRIMARY KEY (symbol, trade_date)
);
