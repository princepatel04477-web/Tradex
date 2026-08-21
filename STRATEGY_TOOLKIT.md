# Forex Top-Down Confluence Toolkit

Your personal price-action strategy, implemented as a real calculation engine
and wired into the Tradly platform. Every module runs actual maths on OHLC
data — nothing on screen is a mock.

> **This is analysis tooling, not financial advice, and nothing in it places an
> order.** The risk percentages transcribed from the notebook are far above
> conventional position sizing; read [Flagged question #2](#2-the-risk-table)
> before applying them to real money.

---

## Run it

Two processes. The backend needs no API keys.

```bash
cd backend && pip install -r requirements.txt && python -m uvicorn main:app --reload --port 8000
```

```bash
cd frontend && npm install && npm run dev
```

Then open <http://localhost:3000/strategy>. It loads a bundled dataset and
immediately shows structure, AOI, a break & retest, patterns, a confluence
score and a sized trade plan — computed, not hardcoded.

API docs: <http://localhost:8000/docs> (the toolkit routes are tagged `strategy`).

```bash
cd backend && python -m pytest tests/ -q
```

---

## Where each module lives

The engine is pure Python with no framework imports, so every rule is
unit-testable on its own. The API and UI are consumers.

| # | Module | Engine | API route | UI |
|---|---|---|---|---|
| 1 | Pair & market basics | [`strategy/reference.py`](backend/app/strategy/reference.py) | `GET /strategy/reference/pairs/{symbol}` | `/strategy/reference` |
| 2 | Trading session clock | [`strategy/sessions.py`](backend/app/strategy/sessions.py) | `GET /strategy/sessions` | `SessionPanel` |
| 3 | Multi-timeframe structure | [`strategy/structure.py`](backend/app/strategy/structure.py) | `GET /strategy/structure/{scenario}/{tf}` | `StructureChart` |
| 4 | Top-down trend dashboard | [`strategy/topdown.py`](backend/app/strategy/topdown.py) | inside `GET /strategy/analysis/{scenario}` | `TrendDashboard` |
| 5 | AOI detector & validator | [`strategy/aoi.py`](backend/app/strategy/aoi.py) | `GET /strategy/aoi/{scenario}/{tf}` | `AOIPanel` |
| 6 | Break & retest | [`strategy/break_retest.py`](backend/app/strategy/break_retest.py) | inside the analysis route | `TriggerPanel` |
| 7 | Candlestick patterns | [`strategy/patterns.py`](backend/app/strategy/patterns.py) | inside the analysis route | `PatternPanel` |
| 8 | Head & Shoulders | [`strategy/head_shoulders.py`](backend/app/strategy/head_shoulders.py) | inside the analysis route | `PatternPanel` + chart neckline |
| 9 | EMA overlay | [`strategy/indicators.py`](backend/app/strategy/indicators.py) | `GET /strategy/ema/{scenario}/{tf}` | chart overlay |
| 10 | Confluence scoring | [`strategy/confluence.py`](backend/app/strategy/confluence.py) | inside the analysis route | `ConfluencePanel` |
| 11 | Risk calculator | [`strategy/risk.py`](backend/app/strategy/risk.py) | `GET /strategy/risk/table`, `POST /strategy/risk/plan` | `/strategy/risk` |
| 12 | Trade journal | [`strategy/journal.py`](backend/app/strategy/journal.py) | `/strategy/journal*` | `/strategy/journal` |
| 13 | Resources | [`strategy/reference.py`](backend/app/strategy/reference.py) | `GET /strategy/reference` | `/strategy/reference` |
| 14 | Discipline guardrails | [`strategy/config.py`](backend/app/strategy/config.py) `GUARDRAIL_MESSAGES` | on every analysis | `GuardrailBanner` |

Supporting files:

| File | Purpose |
|---|---|
| [`strategy/config.py`](backend/app/strategy/config.py) | **Every tunable number, in one place.** All flagged values live here. |
| [`strategy/engine.py`](backend/app/strategy/engine.py) | The end-to-end top-down pass that chains modules 3→11. |
| [`strategy/types.py`](backend/app/strategy/types.py) | Candle, SwingPoint, AOIZone, TradePlan… shared dataclasses. |
| [`strategy/pips.py`](backend/app/strategy/pips.py) | Pip arithmetic — JPY pairs included. |
| [`strategy/sample_data.py`](backend/app/strategy/sample_data.py) | Deterministic OHLC datasets that exercise every module. |
| [`strategy/data_input.py`](backend/app/strategy/data_input.py) | CSV / paste import, plus an optional live source behind a flag. |
| [`services/strategy_service.py`](backend/app/services/strategy_service.py) | Serialisation between the engine and HTTP. |
| [`services/tradingagents_bridge.py`](backend/app/services/tradingagents_bridge.py) | Optional LLM second opinion via TradingAgents. |

---

## How the pass runs

```
Trend (1W/1D/4H)  →  sync gate  →  AOI (1W/1D only)  →  break & retest
      →  pattern at the AOI  →  core 4  →  expanded score  →  sized plan
```

Every stage can refuse. When one does, the pass stops producing a trade and
returns the matching discipline message instead — the refusal is the feature:

```
USD/JPY:  AOI: none valid on Weekly or Daily.
          "If you didn't find an AOI, wait for it. Don't make it up.
           Switch to the next pair."
          tradeable: false, trade_plan: null
```

### Rules enforced in code, not in the UI

- AOI is computed on Weekly and Daily only; asking for 4H returns a refusal.
- A zone needs 3+ genuine reactions. Price sliding through a level is a break,
  not a touch, and two touches from one move count once.
- A zone wider than 60 pips is **rejected, never clipped** to the cap.
- Structure flips on a **body close** past the last HL/LH. Wicks never flip it.
- A swing point **retires** once it stops describing live structure: price body
  closed through the level, or a later CHoCH relabelled it. Retired points are
  kept in the API response with `broken: true` and a reason, and the chart drops
  them — an HH that price has closed above is no longer the high, and leaving it
  drawn only invites reading a trend that has already ended. The chart's history
  toggle brings them back, ghosted. The engine's current reference points
  (`last_valid_hl` / `last_valid_lh` / `last_hh` / `last_ll`) survive the CHoCH
  sweep, because after a flip the level now guarding the trend necessarily
  predates the flip.
- The chart draws AOI zones from **its own timeframe and every higher one**.
  AOI exists only on Weekly and Daily, so a 4H chart filtered to 4H zones would
  show none at all — and the Daily zone is exactly what you drop to 4H to trade
  into.
- A break is a *crossing* of a level, not merely closing on one side of it.
- Entries only ever come from a confirmed break **and** retest.
- A candlestick pattern counts only at a validated AOI, weighted by timeframe.
- A Head & Shoulders is invalid until its neckline breaks; the right shoulder
  is flagged as high-risk/early entry, never as a signal.
- The trade follows the bias. A bullish read never returns a sell trigger.
- No score is computed while any core pillar is missing.
- A plan below 1:2 RR is never rendered.

---

## The two flagged questions

Both are implemented as you specified, and both are surfaced in the UI at
`/strategy/reference` under **Needs your confirmation**.

### 1. The sync rule

**Implemented default:** `REQUIRED_SYNC_TIMEFRAMES = "weekly_daily_must_agree"`
— Weekly and Daily must agree; 4H may diverge because it is entry timing.

**The problem:** your transcribed notes give three worked examples, and they
imply a *different* rule — "any two consecutive timeframes agree":

| Example | Notes say | Default rule says |
|---|---|---|
| W↑ D↑ 4H↓ | valid | valid ✅ |
| W↓ D↑ 4H↑ | valid | **invalid** ❌ |
| W↓ D↑ 4H↓ | invalid | invalid ✅ |

The second row is the disagreement: under the notes' rule that pair is
tradeable, and today the engine rejects it.

Both readings are fully implemented. To switch, change one string in
`backend/app/strategy/config.py`:

```python
REQUIRED_SYNC_TIMEFRAMES = "any_two_consecutive"
```

**Which is right?**

### 2. The risk table

Transcribed exactly as written, including the out-of-order `$17,000` row:

| Account | Risk % | |
|---|---|---|
| $100 | 100% | |
| $400 | 100% | |
| $3,200 | 50–60% | |
| $8,000 | 40–50% | |
| $15,000 | 35–40% | |
| **$17,000** | 35–40% | ⚠️ out of ascending order in the original page |
| $30,000 | 35–40% | ⚠️ part of one bracketed range |
| $55,000 | 35–40% | ⚠️ |
| $308,000 | 35–40% | ⚠️ |
| $1,000,000 | 35–40% | ⚠️ |

Two things to check, not one:

1. **The `$17,000` row** sits out of sequence on the source page, and
   `$15,000`–`$1,000,000` are bracketed together under a single "40%–35%"
   range rather than each having its own value.

2. **The magnitudes.** Risking 35–100% of an account on a single position is
   far outside conventional practice. At $10,000 with a 50-pip stop, the table
   sizes a **9 lot** position — roughly 90× the account in notional, which no
   retail broker would permit. The engine computes it faithfully and attaches
   both warnings, but this reads like the notebook may have meant something
   else (risk *per* something, or a growth target rather than per-trade risk).

Edit `RISK_TIERS` in `backend/app/strategy/config.py` — one list, nothing else
to touch.

### Also assumed, also flagged

Surfaced in the same UI panel:

- **Structure lookback windows** — the notes give calendar spans (Weekly 5–6y,
  Daily 1–2y, 4H 6–12m); converting those to candle counts is my assumption.
- **The "snake trick"** — implemented as: walk backward from the most recent
  extreme through consecutive swing points until direction reverses; that
  reversal point is the last valid HL/LH. Best reading of an unclear passage.
- **Broker spelling** — "1xTrade" in the notes, "IXTrade" in the build brief.

---

## Data input

Three sources, in order of preference:

1. **Bundled scenarios** — deterministic, seeded, and designed so each one
   exercises specific behaviour:

   | Scenario | Demonstrates |
   |---|---|
   | `eurusd_bullish_aoi` | Bullish HH/HL, a validated Buy zone, armed trigger, pattern at the AOI, sized plan |
   | `gbpusd_head_shoulders` | H&S with a broken **and retested** neckline, 9/10 confluence, Low Risk / High Reward |
   | `usdjpy_no_setup` | The refusal path — no AOI, no plan, discipline message |

2. **CSV / paste** — `POST /strategy/analyse` with `csv_by_timeframe`. Accepts
   comma/semicolon/tab, any column order, common header spellings, and epoch or
   ISO timestamps. Export from the UI round-trips straight back in.

3. **Live data (optional)** — off by default, never blocks anything:

   ```bash
   TRADLY_LIVE_DATA=1
   TRADLY_LIVE_API_KEY=your_key   # free tier: twelvedata.com
   ```

---

## The TradingAgents bridge

Where the Tauric Research half of the repo connects. The engine produces a
deterministic verdict; TradingAgents' LLM layer can then argue both sides of it.

```
GET /api/v1/strategy/review/status          # is an LLM configured?
GET /api/v1/strategy/review/{scenario}      # bull case / bear case / verdict
```

Two deliberate constraints:

- **The engine stays authoritative.** The model is told the rule verdicts are
  facts and that it must not recommend a setup the rules rejected. "No
  indicator tells you the trend" applies to language models too.
- **Nothing is fabricated.** With no package or no API key, the response is
  `available: false` with a reason — the engine's own verdict still comes
  through, because that needs no LLM. It never emits templated prose dressed up
  as model output.

Configure it by putting one API key in the repo-root `.env` — nothing else is
required. The bridge picks the provider from whichever supported key is present
and pairs it with a model that provider actually serves:

```bash
# .env — this alone is enough
GROQ_API_KEY=gsk_...
```

The panel on `/strategy` then shows `groq/llama-3.3-70b-versatile` and a button
to run the review. Restart the API after editing `.env`.

Override either half when you want a specific provider or model:

```bash
TRADINGAGENTS_LLM_PROVIDER=groq
TRADINGAGENTS_QUICK_THINK_LLM=openai/gpt-oss-120b
```

Groq (like the other multi-model hosted providers) has no fixed model list in
the catalogue, so the model name has to come from somewhere — that is what
`DEFAULT_MODELS` in `tradingagents_bridge.py` supplies. If your key does not
have access to the default, set `TRADINGAGENTS_QUICK_THINK_LLM` to one it does.

TradingAgents' own `propagate()` pipeline is built around equity/crypto data
vendors, so it is not used to fetch FX prices. What is reused is its provider
registry, model catalogue and client factory.

---

## Tests

208 tests, all deterministic and offline.

| File | Covers |
|---|---|
| `test_strategy_structure.py` | Swings, HH/HL/LH/LL, CHoCH on closes (not wicks), snake trace, lookback |
| `test_strategy_aoi.py` | 3-touch rule, 5–60 pip bounds, W/D-only, Golden Rule tags, structural placement |
| `test_strategy_patterns.py` | Every pattern, body-not-wick engulfing, AOI gating, timeframe weighting |
| `test_strategy_confluence.py` | Core-4 gate, expanded checklist, LRHR threshold, guardrail routing |
| `test_strategy_risk.py` | Risk tiers, pip value (JPY vs standard), sizing, RR floor, weekly pace |
| `test_strategy_flow.py` | Break & retest, H&S, sync rule, sessions, EMA, CSV, end-to-end, data integrity |
| `test_strategy_api.py` | Every HTTP route, the journal write flow, Set & Forget friction, the bridge |

Notable cases: a wick through the HL must **not** flip the trend; a 60-pip-plus
zone must be rejected rather than clipped; a bearish pattern must not satisfy
the pattern pillar for a long; the `$17,000` row must be present and flagged.

---

## Known gaps

- **Storage is in-memory.** The journal resets when the API restarts. The SRS
  specifies Postgres; swapping `JournalStore` is the only change needed.
- **The Tradly RAG assistant (`ai_service.py`) is still a stub** — keyword
  matching over a fixed 8-document corpus, no embeddings and no LLM call. Its
  `model_used` field claimed "Groq LLaMA 3 70B" while doing none of that; I
  relabelled it to say what it actually does. Building the real pipeline from
  SRS §6.1 is separate work.
- **Sessions ignore weekends and DST.** Windows are fixed IST wall-clock times.
- **Cross pairs need a conversion rate** for pip value (e.g. EUR/GBP on a USD
  account); majors are handled automatically.
