# Build Prompt — Forex Top-Down Confluence Toolkit

> Paste this entire file as one message into Claude Code. It is written to be executed end-to-end without further input from me, except for the two flagged questions at the bottom.

## What you're building

A working "Forex Strategy Assistant" that operationalizes my personal top-down, price-action trading strategy (notes below, fully transcribed) into a real, usable tool — not a UI mockup. Every module listed must be functionally wired: real calculations on real OHLC data (sample data is fine for the demo, but the logic must actually run, not be hardcoded/faked).

## Before you start — agent & skill routing

This project already has subagents and skills configured. Inspect what's registered (`.claude/agents/`, `.claude/skills/`, `CLAUDE.md`, or wherever this setup keeps them) and delegate each module below to whichever existing agent/skill best fits its domain — frontend/UI, backend/calculation-engine, data integration, testing, docs. Switch between them automatically as you move through the list. Don't stop to ask me which agent to use for a given module — only stop for the two flagged questions at the very end.

## Stack

If this is dropped into an existing project, follow its existing stack and conventions. If starting fresh, default to Next.js + TypeScript + Tailwind. Every calculation engine (structure detection, AOI validation, pattern recognition, confluence scoring, risk sizing) must be written as pure, independently testable functions — UI is just a consumer of them.

---

## Feature modules (implement all of them, fully wired)

### 1. Pair & market basics reference
- Base currency / quote currency explainer (e.g. EUR/USD → EUR is base, USD is quote; if EUR/USD = 1.10, 1 EUR = 1.10 USD).
- Majors list: EUR/USD, GBP/USD, USD/JPY, USD/CHF, USD/CAD, AUD/USD, NZD/USD.
- Directional logic: price up = base currency stronger; price down = quote currency stronger. Buy when you expect base to strengthen / quote to weaken. Sell when you expect quote to strengthen / base to weaken.

### 2. Trading session clock
- Sessions in IST: Sydney 3:30 AM–12:30 PM, Tokyo 5:30 AM–2:30 PM, London 11:30 AM–10:30 PM, New York 7:00 PM–1:30 AM. Also render in the user's local timezone.
- Primary trading window highlighted distinctly: pre-London open through London close = **11:30 AM–8:30 PM IST**. The UI should visually flag in real time whether we're inside this window right now.
- Candlestick and line chart view toggle (both are referenced as the chart types to support).

### 3. Multi-timeframe market structure engine
- Input: OHLC series per timeframe (1W, 1D, 4H, 2H, 1H, 30M, 15M).
- Detect swing highs/lows (fractal/pivot-style algorithm) and classify them as HH/HL (bullish structure) or LH/LL (bearish structure).
- Structure shift / CHoCH (Change of Character): a candle **body close** beyond the last HL (in an uptrend) or LH (in a downtrend) flips the trend; relabel subsequent points accordingly. A new HH always implies a fresh HL is now in play (same logic mirrored for LL/LH on the bearish side).
- Ignore lower-timeframe noise: sudden/extreme wicks on a lower TF must not affect higher-TF structure classification — structure shift is decided on the relevant TF's own closes only.
- "Last valid structure point" backtrace: implement a swing-point tracing function that walks backward from the most recent extreme through consecutive swing points until direction reverses — that reversal point is the last valid HL/LH used for shift detection. (This is my best reading of a technique I called the "snake trick" in my notes — see flagged question #1.)
- Lookback windows (configurable per timeframe): Weekly ≈ 5–6 years, Daily ≈ 1–2 years, 4H ≈ 6–12 months.

### 4. Top-down trend dashboard
- Show trend direction (bullish/bearish) side by side for Weekly, Daily, and 4H — these three are the **trend + area-of-interest** timeframes.
- Lower timeframes (2H, 1H, 30M, 15M) are the **entry-signal** layer — surface them in a separate panel, not mixed with the trend panel.
- "Trend is your friend" banner/state when timeframes align.
- Sync rule: implement a named, single config value (e.g. `requiredSyncTimeframes`) gating whether a setup is even worth looking at. Default it to "Weekly and Daily must agree in direction; 4H is allowed to diverge since it's used for entry timing, not bias." Flag this as approximate — see flagged question #1.

### 5. Area of Interest (AOI) detector & validator
AOI = the zone that everything else hangs off of. Implement as a real validator, not a visual guess:
- Only ever compute AOI on **Weekly and Daily** — never on 4H.
- A zone is only valid once it has **3 or more touches** (a touch = a support reaction or a resistance reaction at that level). More touches = stronger, surface a confidence indicator that scales with touch count.
- Zone width must be **between 5 and 60 pips**. Anything wider than 60 pips is invalid and should be rejected, not clipped.
- The zone must sit inside the *current* structural range — not above the most recent HH in an uptrend, not below the most recent LL in a downtrend. It must align with either the HH/HL zone (bullish) or LH/LL zone (bearish).
- Golden Rule tagging: a support zone is tagged "Buy zone," a resistance zone is tagged "Sell zone."
- If no valid AOI exists, the system must say so explicitly ("No valid AOI on this pair right now — wait or switch pairs") rather than relaxing the rules to manufacture one.

### 6. Break & retest / structure-shift detector
- Detect when price closes beyond an AOI boundary or a structure point (the "break").
- After a break, watch for the retest (price returning to the broken level) before marking the setup "armed."
- Entries are only ever valid on confirmed break-and-retest — never mid-zone, never on the break candle itself.

### 7. Candlestick pattern recognizer (OHLC rule-based)
Implement standard, deterministic OHLC rules for:
- Doji / Spinning Top
- Hammer / Inverted Hammer (note "wick fill" behavior)
- Bullish Engulfing / Bearish Engulfing — the engulfing candle's **body** must fully cover the prior candle's body (not the wick), and strength should be assessed across the last two candles' bodies collectively, not just the immediately preceding one.
- Morning Star (bullish reversal signal) / Evening Star (bearish reversal signal)

Pattern detection can run anywhere on the chart, but a pattern should only be surfaced as an **actionable confluence** when it occurs at/inside a validated AOI zone. Weight pattern strength by timeframe — higher TF formations are stronger and should score higher in the confluence engine.

### 8. Head & Shoulders detector (+ inverse)
- Identify left shoulder / head / right shoulder from swing structure (and the inverse pattern, which signals bullish continuation/reversal up).
- Compute and render the neckline connecting the two troughs (or peaks, for the inverse).
- The pattern is **invalid until the neckline is broken** — don't surface it as a signal before that.
- Require a break-and-retest of the neckline before treating it as a trigger; the neckline retest *is* the AOI retest, treat them as the same event.
- Trading directly off the right shoulder (before any neckline break) should be flagged separately as "high risk / early entry" — never presented as a primary signal.

### 9. EMA overlay
- 50-period EMA, configurable period, rendered on the relevant chart. Treat it as a supplementary confluence, not a primary trend signal — structure is the primary trend signal (no indicator should override the structure engine's trend call).

### 10. Confluence scoring engine
Implement two linked layers, matching my notes exactly:
- **Core 4-pillar checklist** (all four are mandatory, not optional, before any setup is even eligible): Trend confirmed → AOI valid → Entry trigger (break & retest) confirmed → Pattern confirmed.
- **Expanded checklist** scored on top of the core pillars: directional bias (bullish/bearish), at a valid AOI, Morning/Evening Star present, Head & Shoulders present, EMA alignment, break & retest confirmed, Daily trend confirmation, Engulfing present, 4H Head & Shoulders present, break & retest of the H&S neckline.
- Score = count of confirmed items in the expanded list, only computed once the core 4 are all true. Surface a "Low Risk / High Reward" badge once the score crosses a configurable threshold. Never auto-suggest a trade when any of the core 4 pillars is missing.

### 11. Risk management calculator
- Account-size → risk-% lookup table, loaded from a single editable config object (not hardcoded inline):

  | Account size | Risk % |
  |---|---|
  | $100 | 100% |
  | $400 | 100% |
  | $3,200 | 50–60% |
  | $8,000 | 40–50% |
  | $15,000 | 35–40% |
  | $30,000 | 35–40%* |
  | $55,000 | 35–40%* |
  | $308,000 | 35–40%* |
  | $1,000,000 | 35–40%* |

  *Rows marked with `*` are my best reading of a bracket spanning several account sizes in the original notes — there's also a `$17,000` entry that appears out of ascending order and may be a transcription slip on my end (see flagged question #2). Make the whole table a one-file edit.
- Reward:risk enforcement: minimum acceptable is **1:2**, the system should highlight/aim for **1:4** as the target ratio. Never let a trade plan render with worse than 1:2.
- Standard pip-value-based position sizing for major USD-quoted pairs, computed from entry/stop distance and the risk-table $ amount.
- "1 trade a week" pace tracker — surface how many trades have been taken this week and discourage a second.
- "Set & Forget" lock: once a trade is logged as placed, the UI should discourage/lock editing of entry/stop/target (a deliberate friction point, not a hard block).

### 12. Trade journal
- Log per trade: pair, timeframe sync state, AOI zone used, pattern(s) confirmed, confluence score, entry/stop/target, resulting RR, outcome.
- Weekly view that ties directly into the "1 trade a week" pacer above.

### 13. Resource / reference panel
- Tools: TradingView, Forex Factory, MetaTrader 5.
- Broker shortlist: LQH Markets, IXTrade, Exness (note: MT5 is used for execution).
- A short, static "guiding principle" card: fundamentals/news are roughly a coin-flip signal — price action and structure are the primary edge. This is reference content, not a feature toggle.

### 14. Discipline guardrail messaging
Surface these as contextual messages at the moment the engine finds no valid setup, rather than a blank empty state:
- "Wait for the work — don't make something work."
- "If you didn't find an AOI, wait for it. Don't make it up. Switch to the next pair."

---

## Engineering requirements (non-negotiable)

1. Every module above must be **functionally wired** to real calculations on real (or realistic sample) OHLC data — no static/mocked UI standing in for logic that should actually run.
2. All numbers I'm not fully certain about (risk tiers, the sync-timeframe rule, the structure backtrace lookback windows) live in **one clearly named config file**, so I can correct them without touching algorithm code.
3. Ship sample/test OHLC datasets so every module is demonstrably exercised out of the box — I should be able to open this and immediately see structure, AOI, patterns, and a confluence score computed on real data, not empty states everywhere.
4. Unit tests for the deterministic pieces: structure/swing detection, AOI validator, candlestick pattern functions, confluence scorer, risk calculator.
5. Use my notes' exact terminology in code, UI labels, and docs — HH/HL/LH/LL, AOI, CHoCH, RR, EMA — so the tool matches how I actually think about the strategy.
6. Data input: support CSV/manual OHLC paste at minimum. If wiring in a free-tier forex OHLC API is straightforward, add it as an optional live-data source behind a config flag — don't let it block the rest of the build.
7. Ship a short README mapping each feature module above to where it lives in the codebase, plus the two flagged questions below.

---

## Two things to confirm with me before treating as final (ask, don't silently decide)

1. **Sync rule (module 4):** my notes' worked examples for "2 consecutive timeframes in sync" had arrow directions I couldn't fully verify from the handwriting. I've defaulted to "Weekly & Daily must agree, 4H may diverge" — implement that as the default but flag it as unconfirmed.
2. **Risk table (module 11):** the `$17,000` row appears out of ascending order relative to the rest of the table. Implement the table as transcribed above, but call this row out specifically for me to double-check against the original notes.

## Definition of done

I should be able to open the tool, load the sample data, and watch it: identify Weekly/Daily/4H trend → find (or correctly refuse to find) an AOI → detect a break & retest → flag any candlestick/H&S pattern present → produce a confluence score → and hand back a sized trade plan with a valid RR — end to end, with no manual step faked.
