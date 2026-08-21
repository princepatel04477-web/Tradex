"""Core value types shared by every strategy module.

These are plain dataclasses on purpose: the calculation engine stays free of
web-framework types so it can be unit tested and reused headlessly. Pydantic
models live at the API boundary only (``app/schemas/strategy.py``).

Terminology follows the trader's notes exactly: HH / HL / LH / LL, AOI, CHoCH,
RR, EMA.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class Trend(str, Enum):
    """Market direction as decided by structure - never by an indicator."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    UNDETERMINED = "undetermined"

    @property
    def opposite(self) -> "Trend":
        if self is Trend.BULLISH:
            return Trend.BEARISH
        if self is Trend.BEARISH:
            return Trend.BULLISH
        return Trend.UNDETERMINED


class SwingKind(str, Enum):
    """Whether a pivot is a swing high or a swing low."""

    HIGH = "high"
    LOW = "low"


class StructureLabel(str, Enum):
    """The four structure labels from the notes."""

    HH = "HH"
    HL = "HL"
    LH = "LH"
    LL = "LL"


class ZoneType(str, Enum):
    """Golden Rule: Buy = Support, Sell = Resistance."""

    SUPPORT = "support"
    RESISTANCE = "resistance"

    @property
    def golden_rule_tag(self) -> str:
        return "Buy zone" if self is ZoneType.SUPPORT else "Sell zone"


class Direction(str, Enum):
    """Trade direction."""

    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class Candle:
    """One OHLC bar. ``volume`` is optional - FX tick volume is broker-specific."""

    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    @property
    def body_high(self) -> float:
        """Top of the candle body (ignores wicks)."""
        return max(self.open, self.close)

    @property
    def body_low(self) -> float:
        """Bottom of the candle body (ignores wicks)."""
        return min(self.open, self.close)

    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)

    @property
    def range_size(self) -> float:
        return self.high - self.low

    @property
    def upper_wick(self) -> float:
        return self.high - self.body_high

    @property
    def lower_wick(self) -> float:
        return self.body_low - self.low

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open

    @property
    def body_ratio(self) -> float:
        """Body as a fraction of the full range. 0.0 for a zero-range bar."""
        if self.range_size <= 0:
            return 0.0
        return self.body_size / self.range_size


@dataclass
class SwingPoint:
    """A pivot high or low, optionally labelled HH / HL / LH / LL.

    A swing stops being *live* structure once it is broken. Two things break it:

    * a later candle **body close** through the level - the high was taken out,
      or the low was closed below, so the point is history and its label no
      longer describes where structure sits;
    * a CHoCH after it - the notes relabel everything once the trend flips, so
      a label carried over from the dead trend is stale by definition.

    Broken points are kept (the sequence is still the audit trail of how the
    read was reached) but are flagged so the chart can drop them.
    """

    index: int
    time: datetime
    price: float
    kind: SwingKind
    label: Optional[StructureLabel] = None
    #: True once this point is no longer part of the live structure read.
    broken: bool = False
    #: Candle that broke it, when ``broken``.
    broken_index: Optional[int] = None
    broken_time: Optional[datetime] = None
    #: Why it is no longer live - shown in the chart tooltip.
    broken_reason: str = ""

    @property
    def is_high(self) -> bool:
        return self.kind is SwingKind.HIGH

    @property
    def is_live(self) -> bool:
        """Still part of the current structure read."""
        return not self.broken


@dataclass
class ChochEvent:
    """A Change of Character - the candle body close that flipped the trend.

    Per the notes, a body close beyond the last HL (in an uptrend) or the last
    LH (in a downtrend) flips direction and forces a relabel of everything
    after it.
    """

    index: int
    time: datetime
    close: float
    broken_level: float
    broken_label: StructureLabel
    from_trend: Trend
    to_trend: Trend

    @property
    def description(self) -> str:
        return (
            f"CHoCH: body close at {self.close:g} broke the "
            f"{self.broken_label.value} at {self.broken_level:g} - "
            f"{self.from_trend.value} -> {self.to_trend.value}"
        )


@dataclass
class StructureResult:
    """Everything the structure engine knows about one timeframe."""

    timeframe: str
    trend: Trend
    swings: List[SwingPoint] = field(default_factory=list)
    choch_events: List[ChochEvent] = field(default_factory=list)
    #: The HL that must hold for a bullish trend to survive.
    last_valid_hl: Optional[SwingPoint] = None
    #: The LH that must hold for a bearish trend to survive.
    last_valid_lh: Optional[SwingPoint] = None
    #: Most recent HH (bullish) / LL (bearish) - the structural extreme.
    last_hh: Optional[SwingPoint] = None
    last_ll: Optional[SwingPoint] = None
    #: Candles actually examined after applying the lookback window.
    candles_analysed: int = 0

    @property
    def live_swings(self) -> List[SwingPoint]:
        """Only the swings that still describe the current structure.

        This is what belongs on a chart: every HH/HL/LH/LL whose level has been
        closed through, and every label left over from before the last CHoCH,
        has already been dropped.
        """
        return [s for s in self.swings if s.is_live]

    @property
    def structural_range(self) -> Optional[tuple]:
        """(low, high) of the current structural range, or None.

        The AOI validator uses this: a zone must sit inside the current range -
        not above the most recent HH in an uptrend, not below the most recent
        LL in a downtrend.
        """
        if self.trend is Trend.BULLISH and self.last_hh and self.last_valid_hl:
            return (self.last_valid_hl.price, self.last_hh.price)
        if self.trend is Trend.BEARISH and self.last_ll and self.last_valid_lh:
            return (self.last_ll.price, self.last_valid_lh.price)
        return None


@dataclass
class AOIZone:
    """A validated Area of Interest.

    Only ever produced on Weekly or Daily. A zone that fails any rule is
    returned as ``valid=False`` with ``rejection_reasons`` populated, so the
    UI can explain *why* nothing is tradeable instead of silently hiding it.
    """

    timeframe: str
    lower: float
    upper: float
    zone_type: ZoneType
    touches: int
    touch_indices: List[int] = field(default_factory=list)
    touch_times: List[datetime] = field(default_factory=list)
    width_pips: float = 0.0
    valid: bool = False
    rejection_reasons: List[str] = field(default_factory=list)
    #: 0.0-1.0, scales with touch count.
    confidence: float = 0.0

    @property
    def mid(self) -> float:
        return (self.lower + self.upper) / 2.0

    @property
    def golden_rule_tag(self) -> str:
        return self.zone_type.golden_rule_tag

    def contains(self, price: float) -> bool:
        return self.lower <= price <= self.upper


@dataclass
class BreakRetestSignal:
    """State machine output for the break-and-retest entry trigger.

    ``status`` walks: ``none`` -> ``broken`` -> ``armed`` (retest confirmed).
    Entries are only ever valid at ``armed``.
    """

    status: str = "none"  # none | broken | armed | invalidated
    direction: Optional[Direction] = None
    level: Optional[float] = None
    level_label: str = ""
    break_index: Optional[int] = None
    break_time: Optional[datetime] = None
    break_close: Optional[float] = None
    retest_index: Optional[int] = None
    retest_time: Optional[datetime] = None
    retest_price: Optional[float] = None
    candles_to_retest: Optional[int] = None
    notes: List[str] = field(default_factory=list)

    @property
    def is_armed(self) -> bool:
        return self.status == "armed"


@dataclass
class PatternMatch:
    """A recognised candlestick formation."""

    name: str
    index: int
    time: datetime
    bias: Trend
    #: Raw geometric strength, 0.0-1.0, before timeframe weighting.
    strength: float
    timeframe: str = ""
    #: strength * PATTERN_TIMEFRAME_WEIGHT[timeframe]
    weighted_strength: float = 0.0
    #: True only when the formation sits at/inside a validated AOI. Patterns
    #: away from an AOI are detected but never actionable.
    at_aoi: bool = False
    detail: str = ""


@dataclass
class HeadShouldersPattern:
    """Head & Shoulders or its inverse, built from swing structure."""

    kind: str  # "head_and_shoulders" | "inverse_head_and_shoulders"
    timeframe: str
    left_shoulder: SwingPoint
    head: SwingPoint
    right_shoulder: SwingPoint
    neckline_start: SwingPoint
    neckline_end: SwingPoint
    #: Invalid until the neckline is broken - never surfaced as a signal before.
    neckline_broken: bool = False
    neckline_break_index: Optional[int] = None
    #: Break AND retest of the neckline. The neckline retest IS the AOI retest.
    neckline_retested: bool = False
    neckline_retest_index: Optional[int] = None
    #: Measured move: pattern height projected from the neckline break.
    target_price: Optional[float] = None
    #: True when price sits at the right shoulder with no neckline break yet.
    early_entry_risk: bool = False
    notes: List[str] = field(default_factory=list)

    @property
    def bias(self) -> Trend:
        return Trend.BEARISH if self.kind == "head_and_shoulders" else Trend.BULLISH

    def neckline_price_at(self, index: int) -> float:
        """The neckline's price at a candle index.

        Linear between the two anchors. Past the pattern the slope is only
        honoured for one more pattern-width of candles and then held flat: a
        neckline extrapolated indefinitely drifts away from price and would
        never register a retest, however cleanly price came back to the level.
        """
        i0, i1 = self.neckline_start.index, self.neckline_end.index
        p0, p1 = self.neckline_start.price, self.neckline_end.price
        if i1 == i0:
            return p0

        slope = (p1 - p0) / (i1 - i0)
        width = max(1, self.right_shoulder.index - self.left_shoulder.index)
        horizon = self.right_shoulder.index + width
        effective = min(index, horizon)
        return p0 + slope * (effective - i0)

    @property
    def is_valid_signal(self) -> bool:
        """The pattern only counts once the neckline has actually broken."""
        return self.neckline_broken


@dataclass
class ConfluenceResult:
    """Two linked layers: the mandatory core 4, then the expanded checklist."""

    core_pillars: Dict[str, bool] = field(default_factory=dict)
    core_complete: bool = False
    expanded: Dict[str, bool] = field(default_factory=dict)
    #: Count of confirmed expanded items. Only computed when core_complete.
    score: int = 0
    max_score: int = 0
    low_risk_high_reward: bool = False
    missing_core: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    @property
    def eligible(self) -> bool:
        """No setup is ever suggested with a core pillar missing."""
        return self.core_complete


@dataclass
class TradePlan:
    """A sized, RR-validated plan. Never rendered below the 1:2 RR floor."""

    symbol: str
    direction: Direction
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
    warnings: List[str] = field(default_factory=list)
    risk_tier_unconfirmed: bool = False
