# 00 — Repository Inventory & Baseline Audit

**Date:** 2026-08-21  
**Project:** Tradly — AI/ML-Powered Forex Market Intelligence & Algorithmic Trading Platform  
**Document Version:** 1.0 (Phase 0 Baseline)  
**Author:** 11-Agent Swarm (Mission Planner, Repository Analyst, Architect, Database Engineer, Backend Engineer, Frontend Engineer, Forex Domain Expert, Performance Engineer, Security Analyst, QA Inspector, Documentation Engineer)  
**Source of Truth:** `TRADLY_SRS v1.0` (IEEE Std 830-1998)

---

## 1. Complete File Tree (Excluding `node_modules`, `.next`, `__pycache__`, `.git`)

```text
Tradly/
├── .claude/                                  # Claude tool configuration
├── .dockerignore                             # Docker ignore rules
├── .env.example                              # Root environment variable template (stock/LLM focused)
├── .env.enterprise.example                   # Azure OpenAI enterprise env template
├── .gitignore                                # Git ignore patterns
├── .pytest_cache/                            # Pytest cache directory
├── CHANGELOG.md                              # Upstream TradingAgents changelog (v0.3.0)
├── Dockerfile                                # Root Dockerfile (TradingAgents CLI container)
├── docker-compose.yml                        # Multi-service composition (backend, frontend, postgres, redis)
├── Forex_Trading_Notes.md                    # Discretionary Forex strategy notes & rules
├── LICENSE                                   # Apache 2.0 License
├── main.py                                   # Root runner script for TradingAgents stock graph
├── pyproject.toml                            # Python project config for TradingAgents framework
├── README.md                                 # Upstream framework documentation
├── requirements.txt                          # Stub root requirements file (empty/minimal)
├── STRATEGY_TOOLKIT.md                       # Forex Top-Down Confluence strategy specification
├── test.py                                   # Root test script for TradingAgents
├── Tradly_Month2_Report.md                   # Academic internship Month 2 progress report
├── Tradly_SRS.md                             # Authoritative System Requirements Specification v1.0
├── forex-strategy-toolkit-claude-code-prompt.md # Claude Code prompt pack for strategy engine
├── assets/                                   # Architecture diagrams and promotional images
│   ├── TauricResearch.png
│   ├── analyst.png
│   ├── cli/
│   │   ├── cli_init.png
│   │   ├── cli_news.png
│   │   ├── cli_technical.png
│   │   └── cli_transaction.png
│   ├── researcher.png
│   ├── risk.png
│   ├── schema.png
│   ├── trader.png
│   └── wechat.png
├── backend/                                  # FastAPI Prototype Application
│   ├── Dockerfile                            # FastAPI container image definition
│   ├── conftest.py                           # Pytest configuration for backend
│   ├── main.py                               # FastAPI root server and router definitions
│   ├── requirements.txt                      # Backend Python dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── schemas/                          # Pydantic schema models
│   │   │   ├── __init__.py
│   │   │   ├── ai.py                         # RAG query, sentiment, and economic event schemas
│   │   │   ├── alerts.py                     # Alert creation and response schemas
│   │   │   ├── auth.py                       # User registration, login, token schemas
│   │   │   ├── market.py                     # Currency pair, candle, indicator, session schemas
│   │   │   ├── strategy.py                   # Strategy toolkit schemas (AOI, structure, plans)
│   │   │   └── trading.py                    # Order, position, metrics, analytics schemas
│   │   ├── services/                         # In-memory service implementations
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py                 # Mock RAG & static news corpus
│   │   │   ├── alert_service.py              # In-memory alert management
│   │   │   ├── analysis_service.py           # Technical indicator & composite bias math
│   │   │   ├── auth_service.py               # In-memory JWT auth
│   │   │   ├── market_service.py             # Simulated 15-pair market ticks & candles
│   │   │   ├── strategy_service.py           # Top-down confluence strategy wrapper
│   │   │   ├── trading_service.py            # Simulated paper trading engine
│   │   │   └── tradingagents_bridge.py       # Bridge to upstream stock LLM framework
│   │   └── strategy/                         # Price-action strategy engine modules
│   │       ├── __init__.py
│   │       ├── aoi.py                        # Area of Interest (AOI) detection
│   │       ├── break_retest.py               # Break & Retest trigger evaluation
│   │       ├── config.py                     # Strategy configuration & thresholds
│   │       ├── confluence.py                 # Confluence matrix calculation
│   │       ├── data_input.py                 # CSV and live data ingestion for strategy
│   │       ├── engine.py                     # Strategy pipeline orchestrator
│   │       ├── head_shoulders.py             # H&S chart pattern detector
│   │       ├── indicators.py                 # Strategy specific indicator calculations
│   │       ├── journal.py                    # In-memory strategy trade journal
│   │       ├── patterns.py                   # Candlestick pattern detection
│   │       ├── pips.py                       # Pip calculations (float-based)
│   │       ├── reference.py                  # Reference tables for pairs and sessions
│   │       ├── risk.py                       # Position sizing and risk engine
│   │       ├── sample_data.py                # Bundled OHLC scenarios
│   │       ├── sessions.py                   # Forex session clock helpers
│   │       ├── structure.py                  # Market structure (HH, HL, LH, LL, CHoCH)
│   │       ├── topdown.py                    # Multi-timeframe trend alignment
│   │       └── types.py                      # Internal dataclass types for strategy
│   └── tests/                                # Backend test suite (208 passing tests)
│       ├── test_ai_service.py
│       ├── test_paper_trading.py
│       ├── test_pip_calc.py
│       ├── test_strategy_aoi.py
│       ├── test_strategy_api.py
│       ├── test_strategy_confluence.py
│       ├── test_strategy_flow.py
│       ├── test_strategy_patterns.py
│       ├── test_strategy_risk.py
│       └── test_strategy_structure.py
├── frontend/                                 # Next.js 14 Web Application
│   ├── Dockerfile                            # Multi-stage Next.js container build
│   ├── next-env.d.ts                         # Next.js TypeScript declarations
│   ├── next.config.mjs                       # Next.js configuration
│   ├── package-lock.json                     # NPM lockfile
│   ├── package.json                          # Node.js dependencies and scripts
│   ├── postcss.config.js                     # PostCSS config
│   ├── tailwind.config.js                    # Tailwind styling configuration
│   ├── tsconfig.json                         # TypeScript configuration (strict mode enabled)
│   └── src/
│       ├── app/                              # Next.js 14 App Router routes
│       │   ├── globals.css                   # Global styles and theme definitions
│       │   ├── layout.tsx                    # Root layout with Navbar and Sidebar
│       │   ├── page.tsx                      # Command Center (Dashboard & FXGlobe)
│       │   ├── ai-assistant/page.tsx         # RAG Chat & Assistant UI
│       │   ├── analytics/page.tsx            # Performance analytics & Trade Journal UI
│       │   ├── chart/page.tsx                # Interactive SVG Candlestick Chart UI
│       │   ├── paper-trading/page.tsx        # Paper Order Execution Ticket UI
│       │   └── strategy/                     # Confluence Strategy Toolkit pages
│       │       ├── page.tsx                  # Strategy Scanner & Overview UI
│       │       ├── journal/page.tsx          # Strategy Journal UI
│       │       ├── reference/page.tsx        # Strategy Reference UI
│       │       └── risk/page.tsx             # Risk & Position Sizing UI
│       ├── components/                       # Reusable UI components
│       │   ├── 3d/FXGlobe.tsx                # Three.js 3D Forex Globe visualization
│       │   ├── chart/CandlestickChart.tsx    # Interactive candlestick chart component
│       │   ├── layout/Navbar.tsx             # Top navigation bar with live session clock
│       │   ├── layout/Sidebar.tsx            # Left navigation drawer
│       │   └── strategy/
│       │       ├── StructureChart.tsx        # Market structure visualization chart
│       │       └── panels.tsx                # Strategy toolkit sub-panels
│       ├── services/                         # Frontend API client connectors
│       │   ├── api.ts                        # Core Tradly backend client (hardcoded localhost:8000)
│       │   └── strategyApi.ts                # Strategy API client (supports NEXT_PUBLIC_API_BASE)
│       └── types/                            # Frontend TypeScript interface definitions
│           ├── market.ts                     # Market, trading, AI, alert interfaces
│           └── strategy.ts                   # Strategy toolkit interfaces
├── cli/                                      # Upstream TradingAgents CLI framework
│   ├── __init__.py
│   ├── announcements.py
│   ├── config.py
│   ├── main.py                               # Typer CLI application entry point
│   ├── models.py
│   ├── stats_handler.py
│   ├── utils.py
│   └── static/welcome.txt
├── scripts/                                  # Utility and smoke test scripts
│   └── smoke_structured_output.py
├── tests/                                    # Upstream TradingAgents unit tests (33 collection failures)
│   ├── __init__.py
│   ├── conftest.py
│   └── test_*.py (49 test files)
└── tradingagents/                            # Upstream Multi-Agent Stock Framework
    ├── __init__.py
    ├── default_config.py
    ├── reporting.py
    ├── agents/                               # Stock analyst agents (fundamentals, market, news, social)
    ├── dataflows/                            # Stock data vendors (AlphaVantage, YFinance, FRED, Polymarket)
    ├── graph/                                # LangGraph trading graph setup
    └── llm_clients/                          # LLM client adapters (OpenAI, Anthropic, Google, Azure, Bedrock)
```

---

## 2. Package and Dependency Audit

### 2.1 Frontend Dependencies (`frontend/package.json`)

| Package | Version Spec | Installed/Resolved | Status / Purpose | Dead / Deprecated? |
|---|---|---|---|---|
| `next` | `14.2.15` | `14.2.15` | Core Framework (App Router) | Active |
| `react` | `^18.3.1` | `18.3.1` | UI Library | Active |
| `react-dom` | `^18.3.1` | `18.3.1` | DOM Renderer | Active |
| `recharts` | `^2.13.0` | `2.13.0` | Charting Library | Active (Note: CandlestickChart is custom SVG) |
| `three` | `^0.169.0` | `0.169.0` | 3D Graphics Engine for FXGlobe | Active (Needs bundle dynamic import) |
| `@react-three/fiber` | `^8.17.10` | `8.17.10` | Three.js React Reconciler | Active |
| `@react-three/drei` | `^9.114.0` | `9.114.0` | Three.js Helpers | Active |
| `framer-motion` | `^11.11.9` | `11.11.9` | UI Animations | Active |
| `lucide-react` | `^0.453.0` | `0.453.0` | UI Icons | Active |
| `clsx` | `^2.1.1` | `2.1.1` | Class string utility | Active |
| `tailwind-merge` | `^2.5.4` | `2.5.4` | Tailwind class deduplication | Active |
| `typescript` (dev) | `^5.6.3` | `5.6.3` | TypeScript Compiler | Active |
| `tailwindcss` (dev) | `^3.4.14` | `3.4.14` | CSS Framework | Active |
| `postcss` (dev) | `^8.4.47` | `8.4.47` | PostCSS processor | Active |
| `autoprefixer` (dev)| `^10.4.20` | `10.4.20` | CSS vendor prefixing | Active |

**Dead Dependencies:** `recharts` is installed but `frontend/src/components/chart/CandlestickChart.tsx` implements a custom pure SVG renderer instead of using Recharts.

---

### 2.2 Backend Dependencies (`backend/requirements.txt`)

| Package | Version Spec | Purpose | Status in Architecture |
|---|---|---|---|
| `fastapi` | `>=0.110.0` | Web framework | Core Application Layer |
| `uvicorn[standard]` | `>=0.28.0` | ASGI Web Server | Core Runtime |
| `websockets` | `>=12.0` | WebSocket protocol support | Core Real-time |
| `pydantic` | `>=2.6.0` | Schema validation | Core Validation |
| `numpy` | `>=1.26.0` | Vector calculations | Mathematical operations |
| `pandas` | `>=2.2.0` | Dataframe transformations | Data aggregation |
| `python-jose[cryptography]` | `>=3.3.0` | JWT token handling | Auth Layer (In-memory mock) |
| `passlib[bcrypt]` | `>=1.7.4` | Password hashing | Auth Layer |
| `python-multipart` | `>=0.0.9` | Form data parsing | Auth endpoints |
| `pytest` | `>=8.0.0` | Testing framework | QA verification |
| `requests` | `>=2.31.0` | Synchronous HTTP calls | Provider calls |

**Missing SRS Backend Dependencies:**
- `supabase` / `asyncpg` / `psycopg3` (Supabase Postgres database driver)
- `redis` / `aioredis` (Redis hot cache client)
- `celery` + `redis` (Background task queue and beat scheduler)
- `transformers`, `torch`, `sentencepiece` (FinBERT sentiment inference)
- `openai` / `langchain` (OpenAI embeddings and RAG orchestrator)
- `httpx` (Async HTTP client for OANDA v20 and Groq APIs)

---

### 2.3 Upstream Stock Framework Dependencies (`pyproject.toml`)

| Package | Version Spec | Scope |
|---|---|---|
| `langchain-core` | `>=0.3.81` | Upstream Stock Agent Graphs |
| `langgraph` | `>=0.4.8` | Stock Agent Orchestration |
| `yfinance` | `>=1.4.1` | Stock Market Data Vendor |
| `stockstats` | `>=0.6.5` | Stock Technical Indicators |
| `backtrader` | `>=1.9.78.123`| Stock Backtesting |
| `questionary` | `>=2.1.0` | Interactive CLI UI |
| `typer` | `>=0.21.0` | CLI Framework |
| `rich` | `>=14.0.0` | Terminal formatting |

*Finding:* These dependencies belong to the legacy stock research toolkit (`tradingagents/` & `cli/`) and are completely uninstalled in the primary Python runtime, generating 33 test collection errors when running pytest from root.

---

## 3. Environment Variable Audit & Security Exposure Analysis

Every environment variable referenced across the entire repository was extracted and analyzed for security posture:

| Variable Name | Referenced In (File:Line) | Purpose | Client-Exposed (`NEXT_PUBLIC_*`) | Secret / Sensitive? | Security Classification |
|---|---|---|---|---|---|
| `NEXT_PUBLIC_API_BASE` | `frontend/src/services/strategyApi.ts:23` | Base URL for FastAPI Backend | Yes (Expected) | No | **SAFE** |
| `OANDA_API_KEY` | `docker-compose.yml:13` | OANDA v20 Streaming API Key | No | Yes | **PROTECTED** |
| `GROQ_API_KEY` | `docker-compose.yml:14` | Groq LLaMA 3 LLM API Key | No | Yes | **PROTECTED** |
| `OPENAI_API_KEY` | `docker-compose.yml:15`, `.env.example:2` | OpenAI Embeddings / Chat | No | Yes | **PROTECTED** |
| `DATABASE_URL` | `docker-compose.yml:11` | PostgreSQL Connection String | No | Yes | **PROTECTED** |
| `REDIS_URL` | `docker-compose.yml:12` | Redis Cache Connection String | No | Yes | **PROTECTED** |
| `TRADLY_LIVE_DATA` | `backend/app/strategy/data_input.py:163` | Flag for live data mode | No | No | **SAFE** |
| `TRADLY_LIVE_API_KEY` | `backend/app/strategy/data_input.py:189` | Live data vendor key | No | Yes | **PROTECTED** |
| `SECRET_KEY` (Hardcoded) | `backend/app/services/auth_service.py:8` | JWT signing key | No (In Backend) | **CRITICAL SECRET** | **CRITICAL VULNERABILITY (NFR-S2 Violation)**: Hardcoded `"tradly-super-secret-jwt-key-for-local-dev-and-demo"` in source code. |
| `ALPHA_VANTAGE_API_KEY` | `tradingagents/dataflows/alpha_vantage_common.py:30` | Stock data vendor key | No | Yes | **PROTECTED** (Legacy) |
| `FRED_API_KEY` | `tradingagents/dataflows/fred.py:86` | Macro data vendor key | No | Yes | **PROTECTED** (Legacy) |
| `ANTHROPIC_API_KEY` | `.env.example:4` | LLM Key | No | Yes | **PROTECTED** (Legacy) |
| `GOOGLE_API_KEY` | `.env.example:3` | LLM Key | No | Yes | **PROTECTED** (Legacy) |
| `AZURE_OPENAI_API_KEY`| `.env.enterprise.example:2` | Azure OpenAI Key | No | Yes | **PROTECTED** (Legacy) |

### Key Security Findings:
1. **Critical Secret Leak in Code (NFR-S2):** `backend/app/services/auth_service.py:8` hardcodes the JWT secret key directly in Python code.
2. **Hardcoded Localhost in Frontend Client:** `frontend/src/services/api.ts:7` hardcodes `const API_BASE = "http://localhost:8000/api/v1";` without falling back to `process.env.NEXT_PUBLIC_API_BASE`. This prevents any deployed frontend from reaching a live backend.
3. **Overly Permissive CORS (NFR-S7):** `backend/main.py:35` sets `allow_origins=["*"]` and `allow_credentials=True`.

---

## 4. Frontend Routes & Rendered Views

| Route | Rendered Page File | Key Elements Rendered | Real Network Calls Made |
|---|---|---|---|
| `/` | `frontend/src/app/page.tsx` | Command Center, 3D Three.js FXGlobe, 15-pair live grid, AI Composite Bias card, Quick Paper Trading ticket | `GET /market/pairs`<br>`GET /trading/metrics`<br>`GET /analysis/bias/{symbol}`<br>`POST /trading/orders`<br>`WSS /ws/stream` |
| `/chart` | `frontend/src/app/chart/page.tsx` | Full-screen Candlestick chart (SVG), timeframe selector (M1–D1), indicator overlays (EMA, SMA, BB, RSI, MACD, Fib) | `GET /market/pairs`<br>`GET /market/candles/{symbol}?timeframe={tf}&limit={lim}`<br>`GET /analysis/indicators/{symbol}` |
| `/ai-assistant` | `frontend/src/app/ai-assistant/page.tsx` | Grounded RAG Chat interface, Citation cards, Disclaimer banner, Currency sentiment heatmap, Economic calendar table | `POST /ai/rag/query`<br>`GET /ai/sentiment`<br>`GET /ai/calendar` |
| `/paper-trading` | `frontend/src/app/paper-trading/page.tsx` | Complete paper order ticket (market/limit, lot size, leverage 1:1–1:100, SL/TP, trailing stop), open positions table, account reset modal | `GET /trading/metrics`<br>`GET /trading/positions`<br>`POST /trading/orders`<br>`POST /trading/positions/{id}/close`<br>`POST /trading/reset` |
| `/analytics` | `frontend/src/app/analytics/page.tsx` | Performance metrics grid (win rate, profit factor, drawdown), SVG equity curve, currency pair breakdown, session breakdown, closed trade log | `GET /trading/analytics`<br>`GET /trading/trades` |
| `/strategy` | `frontend/src/app/strategy/page.tsx` | Top-down confluence scanner, scenario picker, structure chart, AOI zone cards, 4-pillar confluence breakdown | `GET /strategy/scenarios`<br>`GET /strategy/analysis/{scenario}`<br>`GET /strategy/candles/{scenario}/{tf}` |
| `/strategy/risk` | `frontend/src/app/strategy/risk/page.tsx` | Risk tier table, 1:2 R:R validator, position sizing calculator | `GET /strategy/risk/table`<br>`POST /strategy/risk/plan` |
| `/strategy/journal` | `frontend/src/app/strategy/journal/page.tsx` | Strategy trade journal, weekly pace indicator (1 trade/week rule), discipline tags | `GET /strategy/journal`<br>`POST /strategy/journal`<br>`GET /strategy/pace` |
| `/strategy/reference` | `frontend/src/app/strategy/reference/page.tsx` | Forex pairs reference, session hours, golden rules | `GET /strategy/reference` |

---

## 5. Frontend-to-Backend Network Call Verification

| Frontend Call | File & Line | Backend Endpoint Path | HTTP Method | Expected Shape | Endpoint Exists in Backend? | Actual Backend Implementation Status |
|---|---|---|---|---|---|---|
| `api.getPairs()` | `api.ts:23` | `/api/v1/market/pairs` | GET | `List[CurrencyPair]` | **YES** (`backend/main.py:45`) | In-memory mock with simulated Brownian prices (`market_service.py:59`) |
| `api.getPair(sym)` | `api.ts:24` | `/api/v1/market/pairs/{symbol}` | GET | `CurrencyPair` | **YES** (`backend/main.py:49`) | In-memory mock (`market_service.py:87`) |
| `api.getCandles(sym, tf, lim)` | `api.ts:25` | `/api/v1/market/candles/{symbol}` | GET | `List[Candle]` | **YES** (`backend/main.py:56`) | On-the-fly random candle generator (`market_service.py:137`) |
| `api.getMarketSessions()` | `api.ts:27` | `/api/v1/market/sessions` | GET | `MarketSessionOverview` | **YES** (`backend/main.py:64`) | Static session hours logic (`market_service.py:186`) |
| `api.getIndicators(sym, tf)` | `api.ts:28` | `/api/v1/analysis/indicators/{symbol}` | GET | `IndicatorSnapshot` | **YES** (`backend/main.py:72`) | Python numpy/list math (`analysis_service.py:9`) |
| `api.getCompositeBias(sym, tf)`| `api.ts:30` | `/api/v1/analysis/bias/{symbol}` | GET | `CompositeBias` | **YES** (`backend/main.py:76`) | Rule-ensemble with hardcoded weights (`analysis_service.py:101`) |
| `api.getAccountMetrics()` | `api.ts:34` | `/api/v1/trading/metrics` | GET | `AccountMetrics` | **YES** (`backend/main.py:87`) | In-memory state, float math (`trading_service.py:196`) |
| `api.getPositions()` | `api.ts:35` | `/api/v1/trading/positions` | GET | `List[Position]` | **YES** (`backend/main.py:99`) | In-memory dictionary (`trading_service.py:100`) |
| `api.placeOrder(payload)` | `api.ts:36` | `/api/v1/trading/orders` | POST | `Position` | **YES** (`backend/main.py:92`) | In-memory order simulation (`trading_service.py:51`) |
| `api.closePosition(id)` | `api.ts:49` | `/api/v1/trading/positions/{id}/close` | POST | `ClosedTrade` | **YES** (`backend/main.py:104`) | In-memory close & P&L (`trading_service.py:96`) |
| `api.resetAccount(bal)` | `api.ts:51` | `/api/v1/trading/reset` | POST | `AccountMetrics` | **YES** (`backend/main.py:111`) | In-memory state reset (`trading_service.py:22`) |
| `api.getAnalytics()` | `api.ts:53` | `/api/v1/trading/analytics` | GET | `PerformanceAnalytics` | **YES** (`backend/main.py:116`) | In-memory analytics (`trading_service.py:228`) |
| `api.getClosedTrades()` | `api.ts:54` | `/api/v1/trading/trades` | GET | `List[ClosedTrade]` | **YES** (`backend/main.py:120`) | In-memory trade array (`trading_service.py:120`) |
| `api.queryRAG(query, cp)` | `api.ts:57` | `/api/v1/ai/rag/query` | POST | `RAGQueryResponse` | **YES** (`backend/main.py:128`) | Keyword search on 5 mock docs (`ai_service.py:70`) |
| `api.getSentiments()` | `api.ts:63` | `/api/v1/ai/sentiment` | GET | `List[CurrencySentiment]` | **YES** (`backend/main.py:132`) | Derived mock sentiment (`ai_service.py:139`) |
| `api.getCalendar()` | `api.ts:64` | `/api/v1/ai/calendar` | GET | `List[EconomicEvent]` | **YES** (`backend/main.py:136`) | Static list of 4 events (`ai_service.py:168`) |
| `strategyApi.*` (17 methods) | `strategyApi.ts` | `/api/v1/strategy/*` | Various | Strategy models | **YES** (`backend/main.py:187-376`) | Pure Python strategy engine (`app/strategy/`) |
| `WebSocket Stream` | `page.tsx:48` | `/api/v1/ws/stream` | WSS | `ticks_update` JSON | **YES** (`backend/main.py:410`) | Simulated 1Hz tick broadcast (`main.py:410`) |
| `Auth Endpoints` | None in UI | `/api/v1/auth/register`, `/login` | POST | `TokenResponse` | **YES** (`backend/main.py:166-178`) | In-memory dict with static secret (`auth_service.py:26`) |
| `Alerts Endpoints` | None in UI | `/api/v1/alerts`, `DELETE` | POST/GET | `AlertItem` | **YES** (`backend/main.py:144-160`) | In-memory dict (`alert_service.py:10`) |

---

## 6. Summary Finding

The repository state is **Option B (Partial Backend with Prototype Implementation)**:
1. A complete prototype backend exists under `backend/app` with 35+ endpoints implementing Forex logic.
2. The entire backend runs **in-memory with simulated data, float math, and zero persistent database wiring**.
3. The deployed Vercel site (`https://tradex-main.vercel.app/`) is an older build pointing to `http://localhost:8000`, causing it to stall indefinitely on `INITIALIZING TERMINAL SEED...`.
4. Upstream `tradingagents` stock framework files exist alongside the Forex codebase but are disjoint from the SRS requirements.
