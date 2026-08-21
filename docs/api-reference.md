# Tradly API Reference Specification

**Version:** 1.0.0  
**Base URL:** `/api/v1`  
**Envelope Format:** `{ "data": T, "error": E, "meta": M }`

---

## Endpoints Overview

### Market Data (`/api/v1/market`)
- `GET /pairs` — List all 15 supported currency pairs with live bid/ask, spread, 24h metrics.
- `GET /pairs/{symbol}` — Get detailed metadata for a single currency pair.
- `GET /ticks` — Snapshot of latest ticks for all pairs.
- `GET /candles/{symbol}?timeframe={tf}&limit={n}` — Fetch OHLCV candles (M1, M5, M15, M30, H1, H4, D1).
- `GET /sessions` — Global Forex session clock (Sydney, Tokyo, London, NY) and active overlap window.

### Technical Analysis (`/api/v1/analysis`)
- `GET /indicators/{symbol}?timeframe={tf}` — Complete indicator suite (RSI-14, MACD, Bollinger Bands, ATR-14, EMA 9/21/50, SMA-200, Fibs).
- `GET /bias/{symbol}?timeframe={tf}` — Explainable composite directional bias score and contributor breakdown.

### Paper Trading (`/api/v1/trading`)
- `GET /account` (and alias `GET /metrics`) — Account balance, equity, used margin, free margin, margin level %.
- `POST /orders` — Place market order with lot size (1.0, 0.1, 0.01), leverage (1:1 to 1:100), SL/TP, and trailing stops.
- `GET /positions` — List active open paper positions.
- `POST /positions/{id}/close` — Close position at current market quote and realize P&L.
- `GET /trades` — Historical closed trades.
- `POST /account/reset` — Reset paper account balance to $10,000.
- `GET /analytics` — Win rate, profit factor, max drawdown, risk:reward, and pair breakdowns.

### AI Market Intelligence (`/api/v1/ai`)
- `POST /rag/query` — Natural language chat assistant with grounded source citations and refusal on low relevance.
- `GET /sentiment` — FinBERT per-currency sentiment scores (-1.0 to +1.0).
- `GET /calendar` — Economic calendar events with AI pre-event briefings and historical pip volatility.

### Alerts & Notifications (`/api/v1/alerts`)
- `POST /` — Create price or indicator alert.
- `GET /` — List user's active alerts (max 50).
- `DELETE /{id}` — Delete alert.
- `POST /{id}/toggle` — Enable/disable alert.
- `GET /notifications` — List in-app notifications.

### Authentication (`/api/v1/auth`)
- `POST /register` — Register new user account.
- `POST /login` — Authenticate and receive JWT access token.
- `GET /me` — Current authenticated user profile.

### Strategy Toolkit (`/api/v1/strategy`)
- `GET /scenarios` — Pre-loaded multi-timeframe scenarios.
- `GET /candles/{scenario}/{timeframe}` — Scenario OHLC candles.
- `GET /analysis/{scenario}` — Full top-down confluence pass.
- `POST /analyse` — Analyze uploaded multi-timeframe CSVs.
- `POST /risk/plan` — Size trade and enforce 1:2 minimum reward:risk floor.
- `GET /reference` — Strategy reference rules and common mistakes.
- `GET /journal` — Trade journal entries.
- `GET /pace` — Weekly trade pacer (1 trade/week rule).
- `GET /review/status` — LLM second opinion bridge status.
- `GET /review/{scenario}` — LLM setup review.

### Real-Time WebSocket (`/api/v1/ws/stream`)
- Streams live ticks, market sessions, account margin recalculations, and alert trigger events every second.
