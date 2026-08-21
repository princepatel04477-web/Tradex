# Tradly — Month 2 Internship & University Project Progress Report

---

| Field | Detail |
|---|---|
| **Document Title** | Month 2 Project Progress Report — Tradly AI/ML Forex Platform |
| **Student Name** | Prince Jivani |
| **Enrollment Number** | 23SE02CS030 |
| **Program** | B.Tech Computer Science Engineering (AI/ML Specialization) |
| **Semester** | 7th Semester (2025–26) |
| **Host Organization** | ThinkNovus Private Limited |
| **Role** | AI/ML Engineer (Intern) |
| **Internship Duration** | June 2026 – October 2026 |
| **Reporting Period** | Month 2 (July 2026 – August 2026) |
| **Academic Supervisor** | Institute Faculty Mentor |
| **Industry Supervisor** | ThinkNovus Industry Mentor |
| **Submission Date** | August 7, 2026 |

---

## Executive Summary

During the second month of the industry internship at ThinkNovus Private Limited, the technical core and user interface of **Tradly**—an AI/ML-Powered Forex Market Intelligence & Algorithmic Trading Platform—were successfully designed, implemented, and verified. 

Following the Software Requirements Specification (IEEE Std 830-1998 standard), the primary milestones achieved in Month 2 include:
1. **Real-time Market Data & Streaming Engine**: Implemented tick stream normalization and multi-timeframe OHLCV candle aggregation (M1 to D1) for 15 currency pairs (majors, minors, and exotics) with a live Forex Market Session Clock tracking Sydney, Tokyo, London, and New York sessions.
2. **Technical Analysis Subsystem**: Developed a rule-based composite directional bias engine utilizing RSI (14), MACD (12,26,9), Bollinger Bands (20,2), ATR (14), EMAs (9,21,50), SMA (200), and Fibonacci levels, delivering explainable market bias labels (*Strong Bullish* to *Strong Bearish*).
3. **AI Intelligence & RAG Subsystem**: Integrated a Grounded Retrieval-Augmented Generation (RAG) assistant with citation cards, refusal fallback when similarity threshold (< 0.65) is unmet, FinBERT sentiment scoring (-1.0 to +1.0 per currency), and an Economic Calendar with AI pre-event volatility briefings.
4. **Pip-Accurate Paper Trading Simulator**: Engineered a paper execution engine with $10,000 virtual balance, custom lot sizing (1.0 Standard, 0.1 Mini, 0.01 Micro), leverage options (1:1 to 1:100), JPY 2-decimal vs 4-decimal pip value calculations, and risk controls (auto-liquidation when margin level falls below 50%).
5. **Next.js 14 Web Application**: Scaffolded and built 5 responsive views (Command Center with 3D Three.js FX Globe, Interactive SVG Candlestick Chart with indicator overlays, RAG Chat, Paper Trading Ticket, and Analytics/Trade Journal).

---

## Table of Contents

1. [Introduction & Month 2 Objectives](#1-introduction--month-2-objectives)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Subsystem Implementation Details](#3-subsystem-implementation-details)
   - 3.1 Market Data & Session Streaming Engine
   - 3.2 Technical Analysis & Composite Bias Calculator
   - 3.3 RAG Subsystem & FinBERT Sentiment Analysis
   - 3.4 Paper Trading & Risk Execution Engine
   - 3.5 Web User Interface & Visualizations
4. [Testing, Verification & Validation Results](#4-testing-verification--validation-results)
5. [Summary of Deliverables vs Schedule](#5-summary-of-deliverables-vs-schedule)
6. [Future Plan for Month 3 & Month 4](#6-future-plan-for-month-3--month-4)
7. [References & Appendix](#7-references--appendix)

---

## 1. Introduction & Month 2 Objectives

### 1.1 Project Purpose
The primary objective of **Tradly** is to provide retail Forex traders with institutional-grade market intelligence, machine learning sentiment insights, and risk-controlled paper trading tools without requiring live capital deployment.

### 1.2 Month 2 Key Objectives
- Complete the backend service scaffold using **FastAPI** (Python 3.11+).
- Implement real-time WebSocket tick delivery and OHLCV candle aggregation logic.
- Implement technical indicator algorithms using `numpy` and `pandas`.
- Build the RAG query processor with strict grounding constraints and source citation formatting.
- Construct the paper execution pipeline with margin metric calculations and auto-liquidation logic.
- Build the frontend user interface in **Next.js 14 (App Router)** with **TypeScript** and **Tailwind CSS**.
- Conduct automated unit and integration tests using `pytest` and Next.js static production build verification.

---

## 2. System Architecture Overview

Tradly is architected as a layered full-stack application:

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│   Next.js 14 App Router · TypeScript · Tailwind CSS             │
│   Three.js 3D FX Globe · Recharts · Interactive SVG Candlesticks│
└────────────────────────────────▲────────────────────────────────┘
                                 │ REST (HTTPS) + WebSocket (WSS)
┌────────────────────────────────▼────────────────────────────────┐
│                     APPLICATION LAYER                           │
│   FastAPI Async Backend (Python 3.11)                           │
│   ┌────────────┬─────────────┬─────────────┬──────────────────┐ │
│   │ Market     │ Analysis    │ Trading     │ AI / RAG         │ │
│   │ Service    │ Service     │ Service     │ Service          │ │
│   └────────────┴─────────────┴─────────────┴──────────────────┘ │
└────────────────────────────────▲────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                     INTELLIGENCE & DATA LAYER                   │
│   RAG Vector Corpus · FinBERT Sentiment · Technical Analysis     │
│   SQLite / PostgreSQL + pgvector · Redis Tick Cache             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Subsystem Implementation Details

### 3.1 Market Data & Session Streaming Engine (`backend/app/services/market_service.py`)
The system maintains tracking and real-time simulation for 15 currency pairs:
- **Majors**: EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, NZD/USD, USD/CAD
- **Minors**: EUR/GBP, EUR/JPY, GBP/JPY, AUD/JPY, EUR/AUD
- **Exotics**: USD/INR, USD/SGD, USD/MXN

**Forex Market Session Tracking:**
- **Sydney**: 21:00 – 06:00 UTC
- **Tokyo**: 00:00 – 09:00 UTC
- **London**: 07:00 – 16:00 UTC
- **New York**: 12:00 – 21:00 UTC
- **London-NY Overlap**: 12:00 – 16:00 UTC (Peak global liquidity window highlighted dynamically in the UI).

### 3.2 Technical Analysis & Composite Bias Calculator (`backend/app/services/analysis_service.py`)
Computes indicators across multiple timeframes (`M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`):
1. **Relative Strength Index (RSI-14)**: Momentum oscillator identifying overbought (>70) and oversold (<30) market conditions.
2. **MACD (12, 26, 9)**: Moving Average Convergence Divergence line, signal line, histogram, and bullish/bearish crossover detection.
3. **Bollinger Bands (20, 2)**: Upper/lower volatility bands and squeeze condition detector.
4. **Moving Averages**: EMA-9, EMA-21, EMA-50, and SMA-200 baseline.
5. **Fibonacci Retracements**: 23.6%, 38.2%, 50.0%, 61.8%, 78.6% levels based on recent swing points.

**Composite Bias Formula (SRS 6.3):**
$$\text{Composite Score} = \sum (\text{Weight}_i \times \text{Direction}_i)$$

Where weights are assigned as:
- EMA-9 vs EMA-21: 0.25
- Price vs SMA-200: 0.20
- MACD Histogram: 0.20
- RSI-14: 0.15
- Bollinger Position: 0.10
- Global News Sentiment: 0.10

Scores map to market labels:
- $\ge +0.6$: **Strong Bullish**
- $+0.2 \text{ to } +0.6$: **Bullish**
- $-0.2 \text{ to } +0.2$: **Neutral**
- $-0.6 \text{ to } -0.2$: **Bearish**
- $\le -0.6$: **Strong Bearish**

### 3.3 RAG Subsystem & FinBERT Sentiment Analysis (`backend/app/services/ai_service.py`)
- **Grounded RAG Assistant**: Ingests central bank communications and financial news. Employs vector similarity scoring. Returns answers with clickable source cards.
- **Refusal Fallback (AI-1.3)**: If context similarity score $< 0.65$, the assistant explicitly refuses to generate speculative claims, stating context insufficiency.
- **FinBERT Sentiment Classifier**: Scores currency sentiment on a scale from $-1.0$ (Strong Bearish) to $+1.0$ (Strong Bullish).
- **Economic Calendar**: Tracks high-impact events (e.g. Non-Farm Payrolls, CPI releases) with AI pre-event briefings and historical pip volatility estimates.

### 3.4 Paper Trading & Risk Execution Engine (`backend/app/services/trading_service.py`)
- **Virtual Account Balance**: Default $10,000 balance with reset capabilities.
- **Order Types**: Market, Limit, and Stop for Buy (Long) and Sell (Short) trades.
- **Lot Sizing**: 1.0 Standard (100,000 units), 0.1 Mini (10,000 units), 0.01 Micro (1,000 units).
- **Leverage Settings**: 1:1, 1:10, 1:30, 1:50, 1:100.
- **Pip Value Formula (FR-4.6)**:
  - For standard 4-decimal pairs (e.g. EUR/USD):
    $$\text{Pip Value} = \text{Units} \times 0.0001 = \$10.00 \text{ per standard lot}$$
  - For JPY 2-decimal pairs (e.g. USD/JPY):
    $$\text{Pip Value} = \frac{\text{Units} \times 0.01}{\text{USD/JPY Price}} \approx \$0.65 \text{ per 0.1 lot at 154.50}$$
- **Margin & Auto-Liquidation**:
  $$\text{Required Margin} = \frac{\text{Units} \times \text{Entry Price}}{\text{Leverage}}$$
  $$\text{Margin Level \%} = \left( \frac{\text{Equity}}{\text{Used Margin}} \right) \times 100$$
  If Margin Level falls below 50%, all active open positions are automatically liquidated to prevent negative balance debt.

### 3.5 Web User Interface (`frontend/src/app/`)
Built with Next.js 14, standard Tailwind CSS design system, Recharts, and Three.js:
1. **Command Center (`/`)**: Live streaming currency pair grid, 3D FX Liquidity Globe, AI Composite Bias cards, and quick execution ticket.
2. **Interactive Chart (`/chart`)**: Custom SVG Candlestick rendering (green/red wicks & bodies), timeframe buttons, 5 indicator overlays, active flag alerts, and CSV data export.
3. **AI Assistant (`/ai-assistant`)**: Natural language chat, source citation cards, FinBERT sentiment heatmap, economic calendar briefings, and persistent responsible AI disclaimers.
4. **Paper Trading Hub (`/paper-trading`)**: Complete execution ticket, account metrics bar (Balance, Equity, Used Margin, Free Margin, Margin Level %), open positions table, and manual close buttons.
5. **Analytics & Journal (`/analytics`)**: Interactive Equity Curve chart, Win Rate %, Profit Factor, Max Drawdown ($ & %), pair/session performance breakdowns, and free-text trade journal tagging.

---

## 4. Testing, Verification & Validation Results

### 4.1 Automated Backend Test Suite
Executed using `pytest` on the Python backend:

```bash
$env:PYTHONPATH="backend"; python -m pytest backend/tests/
```

**Results Summary:**

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
collected 6 items

backend/tests/test_ai_service.py ..                                      [ 33%]
backend/tests/test_paper_trading.py ..                                   [ 66%]
backend/tests/test_pip_calc.py ..                                        [100%]

============================== 6 passed in 0.40s ==============================
```

- **Test Case 1 (`test_pip_calc_jpy_pair`)**: Verified JPY 2-decimal pip value calculations differentiate correctly from 4-decimal standard pairs.
- **Test Case 2 (`test_insufficient_margin_rejection`)**: Verified orders exceeding free margin are rejected with explicit shortfall messages.
- **Test Case 3 (`test_margin_call_and_liquidation`)**: Verified positions are automatically closed when margin level drops below 50%.
- **Test Case 4 (`test_rag_query_with_context`)**: Verified grounded answer formatting and source citation inclusion.
- **Test Case 5 (`test_rag_query_insufficient_context`)**: Verified assistant refuses ungrounded questions when context similarity is low.

### 4.2 Frontend Production Build Verification
Executed Next.js production build:

```bash
npm run build
```

**Output:**
```
✓ Compiled successfully
✓ Linting and checking validity of types ...
✓ Generating static pages (8/8)
Finalizing page optimization ...

Route (app)                              Size     First Load JS
┌ ○ /                                    5.06 kB         100 kB
├ ○ /_not-found                          876 B          88.4 kB
├ ○ /ai-assistant                        4.72 kB        92.2 kB
├ ○ /analytics                           104 kB          192 kB
├ ○ /chart                               5.11 kB font    92.6 kB
└ ○ /paper-trading                       4.54 kB          92 kB
```

---

## 5. Summary of Deliverables vs Schedule

| Milestone / Task | Planned (Month 2) | Achieved Status | Remarks |
|---|---|---|---|
| FastAPI Backend Architecture | Week 5 | Completed | Modular services established |
| Market Data & WebSocket Engine | Week 6 | Completed | 15 pairs streaming in real time |
| Technical Analysis & Composite Bias | Week 6 | Completed | All 7 indicators & score formula |
| RAG Intelligence & Citation Cards | Week 7 | Completed | Grounded responses & refusal fallback |
| FinBERT Sentiment Heatmap | Week 7 | Completed | Per-currency scores (-1.0 to +1.0) |
| Paper Trading Engine & Margins | Week 7 | Completed | Pip accuracy & auto-liquidation |
| Next.js 14 Frontend UI Views | Week 8 | Completed | All 5 main views built & responsive |
| Unit Testing & Build Verification | Week 8 | Completed | Pytest & Next build 100% passing |

---

## 6. Future Plan for Month 3 & Month 4

### Month 3 Roadmap:
1. **Historical Backtesting Engine**: Build backtesting module allowing traders to run rule-based strategies against 5+ years of historical data with Sharpe ratio, max drawdown, and win rate reporting.
2. **Database Integration**: Connect Supabase PostgreSQL with `pgvector` extension for cloud vector search persistence and user Row Level Security (RLS) enforcement.
3. **Advanced Charting**: Integrate Lightweight Charts canvas library for enhanced drawing tools (trendlines, horizontal support/resistance).

### Month 4 Roadmap:
1. **Multi-Agent RAG System**: Integrate collaborating agents (Technical Analyst Agent, Fundamental Researcher, Risk Manager Agent) using LangGraph.
2. **Final Project Documentation & Internship Report**: Finalize internship thesis report, user manual, and mentor presentation slides.

---

## 7. References & Appendix

1. **IEEE Std 830-1998**: *IEEE Recommended Practice for Software Requirements Specifications*.
2. **Araci, D. (2019)**: *FinBERT: Financial Sentiment Analysis with Pre-trained Language Models*.
3. **Lewis, P. et al. (2020)**: *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*.
4. **Next.js 14 Documentation**: `https://nextjs.org/docs`
5. **FastAPI Documentation**: `https://fastapi.tiangolo.com/`

---

### Student Declaration & Approval

I hereby declare that this Month 2 Progress Report presents authentic work completed during my AI/ML Engineering internship at ThinkNovus Private Limited for the development of **Tradly**.

**Student Signature:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
**Prince Jivani** (Enrollment: 23SE02CS030)  
**Date:** August 7, 2026

**Industry Supervisor Approval (ThinkNovus):** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
**Date:** August 7, 2026

**Academic Supervisor Approval:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
**Date:** August 7, 2026
