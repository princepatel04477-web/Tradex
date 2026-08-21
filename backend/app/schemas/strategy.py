"""API models for the Forex Top-Down Confluence Toolkit.

These mirror the engine's dataclasses at the HTTP boundary. The engine itself
stays framework-free; conversion happens in ``services/strategy_service.py``.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Market data
# ---------------------------------------------------------------------------


class CandleOut(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class CandleSeries(BaseModel):
    symbol: str
    timeframe: str
    candles: List[CandleOut]
    count: int


# ---------------------------------------------------------------------------
# Module 3 & 4 - structure and top-down
# ---------------------------------------------------------------------------


class SwingPointOut(BaseModel):
    index: int
    time: datetime
    price: float
    kind: str  # high | low
    label: Optional[str] = None  # HH | HL | LH | LL
    #: False once the level has been closed through, or a later CHoCH
    #: relabelled it. Broken points are not drawn on the chart by default.
    broken: bool = False
    broken_time: Optional[datetime] = None
    broken_reason: str = ""


class ChochOut(BaseModel):
    index: int
    time: datetime
    close: float
    broken_level: float
    broken_label: str
    from_trend: str
    to_trend: str
    description: str


class StructureOut(BaseModel):
    timeframe: str
    trend: str
    #: Every swing found, broken ones included and flagged.
    swings: List[SwingPointOut] = Field(default_factory=list)
    #: How many of ``swings`` still describe the current structure.
    live_swing_count: int = 0
    choch_events: List[ChochOut] = Field(default_factory=list)
    last_valid_hl: Optional[SwingPointOut] = None
    last_valid_lh: Optional[SwingPointOut] = None
    last_hh: Optional[SwingPointOut] = None
    last_ll: Optional[SwingPointOut] = None
    structural_range: Optional[List[float]] = None
    candles_analysed: int = 0
    summary: str = ""
    #: "Snake trick" backtrace result for this timeframe.
    snake_trace_price: Optional[float] = None


class SyncOut(BaseModel):
    in_sync: bool
    rule: str
    direction: str
    agreeing_timeframes: List[str] = Field(default_factory=list)
    explanation: str = ""
    rule_is_unconfirmed: bool = True
    rule_note: str = ""


class TopDownOut(BaseModel):
    symbol: str
    #: Weekly / Daily / 4H - trend + AOI.
    trend_layer: Dict[str, StructureOut] = Field(default_factory=dict)
    #: 2H / 1H / 30M / 15M - entry signal only, kept in a separate panel.
    entry_layer: Dict[str, StructureOut] = Field(default_factory=dict)
    sync: Optional[SyncOut] = None
    trend_is_your_friend: bool = False
    bias: str = "undetermined"
    messages: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Module 5 - AOI
# ---------------------------------------------------------------------------


class AOIZoneOut(BaseModel):
    timeframe: str
    lower: float
    upper: float
    mid: float
    zone_type: str  # support | resistance
    golden_rule_tag: str  # "Buy zone" | "Sell zone"
    touches: int
    touch_times: List[datetime] = Field(default_factory=list)
    width_pips: float
    valid: bool
    confidence: float
    rejection_reasons: List[str] = Field(default_factory=list)


class AOIScanOut(BaseModel):
    timeframe: str
    allowed: bool
    zones: List[AOIZoneOut] = Field(default_factory=list)
    rejected: List[AOIZoneOut] = Field(default_factory=list)
    message: str = ""
    has_valid_aoi: bool = False


# ---------------------------------------------------------------------------
# Module 6 - break & retest
# ---------------------------------------------------------------------------


class TriggerOut(BaseModel):
    status: str  # none | broken | armed | invalidated
    direction: Optional[str] = None
    level: Optional[float] = None
    level_label: str = ""
    break_time: Optional[datetime] = None
    break_close: Optional[float] = None
    retest_time: Optional[datetime] = None
    retest_price: Optional[float] = None
    candles_to_retest: Optional[int] = None
    is_armed: bool = False
    notes: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Modules 7 & 8 - patterns
# ---------------------------------------------------------------------------


class PatternOut(BaseModel):
    name: str
    index: int
    time: datetime
    timeframe: str
    bias: str
    strength: float
    weighted_strength: float
    at_aoi: bool
    detail: str = ""


class HeadShouldersOut(BaseModel):
    kind: str
    timeframe: str
    bias: str
    left_shoulder: SwingPointOut
    head: SwingPointOut
    right_shoulder: SwingPointOut
    neckline_start: SwingPointOut
    neckline_end: SwingPointOut
    neckline_broken: bool
    neckline_retested: bool
    target_price: Optional[float] = None
    is_valid_signal: bool = False
    early_entry_risk: bool = False
    notes: List[str] = Field(default_factory=list)


class EMAOut(BaseModel):
    period: int
    value: Optional[float] = None
    price: float
    alignment: str
    slope: float
    series: List[Optional[float]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Module 10 - confluence
# ---------------------------------------------------------------------------


class ConfluenceOut(BaseModel):
    core_pillars: Dict[str, bool] = Field(default_factory=dict)
    core_complete: bool = False
    missing_core: List[str] = Field(default_factory=list)
    expanded: Dict[str, bool] = Field(default_factory=dict)
    score: int = 0
    max_score: int = 0
    low_risk_high_reward: bool = False
    reasons: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Module 11 - risk
# ---------------------------------------------------------------------------


class TradePlanOut(BaseModel):
    symbol: str
    direction: str
    entry: float
    stop_loss: float
    take_profit: float
    stop_distance_pips: float
    target_distance_pips: float
    reward_risk: float
    account_size: float
    risk_pct: float
    risk_amount: float
    pip_value_per_lot: float
    position_size_lots: float
    position_size_units: float
    meets_min_rr: bool
    meets_target_rr: bool
    risk_tier_unconfirmed: bool = False
    warnings: List[str] = Field(default_factory=list)


class TradePlanRequest(BaseModel):
    symbol: str = Field(..., examples=["EUR_USD"])
    direction: str = Field(..., pattern="^(buy|sell)$")
    entry: float
    stop_loss: float
    account_size: float = 10_000.0
    take_profit: Optional[float] = None
    risk_pct_override: Optional[float] = None
    quote_to_account_rate: Optional[float] = None


class RiskTierOut(BaseModel):
    account_size: float
    risk_pct_min: float
    risk_pct_max: float
    risk_pct_used: float
    unconfirmed: bool
    note: str = ""


class RiskTableOut(BaseModel):
    tiers: List[RiskTierOut]
    min_reward_risk: float
    target_reward_risk: float
    max_trades_per_week: int
    note: str


class WeeklyPaceOut(BaseModel):
    week_start: datetime
    week_end: datetime
    trades_this_week: int
    limit: int
    remaining: int
    at_limit: bool
    message: str


# ---------------------------------------------------------------------------
# Module 2 - sessions
# ---------------------------------------------------------------------------


class SessionWindowOut(BaseModel):
    name: str
    open_ist: str
    close_ist: str
    open_utc: str
    close_utc: str
    is_active: bool
    crosses_midnight: bool
    minutes_until_open: Optional[int] = None
    minutes_until_close: Optional[int] = None


class SessionClockOut(BaseModel):
    now_utc: datetime
    now_ist: datetime
    sessions: List[SessionWindowOut]
    active_sessions: List[str] = Field(default_factory=list)
    overlap: Optional[str] = None
    in_primary_window: bool = False
    primary_window_ist: str = ""
    minutes_until_primary_open: Optional[int] = None
    minutes_until_primary_close: Optional[int] = None
    message: str = ""


# ---------------------------------------------------------------------------
# Modules 1, 13, 14 - reference
# ---------------------------------------------------------------------------


class PairExplainerOut(BaseModel):
    symbol: str
    base: str
    quote: str
    base_name: str
    quote_name: str
    is_major: bool
    pip_size: float
    quote_example: str
    up_means: str
    down_means: str
    buy_when: str
    sell_when: str


class FlaggedItemOut(BaseModel):
    id: str
    title: str
    module: str
    current_value: str
    note: str


class ReferenceOut(BaseModel):
    majors: List[str]
    chart_types: List[str]
    tools: List[Dict[str, str]]
    brokers: List[Dict[str, str]]
    guiding_principle: Dict[str, str]
    golden_rules: List[str]
    flagged_for_confirmation: List[FlaggedItemOut]


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------


class ScenarioOut(BaseModel):
    key: str
    symbol: str
    title: str
    description: str
    demonstrates: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# The full analysis
# ---------------------------------------------------------------------------


class AnalysisOut(BaseModel):
    symbol: str
    generated_at: datetime
    entry_timeframe: str
    current_price: float
    bias: str
    tradeable: bool

    top_down: TopDownOut
    aoi_scans: Dict[str, AOIScanOut] = Field(default_factory=dict)
    valid_zones: List[AOIZoneOut] = Field(default_factory=list)
    active_zone: Optional[AOIZoneOut] = None

    trigger: Optional[TriggerOut] = None
    patterns: Dict[str, List[PatternOut]] = Field(default_factory=dict)
    actionable_patterns: List[PatternOut] = Field(default_factory=list)
    head_shoulders: Dict[str, List[HeadShouldersOut]] = Field(default_factory=dict)
    ema: Optional[EMAOut] = None

    confluence: Optional[ConfluenceOut] = None
    trade_plan: Optional[TradePlanOut] = None
    session: Optional[SessionClockOut] = None
    weekly_pace: Optional[WeeklyPaceOut] = None

    guardrails: List[str] = Field(default_factory=list)
    narrative: List[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    """Analyse pasted OHLC data instead of a bundled scenario."""

    symbol: str = Field(..., examples=["EUR_USD"])
    #: CSV text keyed by timeframe, e.g. ``{"1D": "time,open,...", "1W": "..."}``.
    csv_by_timeframe: Dict[str, str]
    account_size: float = 10_000.0
    entry_timeframe: str = "1H"


# ---------------------------------------------------------------------------
# Module 12 - journal
# ---------------------------------------------------------------------------


class JournalEntryOut(BaseModel):
    id: str
    symbol: str
    direction: str
    placed_at: datetime
    week_key: str

    sync_state: str = ""
    sync_timeframes: List[str] = Field(default_factory=list)
    aoi_zone: Optional[str] = None
    aoi_timeframe: Optional[str] = None
    aoi_touches: int = 0
    patterns: List[str] = Field(default_factory=list)
    confluence_score: int = 0
    confluence_max: int = 0
    low_risk_high_reward: bool = False

    entry: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    planned_rr: float = 0.0
    position_size_lots: float = 0.0
    risk_amount: float = 0.0

    outcome: str = "open"
    exit_price: Optional[float] = None
    closed_at: Optional[datetime] = None
    realised_rr: Optional[float] = None
    pnl: Optional[float] = None
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    is_placed: bool = True


class JournalLogRequest(BaseModel):
    symbol: str
    direction: str = Field(..., pattern="^(buy|sell)$")
    entry: float
    stop_loss: float
    take_profit: float
    position_size_lots: float = 0.0
    risk_amount: float = 0.0
    planned_rr: float = 0.0
    sync_state: str = ""
    sync_timeframes: List[str] = Field(default_factory=list)
    aoi_zone: Optional[str] = None
    aoi_timeframe: Optional[str] = None
    aoi_touches: int = 0
    patterns: List[str] = Field(default_factory=list)
    confluence_score: int = 0
    confluence_max: int = 0
    low_risk_high_reward: bool = False
    notes: str = ""
    tags: List[str] = Field(default_factory=list)


class JournalCloseRequest(BaseModel):
    exit_price: float
    outcome: Optional[str] = None
    pnl: Optional[float] = None


class JournalEditRequest(BaseModel):
    """Set & Forget: editing levels needs an explicit acknowledgement."""

    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    acknowledge_set_and_forget: bool = False


class JournalEditResponse(BaseModel):
    entry: JournalEntryOut
    #: Non-empty when the edit was blocked pending acknowledgement.
    notice: str = ""
    applied: bool = False


class JournalWeekOut(BaseModel):
    week: str
    trade_count: int
    limit: int
    over_limit: bool
    trades: List[JournalEntryOut]


# ---------------------------------------------------------------------------
# TradingAgents bridge - optional LLM second opinion
# ---------------------------------------------------------------------------


class BridgeStatusOut(BaseModel):
    available: bool
    package_importable: bool
    provider: str = ""
    model: str = ""
    api_key_env: Optional[str] = None
    api_key_present: bool = False
    reason: str = ""
    #: True when the provider was inferred from whichever API key is present.
    provider_autodetected: bool = False
    #: True when TRADINGAGENTS_LLM_PROVIDER pinned the provider.
    provider_explicit: bool = False


class SetupReviewOut(BaseModel):
    """LLM commentary on a rule-checked setup. The engine stays authoritative."""

    available: bool
    symbol: str = ""
    engine_verdict: str = ""
    bull_case: str = ""
    bear_case: str = ""
    verdict: str = ""
    key_risks: List[str] = Field(default_factory=list)
    model_used: str = ""
    reason: str = ""
    disclaimer: str = ""


class JournalStatsOut(BaseModel):
    closed_trades: float
    wins: float
    losses: float
    win_rate: float
    average_rr: float
    average_confluence: float
    total_pnl: float
