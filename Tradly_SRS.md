# Software Requirements Specification

## Tradly — An AI/ML-Powered Forex Market Intelligence & Algorithmic Trading Platform

---

| Field | Detail |
|---|---|
| **Document Title** | Software Requirements Specification (SRS) — Tradly |
| **Version** | 1.0 |
| **Prepared By** | Prince Jivani |
| **Enrollment Number** | 23SE02CS030 |
| **Program** | B.Tech Computer Science (AI/ML Specialization) |
| **Semester** | 7th Semester (2025–26) |
| **Organization** | ThinkNovus Private Limited |
| **Role** | AI/ML Engineer (Intern) |
| **Internship Duration** | June 2026 – October 2026 |
| **Standard Followed** | IEEE Std 830-1998 |
| **Status** | Draft for Review |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Specific Requirements](#3-specific-requirements)
4. [System Architecture](#4-system-architecture)
5. [Data Requirements](#5-data-requirements)
6. [AI/ML Subsystem Specification](#6-aiml-subsystem-specification)
7. [External Interface Requirements](#7-external-interface-requirements)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [System Models](#9-system-models)
10. [Testing & Validation Strategy](#10-testing--validation-strategy)
11. [Deployment & Operations](#11-deployment--operations)
12. [Constraints, Assumptions & Dependencies](#12-constraints-assumptions--dependencies)
13. [Future Enhancements](#13-future-enhancements)
14. [Appendices](#14-appendices)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the complete functional and non-functional requirements for **Tradly**, an AI/ML-powered Forex market intelligence and algorithmic trading platform developed during an AI/ML Engineering internship at ThinkNovus Private Limited.

The document is intended for the following audiences:

- **Development team** — as the authoritative reference for implementation scope
- **ThinkNovus industry mentor** — for milestone review and technical validation
- **Institute faculty mentor** — for academic evaluation of the internship project
- **QA/testing personnel** — as the basis for test case derivation
- **Future maintainers** — as the system-of-record for design intent

### 1.2 Scope

**Tradly** is a web-based platform that provides retail Forex traders with institutional-grade market intelligence at an accessible price point. The system ingests real-time currency pair data, applies technical analysis and machine learning models, synthesizes global macroeconomic context through a Retrieval-Augmented Generation (RAG) pipeline, and delivers actionable trade intelligence through an interactive dashboard.

**In scope for this release (v1.0):**

- Real-time price streaming for 15+ major, minor, and exotic currency pairs
- Multi-timeframe OHLCV candle aggregation (M1 through D1)
- Automated technical indicator computation and signal generation
- RAG-powered natural language Forex assistant with source citation
- FinBERT-based sentiment scoring of Forex news and central bank communications
- Economic calendar with AI-generated pre-event briefings
- Paper trading simulator with pip-accurate P&L, leverage, and risk controls
- Trade journal and performance analytics
- User authentication, watchlists, and personalized alerts

**Explicitly out of scope for v1.0:**

- Live order execution with real capital (paper trading only)
- Forex options and derivatives instruments
- Copy-trading or social trading features
- Regulatory-grade trade reporting or tax computation
- Native mobile applications (responsive web only)

### 1.3 Definitions, Acronyms and Abbreviations

| Term | Definition |
|---|---|
| **Forex / FX** | Foreign Exchange — the global market for trading national currencies |
| **Currency Pair** | Two currencies quoted against each other, e.g. EUR/USD |
| **Base Currency** | The first currency in a pair (EUR in EUR/USD) |
| **Quote Currency** | The second currency in a pair (USD in EUR/USD) |
| **Pip** | Percentage in Point — smallest standard price move; 0.0001 for most pairs, 0.01 for JPY pairs |
| **Spread** | Difference between bid (sell) and ask (buy) price |
| **Lot** | Standard trade size unit; 1 standard lot = 100,000 units of base currency |
| **Leverage** | Ratio of position size to margin deposited, e.g. 1:100 |
| **Margin** | Capital required to open and maintain a leveraged position |
| **Drawdown** | Peak-to-trough decline in account equity |
| **OHLCV** | Open, High, Low, Close, Volume — standard candlestick data structure |
| **RSI** | Relative Strength Index — momentum oscillator (0–100) |
| **MACD** | Moving Average Convergence Divergence — trend-following momentum indicator |
| **ATR** | Average True Range — volatility measure |
| **EMA / SMA** | Exponential / Simple Moving Average |
| **RAG** | Retrieval-Augmented Generation — LLM architecture grounding responses in retrieved documents |
| **LLM** | Large Language Model |
| **FinBERT** | BERT variant fine-tuned on financial text for sentiment classification |
| **NFP** | Non-Farm Payrolls — high-impact US employment report |
| **CPI** | Consumer Price Index — inflation indicator |
| **FOMC** | Federal Open Market Committee — US Federal Reserve policy body |
| **RLS** | Row Level Security — PostgreSQL per-row access control |
| **JWT** | JSON Web Token — stateless authentication token format |
| **SLA** | Service Level Agreement |

### 1.4 References

1. IEEE Std 830-1998 — *IEEE Recommended Practice for Software Requirements Specifications*
2. OANDA v20 REST API Documentation — `https://developer.oanda.com/rest-live-v20/introduction/`
3. Bank for International Settlements (BIS) — *Triennial Central Bank Survey of Foreign Exchange Turnover*
4. Araci, D. (2019) — *FinBERT: Financial Sentiment Analysis with Pre-trained Language Models*
5. Lewis, P. et al. (2020) — *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*
6. LangChain Documentation — `https://python.langchain.com/docs/`
7. Supabase Documentation — `https://supabase.com/docs`
8. Next.js 14 App Router Documentation — `https://nextjs.org/docs`
9. Murphy, J.J. — *Technical Analysis of the Financial Markets*, New York Institute of Finance

### 1.5 Document Overview

Section 2 provides a high-level product perspective and user characteristics. Section 3 enumerates detailed functional requirements with unique identifiers. Sections 4–7 cover architecture, data, AI/ML specification, and external interfaces. Section 8 specifies non-functional requirements. Sections 9–11 address system models, testing, and deployment. Sections 12–14 document constraints, future work, and supporting appendices.

---

## 2. Overall Description

### 2.1 Product Perspective

Tradly is a **new, self-contained web application** rather than a component of a larger existing system. It integrates with several external services as data and intelligence providers:

```
                    ┌─────────────────────────────────────┐
                    │        External Providers           │
                    │  OANDA API │ NewsAPI │ Groq │       │
                    │  Perplexity │ OpenAI Embeddings     │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │           TRADLY PLATFORM           │
                    │                                     │
                    │  Frontend (Next.js 14)              │
                    │  Backend  (FastAPI)                 │
                    │  Data     (Supabase + Redis)        │
                    │  AI/ML    (RAG + FinBERT + TA)      │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │      End Users (Retail Traders)     │
                    └─────────────────────────────────────┘
```

### 2.2 Product Functions

At the highest level, Tradly provides six function groups:

| ID | Function Group | Summary |
|---|---|---|
| **FG-1** | Market Data & Charting | Stream live prices, aggregate candles, render interactive charts |
| **FG-2** | Technical Analysis | Compute indicators, detect patterns, generate directional bias signals |
| **FG-3** | AI Market Intelligence | RAG-based Q&A, news sentiment scoring, macro event briefings |
| **FG-4** | Paper Trading | Simulate orders with realistic spreads, leverage, and P&L |
| **FG-5** | Analytics & Journaling | Track performance, compute risk metrics, visualize equity curve |
| **FG-6** | User & Alert Management | Authentication, watchlists, configurable price and indicator alerts |

### 2.3 User Classes and Characteristics

| User Class | Description | Technical Skill | Frequency of Use | Priority |
|---|---|---|---|---|
| **Retail Forex Trader** | Individual trading own capital; primary target user | Low–Medium | Daily, multiple sessions | High |
| **Aspiring Trader / Student** | Learning Forex; uses paper trading and education features heavily | Low | Daily–Weekly | High |
| **Technical Analyst** | Uses indicators and charting intensively; may export data | Medium–High | Daily | Medium |
| **Quantitative Researcher** | Interested in ML signals, backtesting, and data export | High | Weekly | Medium |
| **System Administrator** | Manages deployment, monitors health, handles incidents | High | As needed | Low |

### 2.4 Operating Environment

**Client side:**
- Browsers: Chrome 120+, Firefox 120+, Safari 17+, Edge 120+
- Screen resolutions: 360px (mobile) through 2560px (desktop)
- Required: JavaScript enabled, WebSocket support, WebGL 2.0 for 3D dashboard

**Server side:**
- Runtime: Python 3.11+ (backend), Node.js 20 LTS (frontend build)
- Database: PostgreSQL 15+ with `pgvector` extension (via Supabase)
- Cache: Redis 7+
- Hosting: Vercel (frontend, edge network), Railway/Render (FastAPI backend)

### 2.5 Design and Implementation Constraints

| ID | Constraint |
|---|---|
| **CON-1** | Market data must be sourced from OANDA's free/demo API tier — limits request rate to 120 requests/second and historical depth to 5,000 candles per request |
| **CON-2** | LLM inference costs must remain within internship budget — Groq free tier and selective Perplexity usage only |
| **CON-3** | No real money handling; the platform must never accept payment credentials or execute live trades in v1.0 |
| **CON-4** | All user data must comply with Indian IT Act 2000 data handling provisions |
| **CON-5** | Development must be completed within a 16-week internship timeline |
| **CON-6** | The system must be operable on free/hobby hosting tiers to remain cost-viable |
| **CON-7** | Frontend must use TypeScript with strict mode enabled; no `any` types in production code |

### 2.6 Assumptions and Dependencies

**Assumptions:**
- Users have basic familiarity with Forex terminology (pip, lot, spread) or will use the in-app glossary
- Users access the platform on a stable internet connection (≥2 Mbps) for real-time streaming
- Forex markets operate 24×5 (Sunday 5pm ET to Friday 5pm ET); the system need not stream on weekends

**Dependencies:**
- Continued availability of OANDA v20 API under current terms
- Groq API uptime for LLM inference; Perplexity API for grounded macro research
- Supabase free-tier limits (500MB database, 2GB bandwidth) remaining sufficient
- NewsAPI and central bank RSS feeds remaining publicly accessible

---

## 3. Specific Requirements

### 3.1 Functional Requirements — Market Data & Charting (FG-1)

| ID | Requirement | Priority |
|---|---|---|
| **FR-1.1** | The system shall stream real-time bid and ask prices for at least 15 currency pairs including EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, NZD/USD, USD/CAD, EUR/GBP, EUR/JPY, GBP/JPY, AUD/JPY, USD/INR, USD/SGD, EUR/AUD, and USD/MXN | Must |
| **FR-1.2** | The system shall aggregate incoming ticks into OHLCV candles at M1, M5, M15, M30, H1, H4, and D1 timeframes | Must |
| **FR-1.3** | The system shall persist at least 2 years of historical D1 candles and 6 months of H1 candles per pair | Must |
| **FR-1.4** | The system shall render interactive candlestick charts with zoom, pan, and crosshair inspection | Must |
| **FR-1.5** | The system shall display the current spread in pips for each pair, updated in real time | Must |
| **FR-1.6** | The system shall allow users to overlay up to 5 technical indicators simultaneously on a chart | Should |
| **FR-1.7** | The system shall display a market session indicator showing active Forex sessions (Sydney, Tokyo, London, New York) with overlap highlighting | Should |
| **FR-1.8** | The system shall gracefully degrade to last-known-price display with a staleness indicator if the streaming connection drops | Must |
| **FR-1.9** | The system shall allow export of chart data as CSV for any pair and timeframe | Could |

### 3.2 Functional Requirements — Technical Analysis (FG-2)

| ID | Requirement | Priority |
|---|---|---|
| **FR-2.1** | The system shall compute RSI (period 14) for all active pairs and timeframes | Must |
| **FR-2.2** | The system shall compute MACD (12, 26, 9) including signal line and histogram | Must |
| **FR-2.3** | The system shall compute Bollinger Bands (period 20, 2 standard deviations) | Must |
| **FR-2.4** | The system shall compute ATR (period 14) as a volatility measure | Must |
| **FR-2.5** | The system shall compute EMA-9, EMA-21, EMA-50, and SMA-200 | Must |
| **FR-2.6** | The system shall compute Fibonacci retracement levels (23.6%, 38.2%, 50%, 61.8%, 78.6%) from user-selected or auto-detected swing points | Should |
| **FR-2.7** | The system shall detect and flag MACD bullish/bearish crossovers | Must |
| **FR-2.8** | The system shall detect RSI overbought (>70) and oversold (<30) conditions | Must |
| **FR-2.9** | The system shall detect Bollinger Band squeeze conditions indicating impending volatility expansion | Should |
| **FR-2.10** | The system shall generate a composite directional bias label per pair per timeframe: Strong Bullish, Bullish, Neutral, Bearish, or Strong Bearish | Must |
| **FR-2.11** | The system shall display the reasoning behind each composite bias signal, listing which indicators contributed and in which direction | Must |
| **FR-2.12** | The system shall recompute all indicators within 2 seconds of a new candle close | Must |

### 3.3 Functional Requirements — AI Market Intelligence (FG-3)

| ID | Requirement | Priority |
|---|---|---|
| **FR-3.1** | The system shall provide a natural language chat interface where users can ask Forex-related questions | Must |
| **FR-3.2** | The system shall answer queries using a RAG pipeline that retrieves from an indexed corpus of Forex news, central bank statements, and economic reports | Must |
| **FR-3.3** | Every AI-generated answer shall include citations linking to the source documents used | Must |
| **FR-3.4** | The system shall decline to answer and state its limitation when the retrieved context is insufficient, rather than generating unsupported claims | Must |
| **FR-3.5** | The system shall ingest and embed new Forex news articles into the vector store at least every 30 minutes during market hours | Must |
| **FR-3.6** | The system shall classify each ingested news headline as Bullish, Bearish, or Neutral with respect to specific currencies using FinBERT | Must |
| **FR-3.7** | The system shall compute and display an aggregate sentiment score (−1.0 to +1.0) per currency, updated hourly | Must |
| **FR-3.8** | The system shall display an economic calendar of upcoming high-impact events (NFP, CPI, FOMC, ECB, RBI, BoE, BoJ decisions) with impact ratings | Must |
| **FR-3.9** | The system shall generate an AI pre-event briefing for each high-impact event, summarizing consensus expectations and historically observed pip volatility | Should |
| **FR-3.10** | The system shall clearly label all AI-generated content as such, with a persistent disclaimer that outputs are informational and not financial advice | Must |
| **FR-3.11** | The system shall respond to AI queries within 5 seconds at the 95th percentile | Should |

### 3.4 Functional Requirements — Paper Trading (FG-4)

| ID | Requirement | Priority |
|---|---|---|
| **FR-4.1** | The system shall provide each user with a virtual account funded with a configurable starting balance (default $10,000) | Must |
| **FR-4.2** | The system shall support market orders, limit orders, and stop orders | Must |
| **FR-4.3** | The system shall support both long (buy) and short (sell) positions | Must |
| **FR-4.4** | The system shall simulate realistic execution by filling orders at the current ask (for buys) or bid (for sells), incorporating live spread | Must |
| **FR-4.5** | The system shall support leverage settings of 1:1, 1:10, 1:30, 1:50, and 1:100 | Must |
| **FR-4.6** | The system shall compute pip value correctly per pair, accounting for JPY pairs (2 decimal places) versus standard pairs (4 decimal places) | Must |
| **FR-4.7** | The system shall support position sizing in standard lots (1.0), mini lots (0.1), and micro lots (0.01) | Must |
| **FR-4.8** | The system shall allow attaching Stop Loss and Take Profit levels to any position | Must |
| **FR-4.9** | The system shall support trailing stops with user-defined pip distance | Should |
| **FR-4.10** | The system shall update floating (unrealized) P&L for all open positions in real time | Must |
| **FR-4.11** | The system shall compute and display used margin, free margin, and margin level percentage | Must |
| **FR-4.12** | The system shall trigger a margin call warning when margin level falls below 100% and auto-liquidate positions when it falls below 50% | Must |
| **FR-4.13** | The system shall allow users to reset their paper account to the starting balance, archiving prior trade history | Should |

### 3.5 Functional Requirements — Analytics & Journaling (FG-5)

| ID | Requirement | Priority |
|---|---|---|
| **FR-5.1** | The system shall maintain a complete trade history log with entry/exit price, time, size, pair, direction, P&L, and duration | Must |
| **FR-5.2** | The system shall compute and display win rate, average win, average loss, and profit factor | Must |
| **FR-5.3** | The system shall compute average risk-to-reward ratio across closed trades | Must |
| **FR-5.4** | The system shall render an equity curve chart showing account balance over time | Must |
| **FR-5.5** | The system shall compute maximum drawdown in both absolute and percentage terms | Must |
| **FR-5.6** | The system shall break down performance by currency pair, identifying best and worst performing pairs | Should |
| **FR-5.7** | The system shall break down performance by trading session (Sydney, Tokyo, London, New York) | Should |
| **FR-5.8** | The system shall allow users to attach free-text notes and tags to individual trades for journaling | Should |
| **FR-5.9** | The system shall allow export of the full trade history as CSV | Could |

### 3.6 Functional Requirements — User & Alert Management (FG-6)

| ID | Requirement | Priority |
|---|---|---|
| **FR-6.1** | The system shall allow user registration via email and password | Must |
| **FR-6.2** | The system shall support OAuth login via Google | Should |
| **FR-6.3** | The system shall issue JWT access tokens with a maximum lifetime of 1 hour and support refresh tokens | Must |
| **FR-6.4** | The system shall enforce Row Level Security so that no user can read or modify another user's watchlists, trades, or alerts | Must |
| **FR-6.5** | The system shall allow users to create and manage watchlists of currency pairs | Must |
| **FR-6.6** | The system shall allow users to create price-level alerts (price crosses above/below X) | Must |
| **FR-6.7** | The system shall allow users to create indicator alerts (RSI crosses threshold, MACD crossover, BB breakout) | Must |
| **FR-6.8** | The system shall deliver triggered alerts via in-app notification | Must |
| **FR-6.9** | The system shall deliver triggered alerts via email using a transactional email provider | Should |
| **FR-6.10** | The system shall allow users to enable, disable, or delete any alert | Must |
| **FR-6.11** | The system shall limit each user to a maximum of 50 active alerts to prevent resource abuse | Should |

---

## 4. System Architecture

### 4.1 Architectural Overview

Tradly follows a **layered, service-oriented architecture** with clear separation between presentation, application logic, intelligence, and data layers.

```
┌───────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                            │
│  Next.js 14 (App Router) · TypeScript · Tailwind CSS           │
│  Three.js (3D dashboard) · Recharts (charts) · GSAP (motion)   │
└──────────────────────────┬────────────────────────────────────┘
                           │ REST (HTTPS) + WebSocket (WSS)
┌──────────────────────────▼────────────────────────────────────┐
│  APPLICATION LAYER — FastAPI (async Python 3.11)               │
│  ┌──────────┬──────────┬───────────┬──────────┬─────────────┐ │
│  │ Market   │ Analysis │ Trading   │ Alert    │ Auth        │ │
│  │ Service  │ Service  │ Service   │ Service  │ Service     │ │
│  └──────────┴──────────┴───────────┴──────────┴─────────────┘ │
└──────────────────────────┬────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────┐
│  INTELLIGENCE LAYER                                            │
│  ┌────────────────┬─────────────────┬────────────────────────┐│
│  │ RAG Pipeline   │ Sentiment Engine│ Technical Analysis     ││
│  │ LangChain      │ FinBERT         │ pandas-ta              ││
│  │ pgvector       │ HuggingFace     │ NumPy/Pandas           ││
│  │ Groq LLaMA 3   │ Transformers    │                        ││
│  └────────────────┴─────────────────┴────────────────────────┘│
└──────────────────────────┬────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────┐
│  DATA LAYER                                                    │
│  Supabase PostgreSQL 15 + pgvector  │  Redis 7 (tick cache)    │
└───────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────┐
│  EXTERNAL SERVICES                                             │
│  OANDA v20 API · NewsAPI · Groq · Perplexity · OpenAI · Resend │
└───────────────────────────────────────────────────────────────┘
```

### 4.2 Component Responsibilities

| Component | Responsibility |
|---|---|
| **Market Service** | Maintains OANDA streaming connection, normalizes ticks, aggregates candles, publishes to Redis and WebSocket subscribers |
| **Analysis Service** | Computes technical indicators on candle close, detects signal conditions, produces composite bias labels |
| **Trading Service** | Manages paper trading order lifecycle, position state, margin computation, and P&L updates |
| **Alert Service** | Evaluates active user alert conditions against incoming price and indicator updates; dispatches notifications |
| **Auth Service** | Delegates to Supabase Auth; validates JWTs on protected routes; enforces RLS context |
| **RAG Pipeline** | Ingests and chunks documents, generates embeddings, performs similarity search, orchestrates LLM generation with citations |
| **Sentiment Engine** | Runs FinBERT inference on news headlines, maps sentiment to affected currencies, aggregates scores |

### 4.3 Technology Stack Rationale

| Layer | Technology | Rationale |
|---|---|---|
| Frontend framework | Next.js 14 (App Router) | Server Components reduce client bundle; streaming SSR improves perceived load time for data-heavy dashboards |
| Language | TypeScript (strict) | Compile-time safety across a domain with many numeric invariants (pip values, lot sizes) |
| Backend framework | FastAPI | Native async support essential for concurrent WebSocket streams; automatic OpenAPI docs |
| Database | Supabase PostgreSQL | Managed Postgres with built-in Auth and RLS eliminates a separate auth service; `pgvector` avoids a dedicated vector DB |
| Cache | Redis | Sub-millisecond reads for the hot path of live tick delivery |
| LLM inference | Groq (LLaMA 3 70B) | Extremely low latency (sub-100ms first token) suits interactive trade reasoning |
| Grounded research | Perplexity Sonar | Provides web-current macro context that a static corpus cannot |
| Charting | Recharts | React-native rendering integrates cleanly with component state; sufficient for candlestick + overlays |
| 3D visuals | Three.js | Delivers the differentiated "command center" aesthetic without a heavier engine |

---

## 5. Data Requirements

### 5.1 Logical Data Model

**Core entities and relationships:**

```
users (Supabase auth.users)
  │
  ├──< watchlists ──< watchlist_pairs >── currency_pairs
  │
  ├──< paper_accounts ──< positions >── currency_pairs
  │                   └──< trades
  │
  └──< alerts >── currency_pairs

currency_pairs ──< candles
               └──< indicator_snapshots

news_documents ──< document_chunks (with vector embeddings)
               └──< sentiment_scores >── currencies

economic_events
```

### 5.2 Key Table Specifications

**`currency_pairs`**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `uuid` | PK | Primary key |
| `symbol` | `text` | UNIQUE, NOT NULL | e.g. `EUR_USD` |
| `base_currency` | `char(3)` | NOT NULL | e.g. `EUR` |
| `quote_currency` | `char(3)` | NOT NULL | e.g. `USD` |
| `pip_decimal_places` | `smallint` | NOT NULL | 4 for standard, 2 for JPY pairs |
| `category` | `text` | CHECK IN (major, minor, exotic) | Classification |
| `is_active` | `boolean` | DEFAULT true | Whether streaming is enabled |

**`candles`**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `bigserial` | PK | Primary key |
| `pair_id` | `uuid` | FK → currency_pairs | Associated pair |
| `timeframe` | `text` | CHECK IN (M1,M5,M15,M30,H1,H4,D1) | Candle interval |
| `open_time` | `timestamptz` | NOT NULL | Candle open timestamp (UTC) |
| `open` / `high` / `low` / `close` | `numeric(12,6)` | NOT NULL | OHLC prices |
| `volume` | `bigint` | NOT NULL | Tick volume |

*Composite unique index on `(pair_id, timeframe, open_time)`; BRIN index on `open_time` for time-range scans.*

**`positions`**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `uuid` | PK | Primary key |
| `account_id` | `uuid` | FK → paper_accounts | Owning account |
| `pair_id` | `uuid` | FK → currency_pairs | Traded pair |
| `direction` | `text` | CHECK IN (long, short) | Position side |
| `units` | `numeric(14,2)` | NOT NULL | Position size in base currency units |
| `entry_price` | `numeric(12,6)` | NOT NULL | Fill price |
| `stop_loss` / `take_profit` | `numeric(12,6)` | NULLABLE | Risk levels |
| `trailing_stop_pips` | `numeric(8,2)` | NULLABLE | Trailing distance |
| `opened_at` | `timestamptz` | NOT NULL | Open timestamp |
| `status` | `text` | CHECK IN (open, closed, liquidated) | Lifecycle state |

**`document_chunks`**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `uuid` | PK | Primary key |
| `document_id` | `uuid` | FK → news_documents | Parent document |
| `chunk_index` | `integer` | NOT NULL | Order within document |
| `content` | `text` | NOT NULL | Chunk text |
| `embedding` | `vector(1536)` | NOT NULL | OpenAI embedding |
| `token_count` | `integer` | NOT NULL | For context budgeting |

*HNSW index on `embedding` using cosine distance.*

### 5.3 Data Retention Policy

| Data Type | Retention | Rationale |
|---|---|---|
| M1 candles | 30 days | High volume; limited analytical value beyond short horizon |
| M5–M30 candles | 6 months | Supports intraday backtesting |
| H1/H4 candles | 2 years | Supports swing analysis |
| D1 candles | Indefinite | Low volume, high analytical value |
| News documents | 12 months | Balances RAG corpus richness against storage cost |
| Closed trades | Indefinite | User's permanent performance record |
| Redis tick cache | 60 seconds TTL | Hot path only |

### 5.4 Data Integrity Requirements

- **DI-1**: Candle OHLC values must satisfy `low ≤ open ≤ high` and `low ≤ close ≤ high`; violating records shall be rejected and logged
- **DI-2**: No duplicate candles shall exist for the same `(pair, timeframe, open_time)` tuple
- **DI-3**: Position `units` must be non-zero; closed positions must have a recorded exit price
- **DI-4**: Account equity must equal `balance + sum(floating P&L of open positions)` at all times
- **DI-5**: All monetary and price values shall use fixed-precision `numeric` types, never floating-point, to avoid rounding drift

---

## 6. AI/ML Subsystem Specification

### 6.1 RAG Pipeline

**6.1.1 Ingestion**

| Step | Specification |
|---|---|
| Sources | NewsAPI (Forex category), Reuters/Bloomberg RSS, Federal Reserve, ECB, RBI, BoE, BoJ publication feeds |
| Frequency | Every 30 minutes during market hours; hourly on weekends |
| Deduplication | SHA-256 hash of normalized title + first 200 characters |
| Chunking | Recursive character splitting, 800-token chunks with 100-token overlap, respecting paragraph boundaries |
| Embedding model | OpenAI `text-embedding-3-small` (1536 dimensions) |
| Storage | `document_chunks` table with `pgvector` HNSW index |

**6.1.2 Retrieval**

| Parameter | Value |
|---|---|
| Similarity metric | Cosine distance |
| Initial retrieval | Top-20 chunks |
| Reranking | Cross-encoder rerank to top-5 |
| Recency weighting | Score multiplied by exponential decay, half-life 72 hours |
| Minimum relevance threshold | Cosine similarity ≥ 0.72; below this, the system reports insufficient context |

**6.1.3 Generation**

| Parameter | Value |
|---|---|
| Model | Groq LLaMA 3 70B (primary), Perplexity Sonar (for web-current macro queries) |
| Temperature | 0.2 (low, to prioritize factual consistency) |
| Max output tokens | 800 |
| System prompt constraints | Must cite sources by index; must state uncertainty explicitly; must not provide financial advice or specific trade recommendations |

**6.1.4 Requirements**

| ID | Requirement |
|---|---|
| **AI-1.1** | The RAG pipeline shall return answers grounded only in retrieved context; ungrounded generation is a defect |
| **AI-1.2** | Every factual claim in an AI answer shall map to at least one retrieved chunk |
| **AI-1.3** | When retrieval returns no chunk above the relevance threshold, the system shall respond that it lacks sufficient information rather than generating an answer |
| **AI-1.4** | The pipeline shall log every query, retrieved chunk IDs, and generated response for evaluation and audit |

### 6.2 Sentiment Analysis Engine

| Aspect | Specification |
|---|---|
| Model | `ProsusAI/finbert` (BERT-base fine-tuned on financial corpora) |
| Input | News headline + first 100 words of body |
| Output classes | Positive (bullish), Negative (bearish), Neutral — with confidence scores |
| Currency attribution | Named entity matching against currency and country lexicon; a headline may affect multiple currencies |
| Aggregation | Per-currency hourly score = confidence-weighted mean of classifications, normalized to [−1.0, +1.0] |
| Inference | Batched, CPU-based (batch size 32); ~40ms per headline |

| ID | Requirement |
|---|---|
| **AI-2.1** | Sentiment classification shall achieve ≥ 80% agreement with manual labels on a held-out set of 200 Forex headlines |
| **AI-2.2** | Headlines that mention no identifiable currency shall be excluded from aggregation rather than assigned to a default |
| **AI-2.3** | Aggregate sentiment scores shall be recomputed at least hourly during market hours |

### 6.3 Composite Signal Generation

The directional bias signal is a **rule-based ensemble** over computed indicators, deliberately chosen over a black-box model for explainability.

| Indicator | Bullish Condition | Bearish Condition | Weight |
|---|---|---|---|
| EMA-9 vs EMA-21 | EMA-9 > EMA-21 | EMA-9 < EMA-21 | 0.25 |
| Price vs SMA-200 | Close > SMA-200 | Close < SMA-200 | 0.20 |
| MACD histogram | Histogram > 0 and rising | Histogram < 0 and falling | 0.20 |
| RSI-14 | 50 < RSI < 70 | 30 < RSI < 50 | 0.15 |
| Bollinger position | Close in upper half | Close in lower half | 0.10 |
| Sentiment score | Score > +0.2 | Score < −0.2 | 0.10 |

**Composite score** = Σ (weight × direction), where direction ∈ {+1, 0, −1}

| Score Range | Label |
|---|---|
| ≥ +0.6 | Strong Bullish |
| +0.2 to +0.6 | Bullish |
| −0.2 to +0.2 | Neutral |
| −0.6 to −0.2 | Bearish |
| ≤ −0.6 | Strong Bearish |

| ID | Requirement |
|---|---|
| **AI-3.1** | The system shall display the individual indicator contributions alongside every composite signal |
| **AI-3.2** | The system shall never present a signal as a trade recommendation; labels describe market state only |
| **AI-3.3** | Signal weights shall be stored in configuration, not hardcoded, to permit tuning without redeployment |

### 6.4 Responsible AI Requirements

| ID | Requirement |
|---|---|
| **AI-4.1** | Every AI-generated output shall carry a visible disclaimer that it is informational and not financial advice |
| **AI-4.2** | The system shall not generate specific trade recommendations (entry price, position size, or "buy now" instructions) |
| **AI-4.3** | The system shall not make price predictions presented as certainties; probabilistic framing is required where forecasts appear |
| **AI-4.4** | Model provenance (which model produced an output) shall be recorded and displayable on request |
| **AI-4.5** | User queries sent to third-party LLM providers shall be logged with a notice in the privacy policy |

---

## 7. External Interface Requirements

### 7.1 User Interfaces

| Screen | Key Elements |
|---|---|
| **Dashboard** | Live pair grid with price/spread/change, session clock, sentiment heatmap, open positions summary, alert feed |
| **Chart View** | Full-screen candlestick chart, timeframe selector, indicator panel, drawing tools, composite bias badge |
| **AI Assistant** | Chat interface, citation cards, suggested question chips, model attribution |
| **Paper Trading** | Order ticket (pair, direction, size, leverage, SL/TP), open positions table, account metrics panel |
| **Analytics** | Equity curve, performance metrics grid, pair breakdown, session breakdown |
| **Economic Calendar** | Event list with date/time/impact/consensus, AI briefing expander |
| **Settings** | Profile, watchlists, alert management, account reset, theme |

**UI Requirements:**

| ID | Requirement |
|---|---|
| **UI-1** | All screens shall be responsive across viewport widths from 360px to 2560px |
| **UI-2** | The interface shall meet WCAG 2.1 Level AA contrast requirements |
| **UI-3** | All interactive elements shall be keyboard-navigable with visible focus indicators |
| **UI-4** | Price changes shall be indicated by color (green up, red down) *and* directional arrow, never color alone |
| **UI-5** | Loading states shall use skeleton placeholders rather than blocking spinners for data-heavy views |

### 7.2 Software Interfaces

| Interface | Protocol | Purpose | Failure Handling |
|---|---|---|---|
| **OANDA v20 Streaming** | HTTPS chunked / WSS | Live bid-ask ticks | Exponential backoff reconnect; fall back to REST polling at 5s intervals |
| **OANDA v20 REST** | HTTPS REST | Historical candles, instrument metadata | Retry 3× with backoff; serve cached data on persistent failure |
| **NewsAPI** | HTTPS REST | Forex news articles | Skip cycle and log; RSS feeds serve as partial fallback |
| **Groq API** | HTTPS REST | LLM inference | Fall back to a smaller model; if unavailable, return graceful degradation message |
| **Perplexity API** | HTTPS REST | Web-grounded macro research | Optional enhancement; failure does not block core RAG |
| **OpenAI Embeddings** | HTTPS REST | Vector generation | Queue for retry; ingestion is asynchronous and tolerant of delay |
| **Supabase** | HTTPS REST / PostgREST | Data persistence and auth | Connection pool with retry; health check endpoint |
| **Resend** | HTTPS REST | Transactional email for alerts | Queue with retry; in-app notification is the guaranteed channel |

### 7.3 Communication Interfaces

| ID | Requirement |
|---|---|
| **CI-1** | All client-server communication shall use HTTPS (TLS 1.3) |
| **CI-2** | Real-time price delivery shall use WebSocket (WSS) with automatic reconnection |
| **CI-3** | The WebSocket protocol shall implement heartbeat ping/pong at 30-second intervals to detect stale connections |
| **CI-4** | REST API responses shall use JSON with a consistent envelope: `{ data, error, meta }` |
| **CI-5** | The API shall version endpoints under `/api/v1/` to permit non-breaking evolution |

---

## 8. Non-Functional Requirements

### 8.1 Performance Requirements

| ID | Requirement | Target |
|---|---|---|
| **NFR-P1** | Live price update latency from OANDA tick to browser render | < 500 ms (p95) |
| **NFR-P2** | Dashboard initial page load (Largest Contentful Paint) | < 2.5 s on 4G |
| **NFR-P3** | Technical indicator recomputation after candle close | < 2 s |
| **NFR-P4** | RAG query end-to-end response time | < 5 s (p95) |
| **NFR-P5** | Paper trade order execution acknowledgement | < 300 ms |
| **NFR-P6** | Historical chart data fetch (1 year of D1 candles) | < 1 s |
| **NFR-P7** | Concurrent WebSocket connections supported | ≥ 200 |
| **NFR-P8** | Database query p95 latency | < 100 ms |

### 8.2 Security Requirements

| ID | Requirement |
|---|---|
| **NFR-S1** | Passwords shall be hashed using bcrypt (cost factor ≥ 12); plaintext passwords shall never be stored or logged |
| **NFR-S2** | All API keys and secrets shall be stored in environment variables, never committed to version control |
| **NFR-S3** | PostgreSQL Row Level Security shall be enabled on all user-scoped tables with policies verified by test |
| **NFR-S4** | JWT access tokens shall expire within 1 hour; refresh tokens within 30 days |
| **NFR-S5** | All API endpoints shall be rate-limited: 100 requests/minute per authenticated user, 20/minute per IP for unauthenticated |
| **NFR-S6** | User input shall be validated server-side using Pydantic schemas; client validation is convenience only |
| **NFR-S7** | The system shall set security headers: `Content-Security-Policy`, `X-Frame-Options: DENY`, `Strict-Transport-Security` |
| **NFR-S8** | Dependency vulnerabilities shall be scanned on every CI run; high-severity findings block merge |
| **NFR-S9** | The system shall never request, store, or transmit real broker credentials or payment information |

### 8.3 Reliability & Availability

| ID | Requirement |
|---|---|
| **NFR-R1** | The system shall target 99.0% uptime during Forex market hours |
| **NFR-R2** | Loss of the OANDA connection shall not crash the application; the UI shall display a clear degraded-mode indicator |
| **NFR-R3** | Failure of the AI subsystem shall not impair market data, charting, or paper trading functionality |
| **NFR-R4** | The system shall recover automatically from transient upstream failures without manual intervention |
| **NFR-R5** | Database backups shall be taken daily with 7-day retention |

### 8.4 Usability Requirements

| ID | Requirement |
|---|---|
| **NFR-U1** | A first-time user shall be able to place a paper trade within 3 minutes without external documentation |
| **NFR-U2** | An in-app glossary shall define every Forex term used in the interface |
| **NFR-U3** | Error messages shall state what went wrong and what the user can do, in plain language |
| **NFR-U4** | Destructive actions (account reset, alert deletion) shall require explicit confirmation |

### 8.5 Maintainability Requirements

| ID | Requirement |
|---|---|
| **NFR-M1** | Backend code shall maintain ≥ 70% unit test coverage |
| **NFR-M2** | All public functions shall carry type annotations and docstrings |
| **NFR-M3** | Code shall pass `ruff` (Python) and `eslint` + `tsc --strict` (TypeScript) with zero errors |
| **NFR-M4** | Database schema changes shall be applied via versioned migration files, never manual edits |
| **NFR-M5** | Structured JSON logging shall be used throughout, with correlation IDs propagated across service boundaries |

### 8.6 Portability & Scalability

| ID | Requirement |
|---|---|
| **NFR-X1** | The backend shall be containerized (Docker) for host-agnostic deployment |
| **NFR-X2** | The application shall be stateless at the service layer, permitting horizontal scaling |
| **NFR-X3** | The system shall support adding new currency pairs through configuration without code changes |
| **NFR-X4** | The frontend shall function correctly on the four target browsers without browser-specific code paths |

### 8.7 Legal & Compliance Requirements

| ID | Requirement |
|---|---|
| **NFR-L1** | The platform shall display a prominent disclaimer that it provides informational content only and is not investment advice |
| **NFR-L2** | The platform shall not be represented as SEBI-registered or as an investment advisory service |
| **NFR-L3** | A privacy policy shall disclose all third-party data processors including LLM providers |
| **NFR-L4** | Users shall be able to request deletion of their account and associated data |
| **NFR-L5** | Third-party data usage shall comply with each provider's terms of service, including attribution where required |

---

## 9. System Models

### 9.1 Primary Use Cases

**UC-1: Analyze a Currency Pair**

| Field | Detail |
|---|---|
| **Actor** | Retail Trader |
| **Precondition** | User is authenticated; market is open |
| **Main Flow** | 1. User selects a pair from watchlist → 2. System loads chart with default H1 timeframe → 3. System displays live price, spread, and composite bias → 4. User toggles indicator overlays → 5. System renders indicators and highlights active signal conditions → 6. User reviews sentiment score and recent news for the pair |
| **Postcondition** | User has an informed view of current market state for the pair |
| **Alternate Flow** | If streaming is unavailable, system displays last-known price with staleness badge and continues to serve historical chart data |

**UC-2: Query the AI Assistant**

| Field | Detail |
|---|---|
| **Actor** | Retail Trader |
| **Precondition** | User is authenticated |
| **Main Flow** | 1. User enters a natural language question → 2. System embeds the query → 3. System retrieves top-K relevant chunks from the vector store → 4. System reranks and filters by relevance threshold → 5. System generates an answer with citations via LLM → 6. System displays answer with source cards and disclaimer |
| **Postcondition** | User receives a grounded, cited answer |
| **Alternate Flow** | If no chunk exceeds the relevance threshold, system responds that it lacks sufficient information and suggests rephrasing |

**UC-3: Place and Manage a Paper Trade**

| Field | Detail |
|---|---|
| **Actor** | Retail Trader |
| **Precondition** | User has an active paper account with sufficient free margin |
| **Main Flow** | 1. User opens order ticket → 2. User selects pair, direction, lot size, leverage → 3. System computes and displays required margin and pip value → 4. User optionally sets SL/TP → 5. User submits → 6. System validates margin sufficiency → 7. System fills at current bid/ask including spread → 8. System creates position and updates account metrics |
| **Postcondition** | Position is open; floating P&L updates in real time |
| **Alternate Flow** | If free margin is insufficient, system rejects the order with a clear explanation of the shortfall |

**UC-4: Configure and Receive an Alert**

| Field | Detail |
|---|---|
| **Actor** | Retail Trader |
| **Precondition** | User is authenticated and has fewer than 50 active alerts |
| **Main Flow** | 1. User selects a pair and alert type → 2. User sets threshold parameters → 3. System validates and persists the alert → 4. Alert Service evaluates the condition on each relevant update → 5. On trigger, system dispatches in-app notification and email → 6. System marks the alert as triggered |
| **Postcondition** | User is notified; alert is either disabled or rearmed per configuration |

### 9.2 State Model — Paper Trading Position

```
        ┌─────────┐
        │ PENDING │  (limit/stop order awaiting fill)
        └────┬────┘
             │ price condition met
             ▼
        ┌─────────┐
   ┌───►│  OPEN   │◄──── SL/TP modified
   │    └────┬────┘
   │         │
   │    ┌────┴──────────────┬────────────────┐
   │    │                   │                │
   │    ▼                   ▼                ▼
   │ ┌────────┐      ┌────────────┐   ┌─────────────┐
   │ │ CLOSED │      │ SL/TP HIT  │   │ LIQUIDATED  │
   │ │(manual)│      │  (auto)    │   │(margin call)│
   │ └────────┘      └────────────┘   └─────────────┘
   │                        │
   └────────────────────────┘
      trailing stop adjusts
```

### 9.3 Data Flow — Real-Time Price Pipeline

```
OANDA Stream
     │ raw tick {instrument, bid, ask, time}
     ▼
Market Service — normalize & validate
     │
     ├──► Redis (SET pair:latest, TTL 60s)
     │
     ├──► Candle Aggregator ──► on close ──► Supabase candles table
     │                                            │
     │                                            ▼
     │                                    Analysis Service
     │                                    compute indicators
     │                                            │
     │                                            ▼
     │                                    indicator_snapshots
     │                                            │
     ├──► WebSocket Broadcast ◄───────────────────┘
     │         │
     │         ▼
     │    Connected Clients (browser)
     │
     └──► Alert Service — evaluate conditions ──► notifications
```

---

## 10. Testing & Validation Strategy

### 10.1 Test Levels

| Level | Scope | Tooling | Coverage Target |
|---|---|---|---|
| **Unit** | Individual functions: pip calculation, indicator math, margin computation | Pytest, Vitest | ≥ 70% |
| **Integration** | Service-to-service and service-to-database interactions | Pytest + test Postgres container | Key flows |
| **API** | Endpoint contracts, auth, validation, error handling | Pytest + httpx | 100% of endpoints |
| **End-to-End** | Full user journeys through the browser | Playwright | Critical paths |
| **Performance** | Latency and concurrency under load | Locust | NFR-P targets |
| **Security** | RLS enforcement, injection, auth bypass | Manual + `bandit` + `npm audit` | All user-scoped tables |

### 10.2 Critical Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| **TC-1** | Compute pip value for USD/JPY (2-decimal pair) at 0.1 lot | Correct JPY-adjusted pip value, not standard 4-decimal value |
| **TC-2** | Open position exceeding available margin | Order rejected with explicit margin shortfall message |
| **TC-3** | Margin level falls below 50% | Positions auto-liquidated; account state consistent |
| **TC-4** | User A attempts to read User B's trades via direct API call | Request denied by RLS policy |
| **TC-5** | RAG query with no relevant corpus content | System states insufficient information; no fabricated answer |
| **TC-6** | OANDA stream disconnects mid-session | UI shows degraded indicator; reconnect succeeds; no data loss in candles |
| **TC-7** | Candle with `high < low` received from upstream | Record rejected and logged; not persisted |
| **TC-8** | 200 concurrent WebSocket clients | All receive updates within NFR-P1 latency target |
| **TC-9** | Trailing stop with price moving favorably then reversing | Stop trails correctly; triggers at expected level |
| **TC-10** | FinBERT classification on 200-headline labeled set | ≥ 80% agreement with manual labels |

### 10.3 Acceptance Criteria

The system shall be considered acceptable for internship demonstration when:

1. All **Must** priority functional requirements are implemented and pass their test cases
2. All NFR-P performance targets are met under a 100-concurrent-user load test
3. All NFR-S security requirements are verified, with RLS confirmed by adversarial test
4. Zero high-severity dependency vulnerabilities remain open
5. End-to-end tests pass for all four critical user journeys (UC-1 through UC-4)
6. The application is deployed and publicly accessible at a stable URL
7. Documentation (this SRS, API reference, README) is complete and current

---

## 11. Deployment & Operations

### 11.1 Environments

| Environment | Purpose | Data | Deployment Trigger |
|---|---|---|---|
| **Local** | Development | Seeded sample data | Manual |
| **Preview** | PR review | Anonymized snapshot | Automatic on pull request |
| **Production** | Live use | Real market data | Automatic on merge to `main` |

### 11.2 CI/CD Pipeline

```
Push / Pull Request
    │
    ├─► Lint      (ruff · eslint · tsc --strict)
    ├─► Unit Test (pytest · vitest)
    ├─► Security  (bandit · npm audit)
    │
    └─► [all pass] ─► Build ─► Preview Deploy
                                    │
                          [merge to main]
                                    │
                                    ├─► Run migrations
                                    ├─► Deploy backend  (Railway)
                                    ├─► Deploy frontend (Vercel)
                                    └─► Smoke tests ─► [fail] ─► Auto-rollback
```

### 11.3 Monitoring & Observability

| Signal | Metric | Alert Threshold |
|---|---|---|
| **Availability** | Uptime percentage | < 99% over rolling 24h |
| **Latency** | API p95 response time | > 1 s sustained 5 min |
| **Stream health** | Seconds since last OANDA tick | > 30 s during market hours |
| **Error rate** | 5xx responses as % of total | > 1% over 5 min |
| **AI subsystem** | RAG query failure rate | > 5% over 15 min |
| **Database** | Connection pool utilization | > 80% |
| **Cost** | Daily LLM API spend | > budgeted daily ceiling |

### 11.4 Operational Runbook Summary

| Incident | First Response |
|---|---|
| OANDA stream down | Verify provider status; confirm fallback polling active; notify users via status banner |
| LLM provider outage | Confirm graceful degradation; disable AI features via feature flag if errors surface to users |
| Database connection exhaustion | Check for long-running queries; restart pool; scale connection limit |
| Elevated 5xx rate | Check recent deploys; roll back if correlated; inspect structured logs by correlation ID |

---

## 12. Constraints, Assumptions & Dependencies

### 12.1 Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Paper trading uses simplified fill logic (no slippage or partial fills) | Simulated results may be optimistic versus live trading | Documented prominently in the UI; slippage modeling listed as future work |
| Free-tier API rate limits | Constrains number of simultaneously streamed pairs | Prioritized pair list; Redis caching to reduce redundant calls |
| RAG corpus limited to publicly accessible sources | Cannot include premium research or proprietary analysis | Framed as a general market intelligence tool, not institutional research |
| No backtesting engine in v1.0 | Users cannot validate strategies on historical data | Listed as the highest-priority future enhancement |
| Sentiment attribution via lexicon matching | May miss indirect currency implications | Manual evaluation set used to measure and document accuracy |

### 12.2 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| OANDA changes API terms or pricing | Medium | High | Abstract the data provider behind an interface; evaluate Twelve Data and Polygon as alternates |
| LLM costs exceed budget | Medium | Medium | Aggressive response caching; strict token limits; usage monitoring with alerts |
| Free-tier hosting limits exceeded | Medium | Medium | Monitor usage; architecture supports migration to paid tiers without redesign |
| Scope creep beyond 16-week timeline | High | High | Strict Must/Should/Could prioritization; Should and Could items deferred without renegotiation |
| Users treat informational signals as advice | Medium | High | Persistent disclaimers; explicit refusal to generate trade recommendations |

---

## 13. Future Enhancements

Deferred beyond v1.0, in rough priority order:

| ID | Enhancement | Rationale |
|---|---|---|
| **FE-1** | **Backtesting engine** — test custom rule-based strategies against 10+ years of historical data with Sharpe ratio, max drawdown, and win rate output | Highest user value; validates whether signals have historical merit |
| **FE-2** | **Live broker integration** — OANDA or Interactive Brokers order execution with mandatory confirmation gates | Natural progression from paper trading; requires substantial risk-control work |
| **FE-3** | **Multi-agent analysis system** — LangGraph agents specializing in technical analysis, macro research, and risk assessment, collaborating on a unified view | Improves depth of analysis beyond single-model reasoning |
| **FE-4** | **ML price forecasting** — LSTM and temporal fusion transformer models for probabilistic short-horizon forecasts with confidence intervals | Adds predictive capability; must be framed probabilistically |
| **FE-5** | **Forex options and futures** — options chain, implied volatility surface, USD/INR futures on NSE | Expands addressable instruments |
| **FE-6** | **Native mobile applications** — React Native apps with push notification alerts | Meets traders where they are; alerts benefit most from push |
| **FE-7** | **Social and copy trading** — public trade journals, leaderboards, strategy following | Community growth lever; significant moderation and compliance overhead |
| **FE-8** | **SaaS commercialization** — tiered subscription plans for retail traders, prop firms, and educational institutions | Path to sustainability beyond the internship |

---

## 14. Appendices

### Appendix A — Currency Pairs in Scope

| Symbol | Name | Category | Pip Decimal |
|---|---|---|---|
| EUR/USD | Euro / US Dollar | Major | 4 |
| GBP/USD | British Pound / US Dollar | Major | 4 |
| USD/JPY | US Dollar / Japanese Yen | Major | 2 |
| USD/CHF | US Dollar / Swiss Franc | Major | 4 |
| AUD/USD | Australian Dollar / US Dollar | Major | 4 |
| NZD/USD | New Zealand Dollar / US Dollar | Major | 4 |
| USD/CAD | US Dollar / Canadian Dollar | Major | 4 |
| EUR/GBP | Euro / British Pound | Minor | 4 |
| EUR/JPY | Euro / Japanese Yen | Minor | 2 |
| GBP/JPY | British Pound / Japanese Yen | Minor | 2 |
| AUD/JPY | Australian Dollar / Japanese Yen | Minor | 2 |
| EUR/AUD | Euro / Australian Dollar | Minor | 4 |
| USD/INR | US Dollar / Indian Rupee | Exotic | 4 |
| USD/SGD | US Dollar / Singapore Dollar | Exotic | 4 |
| USD/MXN | US Dollar / Mexican Peso | Exotic | 4 |

### Appendix B — Forex Trading Sessions (UTC)

| Session | Open | Close | Characteristics |
|---|---|---|---|
| Sydney | 21:00 | 06:00 | Lower volatility; AUD/NZD pairs most active |
| Tokyo | 00:00 | 09:00 | JPY pairs active; range-bound tendency |
| London | 07:00 | 16:00 | Highest volume globally; EUR/GBP pairs most active |
| New York | 12:00 | 21:00 | High volatility; USD pairs dominant |
| **London–NY Overlap** | **12:00** | **16:00** | **Peak liquidity and volatility window** |

### Appendix C — Requirements Traceability Matrix (Excerpt)

| Requirement | Objective Served | Component | Test Case |
|---|---|---|---|
| FR-1.1 | Real-time market data access | Market Service | TC-6, TC-8 |
| FR-2.10 | Automated technical analysis | Analysis Service | Indicator unit tests |
| FR-3.2 | AI-powered market intelligence | RAG Pipeline | TC-5 |
| FR-3.6 | Sentiment-driven insight | Sentiment Engine | TC-10 |
| FR-4.6 | Realistic trade simulation | Trading Service | TC-1 |
| FR-4.12 | Risk management education | Trading Service | TC-3 |
| FR-6.4 | Data isolation and privacy | Auth Service | TC-4 |
| NFR-P1 | Responsive real-time experience | Market Service, WebSocket | TC-8 |

### Appendix D — Glossary of Technical Indicators

| Indicator | Formula Summary | Interpretation |
|---|---|---|
| **RSI (14)** | `100 − 100/(1 + avg gain/avg loss)` over 14 periods | > 70 overbought, < 30 oversold |
| **MACD (12,26,9)** | `EMA(12) − EMA(26)`; signal = `EMA(9)` of MACD | Crossovers signal momentum shifts |
| **Bollinger Bands (20,2)** | `SMA(20) ± 2σ` | Band squeeze precedes volatility expansion |
| **ATR (14)** | Moving average of true range over 14 periods | Higher values indicate higher volatility |
| **EMA (n)** | Exponentially weighted moving average | Faster response to recent price than SMA |
| **Fibonacci Retracement** | Swing high/low × {0.236, 0.382, 0.5, 0.618, 0.786} | Potential support/resistance levels |

### Appendix E — Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 0.1 | June 2026 | Prince Jivani | Initial draft — scope and functional requirements |
| 0.2 | July 2026 | Prince Jivani | Added AI/ML subsystem specification and data model |
| 1.0 | August 2026 | Prince Jivani | Complete SRS with NFRs, testing strategy, and deployment specification |

### Appendix F — Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Student / Author | Prince Jivani | | |
| Industry Mentor (ThinkNovus) | _To be completed_ | | |
| Institute Mentor | _To be completed_ | | |

---

**Disclaimer:** Tradly is an educational and informational platform developed as an academic internship project. It does not provide investment advice, does not execute real trades, and is not registered with SEBI or any financial regulatory authority. Forex trading carries substantial risk of loss.

---

*End of Document — Software Requirements Specification v1.0*
