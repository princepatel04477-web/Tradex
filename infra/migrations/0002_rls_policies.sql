-- =============================================================================
-- Migration: 0002_rls_policies.sql
-- Description: Row Level Security (RLS) policies for user data isolation
-- Requirements: NFR-S3, FR-6.4, TC-4
-- =============================================================================

-- Enable Row Level Security (RLS) on all user-scoped tables (NFR-S3)
-- Standard PostgreSQL / Neon auth schema emulation
CREATE SCHEMA IF NOT EXISTS auth;
CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid AS $$
    SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid;
$$ LANGUAGE sql STABLE;

-- 1. PAPER ACCOUNTS
ALTER TABLE paper_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlist_pairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_query_log ENABLE ROW LEVEL SECURITY;

-- Enable RLS on reference tables (read-only for all, write for service_role)
ALTER TABLE currency_pairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE candles ENABLE ROW LEVEL SECURITY;
ALTER TABLE indicator_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE sentiment_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE economic_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE signal_weights_config ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- 1. REFERENCE DATA POLICIES (Read-only for authenticated & anon, service write)
-- -----------------------------------------------------------------------------
CREATE POLICY "Public Read Access on Currency Pairs" ON currency_pairs
    FOR SELECT USING (true);

CREATE POLICY "Public Read Access on Candles" ON candles
    FOR SELECT USING (true);

CREATE POLICY "Public Read Access on Indicator Snapshots" ON indicator_snapshots
    FOR SELECT USING (true);

CREATE POLICY "Public Read Access on News Documents" ON news_documents
    FOR SELECT USING (true);

CREATE POLICY "Public Read Access on Document Chunks" ON document_chunks
    FOR SELECT USING (true);

CREATE POLICY "Public Read Access on Sentiment Scores" ON sentiment_scores
    FOR SELECT USING (true);

CREATE POLICY "Public Read Access on Economic Events" ON economic_events
    FOR SELECT USING (true);

CREATE POLICY "Public Read Access on Signal Weights" ON signal_weights_config
    FOR SELECT USING (true);

-- -----------------------------------------------------------------------------
-- 2. USER-SCOPED POLICIES (Keyed on auth.uid())
-- -----------------------------------------------------------------------------

-- Paper Accounts
CREATE POLICY "Users can view own paper accounts" ON paper_accounts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own paper accounts" ON paper_accounts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own paper accounts" ON paper_accounts
    FOR UPDATE USING (auth.uid() = user_id);

-- Positions (chained through paper_accounts ownership)
CREATE POLICY "Users can view own positions" ON positions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM paper_accounts
            WHERE paper_accounts.id = positions.account_id
            AND paper_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own positions" ON positions
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM paper_accounts
            WHERE paper_accounts.id = positions.account_id
            AND paper_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own positions" ON positions
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM paper_accounts
            WHERE paper_accounts.id = positions.account_id
            AND paper_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own positions" ON positions
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM paper_accounts
            WHERE paper_accounts.id = positions.account_id
            AND paper_accounts.user_id = auth.uid()
        )
    );

-- Trades
CREATE POLICY "Users can view own trade history" ON trades
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM paper_accounts
            WHERE paper_accounts.id = trades.account_id
            AND paper_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own trades" ON trades
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM paper_accounts
            WHERE paper_accounts.id = trades.account_id
            AND paper_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update journal in own trades" ON trades
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM paper_accounts
            WHERE paper_accounts.id = trades.account_id
            AND paper_accounts.user_id = auth.uid()
        )
    );

-- Watchlists & Pairs
CREATE POLICY "Users can manage own watchlists" ON watchlists
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own watchlist pairs" ON watchlist_pairs
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM watchlists
            WHERE watchlists.id = watchlist_pairs.watchlist_id
            AND watchlists.user_id = auth.uid()
        )
    );

-- Alerts & Notifications
CREATE POLICY "Users can manage own alerts" ON alerts
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own notifications" ON notifications
    FOR ALL USING (auth.uid() = user_id);

-- AI Query Log
CREATE POLICY "Users can view own AI query logs" ON ai_query_log
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert AI query logs" ON ai_query_log
    FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);
