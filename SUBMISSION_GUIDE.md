# TRADLY (Tradex) — Final Prototype Submission Guide

> **Live app:** https://tradex-main.vercel.app  ·  **API:** https://tradex-api-q7re.onrender.com (docs at `/docs`, status at `/health`)
> **Login:** `princepatel01258@gmail.com` / `Prince_1258`  ·  **Invite code for registering new users:** `TRADLY_PRINCE_2026`
> Open the site ~2 minutes before presenting so the free-tier API is awake.

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
- Data: **real market history** from Yahoo Finance (mid prices). D1 goes back to 2011, H1/H4 about 2 years, M30 about 60 days. Up to 3,000 most recent closed bars per run.

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
| Backtest EUR/USD H4, EMA 9/21, 1,500 real bars (Nov 2025 – Oct 2026) | 58 trades · win 32.8% · PF 0.95 · Sharpe −0.11 · max DD 16.6% · −1.73% · ~80 ms (21 Oct 2026) |
| Multi-agent run (EUR/USD H1) | 4 agents on live data, ~3–8 s including Groq phrasing |
| Alert crossing → in-app notification (no browser open) | fires within seconds of the live price crossing |

Backtested performance does not predict future results. A losing EMA run on real data is expected — it shows the engine is not curve-fitted to a synthetic series.

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

## 5. Live data sources (no simulated prices anywhere in production)
| Feature | Source |
|---|---|
| Live quotes, all 15 pairs (refreshed every 5 s) | Yahoo Finance FX (Twelve Data fallback) |
| Candles M1–D1 (H4 built from real H1) | Yahoo Finance FX (Twelve Data fallback) |
| Backtest history | Yahoo Finance FX, real closed bars |
| Strategy / Confluence Engine datasets | Real candles for 10 pairs (1W–15M) |
| News + currency sentiment | FXStreet RSS, Finnhub news, Google News RSS (lexicon scoring) |
| Economic calendar | ForexFactory weekly calendar (bundled snapshot of the same week if rate-limited) |
| AI assistant answers | Groq LLM grounded on the retrieved live headlines, with citations |

Check live status any time: `https://tradex-api-q7re.onrender.com/health` → `market_data.mode = "live"`.

## 6. Honest limitations (say these if asked)
- Bid/ask are the real mid price ± each pair's typical retail spread (Yahoo provides mid quotes, not a broker order book).
- Sentiment is lexicon-based scoring of live headlines, not a fine-tuned FinBERT model.
- Runs, alerts and paper-trading state are in memory (Neon DB is used for login); restarting the API clears them.
- The API is on Render's free tier: after 15 idle minutes it sleeps and the first request takes ~1 minute. A keep-alive pings it 08:30–13:30 IST.
- Unit tests run offline (`LIVE_MARKET_DATA=false`), so the suite is deterministic and needs no network.

## 7. New API endpoints
| Method | Path |
|---|---|
| GET | `/api/v1/backtest/strategies` |
| POST | `/api/v1/backtest/run` |
| GET | `/api/v1/backtest/runs`, `/api/v1/backtest/runs/{run_id}` |
| POST | `/api/v1/agents/analyse` |
| GET | `/api/v1/agents/runs` |
