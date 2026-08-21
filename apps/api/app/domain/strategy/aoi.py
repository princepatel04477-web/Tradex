"""Module 5 - Area of Interest detector and validator.

"No AOI, no trade." This is a validator, not a visual guess. A zone is only
returned as valid when it satisfies every rule from the notes:

* computed on **Weekly and Daily only** - never 4H;
* **3 or more touches**, where a touch is a genuine support/resistance
  reaction, not a slice straight through the level;
* width between **5 and 60 pips** - wider is rejected outright, never clipped;
* sitting **inside the current structural range** - not above the most recent
  HH in an uptrend, not below the most recent LL in a downtrend;
* tagged by the Golden Rule - support is a Buy zone, resistance a Sell zone.

When nothing qualifies the scan says so explicitly rather than relaxing a rule
to manufacture a zone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from . import config
from .pips import from_pips, to_pips
from .types import AOIZone, Candle, StructureResult, SwingKind, Trend, ZoneType


@dataclass
class AOIScan:
    """Result of scanning one timeframe for Areas of Interest."""

    timeframe: str
    allowed: bool
    zones: List[AOIZone] = field(default_factory=list)
    rejected: List[AOIZone] = field(default_factory=list)
    message: str = ""

    @property
    def has_valid_aoi(self) -> bool:
        return bool(self.zones)

    @property
    def best(self) -> Optional[AOIZone]:
        """Highest-confidence valid zone, or ``None``."""
        return self.zones[0] if self.zones else None


def aoi_allowed(timeframe: str) -> bool:
    """AOI may only be computed on the timeframes in ``config.AOI_TIMEFRAMES``."""
    return timeframe in config.AOI_TIMEFRAMES


def detect_aoi_zones(
    candles: List[Candle],
    timeframe: str,
    symbol: str,
    structure: Optional[StructureResult] = None,
    max_zones: int = 6,
) -> AOIScan:
    """Find and validate Areas of Interest on a Weekly or Daily series.

    Args:
        candles: OHLC series for ``timeframe``.
        timeframe: must be Weekly or Daily.
        symbol: pair, used for pip conversion.
        structure: structure read for the same timeframe. When supplied, zones
            outside the current structural range are rejected.
        max_zones: cap on how many valid zones to return.

    Returns:
        An :class:`AOIScan`. ``zones`` holds valid zones sorted strongest
        first; ``rejected`` holds near-misses with the reason they failed, so
        the UI can explain itself.
    """
    if not aoi_allowed(timeframe):
        return AOIScan(
            timeframe=timeframe,
            allowed=False,
            message=(
                f"AOI is never computed on {timeframe}. Only look for AOI on "
                f"{' & '.join(config.AOI_TIMEFRAMES)}."
            ),
        )

    if not candles:
        return AOIScan(timeframe, True, message="No candles supplied.")

    scan = AOIScan(timeframe=timeframe, allowed=True)
    swings = structure.swings if structure else []
    if not swings:
        scan.message = config.GUARDRAIL_MESSAGES["no_aoi"]
        return scan

    current_price = candles[-1].close
    clusters = _cluster_levels(swings, symbol)

    seen: List[AOIZone] = []
    for lower, upper, kind in clusters:
        zone = _build_zone(
            lower, upper, kind, candles, timeframe, symbol, current_price, structure
        )
        if _overlaps_existing(zone, seen):
            continue
        seen.append(zone)
        if zone.valid:
            scan.zones.append(zone)
        else:
            scan.rejected.append(zone)

    scan.zones.sort(key=lambda z: (z.confidence, z.touches), reverse=True)
    scan.zones = scan.zones[:max_zones]

    if not scan.zones:
        scan.message = config.GUARDRAIL_MESSAGES["no_aoi"]
    else:
        best = scan.zones[0]
        scan.message = (
            f"{len(scan.zones)} valid AOI on {timeframe}. Strongest: "
            f"{best.lower:g}-{best.upper:g} ({best.golden_rule_tag}, "
            f"{best.touches} touches)."
        )
    return scan


def _cluster_levels(swings, symbol: str) -> List[tuple]:
    """Group nearby swing levels into candidate zones.

    Highs and lows are clustered separately: a cluster of swing highs is a
    resistance candidate, a cluster of swing lows a support candidate. Greedy
    grouping keeps a cluster only while its span stays inside the maximum
    allowed zone width.
    """
    max_width = from_pips(config.AOI.max_width_pips, symbol)
    clusters: List[tuple] = []

    for kind in (SwingKind.HIGH, SwingKind.LOW):
        levels = sorted(s.price for s in swings if s.kind is kind)
        if not levels:
            continue
        group = [levels[0]]
        for price in levels[1:]:
            if price - group[0] <= max_width:
                group.append(price)
            else:
                clusters.append((min(group), max(group), kind))
                group = [price]
        clusters.append((min(group), max(group), kind))

    return clusters


def _build_zone(
    lower: float,
    upper: float,
    kind: SwingKind,
    candles: List[Candle],
    timeframe: str,
    symbol: str,
    current_price: float,
    structure: Optional[StructureResult],
) -> AOIZone:
    """Widen a cluster to the minimum zone width, count touches, then validate."""
    min_width = from_pips(config.AOI.min_width_pips, symbol)

    # A cluster tighter than the 5-pip floor is widened around its midpoint;
    # a cluster wider than 60 pips is left alone so it is REJECTED, not clipped.
    if (upper - lower) < min_width:
        mid = (lower + upper) / 2.0
        lower, upper = mid - min_width / 2.0, mid + min_width / 2.0

    zone_type = _classify(lower, upper, kind, current_price)
    zone = AOIZone(
        timeframe=timeframe,
        lower=lower,
        upper=upper,
        zone_type=zone_type,
        touches=0,
        width_pips=round(to_pips(upper - lower, symbol), 1),
    )

    indices, times = _count_touches(zone, candles, symbol)
    zone.touches = len(indices)
    zone.touch_indices = indices
    zone.touch_times = times

    _validate(zone, symbol, structure)
    return zone


def _classify(
    lower: float, upper: float, kind: SwingKind, current_price: float
) -> ZoneType:
    """Support below price, resistance above; a straddling zone keeps its origin.

    A level flips role once price trades through it, which is why position
    relative to current price wins over the pivot kind that seeded the cluster.
    """
    if current_price > upper:
        return ZoneType.SUPPORT
    if current_price < lower:
        return ZoneType.RESISTANCE
    return ZoneType.RESISTANCE if kind is SwingKind.HIGH else ZoneType.SUPPORT


def _count_touches(zone: AOIZone, candles: List[Candle], symbol: str) -> tuple:
    """Count distinct reactions at the zone.

    A touch requires the candle to trade into the zone **and react away from
    it** - closing back out on the correct side. A candle that closes through
    the zone is a break, not a touch, and is not counted.

    Two touches only count separately once price has genuinely *left* the zone
    in between, by ``touch_separation_pips``. Without that, one slow drift
    through a narrow band would score three "touches" and manufacture an AOI
    out of a single move.
    """
    tol = from_pips(config.AOI.touch_tolerance_pips, symbol)
    separation = from_pips(config.AOI.touch_separation_pips, symbol)
    lower, upper = zone.lower - tol, zone.upper + tol

    indices: List[int] = []
    times: List = []
    last_index = -10_000
    #: Price must clear the zone by `separation` before the next touch counts.
    departed = True

    for i, candle in enumerate(candles):
        entered = candle.low <= upper and candle.high >= lower

        if not entered:
            # Track whether price has moved far enough away to reset the count.
            if candle.low > zone.upper + separation or candle.high < zone.lower - separation:
                departed = True
            continue

        if not departed:
            continue

        if i - last_index < config.AOI.min_candles_between_touches:
            continue

        if not _reacted(zone, candles, i, separation):
            continue

        indices.append(i)
        times.append(candle.time)
        last_index = i
        departed = False

    return indices, times


def _reacted(
    zone: AOIZone, candles: List[Candle], index: int, separation: float, horizon: int = 12
) -> bool:
    """Did price actually react at the zone, or just pass through it?

    The notes count a touch as "a price reaction at either a support point or a
    resistance point" - so a level respected from above *or* from below counts,
    which is what lets one AOI work for both buying and selling.

    What must not count is price sliding straight through. So the approach
    direction decides which way a reaction has to go: price arriving from above
    must go back up, price arriving from below must go back down - within
    ``horizon`` candles and by ``separation`` pips, without ever closing through
    to the far side.
    """
    approach = _approach_side(zone, candles, index)
    if approach is None:
        return False

    for candle in candles[index : index + horizon + 1]:
        if approach == "above":
            if candle.close < zone.lower:
                return False  # Closed through - that is a break, not a touch.
            if candle.high >= zone.upper + separation:
                return True
        else:
            if candle.close > zone.upper:
                return False
            if candle.low <= zone.lower - separation:
                return True

    return False


def _approach_side(
    zone: AOIZone, candles: List[Candle], index: int, lookback: int = 20
) -> Optional[str]:
    """Which side price came from - ``"above"``, ``"below"``, or unknown."""
    for j in range(index - 1, max(-1, index - lookback - 1), -1):
        candle = candles[j]
        if candle.low > zone.upper:
            return "above"
        if candle.high < zone.lower:
            return "below"
    return None


def _validate(
    zone: AOIZone, symbol: str, structure: Optional[StructureResult]
) -> None:
    """Apply every AOI rule, recording each failure rather than silently hiding it."""
    reasons: List[str] = []

    if zone.touches < config.AOI.min_touches:
        reasons.append(
            f"Only {zone.touches} touch(es) - needs at least "
            f"{config.AOI.min_touches} to be a valid AOI."
        )

    if zone.width_pips > config.AOI.max_width_pips:
        reasons.append(
            f"Zone is {zone.width_pips:g} pips wide - wider than the "
            f"{config.AOI.max_width_pips:g} pip maximum, so it is rejected "
            f"(not clipped)."
        )
    elif zone.width_pips < config.AOI.min_width_pips:
        reasons.append(
            f"Zone is {zone.width_pips:g} pips wide - under the "
            f"{config.AOI.min_width_pips:g} pip minimum."
        )

    if structure is not None:
        rng = structure.structural_range
        if rng is None:
            if structure.trend is Trend.UNDETERMINED:
                reasons.append(
                    "Structure is undetermined, so the zone cannot be placed "
                    "inside a structural range."
                )
        else:
            low, high = rng
            # The zone must intersect the current structural range. A support
            # AOI legitimately straddles the HL and a resistance AOI the LH -
            # what is rejected is a zone lying entirely beyond the extreme.
            if zone.lower > high:
                label = "HH" if structure.trend is Trend.BULLISH else "LH"
                reasons.append(
                    f"Zone sits entirely above the current {label} ({high:g}) - "
                    f"outside the structural range."
                )
            elif zone.upper < low:
                label = "HL" if structure.trend is Trend.BULLISH else "LL"
                reasons.append(
                    f"Zone sits entirely below the current {label} ({low:g}) - "
                    f"outside the structural range."
                )

    zone.rejection_reasons = reasons
    zone.valid = not reasons
    zone.confidence = _confidence(zone.touches) if zone.valid else 0.0


def _confidence(touches: int) -> float:
    """0.0-1.0, scaling with touch count. More touches = stronger zone."""
    floor = config.AOI.min_touches
    ceiling = config.AOI.touches_for_full_confidence
    if touches < floor:
        return 0.0
    if ceiling <= floor:
        return 1.0
    span = ceiling - floor + 1
    return round(min(1.0, (touches - floor + 1) / span), 2)


def _overlaps_existing(zone: AOIZone, existing: List[AOIZone]) -> bool:
    """Drop a zone that substantially overlaps one already collected."""
    for other in existing:
        overlap = min(zone.upper, other.upper) - max(zone.lower, other.lower)
        if overlap <= 0:
            continue
        smaller = min(zone.upper - zone.lower, other.upper - other.lower)
        if smaller > 0 and overlap / smaller > 0.5:
            return True
    return False


def zone_at_price(zones: List[AOIZone], price: float) -> Optional[AOIZone]:
    """The valid zone currently containing ``price``, if any."""
    for zone in zones:
        if zone.valid and zone.contains(price):
            return zone
    return None
