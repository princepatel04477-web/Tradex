# TRADLY (Tradex) — Final Prototype Submission Guide

**Student:** Prince Jivani · **Enrollment:** 23SE02CS030 · **Host:** ThinkNovus Private Limited
**Scope completed in this pass:** Month 3 + Month 4 roadmap items from the Month 2 progress report (§6).

---

## 1. What was added to finish the roadmap

| Roadmap item (Month 2 report §6) | Status | Where |
|---|---|---|
| Month 3 — Historical backtesting engine with Sharpe, max drawdown, win rate | ✅ Done | `apps/api/app/domain/backtest.py`, `apps/api/app/providers/historical.py`, `apps/api/app/services/backtest_service.py`, page `/backtest` |
| Month 4 — Multi-agent system (Technical, Macro/Fundamental, Risk Manager + Synthesis) | ✅ Done (replaces the old hard-coded agent text) | `apps/api/app/services/agent_service.py`, `apps/web/src/components/agents/AgentSquadPanel.tsx`, page `/trading-analysis` |
| Alerts (FG-6) — UI + server-side evaluation with crossing semantics | ✅ Done | `apps/api/app/services/alert_service.py`, page `/alerts` |
| Responsible AI (AI-4.2) — no entry prices / lot sizes / buy-sell instructions | ✅ Done | `apps/api/app/domain/ai_safety.py` (output filter + RAG refusal) |
| Bug fix — seed candles all had the same timestamp | ✅ Fixed | `apps/api/app/services/market_service.py` |
| Bug fix — alert/auth calls never sent the login token | ✅ Fixed | `apps/web/src/services/api.ts` |

### Backtesting engine (Month 3)
- Strategies: **EMA crossover**, **RSI mean-reversion**, **MACD momentum** (parameters editable in the UI).
- Signal on bar close → fill on **next bar open** (no look-ahead). Buys fill at **ask**, sells at **bid** using each pair's spread.
- ATR-sized stop-loss / take-profit, risk-% position sizing, conservative "stop first" intrabar rule.
- Outputs: net profit, return %, win rate, profit factor, expectancy, avg R, **Sharpe (annualised)**, **max drawdown**, exposure, equity curve with drawdown shading, full trade ledger, exit breakdown.
- Data: deterministic, seeded historical dataset (reproducible for grading); D1 bars open at 17:00 New York with DST handled by timezone; bars respect the FX trading week. Up to 3,000 bars (D1 ≈ 5.8 years).

### Multi-agent analysis (Month 4)
- **Technical Analyst** — indicators + composite bias, top-down H1/H4/D1 alignment.
- **Macro Researcher** — grounded RAG citations (central-bank documents) + currency sentiment; returns *insufficient context* rather than guessing.
- **Risk Manager** — ATR vs spread, account margin, open exposure, high-impact calendar events.
- **Synthesis Lead** — accepts only claims that cite evidence the agent actually retrieved; discards the rest (shown in UI). Probabilistic verdict + confidence; optional Groq LLM phrasing passes an advice filter, otherwise the deterministic narrative is used.
- Agents run in parallel; one failing agent degrades only its own panel.

---

## 2. Measured results (from real runs, 28 Sep 2026)

| Check | Result |
|---|---|
| Backend test suite (`pytest`, `apps/api`) | **267 passed**, 0 failed (was 232 before this pass; +35 new tests) |
| TypeScript (`tsc --noEmit`, `apps/web`) | 0 errors |
| Production build (`next build`, `apps/web`) | ✅ 14 routes incl. `/backtest`, `/alerts` |
| Backtest EUR/USD H4, EMA 9/21, 1,500 bars | 53 trades · win 39.6% · PF 1.40 · Sharpe 1.26 · max DD 6.82% · +11.62% · ~15–40 ms |
| Multi-agent run (EUR/USD H1) | 4 agents, ~8–15 ms deterministic path |
| Alert crossing → in-app notification (no browser open) | fired within seconds on the live simulated feed |

Simulated / backtested performance does not predict future results.

---

## 3. Run it locally

```bash
# API
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000        # docs at http://localhost:8000/docs

# Web
cd apps/web
npm install
npm run dev                                       # http://localhost:3000
```
Login (seeded admin): `princepatel01258@gmail.com` / `Prince_1258`
Run tests: `cd apps/api && pytest -q`

## 4. Demo script for the viva (≈5 minutes)
1. **Command Center** — live ticks, sessions, account.
2. **Analysis Workspace** → *Deploy AI Analysis Squad* → show verdict card, then Technical / Macro / Risk / Synthesis tabs and evidence chips.
3. **Backtest Lab** → *Run backtest* (EUR/USD H4 EMA) → equity curve + drawdown, ledger; switch to RSI or D1 and rerun.
4. **Alerts** → pick EUR/USD → *+3 pips* → *Create alert* → notification appears when price crosses.
5. **AI Macro Assistant** → ask "Should I buy EUR/USD?" → it refuses to give a trade instruction (AI-4.2).
6. **Paper Trading** → place and close a trade → **Performance & Journal**.

## 5. Honest limitations (say these if asked)
- Historical data is a seeded synthetic dataset, not broker history; the engine only consumes `List[Bar]`, so an OANDA/Twelve Data adapter can replace it.
- The RAG corpus is a small curated set of central-bank documents; no live vector DB ingestion in this build.
- Runs, alerts and paper-trading state are in memory (Neon DB used for auth when reachable); restarting the API clears them.
- LLM phrasing needs a valid `GROQ_API_KEY`; without it the deterministic narrative is shown.

## 6. New API endpoints
| Method | Path |
|---|---|
| GET | `/api/v1/backtest/strategies` |
| POST | `/api/v1/backtest/run` |
| GET | `/api/v1/backtest/runs`, `/api/v1/backtest/runs/{run_id}` |
| POST | `/api/v1/agents/analyse` |
| GET | `/api/v1/agents/runs` |
