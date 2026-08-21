"""Module 3 - Multi-timeframe market structure engine.

Implements the notes' structure rules literally:

* Swing highs/lows are found with a fractal/pivot scan, then labelled
  HH / HL (bullish) or LH / LL (bearish).
* A **candle body close** beyond the last HL (uptrend) or last LH (downtrend)
  is a CHoCH - it flips the trend and forces a relabel of everything after it.
  Wicks never flip structure, only closes do.
* A new HH puts a fresh HL in play; mirrored for LL -> LH.
* Each timeframe is analysed against its own closes only, so a violent wick on
  a lower timeframe cannot disturb a higher timeframe's read.
* ``trace_last_valid_structure_point`` is the "snake trick": walk backward from
  the most recent extreme until the zigzag turns.

Everything here is a pure function of the candle series.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from . import config
from .types import (
    Candle,
    ChochEvent,
    StructureLabel,
    StructureResult,
    SwingKind,
    SwingPoint,
    Trend,
)


def apply_lookback(candles: List[Candle], timeframe: str) -> List[Candle]:
    """Trim the series to the configured lookback window for this timeframe.

    Weekly reads ~5-6 years, Daily ~1-2 years, 4H ~6-12 months (notes s.9).
    """
    limit = config.STRUCTURE_LOOKBACK_CANDLES.get(timeframe)
    if not limit or len(candles) <= limit:
        return list(candles)
    return list(candles[-limit:])


def find_swing_points(
    candles: List[Candle],
    lookback: int = 3,
    enforce_alternation: bool = True,
) -> List[SwingPoint]:
    """Fractal/pivot scan for swing highs and lows.

    A swing high at ``i`` has no higher high within ``lookback`` candles either
    side; a swing low has no lower low. Wicks (high/low) define pivots - this is
    the one place wicks matter, because a pivot *is* an extreme.

    Args:
        candles: the series to scan.
        lookback: half-width of the pivot window.
        enforce_alternation: collapse runs of same-kind swings down to the most
            extreme one, so the result is a clean alternating zigzag.

    Returns:
        Swing points in chronological order.
    """
    if lookback < 1 or len(candles) < (2 * lookback + 1):
        return []

    raw: List[SwingPoint] = []
    for i in range(lookback, len(candles) - lookback):
        window = candles[i - lookback : i + lookback + 1]
        pivot = candles[i]

        highs = [c.high for c in window]
        lows = [c.low for c in window]

        # Strict on the left, non-strict on the right: with a flat double top
        # the first bar owns the pivot, so the same bar is never emitted twice.
        is_high = pivot.high == max(highs) and all(
            c.high < pivot.high for c in candles[i - lookback : i]
        )
        is_low = pivot.low == min(lows) and all(
            c.low > pivot.low for c in candles[i - lookback : i]
        )

        if is_high:
            raw.append(SwingPoint(i, pivot.time, pivot.high, SwingKind.HIGH))
        if is_low:
            raw.append(SwingPoint(i, pivot.time, pivot.low, SwingKind.LOW))

    raw.sort(key=lambda s: (s.index, 0 if s.kind is SwingKind.LOW else 1))

    if not enforce_alternation:
        return raw
    return _collapse_to_zigzag(raw)


def _collapse_to_zigzag(swings: List[SwingPoint]) -> List[SwingPoint]:
    """Reduce runs of consecutive same-kind swings to the most extreme one."""
    result: List[SwingPoint] = []
    for swing in swings:
        if not result or result[-1].kind is not swing.kind:
            result.append(swing)
            continue
        prev = result[-1]
        keep_new = (
            swing.price > prev.price
            if swing.kind is SwingKind.HIGH
            else swing.price < prev.price
        )
        if keep_new:
            result[-1] = swing
    return result


def _initial_trend(swings: List[SwingPoint]) -> Trend:
    """Seed the trend from the first two highs and two lows available."""
    highs = [s for s in swings if s.kind is SwingKind.HIGH]
    lows = [s for s in swings if s.kind is SwingKind.LOW]
    if len(highs) < 2 or len(lows) < 2:
        return Trend.UNDETERMINED

    rising_highs = highs[1].price > highs[0].price
    rising_lows = lows[1].price > lows[0].price
    if rising_highs and rising_lows:
        return Trend.BULLISH
    if not rising_highs and not rising_lows:
        return Trend.BEARISH
    # Highs and lows disagree - fall back to the wider leg's direction.
    return Trend.BULLISH if rising_lows else Trend.BEARISH


def _label(swing: SwingPoint, prev_same_kind: Optional[SwingPoint]) -> StructureLabel:
    """Label a swing purely by comparison with the previous swing of its kind."""
    if swing.kind is SwingKind.HIGH:
        if prev_same_kind is None or swing.price > prev_same_kind.price:
            return StructureLabel.HH
        return StructureLabel.LH
    if prev_same_kind is None or swing.price > prev_same_kind.price:
        return StructureLabel.HL
    return StructureLabel.LL


def analyse_structure(
    candles: List[Candle],
    timeframe: str,
    lookback: Optional[int] = None,
) -> StructureResult:
    """Full structure read for one timeframe.

    Walks the series forward in time. A swing at index ``i`` is only *known*
    once ``lookback`` further candles have printed, so CHoCH detection never
    peeks at future data.

    Args:
        candles: OHLC series, chronological.
        timeframe: one of ``config.TIMEFRAMES``.
        lookback: pivot half-width; defaults to ``config.SWING_LOOKBACK``.

    Returns:
        A :class:`StructureResult` with labelled swings, CHoCH events, the
        levels whose break would flip the trend, and the structural extremes.
    """
    lb = lookback if lookback is not None else config.SWING_LOOKBACK.get(timeframe, 3)
    series = apply_lookback(candles, timeframe)

    result = StructureResult(
        timeframe=timeframe,
        trend=Trend.UNDETERMINED,
        candles_analysed=len(series),
    )
    if len(series) < (2 * lb + 1):
        return result

    swings = find_swing_points(series, lb)
    if not swings:
        return result

    # A swing is only confirmed lb candles after it prints.
    pending = [(s.index + lb, s) for s in swings]
    pending.sort(key=lambda t: t[0])

    confirmed: List[SwingPoint] = []
    last_high: Optional[SwingPoint] = None
    last_low: Optional[SwingPoint] = None
    trend = Trend.UNDETERMINED
    #: The low that formed after the most recent HH - breaking it ends the uptrend.
    valid_hl: Optional[SwingPoint] = None
    #: The high that formed after the most recent LL - breaking it ends the downtrend.
    valid_lh: Optional[SwingPoint] = None
    last_hh: Optional[SwingPoint] = None
    last_ll: Optional[SwingPoint] = None
    #: A new HH puts a fresh HL in play - but the previous HL stays the level
    #: that must hold until that fresh low actually confirms. Mirrored for LL.
    awaiting_hl = False
    awaiting_lh = False

    cursor = 0
    for i, candle in enumerate(series):
        # 1. Absorb every swing confirmed as of this candle.
        while cursor < len(pending) and pending[cursor][0] <= i:
            swing = pending[cursor][1]
            cursor += 1
            prev = last_high if swing.kind is SwingKind.HIGH else last_low
            swing.label = _label(swing, prev)
            confirmed.append(swing)

            if swing.kind is SwingKind.HIGH:
                last_high = swing
                if swing.label is StructureLabel.HH:
                    last_hh = swing
                    # A new HH puts a fresh HL in play. The old HL keeps
                    # guarding the trend until that fresh low confirms.
                    awaiting_hl = True
                if trend is Trend.BEARISH and (valid_lh is None or awaiting_lh):
                    valid_lh = swing
                    awaiting_lh = False
            else:
                last_low = swing
                if swing.label is StructureLabel.LL:
                    last_ll = swing
                    awaiting_lh = True
                if trend is Trend.BULLISH and (valid_hl is None or awaiting_hl):
                    valid_hl = swing
                    awaiting_hl = False

            if trend is Trend.UNDETERMINED:
                trend = _initial_trend(confirmed)
                if trend is Trend.BULLISH:
                    valid_hl = valid_hl or last_low
                    last_hh = last_hh or last_high
                elif trend is Trend.BEARISH:
                    valid_lh = valid_lh or last_high
                    last_ll = last_ll or last_low

        # 2. CHoCH: body close beyond the level that defines the current trend.
        #    Wicks are ignored on purpose - only a close flips structure.
        if trend is Trend.BULLISH and valid_hl is not None:
            if candle.close < valid_hl.price:
                result.choch_events.append(
                    ChochEvent(
                        index=i,
                        time=candle.time,
                        close=candle.close,
                        broken_level=valid_hl.price,
                        broken_label=StructureLabel.HL,
                        from_trend=Trend.BULLISH,
                        to_trend=Trend.BEARISH,
                    )
                )
                trend = Trend.BEARISH
                # Relabel forward: the high that led into the break is now the
                # LH to watch, and the broken HL becomes the reference low.
                valid_lh = last_high
                valid_hl = None
                awaiting_hl = False
                awaiting_lh = valid_lh is None
                last_ll = last_low

        elif trend is Trend.BEARISH and valid_lh is not None:
            if candle.close > valid_lh.price:
                result.choch_events.append(
                    ChochEvent(
                        index=i,
                        time=candle.time,
                        close=candle.close,
                        broken_level=valid_lh.price,
                        broken_label=StructureLabel.LH,
                        from_trend=Trend.BEARISH,
                        to_trend=Trend.BULLISH,
                    )
                )
                trend = Trend.BULLISH
                valid_hl = last_low
                valid_lh = None
                awaiting_lh = False
                awaiting_hl = valid_hl is None
                last_hh = last_high

    result.trend = trend
    result.swings = confirmed
    result.last_valid_hl = valid_hl or _last_labelled(confirmed, StructureLabel.HL)
    result.last_valid_lh = valid_lh or _last_labelled(confirmed, StructureLabel.LH)
    result.last_hh = last_hh or _last_labelled(confirmed, StructureLabel.HH)
    result.last_ll = last_ll or _last_labelled(confirmed, StructureLabel.LL)

    # The reference points survive the CHoCH sweep: after a flip the level that
    # now guards the trend is, by construction, a swing from before the flip.
    mark_broken_swings(
        series,
        confirmed,
        result.choch_events,
        keep=(
            result.last_valid_hl,
            result.last_valid_lh,
            result.last_hh,
            result.last_ll,
        ),
    )
    return result


def mark_broken_swings(
    candles: List[Candle],
    swings: List[SwingPoint],
    choch_events: Optional[List[ChochEvent]] = None,
    keep: Sequence[Optional[SwingPoint]] = (),
) -> None:
    """Flag every swing that is no longer part of the live structure read.

    Mutates ``swings`` in place. Two things retire a point, both straight out of
    the notes:

    1. **A body close through the level.** A swing high whose price is later
       closed above has been taken out - the market made a new high, so that
       point is no longer *the* high. Same, mirrored, for a swing low. Wicks are
       ignored here exactly as they are for CHoCH: only a close counts.
    2. **A CHoCH after it.** "A body close beyond the last HL flips the trend
       and forces a relabel of everything after it" - so an HH/HL carried over
       from before the flip is describing a structure that no longer exists.

    Rule 1 alone would leave the losing trend's LLs sitting under a fresh
    uptrend forever, because price never closes below them again; rule 2 is what
    clears them.

    Args:
        candles: the same series the swings were found in.
        swings: labelled swings, chronological. Mutated.
        choch_events: CHoCH events from the same pass, if any.
        keep: swings that must never be retired by rule 2 - the current
            reference points. After a flip the level now guarding the trend is
            necessarily a swing from *before* the flip, so the CHoCH sweep would
            otherwise delete the one line the trader most needs on the chart.
            A genuine close through them (rule 1) still retires them.
    """
    last_choch_index: Optional[int] = None
    if choch_events:
        last_choch_index = choch_events[-1].index
    protected = {id(s) for s in keep if s is not None}

    for swing in swings:
        swing.broken = False
        swing.broken_index = None
        swing.broken_time = None
        swing.broken_reason = ""

        # 1. First later candle whose body closes through the level.
        for j in range(swing.index + 1, len(candles)):
            candle = candles[j]
            through = (
                candle.close > swing.price
                if swing.kind is SwingKind.HIGH
                else candle.close < swing.price
            )
            if through:
                swing.broken = True
                swing.broken_index = j
                swing.broken_time = candle.time
                side = "above" if swing.kind is SwingKind.HIGH else "below"
                swing.broken_reason = (
                    f"Body closed {side} {swing.price:g} at {candle.close:g}"
                )
                break

        # 2. Stale label: the trend flipped after this point was confirmed.
        if not swing.broken and last_choch_index is not None:
            if swing.index < last_choch_index and id(swing) not in protected:
                swing.broken = True
                swing.broken_index = last_choch_index
                swing.broken_time = candles[last_choch_index].time
                swing.broken_reason = "Relabelled by a later CHoCH"


def live_swings(result: StructureResult) -> List[SwingPoint]:
    """Only the swings that still describe the current structure."""
    return result.live_swings


def _last_labelled(
    swings: List[SwingPoint], label: StructureLabel
) -> Optional[SwingPoint]:
    for swing in reversed(swings):
        if swing.label is label:
            return swing
    return None


def trace_last_valid_structure_point(
    swings: List[SwingPoint], trend: Trend
) -> Optional[SwingPoint]:
    """The "snake trick" - backtrace to the last valid HL (or LH).

    Walk backward from the most recent structural extreme along the zigzag,
    stepping over same-direction continuation points, until the line turns.
    That turning point is the last valid structure point: the level whose break
    would flip the trend.

    UNCONFIRMED: this is the engine's best reading of a partially unclear
    passage in the handwritten notes. See ``config.FLAGGED_FOR_CONFIRMATION``.

    Args:
        swings: labelled swing points in chronological order.
        trend: the current trend - decides which extreme we start from.

    Returns:
        The last valid HL in an uptrend, the last valid LH in a downtrend, or
        ``None`` if the zigzag never turns within the available swings.
    """
    if not swings or trend is Trend.UNDETERMINED:
        return None

    want_extreme = SwingKind.HIGH if trend is Trend.BULLISH else SwingKind.LOW
    want_turn = SwingKind.LOW if trend is Trend.BULLISH else SwingKind.HIGH

    # Start at the most recent extreme of the trend's own kind.
    start = None
    for pos in range(len(swings) - 1, -1, -1):
        if swings[pos].kind is want_extreme:
            start = pos
            break
    if start is None:
        return None

    extreme = swings[start]
    for pos in range(start - 1, -1, -1):
        swing = swings[pos]
        if swing.kind is want_extreme:
            # Same-direction continuation point - keep walking back.
            continue
        turned = (
            swing.price < extreme.price
            if trend is Trend.BULLISH
            else swing.price > extreme.price
        )
        if turned and swing.kind is want_turn:
            return swing
    return None


def structural_range(result: StructureResult) -> Optional[Tuple[float, float]]:
    """``(low, high)`` of the current structural range, or ``None``.

    Used by the AOI validator: a zone must sit inside this range - never above
    the most recent HH in an uptrend, never below the most recent LL in a
    downtrend.
    """
    return result.structural_range


def describe(result: StructureResult) -> str:
    """One-line human summary, in the notes' own vocabulary."""
    if result.trend is Trend.UNDETERMINED:
        return f"{result.timeframe}: structure undetermined ({result.candles_analysed} candles)"
    if result.trend is Trend.BULLISH:
        hh = f"{result.last_hh.price:g}" if result.last_hh else "n/a"
        hl = f"{result.last_valid_hl.price:g}" if result.last_valid_hl else "n/a"
        return f"{result.timeframe}: bullish (HH {hh}, HL {hl} must hold)"
    ll = f"{result.last_ll.price:g}" if result.last_ll else "n/a"
    lh = f"{result.last_valid_lh.price:g}" if result.last_valid_lh else "n/a"
    return f"{result.timeframe}: bearish (LL {ll}, LH {lh} must hold)"
