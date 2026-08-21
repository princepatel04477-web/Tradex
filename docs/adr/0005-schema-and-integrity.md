# ADR 0005: Database Schema Constraints and Data Integrity

**Status:** Accepted  
**Date:** 2026-08-21  
**Author:** 11-Agent Swarm  
**Context:** SRS §5, DI-1, DI-2, DI-3, DI-5, NFR-S3.

---

## Context
Financial trading systems must prevent corrupt candle data, duplicate ticks, ghost positions, and floating-point rounding errors at the database layer.

## Decision
Enforce data integrity rules in PostgreSQL:
1. **DI-1 (Candle OHLC):** `CHECK (low <= open AND open <= high AND low <= close AND close <= high AND low <= high)`
2. **DI-2 (Unique Candles):** `UNIQUE (pair_id, timeframe, open_time)`
3. **DI-3 (Position Lifecycle):** `CHECK (units <> 0)` and `(status = 'open' AND exit_price IS NULL) OR (status IN ('closed', 'liquidated') AND exit_price IS NOT NULL)`
4. **DI-5 (Numeric Money):** All prices and monetary balances stored as `NUMERIC(12, 6)` or `NUMERIC(14, 2)`.
5. **NFR-S3 (Row Level Security):** All user tables enable RLS keyed on `auth.uid() = user_id`.

## Consequences
- Database rejects invalid states even if service layer validation fails.
- Guaranteed multi-tenant data isolation.
