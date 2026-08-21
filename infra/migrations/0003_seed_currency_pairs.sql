-- =============================================================================
-- Migration: 0003_seed_currency_pairs.sql
-- Description: Seed 15 in-scope currency pairs (Appendix A) & default signal weights (AI-3.3)
-- Verification: JPY pairs have pip_decimal_places = 2; all standard pairs = 4
-- =============================================================================

INSERT INTO currency_pairs (symbol, base_currency, quote_currency, pip_decimal_places, category, is_active) VALUES
    -- Majors
    ('EUR_USD', 'EUR', 'USD', 4, 'major', TRUE),
    ('GBP_USD', 'GBP', 'USD', 4, 'major', TRUE),
    ('USD_JPY', 'USD', 'JPY', 2, 'major', TRUE),
    ('USD_CHF', 'USD', 'CHF', 4, 'major', TRUE),
    ('AUD_USD', 'AUD', 'USD', 4, 'major', TRUE),
    ('NZD_USD', 'NZD', 'USD', 4, 'major', TRUE),
    ('USD_CAD', 'USD', 'CAD', 4, 'major', TRUE),
    -- Minors
    ('EUR_GBP', 'EUR', 'GBP', 4, 'minor', TRUE),
    ('EUR_JPY', 'EUR', 'JPY', 2, 'minor', TRUE),
    ('GBP_JPY', 'GBP', 'JPY', 2, 'minor', TRUE),
    ('AUD_JPY', 'AUD', 'JPY', 2, 'minor', TRUE),
    ('EUR_AUD', 'EUR', 'AUD', 4, 'minor', TRUE),
    -- Exotics
    ('USD_INR', 'USD', 'INR', 4, 'exotic', TRUE),
    ('USD_SGD', 'USD', 'SGD', 4, 'exotic', TRUE),
    ('USD_MXN', 'USD', 'MXN', 4, 'exotic', TRUE)
ON CONFLICT (symbol) DO NOTHING;

-- Seed Default Composite Signal Weights (SRS §6.3, AI-3.3)
INSERT INTO signal_weights_config (indicator_name, weight, description) VALUES
    ('ema_cross', 0.25, 'EMA-9 vs EMA-21 trend alignment'),
    ('sma_200', 0.20, 'Price position relative to SMA-200 baseline'),
    ('macd_hist', 0.20, 'MACD histogram direction and slope'),
    ('rsi_14', 0.15, 'RSI-14 momentum oscillator zone'),
    ('bb_position', 0.10, 'Price position within Bollinger Bands'),
    ('sentiment', 0.10, 'FinBERT currency news sentiment score')
ON CONFLICT (indicator_name) DO UPDATE SET
    weight = EXCLUDED.weight,
    description = EXCLUDED.description;
