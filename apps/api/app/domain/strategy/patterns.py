"""Module 7 - Candlestick pattern recognizer.

Deterministic OHLC geometry only; no fitting, no fuzzy matching. Every
threshold comes from ``config.PATTERNS``.

Two rules from the notes govern how results are *used*, and both are enforced
here rather than left to the UI:

* a pattern is only **actionable** when it sits at/inside a validated AOI
  (``at_aoi``) - detection still runs everywhere so the chart can show them;
* the higher the timeframe, the stronger the formation - ``weighted_strength``
  applies ``config.PATTERN_TIMEFRAME_WEIGHT``.
"""

from __future__ import annotations

from typing import Callable, List, Optional

from . import config
from .pips import to_pips
from .types import AOIZone, Candle, PatternMatch, Trend


def _too_small(candle: Candle, symbol: str) -> bool:
    """Noise filter - a candle with almost no range never forms a pattern."""
    return to_pips(candle.range_size, symbol) < config.PATTERNS.min_candle_range_pips


# ---------------------------------------------------------------------------
# Single-candle patterns
# ---------------------------------------------------------------------------


def detect_doji(candles: List[Candle], i: int, symbol: str) -> Optional[PatternMatch]:
    """Doji - open and close effectively equal. Indecision."""
    c = candles[i]
    if _too_small(c, symbol) or c.range_size <= 0:
        return None
    if c.body_ratio > config.PATTERNS.doji_max_body_ratio:
        return None

    strength = 1.0 - (c.body_ratio / config.PATTERNS.doji_max_body_ratio)
    return PatternMatch(
        name="Doji",
        index=i,
        time=c.time,
        bias=Trend.UNDETERMINED,
        strength=round(max(0.2, strength), 3),
        detail=f"Body is {c.body_ratio:.1%} of range - indecision.",
    )


def detect_spinning_top(
    candles: List[Candle], i: int, symbol: str
) -> Optional[PatternMatch]:
    """Spinning Top - small body with meaningful wicks on both sides."""
    c = candles[i]
    if _too_small(c, symbol) or c.range_size <= 0:
        return None
    if c.body_ratio > config.PATTERNS.spinning_top_max_body_ratio:
        return None
    if c.body_ratio <= config.PATTERNS.doji_max_body_ratio:
        return None  # That is a doji, not a spinning top.

    upper = c.upper_wick / c.range_size
    lower = c.lower_wick / c.range_size
    min_wick = config.PATTERNS.spinning_top_min_wick_ratio
    if upper < min_wick or lower < min_wick:
        return None

    return PatternMatch(
        name="Spinning Top",
        index=i,
        time=c.time,
        bias=Trend.UNDETERMINED,
        strength=round(min(upper, lower) * 2, 3),
        detail=f"Small body ({c.body_ratio:.1%}) between two wicks - indecision.",
    )


def detect_hammer(candles: List[Candle], i: int, symbol: str) -> Optional[PatternMatch]:
    """Hammer - long lower wick that filled back up. Bullish reversal."""
    c = candles[i]
    if _too_small(c, symbol) or c.range_size <= 0 or c.body_size <= 0:
        return None

    long_lower = c.lower_wick >= config.PATTERNS.hammer_min_wick_to_body * c.body_size
    small_upper = (
        c.upper_wick / c.range_size
    ) <= config.PATTERNS.hammer_max_opposite_wick_ratio
    if not (long_lower and small_upper):
        return None

    ratio = c.lower_wick / c.body_size
    return PatternMatch(
        name="Hammer",
        index=i,
        time=c.time,
        bias=Trend.BULLISH,
        strength=round(min(1.0, ratio / 4.0), 3),
        detail=(
            f"Lower wick {ratio:.1f}x the body and filled back up - "
            f"sellers rejected."
        ),
    )


def detect_inverted_hammer(
    candles: List[Candle], i: int, symbol: str
) -> Optional[PatternMatch]:
    """Inverted Hammer - long upper wick that filled back down. Bearish rejection."""
    c = candles[i]
    if _too_small(c, symbol) or c.range_size <= 0 or c.body_size <= 0:
        return None

    long_upper = c.upper_wick >= config.PATTERNS.hammer_min_wick_to_body * c.body_size
    small_lower = (
        c.lower_wick / c.range_size
    ) <= config.PATTERNS.hammer_max_opposite_wick_ratio
    if not (long_upper and small_lower):
        return None

    ratio = c.upper_wick / c.body_size
    return PatternMatch(
        name="Inverted Hammer",
        index=i,
        time=c.time,
        bias=Trend.BEARISH,
        strength=round(min(1.0, ratio / 4.0), 3),
        detail=(
            f"Upper wick {ratio:.1f}x the body and filled back down - "
            f"buyers rejected."
        ),
    )


# ---------------------------------------------------------------------------
# Two-candle patterns
# ---------------------------------------------------------------------------


def detect_engulfing(
    candles: List[Candle], i: int, symbol: str
) -> Optional[PatternMatch]:
    """Bullish / Bearish Engulfing.

    The engulfing candle's **body** must fully cover the prior candle's body -
    body, never the wick. Strength is then assessed across the last two
    candles' bodies collectively, so a candle that swallows two prior bodies
    scores higher than one that only clears its immediate neighbour.
    """
    if i < 1:
        return None
    c, prev = candles[i], candles[i - 1]
    if _too_small(c, symbol) or c.body_size <= 0 or prev.body_size <= 0:
        return None

    covers_prev = c.body_low <= prev.body_low and c.body_high >= prev.body_high
    if not covers_prev:
        return None

    if c.is_bullish and prev.is_bearish:
        name, bias = "Bullish Engulfing", Trend.BULLISH
    elif c.is_bearish and prev.is_bullish:
        name, bias = "Bearish Engulfing", Trend.BEARISH
    else:
        return None

    # Collective assessment over the previous two bodies.
    span_low, span_high = prev.body_low, prev.body_high
    covered_two = False
    if i >= 2:
        prev2 = candles[i - 2]
        span_low = min(span_low, prev2.body_low)
        span_high = max(span_high, prev2.body_high)
        covered_two = c.body_low <= span_low and c.body_high >= span_high

    span = max(span_high - span_low, 1e-12)
    ratio = c.body_size / span
    strength = min(1.0, ratio / config.PATTERNS.engulfing_strong_body_ratio)
    if covered_two:
        strength = min(1.0, strength + 0.2)

    detail = f"Body covers the prior body {ratio:.2f}x"
    detail += " and engulfs both preceding bodies." if covered_two else "."
    if ratio >= config.PATTERNS.engulfing_strong_body_ratio:
        detail += " Strong."

    return PatternMatch(
        name=name,
        index=i,
        time=c.time,
        bias=bias,
        strength=round(strength, 3),
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Three-candle patterns
# ---------------------------------------------------------------------------


def detect_star(candles: List[Candle], i: int, symbol: str) -> Optional[PatternMatch]:
    """Morning Star (bullish) / Evening Star (bearish).

    Three candles: a decisive first candle, a small-bodied middle candle that
    stalls, then a third candle closing well back into the first candle's body.
    """
    if i < 2:
        return None
    first, middle, last = candles[i - 2], candles[i - 1], candles[i]
    if first.body_size <= 0 or last.body_size <= 0:
        return None
    if _too_small(last, symbol):
        return None

    middle_is_small = (
        middle.body_size <= config.PATTERNS.star_max_middle_body_ratio * first.body_size
    )
    if not middle_is_small:
        return None

    if first.is_bearish and last.is_bullish:
        name, bias = "Morning Star", Trend.BULLISH
        # Third candle must close back up into the first candle's body.
        penetration = (last.close - first.close) / first.body_size
        middle_stalls = middle.body_high < first.close or middle.low < first.close
    elif first.is_bullish and last.is_bearish:
        name, bias = "Evening Star", Trend.BEARISH
        penetration = (first.close - last.close) / first.body_size
        middle_stalls = middle.body_low > first.close or middle.high > first.close
    else:
        return None

    if penetration < config.PATTERNS.star_min_penetration or not middle_stalls:
        return None

    return PatternMatch(
        name=name,
        index=i,
        time=last.time,
        bias=bias,
        strength=round(min(1.0, penetration), 3),
        detail=(
            f"Small middle body ({middle.body_size / first.body_size:.0%} of "
            f"candle 1) then a close {penetration:.0%} back into candle 1 - "
            f"{'bullish reversal' if bias is Trend.BULLISH else 'bearish reversal'}."
        ),
    )


DETECTORS: tuple[Callable[[List[Candle], int, str], Optional[PatternMatch]], ...] = (
    detect_doji,
    detect_spinning_top,
    detect_hammer,
    detect_inverted_hammer,
    detect_engulfing,
    detect_star,
)


def detect_patterns(
    candles: List[Candle],
    timeframe: str,
    symbol: str,
    aoi_zones: Optional[List[AOIZone]] = None,
    scan_last: Optional[int] = None,
) -> List[PatternMatch]:
    """Run every detector across the series.

    Args:
        candles: OHLC series.
        timeframe: used for the strength weighting.
        symbol: pair, for pip-based noise filtering.
        aoi_zones: validated AOI zones. A pattern overlapping one is flagged
            ``at_aoi`` - the only state in which it is actionable.
        scan_last: only scan the final N candles (the whole series if ``None``).

    Returns:
        Matches in chronological order.
    """
    if not candles:
        return []

    start = 0 if scan_last is None else max(0, len(candles) - scan_last)
    weight = config.PATTERN_TIMEFRAME_WEIGHT.get(timeframe, 1.0)
    valid_zones = [z for z in (aoi_zones or []) if z.valid]

    matches: List[PatternMatch] = []
    for i in range(start, len(candles)):
        for detector in DETECTORS:
            match = detector(candles, i, symbol)
            if match is None:
                continue
            match.timeframe = timeframe
            match.weighted_strength = round(match.strength * weight, 3)
            match.at_aoi = _touches_zone(candles[i], valid_zones)
            matches.append(match)

    return matches


def _touches_zone(candle: Candle, zones: List[AOIZone]) -> bool:
    """True when the candle trades inside any validated AOI."""
    return any(candle.low <= z.upper and candle.high >= z.lower for z in zones)


def actionable(matches: List[PatternMatch]) -> List[PatternMatch]:
    """Only patterns formed at a validated AOI can be traded."""
    return [m for m in matches if m.at_aoi]


def strongest(
    matches: List[PatternMatch], bias: Optional[Trend] = None
) -> Optional[PatternMatch]:
    """Highest weighted-strength actionable match, optionally filtered by bias."""
    pool = actionable(matches)
    if bias is not None:
        pool = [m for m in pool if m.bias is bias]
    if not pool:
        return None
    return max(pool, key=lambda m: m.weighted_strength)
