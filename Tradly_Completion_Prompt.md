# TRADLY — PROJECT COMPLETION MISSION

> Paste this entire file as the opening message in Claude Code, Cursor (Agent mode) or Antigravity, from the repository root. Attach `TRADLY_SRS.md` and the UI/UX Architecture v2 spec if the agent cannot already see them.

---

## 0. Mission

You are completing **Tradly**, an AI/ML-powered Forex market intelligence and paper-trading platform, so that it fully satisfies **Software Requirements Specification v1.0** (IEEE 830) and every claim made in the internship progress reports (Reporting 2, 3 and 4).

Those reports describe the finished system. **Your job is to make the repository match them, then measure it, so every number in the reports is replaced by a real one.** Where the code and the reports disagree, the code is changed — never the evidence.

**Definition of done:** all SRS "Must" requirements implemented and tested; every NFR-P target measured under load; RLS proven by adversarial test; zero high-severity vulnerabilities; four critical journeys (UC-1 to UC-4) pass end-to-end in a browser; deployed at a stable public URL; `EVIDENCE.md` populated with measured results.

---

## 1. Agent Swarm

Operate as the following roster. Name the active agent at the start of each work block. Every phase ends with a sign-off from **QA Inspector** and **Final Reviewer**.

| # | Agent | Owns |
|---|---|---|
| 1 | **Mission Planner** | Phase sequencing, contracts, readiness reviews, scope control |
| 2 | **Architect** | Layering, service boundaries, interfaces, migration design |
| 3 | **Forex Domain Expert** | Pips, lots, spreads, sessions, margin, fills — vetoes any domain violation |
| 4 | **Backend Engineer** | FastAPI services, Celery/Redis workers, adapters |
| 5 | **Frontend Engineer** | Next.js 14 App Router, TypeScript strict, UI/UX v2 spec compliance |
| 6 | **AI/ML Engineer** | RAG, FinBERT, agent orchestration, prompt safety |
| 7 | **Data Engineer** | Supabase schema, migrations, pgvector, retention |
| 8 | **Security Analyst** | Auth, RLS, cookies, rate limits, headers, dependency scan |
| 9 | **Performance Engineer** | Profiling, load tests, NFR-P verification |
| 10 | **QA Inspector** | Tests at every level, quality gates, regression |
| 11 | **Final Reviewer** | Phase acceptance, evidence integrity, report reconciliation |

---

## 2. Non-Negotiable Laws

Violating any of these fails the phase regardless of anything else.

### 2.1 Forex domain
1. **Money and prices are `Decimal` end to end.** Python `decimal.Decimal`, Postgres `numeric`, and a decimal library on the client. No `float` in any money path — including JSON serialisation (send strings).
2. **Pip size is per pair.** JPY pairs `0.01`, all others `0.0001`, read from the pair registry — never hardcoded at a call site.
3. **D1 candles close at 17:00 America/New_York**, not midnight UTC, with DST handled by timezone, not by a fixed offset.
4. **Fills use bid/ask, never mid.** Buys fill at ask, sells at bid, in live paper trading *and* backtests.
5. **Equity is derived, never stored.** `equity = balance + Σ floating P&L`, computed on read.
6. **Alerts fire on crossing, not on state.** Store the previous evaluation per alert; dispatch only on transition.
7. **Trailing stops only tighten.** A reversal never loosens a stop.
8. **No look-ahead.** Any backtest indicator may read only bars closed at or before the decision point.

### 2.2 Security
1. Sessions in **httpOnly, Secure, SameSite=Lax cookies**. No token in `localStorage`/`sessionStorage`.
2. **RLS enabled on every user-scoped table**, with policies proven by an adversarial cross-account test.
3. Server-side Pydantic validation on every endpoint; rate limits per SRS NFR-S5; security headers per NFR-S7.
4. No secrets in the repo. No real broker credentials or payment data, ever (NFR-S9).

### 2.3 AI safety
1. RAG answers only from retrieved context. Below the relevance threshold, **refuse** — do not generate.
2. No output may contain an entry price, position size, or buy/sell instruction (AI-4.2). Enforce in prompt *and* with an output filter *and* with adversarial tests.
3. Every AI surface shows model attribution and the non-dismissible "informational only · not financial advice" notice.

### 2.4 Architecture
1. **Pure domain layer**: `lib/risk`, pip maths, margin, indicators and bias scoring are side-effect-free functions with no I/O.
2. **Existing core services are extend-only**: Worker Manager, Market Data Service, Notification Service, Signal Pipeline. Extend through their interfaces; never rewrite or change their contracts.
3. External providers sit behind adapters (market feed, LLM, news, email) so each is swappable.

### 2.5 Code standards
- TypeScript `strict: true`. **No `any`** — use `unknown` with narrowing, generics, or explicit types.
- **No `console.log`** in production code. Use the structured logger.
- No stubs, `TODO` placeholders, mock data in production paths, or commented-out code. Every file you touch is complete and working.
- Every public Python function is typed and documented; every exported TS function is typed.
- Lint clean: `ruff`, `eslint`, `tsc --noEmit`.

---

## 3. Phase Contract Format

Every phase is delivered in exactly this structure. Do not begin the next phase until the readiness review passes.

```
PHASE N — <name>
MUST NOT CHANGE:   <files, contracts and behaviours frozen for this phase>
EXTENDS:           <what is added, and through which interfaces>
DELIVERABLES:      <files and features>
TESTS:             <what proves it>
QUALITY GATE:      <commands that must all pass>
READINESS REVIEW:  <QA Inspector + Final Reviewer sign-off, open risks>
```

**Standard quality gate** (run at the end of every phase from Phase 1):
```bash
ruff check backend && pytest backend -q
cd frontend && npx tsc --noEmit && npx eslint . --max-warnings 0 && npm run build
grep -rn "console\.log" frontend/src && exit 1 || true
grep -rn ": any\b\|as any\b\|<any>" frontend/src && exit 1 || true
```

---

## 4. Phases

### PHASE 0 — Read-Only Audit and Reconciliation ⛔ STOP AFTER THIS PHASE

**Change nothing.** The live deployment has been observed presenting as a stock-analysis / multi-agent report terminal, while the SRS specifies a Forex intelligence and paper-trading platform. This must be resolved before any code is written.

1. Map the repository: frameworks, routes, services, schema, tests, deployment config.
2. Build a **gap matrix** in `AUDIT.md` with one row per SRS requirement (FR-1.1 … FR-6.11, AI-*, NFR-*, UI-*):
   `Requirement | Status (Done / Partial / Missing / Divergent) | Evidence (file:line) | Work needed`
3. Add one row per concrete claim in Reporting 2, 3 and 4 (endpoints, tables, tests, metrics, features) with the same columns.
4. List every existing module that does **not** belong to the Forex SRS (e.g. equity/NSE analysis) and propose: remove, isolate behind a flag, or keep as a separate route.
5. Record every violation of Section 2 you find.
6. Note one known inconsistency: the SRS sets the RAG relevance threshold at **0.72**; Reporting 2 states **0.65**. Recommend one value; it will live in configuration.
7. Produce a phase plan with estimated effort per phase.

**Then stop and wait for explicit approval.** Do not proceed on your own.

---

### PHASE 1 — Foundations: Data, Domain Core, Persistence

- Pair registry (15 pairs from SRS Appendix A) with `pip_decimal_places`, category, active flag — configuration-driven (NFR-X3).
- Pure domain module: `pipValue`, `positionUnits`, `requiredMargin`, `marginLevel`, `floatingPnl`, `riskReward` — all Decimal.
- Market feed adapter for OANDA v20 streaming, exponential-backoff reconnect, fallback to REST polling every 5 s, staleness flag (FR-1.8, NFR-R2).
- Candle aggregator M1–D1 with the 17:00 NY D1 boundary; OHLC integrity check (DI-1); idempotent upsert on `(pair_id, timeframe, open_time)` (DI-2).
- Redis latest-tick cache, TTL 60 s.
- Supabase migrations for every table in SRS §5.2 plus `alerts`, `backtest_runs`, `backtest_trades`, `chart_drawings`, `agent_runs`, `agent_outputs`. RLS on all user-scoped tables. Retention jobs per SRS §5.3.
- Auth: Supabase Auth, email/password + Google OAuth, httpOnly cookie session, JWT claims propagated to the DB session.

**Tests:** SRS TC-1 (USD/JPY pip value at 0.1 lot), TC-4 (cross-account read denied), TC-6 (stream drop → degraded → reconnect, no candle loss), TC-7 (`high < low` rejected), D1 boundary across a DST change.

---

### PHASE 2 — Technical Analysis and Composite Bias

- Indicators: RSI-14, MACD 12/26/9, BB 20/2, ATR-14, EMA 9/21/50, SMA-200, Fibonacci — computed on candle close, not on tick (FR-2.12, < 2 s).
- Signal flags: MACD cross, RSI 70/30, BB squeeze, each carrying the timestamp of the bar that produced it.
- Composite bias per SRS §6.3 with **weights in configuration** (AI-3.3) and per-indicator contributions returned with every label (FR-2.11, AI-3.1).
- Indicator snapshot channel published over WebSocket.

**Tests:** each indicator against a hand-computed fixture; bias label boundaries at ±0.2 and ±0.6; recompute latency.

---

### PHASE 3 — Paper Trading Engine

- Account with configurable starting balance (default 10,000); reset archives history (FR-4.13).
- Market, limit and stop orders; long and short; lots 1.0 / 0.1 / 0.01; leverage 1:1, 1:10, 1:30, 1:50, 1:100.
- Bid/ask fills with live spread; SL, TP and trailing stop; order lifecycle `draft → validating → submitting → filled | rejected | pending`.
- Margin monitoring: warning below 100 %, auto-liquidation below 50 %, liquidation report shown to the user (FR-4.12).
- One account recalculation per tick after all positions update — never incremental mutation.

**Tests:** SRS TC-2 (margin rejection states exact shortfall), TC-3 (liquidation below 50 %, consistent state), TC-9 (trailing stop tightens then triggers), equity-derivation identity after multi-position updates.

---

### PHASE 4 — AI Intelligence

- RAG ingestion every 30 min in market hours: dedupe (SHA-256), 800-token chunks / 100 overlap, `text-embedding-3-small`, HNSW index.
- Retrieval: top-20 → cross-encoder rerank → top-5, recency decay (72 h half-life), threshold from config; refusal state when unmet.
- Generation via LLM adapter (Groq primary, fallback model, graceful degradation); citations by index; query/chunk/response audit log (AI-1.4).
- FinBERT sentiment per currency, hourly aggregate −1.0…+1.0, headlines with no identifiable currency excluded (AI-2.2).
- Economic calendar with AI pre-event briefings.

**Tests:** SRS TC-5 (no relevant corpus → refusal, no fabrication); TC-10 (FinBERT ≥ 80 % agreement on a 200-headline labelled set — build the set and commit it); adversarial prompts requesting entry prices or position sizes are refused.

---

### PHASE 5 — Alerts, Backtesting, Analytics, Charting

- Alerts: price, RSI, MACD, BB; crossing semantics; in-app (guaranteed) + email (queued, retried); max 50 active per user (FR-6.11).
- Backtesting: deterministic bar-by-bar loop reusing Phase 2 indicator functions **unchanged**; bid/ask fills with historical spread; async run with polling; Sharpe, max drawdown, win rate, profit factor; per-trade ledger.
- Analytics: equity curve with drawdown shading, win rate, avg win/loss, profit factor, avg R:R, breakdown by pair and session; journal notes and tags; CSV export.
- Charting: canvas chart with trendline and horizontal-level drawing tools persisted per user and pair; overlay cap of 5 with the sixth disabled and explained.

**Tests:** alert fires once while price holds beyond threshold; look-ahead guard fails loudly if violated; backtest fills match hand-computed ledger on a reduced range.

---

### PHASE 6 — Multi-Agent Analysis System

- LangGraph orchestrator with four agents: **Technical** (reads Analysis Service), **Macro** (reads RAG pipeline, same threshold), **Risk** (reads Trading Service), **Synthesis**.
- Typed input and output per agent: `reasoning`, `confidence` (Decimal 0–1), `cited_chunk_ids`.
- Synthesis **discards any claim without evidence**. Agents run in parallel; per-agent progress streams to the client; one agent failing degrades that panel only (NFR-R3).
- Model provenance stored per run (AI-4.4). Probabilistic framing only (AI-4.3).
- UI: "Analyse" action per pair, verdict card first, agent evidence as tabs, citation chips, disclaimer.

**Tests:** uncited claim is dropped; recommendation-seeking prompts refused; single-agent failure leaves others rendered.

---

### PHASE 7 — Hardening, Performance, Deployment, Documentation

**Security:** rate limiting, CSP / `X-Frame-Options: DENY` / HSTS, dependency scan blocking merge on high severity, account data export and account deletion with cascade test (NFR-L4).

**Performance** — Locust, 100-user sustained test plus a 200-WebSocket-client run. Measure and record every NFR-P target:

| ID | Target |
|---|---|
| NFR-P1 | Tick → browser render < 500 ms p95 |
| NFR-P2 | LCP < 2.5 s on 4G |
| NFR-P3 | Indicator recompute < 2 s |
| NFR-P4 | RAG end-to-end < 5 s p95 |
| NFR-P5 | Order ack < 300 ms |
| NFR-P6 | 1 year D1 fetch < 1 s |
| NFR-P7 | ≥ 200 concurrent WebSocket clients |
| NFR-P8 | DB query < 100 ms p95 |

Profile before optimising. In particular, serialise each broadcast payload once per tick, not once per client.

**Frontend (UI/UX v2 spec):** direction encoded by colour **and** glyph **and** sign; near-black ink on saturated fills; tabular numerals with per-pair precision; nine-state matrix per data panel (skeleton, stale, degraded, market-closed, empty, error, rate-limited…); keyboard model with no single-key order submission; responsive 360–2560 px; `prefers-reduced-motion`; axe scan clean on every route.

**Deployment:** frontend on Vercel; backend in Docker; structured JSON logs with correlation IDs; health endpoints; uptime and error-rate alerts; smoke tests after deploy with automatic rollback.

**E2E:** Playwright for UC-1 (analyse a pair), UC-2 (AI query), UC-3 (place and manage a trade), UC-4 (configure and receive an alert).

**Documentation:** README, user manual, API reference from OpenAPI, architecture decision records.

---

### PHASE 8 — Evidence Pack and Report Reconciliation

Create `EVIDENCE.md` containing, from real runs only:

1. Full `pytest` output with counts, and coverage (target ≥ 70 %).
2. `npm run build` route table.
3. Every NFR-P measurement with the command that produced it.
4. The RLS adversarial test output.
5. The FinBERT agreement score on the labelled set.
6. One real backtest summary (strategy, pair, period, trades, win rate, profit factor, Sharpe, max drawdown, runtime).
7. Test counts per area: Functional, Integration, System, Performance, UAT — conducted / passed / failed.
8. Every bug found in Phases 5–7 with severity and resolution.
9. A **reconciliation table**: each number stated in Reporting 2, 3 and 4 beside the measured value, marked *Match* or *Replace with measured*.
10. Screenshot checklist: Command Center, Paper Trading Hub, Backtest Results, Alert Management, Chart with Drawing Tools, Multi-Agent Panel, Load Test Dashboard, Production Monitoring.

If any measured value misses its target, **report it as missed** and list it as a finding. Do not tune the measurement to pass.

---

## 5. Working Rules

- Begin with Phase 0 and stop for approval. After that, proceed phase by phase, stopping at each readiness review.
- Before editing a file, read it. Before changing an interface, find its callers.
- Prefer small, reviewable commits with conventional messages (`feat(trading): ...`).
- When a requirement is ambiguous, state the assumption in the phase notes and continue — ask only when the choice changes the data model or a security boundary.
- If you find a Section 2 violation in existing code, fix it in the phase that owns that area and record it.

**Start now with Phase 0.**
