-- =============================================================================
-- Migration: 0001_initial_schema.sql
-- Description: Core schema for Tradly Forex Platform (TRADLY_SRS v1.0 §5.1-§5.2)
-- Constraints: DI-1, DI-2, DI-3, DI-4, DI-5 (Exact Types, Numeric Money, Checks)
-- =============================================================================

-- Enable pgvector extension for RAG embeddings
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. CURRENCY PAIRS (Reference Data)
CREATE TABLE IF NOT EXISTS currency_pairs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(16) UNIQUE NOT NULL,
    base_currency CHAR(3) NOT NULL,
    quote_currency CHAR(3) NOT NULL,
    pip_decimal_places SMALLINT NOT NULL CHECK (pip_decimal_places IN (2, 4)),
    category VARCHAR(16) NOT NULL CHECK (category IN ('major', 'minor', 'exotic')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. CANDLES (Market Data, Multi-Timeframe)
CREATE TABLE IF NOT EXISTS candles (
    id BIGSERIAL PRIMARY KEY,
    pair_id UUID NOT NULL REFERENCES currency_pairs(id) ON DELETE CASCADE,
    timeframe VARCHAR(8) NOT NULL CHECK (timeframe IN ('M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1')),
    open_time TIMESTAMPTZ NOT NULL,
    open NUMERIC(12, 6) NOT NULL,
    high NUMERIC(12, 6) NOT NULL,
    low NUMERIC(12, 6) NOT NULL,
    close NUMERIC(12, 6) NOT NULL,
    volume BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- DI-1: Candle integrity constraint
    CONSTRAINT chk_candle_ohlc CHECK (
        low <= open AND open <= high AND
        low <= close AND close <= high AND
        low <= high
    ),
    -- DI-2: Unique candle per pair, timeframe, and open timestamp
    CONSTRAINT uq_pair_timeframe_opentime UNIQUE (pair_id, timeframe, open_time)
);

-- BRIN index on open_time for time-range analytical scans
CREATE INDEX IF NOT EXISTS idx_candles_open_time_brin ON candles USING BRIN (open_time);
CREATE INDEX IF NOT EXISTS idx_candles_pair_tf_time ON candles (pair_id, timeframe, open_time DESC);

-- 3. INDICATOR SNAPSHOTS
CREATE TABLE IF NOT EXISTS indicator_snapshots (
    id BIGSERIAL PRIMARY KEY,
    pair_id UUID NOT NULL REFERENCES currency_pairs(id) ON DELETE CASCADE,
    timeframe VARCHAR(8) NOT NULL CHECK (timeframe IN ('M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1')),
    candle_time TIMESTAMPTZ NOT NULL,
    rsi_14 NUMERIC(8, 4),
    macd_line NUMERIC(12, 6),
    macd_signal NUMERIC(12, 6),
    macd_hist NUMERIC(12, 6),
    bb_upper NUMERIC(12, 6),
    bb_middle NUMERIC(12, 6),
    bb_lower NUMERIC(12, 6),
    atr_14 NUMERIC(12, 6),
    ema_9 NUMERIC(12, 6),
    ema_21 NUMERIC(12, 6),
    ema_50 NUMERIC(12, 6),
    sma_200 NUMERIC(12, 6),
    fib_levels JSONB,
    bias_score NUMERIC(5, 2),
    bias_label VARCHAR(32),
    bias_breakdown JSONB,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_indicator_snapshot UNIQUE (pair_id, timeframe, candle_time)
);

-- 4. PAPER ACCOUNTS (User Virtual Accounts)
CREATE TABLE IF NOT EXISTS paper_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    balance NUMERIC(14, 2) NOT NULL DEFAULT 10000.00 CHECK (balance >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_active_account UNIQUE (user_id)
);

-- 5. POSITIONS (Open Paper Positions)
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES paper_accounts(id) ON DELETE CASCADE,
    pair_id UUID NOT NULL REFERENCES currency_pairs(id),
    direction VARCHAR(8) NOT NULL CHECK (direction IN ('long', 'short')),
    lot_size NUMERIC(8, 2) NOT NULL,
    units NUMERIC(14, 2) NOT NULL,
    leverage NUMERIC(6, 2) NOT NULL CHECK (leverage IN (1, 10, 30, 50, 100)),
    entry_price NUMERIC(12, 6) NOT NULL,
    current_price NUMERIC(12, 6) NOT NULL,
    stop_loss NUMERIC(12, 6),
    take_profit NUMERIC(12, 6),
    trailing_stop_pips NUMERIC(8, 2),
    required_margin NUMERIC(12, 2) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed', 'liquidated')),
    exit_price NUMERIC(12, 6),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    -- DI-3: units must be non-zero and closed positions must record exit_price
    CONSTRAINT chk_position_units CHECK (units <> 0),
    CONSTRAINT chk_position_closure CHECK (
        (status = 'open' AND exit_price IS NULL AND closed_at IS NULL) OR
        (status IN ('closed', 'liquidated') AND exit_price IS NOT NULL AND closed_at IS NOT NULL)
    )
);

-- Partial index for active open positions (hot query path)
CREATE INDEX IF NOT EXISTS idx_positions_open ON positions (account_id) WHERE status = 'open';

-- 6. TRADES (Historical Closed Trades & Journal)
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES paper_accounts(id) ON DELETE CASCADE,
    position_id UUID REFERENCES positions(id),
    pair_id UUID NOT NULL REFERENCES currency_pairs(id),
    direction VARCHAR(8) NOT NULL CHECK (direction IN ('long', 'short')),
    lot_size NUMERIC(8, 2) NOT NULL,
    units NUMERIC(14, 2) NOT NULL,
    entry_price NUMERIC(12, 6) NOT NULL,
    exit_price NUMERIC(12, 6) NOT NULL,
    realized_pnl NUMERIC(14, 2) NOT NULL,
    realized_pnl_pips NUMERIC(10, 1) NOT NULL,
    close_reason VARCHAR(32) NOT NULL CHECK (close_reason IN ('manual', 'stop_loss', 'take_profit', 'liquidation')),
    opened_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session VARCHAR(16),
    journal_notes TEXT,
    journal_tags TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_account_closed ON trades (account_id, closed_at DESC);

-- 7. WATCHLISTS & WATCHLIST PAIRS
CREATE TABLE IF NOT EXISTS watchlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(64) NOT NULL DEFAULT 'My Watchlist',
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS watchlist_pairs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    watchlist_id UUID NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    pair_id UUID NOT NULL REFERENCES currency_pairs(id) ON DELETE CASCADE,
    display_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_watchlist_pair UNIQUE (watchlist_id, pair_id)
);

-- 8. ALERTS & NOTIFICATIONS
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    pair_id UUID NOT NULL REFERENCES currency_pairs(id) ON DELETE CASCADE,
    alert_type VARCHAR(32) NOT NULL CHECK (alert_type IN ('price_above', 'price_below', 'rsi_overbought', 'rsi_oversold', 'macd_crossover', 'bb_squeeze')),
    threshold_value NUMERIC(12, 6) NOT NULL,
    timeframe VARCHAR(8) DEFAULT 'H1',
    note TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_triggered BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_triggered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts (pair_id, alert_type) WHERE is_active = TRUE;

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    alert_id UUID REFERENCES alerts(id) ON DELETE SET NULL,
    title VARCHAR(256) NOT NULL,
    message TEXT NOT NULL,
    channel VARCHAR(32) NOT NULL CHECK (channel IN ('in_app', 'email')),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications (user_id, is_read, created_at DESC);

-- 9. NEWS DOCUMENTS & DOCUMENT CHUNKS (RAG Pipeline)
CREATE TABLE IF NOT EXISTS news_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(512) NOT NULL,
    source VARCHAR(128) NOT NULL,
    url TEXT,
    content_hash CHAR(64) UNIQUE NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES news_documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    token_count INT NOT NULL,
    currencies TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW index for vector cosine similarity search
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw 
ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- 10. SENTIMENT SCORES
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    currency CHAR(3) NOT NULL,
    score NUMERIC(5, 2) NOT NULL CHECK (score >= -1.0 AND score <= 1.0),
    label VARCHAR(16) NOT NULL CHECK (label IN ('Bullish', 'Bearish', 'Neutral')),
    article_count INT NOT NULL DEFAULT 0,
    hourly_timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_currency_hourly_sentiment UNIQUE (currency, hourly_timestamp)
);

-- 11. ECONOMIC EVENTS
CREATE TABLE IF NOT EXISTS economic_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(256) NOT NULL,
    country VARCHAR(64) NOT NULL,
    currency CHAR(3) NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    impact VARCHAR(16) NOT NULL CHECK (impact IN ('High', 'Medium', 'Low')),
    previous VARCHAR(32),
    consensus VARCHAR(32),
    actual VARCHAR(32),
    ai_briefing TEXT,
    historical_pip_volatility VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_economic_events_time ON economic_events (scheduled_at);

-- 12. SIGNAL WEIGHTS CONFIG (AI-3.3: Configurable in DB)
CREATE TABLE IF NOT EXISTS signal_weights_config (
    id SERIAL PRIMARY KEY,
    indicator_name VARCHAR(64) UNIQUE NOT NULL,
    weight NUMERIC(4, 2) NOT NULL CHECK (weight >= 0 AND weight <= 1),
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 13. AI QUERY LOG (AI-1.4: Audit & Evaluation)
CREATE TABLE IF NOT EXISTS ai_query_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    query TEXT NOT NULL,
    retrieved_chunk_ids UUID[],
    response TEXT NOT NULL,
    model VARCHAR(64) NOT NULL,
    latency_ms INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
