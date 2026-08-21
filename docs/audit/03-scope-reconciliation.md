# 03 — Scope Reconciliation Decision

**Date:** 2026-08-21  
**Project:** Tradly — AI/ML-Powered Forex Market Intelligence & Algorithmic Trading Platform  
**Document Version:** 1.0 (Phase 0 Baseline)  
**Author:** 11-Agent Swarm  
**Source of Truth:** `TRADLY_SRS v1.0` (IEEE Std 830-1998)

---

## 1. Context & The Core Dilemma

The live deployment at `https://tradex-main.vercel.app/` presents as an **"AI-Powered Trading Analysis Terminal"** featuring stock research reports, multi-agent LLM analysis (derived from the upstream `tradingagents` framework), and a stalled initialization state.

In contrast, the authoritative **`TRADLY_SRS v1.0`** specifies an **institutional-grade Forex market intelligence and paper-trading platform** with:
- Real-time OANDA v20 streaming for 15 currency pairs with pip-accurate bid/ask spreads.
- Multi-timeframe OHLCV candle aggregation (M1–D1).
- Decimal-accurate paper trading with leverage (1:1–1:100), JPY 2dp conversion, and auto-liquidation.
- Grounded RAG with source citations and strict refusal thresholds.
- FinBERT news sentiment scoring (-1.0 to +1.0).
- Economic calendar with AI pre-event briefings.
- Supabase PostgreSQL persistence with Row Level Security (RLS).

---

## 2. Evaluation of Strategic Options

Three possible paths were evaluated against constraint **CON-5** (16-week internship timeline) and the seven acceptance criteria in **SRS §10.3**:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  OPTION (A): PIVOT FULLY TO SRS FOREX SCOPE (RECOMMENDED)                      │
│  - Retire legacy stock framework (tradingagents/ & cli/).                      │
│  - Refactor existing Forex prototype into production target monorepo.         │
│  - Implement all SRS requirements (P1 through P10).                            │
├────────────────────────────────────────────────────────────────────────────────┤
│  OPTION (B): DUAL-ENGINE ARCHITECTURE (FOREX + STOCK ANNEX)                    │
│  - Freeze stock framework as an out-of-scope secondary annex.                 │
│  - Build Forex platform alongside stock terminal.                              │
│  - Maintain dual dependency chains (LangChain + FastAPI + Next.js).           │
├────────────────────────────────────────────────────────────────────────────────┤
│  OPTION (C): AMEND SRS TO MATCH BUILT STOCK PRODUCT                            │
│  - Rewrite SRS v1.0 to drop Forex, pips, leverage, and OANDA.                  │
│  - Standardize on equity research and multi-agent report generation.           │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

### Option (A): Pivot Fully to the SRS Forex Scope (RECOMMENDED)

- **Description:** Formally retire and remove the legacy upstream stock framework (`tradingagents/`, `cli/`, root `main.py`). Restructure the repository around the target monorepo architecture (`apps/web`, `apps/api`, `infra/`, `docs/`). Retain and refactor the pure Forex top-down strategy engine and build the persistent data, streaming, RAG, and paper-trading services specified in the SRS.
- **Cost Analysis:**
  - Zero ongoing maintenance of broken stock dependencies (`yfinance`, `stockstats`, etc.).
  - 100% development velocity focused on Forex modules (P1–P10).
  - Eliminates 33 test collection errors immediately.
- **Risk Analysis:** **LOW**. Eliminates architectural schizophrenia and aligns the codebase directly with academic and industry internship deliverables.
- **Timeline Impact (CON-5):** Optimal. Fits comfortably within the 16-week schedule because all efforts directly satisfy SRS functional requirements.

---

### Option (B): Dual-Engine Architecture (Forex + Stock Annex)

- **Description:** Maintain the stock multi-agent framework in a separate directory (`legacy/` or `annex/`), keeping it frozen while building the Forex platform in parallel.
- **Cost Analysis:**
  - High build and CI complexity: must maintain two separate Python environments or a bloated `pyproject.toml`.
  - Fragile dependency tree (LangChain/LangGraph version conflicts with lightweight FastAPI services).
- **Risk Analysis:** **HIGH**. Diverts engineering focus, causes confusion in API contracts, and complicates Docker deployment images.
- **Timeline Impact (CON-5):** Negative. Increases risk of timeline slip by 2–3 weeks due to CI/CD and dependency overhead.

---

### Option (C): Amend SRS to Match the Built Stock Product

- **Description:** Discard the Forex requirements in TRADLY_SRS v1.0 and rewrite the specification to describe a stock analysis tool.
- **Cost Analysis:**
  - Requires renegotiating internship scope, learning objectives, and project deliverables with university faculty and ThinkNovus mentors.
  - Discards already verified Month 2 milestones (15 Forex pairs, pip calculations, session clock).
- **Risk Analysis:** **CRITICAL**. High academic and organizational risk; violates the approved internship charter.
- **Timeline Impact (CON-5):** Severe disruption.

---

## 3. Final Recommendation & Strategic Decision

**Recommendation:** **Execute Option (A) — Full Pivot to TRADLY_SRS v1.0 Forex Scope.**

### Key Action Directives:
1. **Archive Legacy Stock Modules:** Isolate `tradingagents/` and `cli/` from the build system. Remove their dependencies from root `pyproject.toml` in Phase 1.
2. **Standardize on Target Monorepo Layout:**
   - Move `frontend/` into `apps/web/`.
   - Re-architect `backend/` into `apps/api/` following the layering law (`routers → services → repositories → DB`).
3. **Integrate the Forex Strategy Toolkit:** Keep the 14 pure price-action strategy modules (`backend/app/strategy/`) as a specialized domain library in `apps/api/app/domain/strategy/`, porting all math to `decimal.Decimal`.
4. **Deploy Fresh Next.js 14 Web Terminal:** Update the Vercel deployment configuration to deploy `apps/web` pointing to the live API gateway, eliminating the stalled stock terminal frontend.
