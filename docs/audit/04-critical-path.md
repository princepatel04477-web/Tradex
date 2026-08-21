# 04 — Critical Path to Phase 1 Execution

**Date:** 2026-08-21  
**Project:** Tradly — AI/ML-Powered Forex Market Intelligence & Algorithmic Trading Platform  
**Document Version:** 1.0 (Phase 0 Baseline)  
**Author:** 11-Agent Swarm  
**Source of Truth:** `TRADLY_SRS v1.0` (IEEE Std 830-1998)

---

## 1. Overview & Pre-Conditions

Phase 0 (Reconnaissance & Gap Audit) establishes the baseline evidence and resolves the product scope. Before **Phase 1 (Foundation, Contracts, CI/CD)** can begin, the following pre-conditions must be satisfied in order:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          PHASE 0 → PHASE 1 CRITICAL PATH                        │
│                                                                                 │
│  [1. Scope Approval] ──► [2. Legacy Isolation] ──► [3. Monorepo Target Layout] │
│                                                              │                  │
│  [6. Contract Pipe]  ◄── [5. Env & Secret Clean] ◄── [4. Runtime Baseline]     │
│         │                                                                       │
│         ▼                                                                       │
│  READY FOR PHASE 1 FOUNDATION & FASTAPI SHELL                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Ordered Critical Path Pre-Conditions

### Step 1: Formal Scope Reconciliation (ADR-0001 Adopted)
- **Condition:** ADR-0001 (Scope Reconciliation) is approved and committed to `docs/adr/0001-scope-reconciliation.md`.
- **Status:** **SATISFIED** (Delivered in Phase 0).

### Step 2: Legacy Stock Framework Isolation
- **Condition:** The legacy stock modules (`tradingagents/`, `cli/`, root `main.py`) are decoupled from the build and test paths so that `pytest` and `npm test` execute cleanly against active Forex code.
- **Action for P1:** Restructure repository root to exclude `tradingagents` from standard packaging; clean up `pyproject.toml`.

### Step 3: Monorepo Target Directory Restructuring
- **Condition:** Repository layout conforms to §2 Target Architecture:
  - `apps/web/`: Next.js 14 App Router application.
  - `apps/api/`: FastAPI async backend application.
  - `infra/`: Migrations, Docker, and CI definitions.
  - `docs/`: ADRs, API references, runbooks, and domain math documentation.
- **Action for P1:** Move `frontend/` into `apps/web/` and `backend/` into `apps/api/`.

### Step 4: Python & Node.js Runtime Baseline Verification
- **Condition:**
  - Python 3.11+ environment with `fastapi`, `uvicorn`, `pydantic>=2.6`, `decimal`, `pytest`.
  - Node.js 20 LTS with TypeScript 5.x configured in strict mode (`"strict": true`, zero `any`).
- **Action for P1:** Update `apps/api/pyproject.toml` and lock dependencies.

### Step 5: Environment Variable & Secret Sanitization
- **Condition:**
  - All hardcoded secrets (specifically `SECRET_KEY` in `auth_service.py:8`) removed from source code.
  - Standardized `.env.example` created in `apps/api/` containing all required provider and service keys (`OANDA_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`, `REDIS_URL`, `DATABASE_URL`).
  - Frontend `NEXT_PUBLIC_API_BASE` configured to dynamically point to the API gateway rather than hardcoded `localhost:8000`.

### Step 6: OpenAPI-to-TypeScript Contract Generation Pipeline Readiness
- **Condition:**
  - Standardized `{ data, error, meta }` response envelope model designed in FastAPI.
  - Codegen tooling (`openapi-typescript` or `orval`) specified to emit typed contracts into `apps/web/types/generated/`.
- **Action for P1:** Implement envelope middleware and codegen script.

---

## 3. Phase 1 Entry Checklist

| Item # | Verification Check | Responsible Role | Pass Criterion |
|---|---|---|---|
| 1 | Scope defined as pure Forex per SRS v1.0 | Mission Planner | ADR-0001 signed off |
| 2 | Target monorepo structure mapped | Architect | Directory layout matches §2 |
| 3 | In-memory secrets eradicated | Security Analyst | Grep search for hardcoded secrets returns 0 |
| 4 | Monorepo build targets isolated | Repository Analyst | Frontend and API build independently |
| 5 | Error envelope model defined | Backend Engineer | Model `{data: T, error: E, meta: M}` ready |
| 6 | Quality Gates G1–G11 acknowledged | QA Inspector | Test harness ready for P1 verification |
