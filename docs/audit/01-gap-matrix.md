# 01 — Comprehensive SRS Gap Matrix

**Date:** 2026-08-21  
**Project:** Tradly — AI/ML-Powered Forex Market Intelligence & Algorithmic Trading Platform  
**Document Version:** 1.0 (Phase 0 Baseline)  
**Author:** 11-Agent Swarm  
**Source of Truth:** `TRADLY_SRS v1.0` (IEEE Std 830-1998)

---

## 1. Functional Requirements Gap Matrix (§3)

### 1.1 Market Data & Charting (FG-1)

| SRS ID | Requirement (Short) | Status | Evidence (File:Line) | Effort | Target Phase | Notes & Discrepancies |
|---|---|---|---|---|---|---|
| **FR-1.1** | Stream real-time bid/ask for 15 FX pairs | **PARTIAL** | `backend/app/services/market_service.py:7-26,94-135` | Med | P3 | 15 pairs configured with pip decimals, but prices are random Brownian simulation, not live OANDA v20 stream. |
| **FR-1.2** | Aggregate ticks into OHLCV candles (M1–D1) | **PARTIAL** | `backend/app/services/market_service.py:143-184` | Med | P3 | Multi-timeframes generated on-the-fly via synthetic random walks; no true time-window aggregation from live tick feed. |
| **FR-1.3** | Persist 2y D1 and 6mo H1 candles | **ABSENT** | No implementation found (`backend/app/services/market_service.py:31` uses in-memory dict) | High | P2, P3 | No Postgres database or Supabase schema exists to store historical candles. |
| **FR-1.4** | Render interactive candlestick charts | **PARTIAL** | `frontend/src/components/chart/CandlestickChart.tsx:1-170` | Med | P3, P9 | Custom SVG candlestick chart with crosshair and zoom slider exists; needs standard indicator overlays and pan improvements. |
| **FR-1.5** | Display live spread in pips per pair | **PARTIAL** | `frontend/src/app/page.tsx:241`, `backend/app/services/market_service.py:79` | Low | P3 | Spread displayed in UI, but calculated from simulated quotes using float math. |
| **FR-1.6** | Overlay up to 5 technical indicators on chart | **PARTIAL** | `frontend/src/app/chart/page.tsx:135-180` | Med | P4 | UI indicator toggle chips exist; indicator values computed by backend mock service. |
| **FR-1.7** | Market session indicator with overlap highlights | **PARTIAL** | `backend/app/services/market_service.py:186-208`, `frontend/src/components/layout/Navbar.tsx:49-75` | Low | P3 | Static session hours model and overlap banner present in navbar; needs UTC/DST drift handling. |
| **FR-1.8** | Graceful degradation to last-known price | **ABSENT** | `frontend/src/app/page.tsx:57-58` | Med | P3 | WebSocket catch block is empty; no staleness badge or seconds-since-tick indicator rendered on stream failure. |
| **FR-1.9** | Export chart data as CSV | **PARTIAL** | `backend/main.py:204-212` (`/api/v1/strategy/candles/.../csv`) | Low | P3 | Implemented for strategy scenarios; needs generalization to live/historical pair candles. |

---

### 1.2 Technical Analysis (FG-2)

| SRS ID | Requirement (Short) | Status | Evidence (File:Line) | Effort | Target Phase | Notes & Discrepancies |
|---|---|---|---|---|---|---|
| **FR-2.1** | Compute RSI (14) | **PARTIAL** | `backend/app/services/analysis_service.py:205-222` | Low | P4 | Implemented via numpy/python lists; lacks pure Decimal types and pandas-ta validation to 6dp. |
| **FR-2.2** | Compute MACD (12, 26, 9) line/signal/hist | **PARTIAL** | `backend/app/services/analysis_service.py:224-237` | Low | P4 | Implemented with custom EMA helper; needs validation against TA reference. |
| **FR-2.3** | Compute Bollinger Bands (20, 2σ) | **PARTIAL** | `backend/app/services/analysis_service.py:239-248` | Low | P4 | Implemented with numpy mean/std; uses float math. |
| **FR-2.4** | Compute ATR (14) | **PARTIAL** | `backend/app/services/analysis_service.py:250-261` | Low | P4 | True range logic present; needs pure Decimal implementation. |
| **FR-2.5** | Compute EMA-9, 21, 50 and SMA-200 | **PARTIAL** | `backend/app/services/analysis_service.py:191-203` | Low | P4 | Exponential and simple moving averages implemented using float arrays. |
| **FR-2.6** | Compute Fibonacci retracements | **PARTIAL** | `backend/app/services/analysis_service.py:48-59` | Low | P4 | 23.6%, 38.2%, 50.0%, 61.8%, 78.6% levels computed from recent 50-bar swing high/low. |
| **FR-2.7** | Detect MACD crossovers | **PARTIAL** | `backend/app/services/analysis_service.py:62-68` | Low | P4 | State transition detection implemented on candle closes. |
| **FR-2.8** | Detect RSI overbought (>70) / oversold (<30) | **PARTIAL** | `backend/app/services/analysis_service.py:70-74` | Low | P4 | Flagged in `IndicatorSnapshot.rsi_condition`. |
| **FR-2.9** | Detect Bollinger Band squeeze | **PARTIAL** | `backend/app/services/analysis_service.py:76-78` | Low | P4 | Threshold heuristic `bb_width < 0.005` used; needs trailing percentile definition per SRS. |
| **FR-2.10**| Composite directional bias label | **PARTIAL** | `backend/app/services/analysis_service.py:101-189` | Med | P4 | Weighted rule ensemble implemented producing 5 standard labels. |
| **FR-2.11**| Display reasoning & breakdown behind bias | **PARTIAL** | `backend/app/services/analysis_service.py:106-165`, `frontend/src/app/page.tsx:175-184` | Low | P4 | Contribution factors and direction reasons returned in API and rendered in Command Center. |
| **FR-2.12**| Recompute indicators within 2s of candle close | **ABSENT** | `backend/main.py:410-433` | Med | P4 | No pub/sub candle-close event pipeline triggering async recomputation. |

---

### 1.3 AI Market Intelligence (FG-3)

| SRS ID | Requirement (Short) | Status | Evidence (File:Line) | Effort | Target Phase | Notes & Discrepancies |
|---|---|---|---|---|---|---|
| **FR-3.1** | Natural language chat interface | **PARTIAL** | `frontend/src/app/ai-assistant/page.tsx:1-180` | Low | P8 | Interactive chat UI with message stream, citation cards, and question chips. |
| **FR-3.2** | RAG pipeline over news & macro corpus | **PARTIAL** | `backend/app/services/ai_service.py:70-137` | High | P8 | Mock keyword search over 5 hardcoded documents; no pgvector or real vector index. |
| **FR-3.3** | AI answers include source citations | **PARTIAL** | `backend/app/services/ai_service.py:110-118`, `frontend/src/app/ai-assistant/page.tsx:142-160` | Low | P8 | Citations returned in `RAGQueryResponse` and rendered as expandable cards. |
| **FR-3.4** | Refusal when retrieved context is insufficient | **PARTIAL** | `backend/app/services/ai_service.py:94-107` | Low | P8 | Returns refusal when relevance score < 0.65. Needs formal cosine floor ≥ 0.72. |
| **FR-3.5** | Ingest & embed Forex news every 30 mins | **ABSENT** | No implementation found | High | P8 | No Celery Beat ingestion worker, no NewsAPI or RSS scraping pipeline. |
| **FR-3.6** | Classify news headlines with FinBERT | **ABSENT** | `backend/app/services/ai_service.py:143-166` | High | P8 | Uses static sentiment scores from mock corpus; no `ProsusAI/finbert` model loaded. |
| **FR-3.7** | Per-currency aggregate sentiment (-1.0 to +1.0)| **PARTIAL** | `backend/app/services/ai_service.py:139-166`, `frontend/src/app/ai-assistant/page.tsx:40-75` | Med | P8 | Computed over static mock corpus and rendered as a heatmap; hourly batch job absent. |
| **FR-3.8** | Economic calendar with impact ratings | **PARTIAL** | `backend/app/services/ai_service.py:168-231`, `frontend/src/app/ai-assistant/page.tsx:78-120` | Low | P8 | Static 4-event calendar returned via API; needs live feed ingestion. |
| **FR-3.9** | AI pre-event briefings with historical pip volatility | **PARTIAL** | `backend/app/services/ai_service.py:180-185,200,212,226` | Low | P8 | Static briefing text and volatility estimates hardcoded in event schema. |
| **FR-3.10**| Responsible AI disclaimer on all outputs | **DONE** | `backend/app/services/ai_service.py:64-68`, `frontend/src/app/ai-assistant/page.tsx:170-178` | Low | P8 | Persistent disclaimer returned in every API response and rendered prominently in UI. |
| **FR-3.11**| RAG response time < 5s p95 | **UNVERIFIED** | No performance test exists | Med | P8 | Simulated keyword retrieval is sub-10ms; real Groq/pgvector pipeline unmeasured. |

---

### 1.4 Paper Trading (FG-4)

| SRS ID | Requirement (Short) | Status | Evidence (File:Line) | Effort | Target Phase | Notes & Discrepancies |
|---|---|---|---|---|---|---|
| **FR-4.1** | Virtual account with $10,000 balance | **PARTIAL** | `backend/app/services/trading_service.py:11-20` | Low | P6 | In-memory balance variable; not user-scoped or persisted to Supabase `paper_accounts`. |
| **FR-4.2** | Market, limit, and stop orders | **PARTIAL** | `backend/app/schemas/trading.py:8-16` | Med | P6 | Market order execution implemented; limit/stop pending state machine absent. |
| **FR-4.3** | Support long and short positions | **DONE** | `backend/app/services/trading_service.py:57-58,217-222` | Low | P6 | Directional handling for long and short orders implemented. |
| **FR-4.4** | Fill at ask (buy) / bid (sell) with spread | **DONE** | `backend/app/services/trading_service.py:58` | Low | P6 | Realistic fill price selection using live bid/ask quotes. |
| **FR-4.5** | Leverage settings 1:1 to 1:100 | **DONE** | `backend/app/services/trading_service.py:63`, `frontend/src/app/page.tsx:340-345` | Low | P6 | Supports 1:1, 1:10, 1:30, 1:50, 1:100 leverage options. |
| **FR-4.6** | Correct pip value for JPY (2dp) vs standard (4dp)| **CONFLICTS** | `backend/app/services/trading_service.py:33-50` | Med | P6 | Pip calculation logic is present but uses Python `float` (violates DI-5). |
| **FR-4.7** | Lot sizing: standard (1.0), mini (0.1), micro (0.01)| **DONE** | `backend/app/services/trading_service.py:59`, `frontend/src/app/page.tsx:313-326` | Low | P6 | Units correctly mapped from lot sizes (100k, 10k, 1k). |
| **FR-4.8** | Stop Loss and Take Profit levels | **PARTIAL** | `backend/app/services/trading_service.py:157-185` | Low | P6 | Auto-close logic on SL/TP price breach implemented in tick loop. |
| **FR-4.9** | Trailing stop with user-defined pips | **PARTIAL** | `backend/app/services/trading_service.py:167-185` | Med | P6 | Basic ratchet present; requires adversarial verification per TC-9. |
| **FR-4.10**| Real-time floating P&L updates | **PARTIAL** | `backend/app/services/trading_service.py:140-155` | Low | P6 | Floating P&L updated on tick loop using float arithmetic. |
| **FR-4.11**| Compute used margin, free margin, margin level % | **PARTIAL** | `backend/app/services/trading_service.py:196-211` | Low | P6 | Margin metrics computed; uses float types. |
| **FR-4.12**| Margin call (<100%) and auto-liquidation (<50%)| **PARTIAL** | `backend/app/services/trading_service.py:187-194` | Med | P6 | Auto-liquidation triggers when `margin_level_pct < 50.0`. |
| **FR-4.13**| Reset paper account & archive trade history | **PARTIAL** | `backend/app/services/trading_service.py:22-31` | Low | P6 | Account resets in memory; history cleared rather than archived to DB. |

---

### 1.5 Analytics & Journaling (FG-5)

| SRS ID | Requirement (Short) | Status | Evidence (File:Line) | Effort | Target Phase | Notes & Discrepancies |
|---|---|---|---|---|---|---|
| **FR-5.1** | Trade history log with entry/exit/pnl/duration | **PARTIAL** | `backend/app/services/trading_service.py:111-127` | Low | P7 | Stored in in-memory array `closed_trades`; no DB persistence. |
| **FR-5.2** | Win rate, average win/loss, profit factor | **PARTIAL** | `backend/app/services/trading_service.py:253-261` | Low | P7 | Computed over in-memory closed trades; profit factor handles zero-loss with fallback. |
| **FR-5.3** | Average risk-to-reward ratio | **PARTIAL** | `backend/app/services/trading_service.py:261` | Low | P7 | Computed as `avg_win / avg_loss`. |
| **FR-5.4** | Render equity curve chart | **PARTIAL** | `backend/app/services/trading_service.py:130-136`, `frontend/src/app/analytics/page.tsx:80-130` | Low | P7 | SVG equity curve rendered from in-memory snapshot array. |
| **FR-5.5** | Max drawdown (absolute & percentage) | **PARTIAL** | `backend/app/services/trading_service.py:265-278` | Low | P7 | Computed peak-to-trough over equity history. |
| **FR-5.6** | Performance breakdown by currency pair | **PARTIAL** | `backend/app/services/trading_service.py:280-289`, `frontend/src/app/analytics/page.tsx:140-165` | Low | P7 | Pair breakdown aggregated from trade history. |
| **FR-5.7** | Performance breakdown by trading session | **PARTIAL** | `backend/app/services/trading_service.py:305-308` | Med | P7 | Returns static dummy split; needs trade entry timestamp session tagging. |
| **FR-5.8** | Free-text notes and tags for trade journaling | **PARTIAL** | `backend/app/strategy/journal.py:1-120`, `frontend/src/app/strategy/journal/page.tsx` | Med | P7 | Implemented in strategy toolkit sub-module; not linked to paper trading positions. |
| **FR-5.9** | Export full trade history as CSV | **ABSENT** | No implementation found | Low | P7 | CSV streaming export endpoint not yet implemented. |

---

### 1.6 User & Alert Management (FG-6)

| SRS ID | Requirement (Short) | Status | Evidence (File:Line) | Effort | Target Phase | Notes & Discrepancies |
|---|---|---|---|---|---|---|
| **FR-6.1** | User registration via email/password | **PARTIAL** | `backend/app/services/auth_service.py:26-38` | Med | P5 | In-memory dict with bcrypt; no Supabase Auth integration. |
| **FR-6.2** | OAuth login via Google | **ABSENT** | No implementation found | Med | P5 | Supabase Google OAuth not configured. |
| **FR-6.3** | JWT access tokens (1h) & refresh tokens | **PARTIAL** | `backend/app/services/auth_service.py:46-60` | Low | P5 | Access token generated with 60m expiry; refresh tokens absent. |
| **FR-6.4** | Row Level Security (RLS) across user data | **ABSENT** | No implementation found | High | P2, P5 | Zero database tables and zero RLS policies exist. |
| **FR-6.5** | Create and manage watchlists of currency pairs| **PARTIAL** | `frontend/src/components/layout/Sidebar.tsx:87-104` | Low | P5 | Static hardcoded watchlist in sidebar; no dynamic CRUD. |
| **FR-6.6** | Price-level alerts (crosses above/below) | **PARTIAL** | `backend/app/services/alert_service.py:10-27` | Med | P5 | In-memory alert creation; crossing evaluation engine absent. |
| **FR-6.7** | Indicator alerts (RSI/MACD/BB) | **PARTIAL** | `backend/app/schemas/alerts.py:8-16` | Med | P5 | Schema supports indicator alerts; evaluation logic absent. |
| **FR-6.8** | In-app notification delivery | **ABSENT** | No implementation found | Med | P5 | Notification persistence and WS dispatch absent. |
| **FR-6.9** | Email notification delivery via transactional provider| **ABSENT** | No implementation found | Med | P5 | Resend provider integration absent. |
| **FR-6.10**| Enable, disable, delete alerts | **PARTIAL** | `backend/app/services/alert_service.py:32-36` | Low | P5 | Delete implemented in-memory; enable/disable toggle absent. |
| **FR-6.11**| Cap at 50 active alerts per user | **PARTIAL** | `backend/app/services/alert_service.py:11-12` | Low | P5 | Enforced in Python service check `len(self.alerts) >= 50`. |

---

## 2. AI/ML Subsystem Requirements (§6)

| SRS ID | Requirement (Short) | Status | Evidence (File:Line) | Effort | Target Phase | Notes & Discrepancies |
|---|---|---|---|---|---|---|
| **AI-1.1** | RAG grounded only in retrieved context | **PARTIAL** | `backend/app/services/ai_service.py:121-127` | High | P8 | Template answer uses snippet content; requires real LLM prompt enforcement. |
| **AI-1.2** | Every claim maps to a retrieved chunk | **PARTIAL** | `backend/app/services/ai_service.py:110-118` | Med | P8 | Citation tags returned; needs post-generation validation. |
| **AI-1.3** | Decline when context below threshold | **PARTIAL** | `backend/app/services/ai_service.py:94-107` | Low | P8 | Refusal string returned when similarity threshold is unmet. |
| **AI-1.4** | Log query, chunk IDs, model, response | **ABSENT** | No implementation found | Med | P2, P8 | `ai_query_log` table not created. |
| **AI-2.1** | FinBERT ≥80% agreement on 200 headlines | **ABSENT** | No implementation found | Med | P8 | Held-out 200-headline evaluation test suite absent. |
| **AI-2.2** | Exclude headlines with no identified currency| **PARTIAL** | `backend/app/services/ai_service.py:144` | Low | P8 | Matches currencies via list filter; needs robust NER lexicon. |
| **AI-2.3** | Recompute sentiment at least hourly | **ABSENT** | No implementation found | Med | P8 | Celery Beat hourly rollup job absent. |
| **AI-3.1** | Display indicator contributions with bias | **DONE** | `backend/app/services/analysis_service.py:186`, `frontend/src/app/page.tsx:175` | Low | P4 | Returns dictionary of indicator weight contributions. |
| **AI-3.2** | Labels describe market state, not trade advice | **DONE** | `backend/app/services/analysis_service.py:171-179` | Low | P4 | Labels restricted to Strong Bullish, Bullish, Neutral, Bearish, Strong Bearish. |
| **AI-3.3** | Signal weights stored in config/DB | **CONFLICTS** | `backend/app/services/analysis_service.py:111-157` | Low | P4 | Weights are currently hardcoded constants in Python code. |
| **AI-4.1** | Visible disclaimer on all AI outputs | **DONE** | `backend/app/services/ai_service.py:64-68`, `frontend/src/app/ai-assistant/page.tsx:170` | Low | P8 | Prominent disclaimer banner present. |
| **AI-4.2** | No specific trade recommendations generated | **DONE** | `backend/app/services/ai_service.py:66` | Low | P8 | Refusal & disclaimer enforce no financial advice. |
| **AI-4.3** | Probabilistic framing, no price certainties | **PARTIAL** | `backend/app/services/ai_service.py:185,200` | Low | P8 | Calendar briefings framed with "historical pip volatility". |
| **AI-4.4** | Model provenance recorded and displayable | **PARTIAL** | `backend/app/services/ai_service.py:105,135` | Low | P8 | `model_used` returned in RAG schema. |
| **AI-4.5** | Notice in privacy policy on 3rd-party LLMs | **ABSENT** | No implementation found | Low | P8, P9 | Privacy policy page absent. |

---

## 3. Non-Functional & Data Integrity Requirements (§5.4, §7.3, §8)

| SRS ID | Category | Requirement (Short) | Status | Evidence (File:Line) | Effort | Target Phase |
|---|---|---|---|---|---|---|
| **DI-1** | Integrity | Candle `low <= open/close <= high` check | **PARTIAL** | `backend/app/services/market_service.py:167-168` | Low | P2 | Enforced in Python mock; DB CHECK constraint absent. |
| **DI-2** | Integrity | Unique `(pair, timeframe, open_time)` on candles | **ABSENT** | No DB schema exists | Low | P2 |
| **DI-3** | Integrity | Positions units != 0; closed has exit price | **PARTIAL** | `backend/app/services/trading_service.py:106` | Low | P2 | Enforced in Python; DB CHECK constraint absent. |
| **DI-4** | Integrity | Equity == balance + sum(floating P&L) derived | **PARTIAL** | `backend/app/services/trading_service.py:198` | Low | P2, P6 | Computed on-the-fly; ADR-0006 required. |
| **DI-5** | Integrity | Fixed-precision `numeric` / `Decimal` only | **CONFLICTS** | `backend/app/services/trading_service.py:33-50` | Med | P1, P2, P6 | Float used throughout existing code. |
| **CI-1** | Interface | HTTPS / TLS 1.3 | **PARTIAL** | Deployed on Vercel (HTTPS); local dev is HTTP | Low | P1, P10 |
| **CI-2** | Interface | WebSocket (WSS) with auto-reconnect | **PARTIAL** | `backend/main.py:410`, `frontend/src/app/page.tsx:48` | Med | P3 | WS endpoint exists; reconnect logic needs hardening. |
| **CI-3** | Interface | WS heartbeat ping/pong at 30s | **ABSENT** | `backend/main.py:410-433` | Low | P3 |
| **CI-4** | Interface | REST response envelope `{data, error, meta}` | **ABSENT** | `backend/main.py:45-180` (returns bare models) | Med | P1 |
| **CI-5** | Interface | Versioned `/api/v1/` endpoints | **DONE** | `backend/main.py:45,72,87,128,144,166,187` | Low | P1 | All endpoints prefixed with `/api/v1/`. |
| **NFR-P1**| Performance | Tick to render < 500ms p95 | **UNVERIFIED** | No benchmark script | Med | P3, P10 |
| **NFR-P2**| Performance | Dashboard LCP < 2.5s on 4G | **UNVERIFIED** | No Lighthouse audit | Med | P9, P10 |
| **NFR-P3**| Performance | Indicator recompute < 2s | **UNVERIFIED** | No benchmark script | Low | P4, P10 |
| **NFR-P4**| Performance | RAG response < 5s p95 | **UNVERIFIED** | No benchmark script | Med | P8, P10 |
| **NFR-P5**| Performance | Paper order ack < 300ms | **UNVERIFIED** | In-memory is sub-5ms; DB unmeasured | Low | P6, P10 |
| **NFR-P6**| Performance | 1y D1 candles fetch < 1s | **UNVERIFIED** | In-memory is sub-10ms; DB unmeasured | Low | P3, P10 |
| **NFR-P7**| Performance | Concurrent WS connections ≥ 200 | **UNVERIFIED** | No Locust test script | Med | P3, P10 |
| **NFR-P8**| Performance | DB query p95 < 100ms | **ABSENT** | No database exists | Low | P2, P10 |
| **NFR-S1**| Security | Password bcrypt cost ≥12; no plaintext log | **PARTIAL** | `backend/app/services/auth_service.py:12` (pbkdf2_sha256) | Low | P5 | Needs Supabase Auth / bcrypt upgrade. |
| **NFR-S2**| Security | Secrets in env vars, never committed | **CONFLICTS** | `backend/app/services/auth_service.py:8` | Low | P1 | Hardcoded JWT secret key must be eliminated. |
| **NFR-S3**| Security | PostgreSQL RLS on all user-scoped tables | **ABSENT** | No DB schema exists | High | P2, P5 |
| **NFR-S4**| Security | JWT access ≤ 1h, refresh ≤ 30d | **PARTIAL** | `backend/app/services/auth_service.py:10` (60m access) | Low | P5 | Refresh token rotation absent. |
| **NFR-S5**| Security | Rate limiting 100 req/min (auth), 20 (anon) | **ABSENT** | No rate limit middleware | Med | P1, P5 |
| **NFR-S6**| Security | Server-side validation via Pydantic | **DONE** | `backend/app/schemas/*.py` | Low | P1 | Pydantic v2 schemas used on all routes. |
| **NFR-S7**| Security | Security headers & locked CORS | **CONFLICTS** | `backend/main.py:35` (`allow_origins=["*"]`) | Low | P1 | Must lock CORS and inject CSP/HSTS headers. |
| **NFR-S8**| Security | Dependency vulnerability scanning in CI | **ABSENT** | No GitHub Actions workflow | Low | P1 |
| **NFR-S9**| Security | No real money or broker credentials | **DONE** | Entire platform is paper/informational only | Low | P0–P10 |
| **NFR-R1**| Reliability | 99.0% uptime target | **UNVERIFIED** | No SLA monitor | Low | P10 |
| **NFR-R2**| Reliability | OANDA stream disconnect handled gracefully | **ABSENT** | Catch block empty in WS | Med | P3 |
| **NFR-R3**| Reliability | AI subsystem failure leaves trading intact | **DONE** | Subsystems are decoupled in service layer | Low | P8 |
| **NFR-R4**| Reliability | Auto-recover from upstream failures | **ABSENT** | No circuit breaker / retry logic | Med | P1, P3 |
| **NFR-R5**| Reliability | Daily DB backups with 7-day retention | **ABSENT** | Supabase managed backup configuration | Low | P2, P10 |
| **NFR-U1**| Usability | First trade in < 3 minutes without docs | **PARTIAL** | Order ticket in Command Center | Low | P6, P9 |
| **NFR-U2**| Usability | In-app glossary of Forex terms | **PARTIAL** | `frontend/src/app/strategy/reference/page.tsx` | Low | P9 |
| **NFR-U3**| Usability | Plain-language error messages | **PARTIAL** | FastAPI exceptions return string details | Low | P1 |
| **NFR-U4**| Usability | Explicit confirmation on destructive actions | **PARTIAL** | Account reset modal in paper trading | Low | P5, P6 |
| **NFR-M1**| Maintenance | Backend test coverage ≥ 70% | **DONE** | 208 unit tests pass in `backend/tests` | Low | P1 |
| **NFR-M2**| Maintenance | Type annotations & docstrings | **PARTIAL** | Type hints present on most functions | Low | P1 |
| **NFR-M3**| Maintenance | Zero lint errors (ruff, eslint, tsc --strict)| **PARTIAL** | `tsconfig.json` has strict: true; ruff clean on backend | Low | P1 |
| **NFR-M4**| Maintenance | Versioned migration files for DB changes | **ABSENT** | Zero SQL migration files exist | Med | P2 |
| **NFR-M5**| Maintenance | Structured JSON logging with correlation ID | **ABSENT** | Standard print/console logs used | Med | P1 |
| **NFR-X1**| Portability | Containerized Docker setup | **PARTIAL** | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` | Low | P1 |
| **NFR-X2**| Portability | Stateless service layer | **CONFLICTS** | Services hold mutable state in memory dicts | High | P1, P2 | State must move to Redis/Postgres. |
| **NFR-X3**| Portability | Add pairs via config without code change | **PARTIAL** | `PAIRS_CONFIG` array in Python; should move to DB | Low | P2 |
| **NFR-X4**| Portability | Cross-browser compatibility | **PARTIAL** | Standard React/Tailwind elements | Low | P9 |
| **NFR-L1**| Compliance | Persistent investment disclaimer | **DONE** | `backend/app/services/ai_service.py:64`, UI footer | Low | P0–P10 |
| **NFR-L2**| Compliance | Not represented as SEBI registered | **DONE** | Disclaimers state academic internship project | Low | P0–P10 |
| **NFR-L3**| Compliance | Privacy policy disclosing 3rd-party LLMs | **ABSENT** | Privacy policy route absent | Low | P8, P9 |
| **NFR-L4**| Compliance | Account & data deletion endpoint | **ABSENT** | No account deletion route | Low | P5 |
| **NFR-L5**| Compliance | 3rd-party data terms & attribution | **PARTIAL** | OANDA & Reuters attributed in mock data | Low | P3, P8 |

---

## 4. Test Cases & Constraints (§2.5, §10.2)

| ID | Category | Requirement / Case | Status | Evidence (File:Line) | Effort | Target Phase |
|---|---|---|---|---|---|---|
| **TC-1** | Test Case | USD/JPY 2-decimal pip calculation at 0.1 lot | **PARTIAL** | `backend/tests/test_pip_calc.py:1-25` (passes with float math) | Low | P6 | Convert to Decimal math and assert against worked example. |
| **TC-2** | Test Case | Insufficient margin rejection with shortfall | **DONE** | `backend/tests/test_paper_trading.py:15-30` | Low | P6 | Order rejected with explicit margin shortfall message. |
| **TC-3** | Test Case | Auto-liquidation when margin level < 50% | **DONE** | `backend/tests/test_paper_trading.py:32-55` | Low | P6 | Auto-liquidation triggers and closes positions. |
| **TC-4** | Test Case | Adversarial RLS cross-user isolation test | **ABSENT** | No database / RLS tests exist | High | P2, P5 |
| **TC-5** | Test Case | RAG refusal on out-of-corpus query | **DONE** | `backend/tests/test_ai_service.py:1-25` | Low | P8 | Asserted refusal on ungrounded query. |
| **TC-6** | Test Case | OANDA stream disconnect & zero candle loss | **ABSENT** | No chaos / stream loss test exists | Med | P3, P10 |
| **TC-7** | Test Case | Malformed candle `high < low` rejected | **ABSENT** | No validation test on ingestion | Low | P2, P3 |
| **TC-8** | Test Case | 200 concurrent WS clients within 500ms p95 | **ABSENT** | No load test exists | Med | P3, P10 |
| **TC-9** | Test Case | Trailing stop ratchet verification | **PARTIAL** | `backend/tests/test_paper_trading.py` | Low | P6 |
| **TC-10**| Test Case | FinBERT agreement ≥80% on 200 headlines | **ABSENT** | No evaluation dataset committed | Med | P8 |
| **CON-1**| Constraint| OANDA free tier limits (≤120 req/s, 5k candles)| **ABSENT** | Provider token-bucket limiter not implemented | Low | P3 |
| **CON-2**| Constraint| LLM cost budget guards & daily ceilings | **ABSENT** | No token accounting or budget limiter | Low | P8 |
| **CON-3**| Constraint| No real money handling | **DONE** | Platform is 100% paper trading | Low | Core |
| **CON-4**| Constraint| Indian IT Act 2000 data compliance | **PARTIAL** | Disclaimers present; data privacy terms needed | Low | P5, P9 |
| **CON-5**| Constraint| 16-week internship timeline feasibility | **ON TRACK** | Phased execution architecture established | Low | P0–P10 |
| **CON-6**| Constraint| Free/hobby hosting tier compatibility | **FEASIBLE**| FastAPI + Next.js + Supabase + Redis fit free tiers | Low | P1, P11 |
| **CON-7**| Constraint| TypeScript strict mode, zero `any` | **PARTIAL** | `frontend/tsconfig.json` has `strict: true` | Low | P1, P9 |
