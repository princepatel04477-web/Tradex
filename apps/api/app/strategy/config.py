"""Single source of truth for every tunable number in the strategy engine.

EVERY value the trader flagged as uncertain lives here and nowhere else.
Algorithm modules import from this file; they never hardcode a threshold.

Values marked ``UNCONFIRMED`` are transcriptions from a handwritten notebook
that the trader has not yet verified against the original page. They are
implemented exactly as transcribed and surfaced in the API/UI as unconfirmed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Timeframes
# ---------------------------------------------------------------------------

#: Every timeframe the engine understands, ordered high -> low.
TIMEFRAMES: Tuple[str, ...] = ("1W", "1D", "4H", "2H", "1H", "30M", "15M")

#: Trend + Area-of-Interest timeframes (notes section 9, "The 3-Tier Framework").
TREND_TIMEFRAMES: Tuple[str, ...] = ("1W", "1D", "4H")

#: Entry-signal timeframes. Never used for bias, only for trigger timing.
ENTRY_TIMEFRAMES: Tuple[str, ...] = ("2H", "1H", "30M", "15M")

#: AOI may only ever be computed on these. Notes: "Only look for AOI on
#: Weekly & Daily charts - never on 4H."
AOI_TIMEFRAMES: Tuple[str, ...] = ("1W", "1D")

#: Pattern strength multiplier by timeframe. "The higher the time frame, the
#: stronger the formation." Used to weight pattern confluence.
PATTERN_TIMEFRAME_WEIGHT: Dict[str, float] = {
    "1W": 3.0,
    "1D": 2.5,
    "4H": 2.0,
    "2H": 1.5,
    "1H": 1.2,
    "30M": 1.0,
    "15M": 0.8,
}

# ---------------------------------------------------------------------------
# Structure detection
# ---------------------------------------------------------------------------

#: Fractal/pivot half-width per timeframe: a swing high needs `n` lower highs
#: on each side. Larger = fewer, more significant swings.
SWING_LOOKBACK: Dict[str, int] = {
    "1W": 2,
    "1D": 3,
    "4H": 3,
    "2H": 3,
    "1H": 4,
    "30M": 4,
    "15M": 5,
}

#: UNCONFIRMED - how far back to read structure, from notes section 9
#: ("How Far Back to Look"). Expressed as a candle count per timeframe,
#: derived from the stated calendar spans:
#:   Weekly ~ 5-6 years   -> ~286 weekly candles (5.5y)
#:   Daily  ~ 1-2 years   -> ~390 daily candles (1.5y at ~260 sessions/yr)
#:   4H     ~ 6-12 months -> ~1350 4H candles (9 months at 30 bars/week)
STRUCTURE_LOOKBACK_CANDLES: Dict[str, int] = {
    "1W": 286,
    "1D": 390,
    "4H": 1350,
    "2H": 900,
    "1H": 720,
    "30M": 480,
    "15M": 480,
}

# ---------------------------------------------------------------------------
# Timeframe sync rule  (FLAGGED QUESTION #1)
# ---------------------------------------------------------------------------

#: How many trend timeframes must agree before a pair is worth looking at.
#:
#: Two readings of the notes exist and BOTH are implemented:
#:
#:   "weekly_daily_must_agree"
#:       Weekly and Daily must point the same way; 4H may diverge because it
#:       is used for entry timing, not bias. This is the trader's stated
#:       default in the build brief.
#:
#:   "any_two_consecutive"
#:       Any two adjacent trend timeframes agreeing is enough (W+D, or D+4H).
#:       This matches the three worked examples transcribed in the notes:
#:           W up   / D up   / 4H down -> valid   (W & D agree)
#:           W down / D up   / 4H up   -> valid   (D & 4H agree)
#:           W down / D up   / 4H down -> invalid (no adjacent pair agrees)
#:       Example 2 is valid under this rule but INVALID under
#:       "weekly_daily_must_agree" - that is the open discrepancy.
#:
#: Change this one string to switch the whole engine's gate.
REQUIRED_SYNC_TIMEFRAMES: str = "weekly_daily_must_agree"

SYNC_RULE_IS_UNCONFIRMED: bool = True

SYNC_RULE_NOTE: str = (
    "UNCONFIRMED. Default follows the build brief (Weekly & Daily must agree, "
    "4H free to diverge). The transcribed notes' own worked examples instead "
    "imply 'any two consecutive timeframes agree' - under which W-down / D-up / "
    "4H-up would be tradeable, but it is rejected today. Switch "
    "REQUIRED_SYNC_TIMEFRAMES to 'any_two_consecutive' in "
    "backend/app/strategy/config.py to adopt the other reading."
)

# ---------------------------------------------------------------------------
# Area of Interest
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AOIConfig:
    """Rules that decide whether a price zone is a tradeable Area of Interest."""

    #: "An AOI is only valid once it has been tested at least 3 times."
    min_touches: int = 3

    #: Zone width bounds, in pips. Notes: min 5, max 60. A wider zone is
    #: REJECTED outright - never clipped down to 60.
    min_width_pips: float = 5.0
    max_width_pips: float = 60.0

    #: A candle counts as touching the zone if it trades within this many
    #: pips of a zone edge. Keeps near-misses from being discarded.
    touch_tolerance_pips: float = 2.0

    #: Two touches closer together than this many candles count as one
    #: reaction, not two independent tests of the level.
    min_candles_between_touches: int = 3

    #: Between two counted touches price must actually LEAVE the zone by this
    #: many pips. Without this, a slow drift through a narrow band scores a
    #: touch every few candles and manufactures an AOI out of one move.
    touch_separation_pips: float = 15.0

    #: Touch count at which the zone is considered maximally strong for the
    #: confidence indicator (confidence saturates here).
    touches_for_full_confidence: int = 6

    #: Candidate zone widths swept when clustering price reactions, in pips.
    candidate_widths_pips: Tuple[float, ...] = (10.0, 20.0, 30.0, 45.0, 60.0)


AOI = AOIConfig()

# ---------------------------------------------------------------------------
# Break & retest
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BreakRetestConfig:
    """Rules for the break-and-retest entry trigger."""

    #: A break requires a candle BODY close beyond the level, not a wick.
    require_body_close: bool = True

    #: The close must clear the level by at least this many pips to count as a
    #: genuine break rather than noise sitting on the line.
    min_break_pips: float = 1.0

    #: Price must return to within this many pips of the broken level for the
    #: move to count as a retest.
    retest_tolerance_pips: float = 5.0

    #: The retest must happen within this many candles of the break, otherwise
    #: the setup is stale and is dropped.
    max_candles_to_retest: int = 30

    #: A close back through the level by more than this many pips invalidates
    #: the break entirely (it was a fakeout, not a break).
    invalidation_pips: float = 10.0


BREAK_RETEST = BreakRetestConfig()

# ---------------------------------------------------------------------------
# Candlestick pattern geometry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PatternConfig:
    """Deterministic OHLC geometry thresholds for candlestick recognition."""

    #: Body <= this fraction of the full range makes the candle a doji.
    doji_max_body_ratio: float = 0.10

    #: Spinning top: small body, meaningful wick on both sides.
    spinning_top_max_body_ratio: float = 0.30
    spinning_top_min_wick_ratio: float = 0.25

    #: Hammer family: one wick at least this multiple of the body, and the
    #: opposite wick no larger than this fraction of the range.
    hammer_min_wick_to_body: float = 2.0
    hammer_max_opposite_wick_ratio: float = 0.20

    #: Star patterns: the middle candle's body must be small relative to the
    #: first candle's body...
    star_max_middle_body_ratio: float = 0.50
    #: ...and the third candle must close at least this far back into the
    #: first candle's body.
    star_min_penetration: float = 0.50

    #: Engulfing: the engulfing body must exceed the prior body by this factor
    #: to be graded "strong" rather than merely valid.
    engulfing_strong_body_ratio: float = 1.5

    #: A candle whose full range is under this many pips is treated as noise
    #: and never produces a pattern.
    min_candle_range_pips: float = 1.0


PATTERNS = PatternConfig()

# ---------------------------------------------------------------------------
# Head & Shoulders
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HeadShouldersConfig:
    """Tolerances for head-and-shoulders geometry."""

    #: The two shoulders must be within this fraction of each other's height
    #: (measured from the neckline) to count as a matched pair.
    shoulder_symmetry_tolerance: float = 0.35

    #: The head must exceed the taller shoulder by at least this fraction.
    min_head_prominence: float = 0.10

    #: The two neckline points must be within this fraction of the pattern
    #: height of each other, so the neckline is not wildly sloped.
    max_neckline_slope_ratio: float = 0.40


HEAD_SHOULDERS = HeadShouldersConfig()

# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------

#: The notes name a single indicator: the 50 EMA. It is a *supplementary*
#: confluence only - structure remains the primary trend signal and no
#: indicator may override the structure engine's trend call.
EMA_PERIOD: int = 50

# ---------------------------------------------------------------------------
# Confluence scoring
# ---------------------------------------------------------------------------

#: The mandatory 4 pillars. If any one is false the setup is not eligible and
#: no score is produced at all.
CORE_PILLARS: Tuple[str, ...] = (
    "trend_confirmed",
    "aoi_valid",
    "entry_trigger_confirmed",
    "pattern_confirmed",
)

#: The expanded checklist, scored only once all four core pillars are true.
EXPANDED_CHECKLIST: Tuple[str, ...] = (
    "directional_bias",
    "at_valid_aoi",
    "star_pattern",
    "head_and_shoulders",
    "ema_alignment",
    "break_and_retest",
    "daily_trend_confirmation",
    "engulfing",
    "h4_head_and_shoulders",
    "hs_neckline_break_retest",
)

#: Expanded-checklist score at or above which the setup earns the
#: "Low Risk / High Reward" badge.
LOW_RISK_HIGH_REWARD_THRESHOLD: int = 7

# ---------------------------------------------------------------------------
# Risk management  (FLAGGED QUESTION #2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RiskTier:
    """One row of the account-size -> risk-% table."""

    account_size: float
    risk_pct_min: float
    risk_pct_max: float
    unconfirmed: bool = False
    note: str = ""

    @property
    def risk_pct(self) -> float:
        """Midpoint of the tier's range - what the sizer actually uses."""
        return (self.risk_pct_min + self.risk_pct_max) / 2.0


#: Transcribed exactly as written in the notes, including the out-of-order
#: $17,000 row. Edit this list and nothing else to correct the table.
#:
#: FLAGGED: the original notebook brackets everything from $15,000 to $1M
#: under a single "40%-35%" range rather than giving each tier its own value,
#: and $17,000 appears between $15,000 and $30,000, out of the ascending run
#: on the source page. Rows below are marked unconfirmed accordingly.
RISK_TIERS: List[RiskTier] = [
    RiskTier(100.0, 100.0, 100.0),
    RiskTier(400.0, 100.0, 100.0),
    RiskTier(3_200.0, 50.0, 60.0),
    RiskTier(8_000.0, 40.0, 50.0),
    RiskTier(15_000.0, 35.0, 40.0),
    RiskTier(
        17_000.0,
        35.0,
        40.0,
        unconfirmed=True,
        note="Appears out of ascending order in the original notebook page - verify.",
    ),
    RiskTier(30_000.0, 35.0, 40.0, unconfirmed=True, note="Part of the bracketed 40%-35% range."),
    RiskTier(55_000.0, 35.0, 40.0, unconfirmed=True, note="Part of the bracketed 40%-35% range."),
    RiskTier(308_000.0, 35.0, 40.0, unconfirmed=True, note="Part of the bracketed 40%-35% range."),
    RiskTier(1_000_000.0, 35.0, 40.0, unconfirmed=True, note="Part of the bracketed 40%-35% range."),
]

RISK_TABLE_NOTE: str = (
    "UNCONFIRMED. These percentages are transcribed from a handwritten page "
    "where $15,000 through $1,000,000 are bracketed together under one "
    "'40%-35%' range, and the $17,000 row sits out of ascending order. They "
    "are also far above any conventional risk standard - risking 35-100% of an "
    "account on a single position means a short run of losses ends the account. "
    "Verify against the original page before sizing real money."
)

#: Reward:risk floor. A trade plan worse than this must never be rendered.
MIN_REWARD_RISK: float = 2.0

#: Floor on the stop distance. A stop closer than this to entry is inside
#: normal spread-and-noise range and would be taken out by chance, which also
#: inflates position size to absurd levels.
MIN_STOP_DISTANCE_PIPS: float = 10.0

#: Warn when a sized position's notional exceeds this multiple of the account.
#: Purely a sanity alarm on top of the (very aggressive) risk table.
NOTIONAL_LEVERAGE_WARNING: float = 30.0

#: The ratio the tool actively aims for and highlights.
TARGET_REWARD_RISK: float = 4.0

#: "Rule: Take only 1 trade a week."
MAX_TRADES_PER_WEEK: int = 1

#: Once a trade is logged as placed, editing entry/stop/target is discouraged
#: (deliberate friction, not a hard block) - "Set & Forget".
SET_AND_FORGET_LOCK: bool = True

# ---------------------------------------------------------------------------
# Sessions (IST)
# ---------------------------------------------------------------------------

#: Session windows in IST (UTC+05:30), as written in the notes.
SESSIONS_IST: Tuple[Tuple[str, str, str], ...] = (
    ("Sydney", "03:30", "12:30"),
    ("Tokyo", "05:30", "14:30"),
    ("London", "11:30", "22:30"),
    ("New York", "19:00", "01:30"),
)

#: The primary trading window: pre-London open through London close.
PRIMARY_WINDOW_IST: Tuple[str, str] = ("11:30", "20:30")

IST_UTC_OFFSET_MINUTES: int = 330

# ---------------------------------------------------------------------------
# Discipline guardrail messaging
# ---------------------------------------------------------------------------

GUARDRAIL_MESSAGES: Dict[str, str] = {
    "no_setup": "Wait for the work - don't make something work.",
    "no_aoi": (
        "If you didn't find an AOI, wait for it. Don't make it up. "
        "Switch to the next pair."
    ),
    "no_sync": (
        "Trend is your friend - and it isn't here yet. Timeframes disagree; "
        "skip this pair."
    ),
    "no_trigger": (
        "No break & retest yet. Never enter mid-zone and never on the break "
        "candle itself."
    ),
    "weekly_pace": (
        "You've already taken your trade this week. Set & forget - don't hunt "
        "a second."
    ),
}

# ---------------------------------------------------------------------------
# Aggregate view for the API / UI "unconfirmed values" panel
# ---------------------------------------------------------------------------

FLAGGED_FOR_CONFIRMATION: List[Dict[str, str]] = [
    {
        "id": "sync_rule",
        "title": "Timeframe sync rule",
        "module": "4 - Top-down trend dashboard",
        "current_value": REQUIRED_SYNC_TIMEFRAMES,
        "note": SYNC_RULE_NOTE,
    },
    {
        "id": "risk_table",
        "title": "Account-size risk table",
        "module": "11 - Risk management calculator",
        "current_value": (
            "$17,000 row out of ascending order; $15k-$1M share one bracketed range"
        ),
        "note": RISK_TABLE_NOTE,
    },
    {
        "id": "structure_lookback",
        "title": "Structure lookback windows",
        "module": "3 - Multi-timeframe structure engine",
        "current_value": str(STRUCTURE_LOOKBACK_CANDLES),
        "note": (
            "Derived from the notes' calendar spans (Weekly 5-6y, Daily 1-2y, "
            "4H 6-12m) converted to candle counts. The conversion is an "
            "assumption, not a transcription."
        ),
    },
    {
        "id": "snake_trick",
        "title": "'Snake trick' backtrace",
        "module": "3 - Multi-timeframe structure engine",
        "current_value": "trace_last_valid_structure_point()",
        "note": (
            "Implemented as: walk backward from the most recent extreme through "
            "consecutive swing points until direction reverses; that reversal "
            "point is the last valid HL/LH. Best reading of a partially unclear "
            "handwritten passage."
        ),
    },
]
