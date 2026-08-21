# ADR 0001: Scope Reconciliation & Product Pivot to Forex Intelligence

**Status:** Accepted  
**Date:** 2026-08-21  
**Author:** 11-Agent Swarm (Mission Planner, Repository Analyst, Architect, Database Engineer, Backend Engineer, Frontend Engineer, Forex Domain Expert, Performance Engineer, Security Analyst, QA Inspector, Documentation Engineer)  
**Target:** Tradly Platform Architecture  
**Context Source:** `TRADLY_SRS v1.0` (IEEE Std 830-1998)

---

## 1. Context and Problem Statement

The live frontend deployed at `https://tradex-main.vercel.app/` presents as an **"AI-Powered Trading Analysis Terminal"** with routes `/`, `/trading-analysis`, `/analysis`, `/reports`, `/forex`, and `/settings`. Its content and metadata emphasize equity stock analysis, financial filings, and multi-agent LLM debate graphs (originating from the upstream `tradingagents` framework). Furthermore, the deployed site stalls indefinitely on a client-side seed initialization state (`INITIALIZING TERMINAL SEED...`) due to hardcoded connections to `localhost:8000`.

In contrast, the system-of-record specification—**`TRADLY_SRS v1.0`**—defines Tradly as an **AI/ML-Powered Forex Market Intelligence & Algorithmic Trading Platform**, developed as an academic internship project at ThinkNovus Private Limited. The SRS mandates:
1. Real-time streaming and tick normalization for 15 Forex currency pairs (majors, minors, exotics) via OANDA v20.
2. Multi-timeframe OHLCV candle aggregation (M1 to D1) and technical indicator computation.
3. Pip-accurate paper trading simulator supporting leverage (1:1 to 1:100), JPY 2-decimal vs 4-decimal pip valuation, and automated liquidation risk controls.
4. Grounded RAG natural language assistant with verifiable source citations and refusal on low relevance.
5. FinBERT-based Forex news and central bank sentiment scoring (-1.0 to +1.0).
6. PostgreSQL Row Level Security (RLS) data isolation and structured JSON logging.

A fundamental divergence exists between the legacy stock framework in the repository and the approved SRS. The project must establish a single, authoritative scope before production engineering commences.

---

## 2. Decision Drivers

- **SRS v1.0 Compliance (CON-5):** The internship deliverables and academic evaluation are strictly tied to the 6 function groups (FG-1 to FG-6) in TRADLY_SRS v1.0.
- **Defect Prevention & Type Law (DI-5):** Forex market mechanics require exact Decimal precision, pip arithmetic, bid/ask spread asymmetry, and margin level formulas. Stock frameworks do not support these domain invariants.
- **Build & CI Stability:** The legacy `tradingagents` stock framework introduces 33 test collection errors due to uninstalled dependencies (`langchain_core`, `yfinance`, `questionary`).
- **Timeline Feasibility (CON-5):** Completing the project within a 16-week internship window requires 100% development focus on the core Forex requirements.

---

## 3. Considered Options

1. **Option A (Pivot Fully to SRS Forex Scope):** Retire and isolate the legacy stock framework (`tradingagents/`, `cli/`); adopt the target monorepo architecture (`apps/web`, `apps/api`); build all Forex requirements (P1–P10).
2. **Option B (Dual-Engine Forex + Stock Annex):** Maintain stock agents as a secondary out-of-scope subsystem and build the Forex platform alongside.
3. **Option C (Amend SRS to Match Stock Tool):** Discard the Forex specification and rewrite the SRS to describe a stock analysis tool.

---

## 4. Decision Outcome

**Chosen Option:** **Option A — Pivot Fully to SRS Forex Scope.**

### Key Decisions:
1. **Retire Stock Subsystems:** The `tradingagents/` package and `cli/` application are retired from the active build path. Their dependencies are removed from root configuration.
2. **Adopt Target Monorepo Architecture:** The project will be restructured in Phase 1 into:
   - `apps/web/`: Next.js 14 App Router web terminal with TypeScript strict mode.
   - `apps/api/`: FastAPI async backend with pure Decimal domain math and clean layering (`routers → services → repositories → DB`).
   - `infra/`: Docker, migrations, and CI/CD pipelines.
   - `docs/`: Comprehensive technical documentation, ADRs, and worked domain math examples.
3. **Salvage & Refactor Strategy Toolkit:** The 14 price-action strategy modules in `backend/app/strategy/` will be preserved and refactored into pure domain functions in `apps/api/app/domain/strategy/`, standardizing all monetary and pip math on Python `decimal.Decimal`.
4. **Deploy Dedicated Forex Terminal:** The Vercel deployment will be updated to point to the refactored `apps/web` application communicating with the production FastAPI gateway via `NEXT_PUBLIC_API_BASE`.

---

## 5. Consequences

### Positive Consequences:
- Eliminates 33 test collection failures and resolves dependency bloat.
- Restores 100% alignment with academic and industry internship deliverables (`Tradly_SRS.md` and `Tradly_Month2_Report.md`).
- Guarantees institutional correctness for Forex pip, margin, and P&L calculations.
- Establishes a clean, scalable monorepo ready for CI/CD automation.

### Negative Consequences / Trade-offs:
- Stock market analysis and multi-agent equity debate graphs will not be present in the v1.0 release (noted as potential future work in SRS §13).

---

## 6. Traceability

- **Satisfies:** CON-5 (16-week timeline), CON-7 (TypeScript strict mode), DI-5 (Fixed-precision Decimal), §10.3 (Acceptance Criteria).
- **Supersedes:** Any informal stock-terminal scoping assumptions.
- **Guides:** Phase 1 through Phase 10 implementation plans.
