# 02 — Subsystem Salvage Assessment

**Date:** 2026-08-21  
**Project:** Tradly — AI/ML-Powered Forex Market Intelligence & Algorithmic Trading Platform  
**Document Version:** 1.0 (Phase 0 Baseline)  
**Author:** 11-Agent Swarm  
**Source of Truth:** `TRADLY_SRS v1.0` (IEEE Std 830-1998)

---

## 1. Executive Summary

Every existing subsystem across the repository was evaluated against the **TRADLY_SRS v1.0** specifications, target monorepo architecture, and engineering non-negotiables (Type Law, Decimal precision, RLS security, and layering).

The verdict assigns one of four actions to each module:
- **KEEP**: Reusable as-is with minimal relocation.
- **REFACTOR**: Architectural structure or domain algorithms are sound, but must be adapted (e.g., Decimal precision, layer decoupling, schema alignment).
- **REPLACE**: Prototype or stub implementation that cannot support production requirements (e.g., in-memory mocks, keyword search).
- **DELETE**: Legacy stock/equity framework components that conflict with Forex specifications and create dependency friction.

---

## 2. Subsystem Salvage Table

| Subsystem / Path | Action | One-Sentence Justification | Target Destination (Phase) |
|---|---|---|---|
| **`tradingagents/`** (Stock Agent Graph & Vendors) | **DELETE** | Legacy multi-agent equity framework is unaligned with Forex domain math, lacks pip/margin mechanics, and introduces 33 test collection errors. | Retire / Remove from runtime path (P1) |
| **`cli/`** (TradingAgents Typer CLI) | **DELETE** | Upstream stock CLI tool is redundant with Tradly's web-first Next.js terminal architecture. | Retire (P1) |
| **`backend/app/strategy/`** (Price-Action Strategy Modules 1–14) | **REFACTOR** | Core price-action algorithms (AOI, structure, break-and-retest, confluence) are mathematically sound with 208 passing tests, but must be ported to pure Decimal math and placed in `app/domain/`. | `apps/api/app/domain/strategy/` (P1, P4) |
| **`backend/app/services/market_service.py`** | **REPLACE** | In-memory simulated Brownian walk quotes must be replaced by a real OANDA v20 streaming/REST provider with Redis caching and candle aggregation. | `apps/api/app/providers/oanda.py` & `app/services/market_service.py` (P3) |
| **`backend/app/services/analysis_service.py`** | **REFACTOR** | Indicator algorithms (RSI, MACD, BB, ATR, EMA) and composite bias formulas are directionally correct but must be refactored into pure functions verified to 6dp against pandas-ta references. | `apps/api/app/domain/indicators.py` & `signals.py` (P4) |
| **`backend/app/services/trading_service.py`** | **REPLACE** | In-memory dict position store and float-based calculations must be replaced by a PostgreSQL/Supabase-backed persistence layer with pure Decimal margin/P&L domain math. | `apps/api/app/services/trading_service.py` & `app/domain/` (P6) |
| **`backend/app/services/ai_service.py`** | **REPLACE** | Mock keyword search over 5 hardcoded docs must be replaced by a production RAG pipeline (OpenAI embeddings + pgvector + Groq LLaMA 3) and FinBERT CPU inference. | `apps/api/app/services/rag_service.py` & `sentiment_service.py` (P8) |
| **`backend/app/services/auth_service.py`** | **REPLACE** | In-memory user store with a hardcoded JWT secret must be replaced with Supabase Auth JWT verification and RLS user context injection. | `apps/api/app/services/auth_service.py` & `core/deps.py` (P5) |
| **`backend/app/services/alert_service.py`** | **REPLACE** | In-memory alert dictionary must be replaced by a persistent Alert Service with crossing evaluation loops, WebSocket delivery, and Resend email tasks. | `apps/api/app/services/alert_service.py` (P5) |
| **`backend/app/services/tradingagents_bridge.py`** | **REFACTOR** | Bridge logic between rule-checked setups and LLMs can be repurposed to provide AI second opinions for the strategy toolkit via the unified LLM provider. | `apps/api/app/services/strategy_review_service.py` (P8) |
| **`backend/app/schemas/`** (Pydantic Models) | **REFACTOR** | Pydantic schemas accurately model Forex entities but must be updated to support the standardized `{data, error, meta}` response envelope. | `apps/api/app/schemas/` (P1) |
| **`frontend/src/app/`** (Next.js 14 App Pages) | **REFACTOR** | Next.js App Router structure and UI components provide an excellent visual foundation, but need API base centralization, envelope unwrapping, and WCAG AA contrast adjustments. | `apps/web/app/` (P1, P9) |
| **`frontend/src/components/3d/FXGlobe.tsx`** | **REFACTOR** | Three.js visual globe provides distinctive terminal branding, but must be dynamically imported with SSR disabled and WebGL 2.0 fallback detection. | `apps/web/components/3d/FXGlobe.tsx` (P9) |
| **`frontend/src/components/chart/CandlestickChart.tsx`** | **KEEP** | Custom responsive SVG candlestick chart renders without heavy charting dependencies and can be enhanced with indicator overlays. | `apps/web/components/chart/CandlestickChart.tsx` (P3) |
| **`frontend/src/services/api.ts` & `strategyApi.ts`** | **REPLACE** | Hardcoded `http://localhost:8000` URLs and manual fetch wrappers must be replaced by a generated OpenAPI TypeScript client and standardized fetch hook. | `apps/web/lib/api/` & `types/generated/` (P1) |
| **`docker-compose.yml`** | **REFACTOR** | Service layout (Postgres+pgvector, Redis, API, Web) is architecturally aligned with SRS §4 and requires only monorepo path adjustments. | `infra/docker/docker-compose.yml` (P1) |

---

## 3. Salvage Strategy & Rationale

1. **Be Ruthless on In-Memory State**: The existing `backend/app/services` layer was built as a rapid prototyping harness. Attempting to patch in-memory dicts to simulate database persistence creates technical debt; full replacement with versioned SQL migrations and Supabase repository patterns in P2 is vastly cleaner.
2. **Preserve Validated Algorithmic Logic**: The top-down confluence price-action engine (`backend/app/strategy/`) and technical indicators (`backend/app/services/analysis_service.py`) contain high-value mathematical models that pass 208 tests. Refactoring them to pure Decimal domain functions in `app/domain/` preserves intellectual property while strictly honoring Type Law.
3. **Frontend Shell Preservation**: The Next.js 14 frontend (`frontend/src/`) already implements 80% of the UI screens required by SRS §7.1 (Command Center, Candlestick Chart, AI Assistant, Paper Trading, Analytics). Relocating it into `apps/web/` in P1 and refining in P9 avoids unnecessary rebuilds.
