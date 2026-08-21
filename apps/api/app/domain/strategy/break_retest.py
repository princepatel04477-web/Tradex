"""Module 6 - Break & retest / structure-shift detector.

The only valid entry trigger in this strategy. "Don't buy or sell in the
middle of a move" - price must break a level on a **body close**, then come
back and retest it. Entries are never taken mid-zone and never on the break
candle itself.

The signal walks a small state machine::

    none -> broken -> armed
                   -> invalidated
"""

from __future__ import annotations

from typing import List, Optional

from . import config
from .pips import from_pips
from .types import AOIZone, BreakRetestSignal, Candle, Direction, StructureResult, Trend


def detect_break_retest(
    candles: List[Candle],
    level: float,
    symbol: str,
    level_label: str = "",
    direction: Optional[Direction] = None,
    start_index: int = 0,
) -> BreakRetestSignal:
    """Track the most recent break of ``level`` and whether it has been retested.

    Args:
        candles: OHLC series, chronological.
        level: the price being broken - an AOI boundary or a structure point.
        symbol: pair, for pip conversion.
        level_label: human label for the level, e.g. ``"Daily AOI upper"``.
        direction: restrict to up-breaks (``BUY``) or down-breaks (``SELL``).
            ``None`` accepts whichever comes first.
        start_index: ignore candles before this index.

    Returns:
        A :class:`BreakRetestSignal`. ``status`` is ``armed`` only when a break
        has been followed by a confirmed retest - that is the only tradeable
        state.
    """
    signal = BreakRetestSignal(level=level, level_label=level_label)
    if not candles:
        return signal

    min_break = from_pips(config.BREAK_RETEST.min_break_pips, symbol)
    retest_tol = from_pips(config.BREAK_RETEST.retest_tolerance_pips, symbol)
    invalidate = from_pips(config.BREAK_RETEST.invalidation_pips, symbol)

    begin = max(0, start_index)
    #: Where price closed on the previous bar. A break is a *crossing* of the
    #: level, so a candle that merely sits on one side of it is not a break -
    #: without this, any series trading below a level would read as an
    #: immediate downside break on its very first bar.
    prev_close = candles[begin].close

    for i in range(begin, len(candles)):
        candle = candles[i]

        if signal.status in ("none", "invalidated"):
            # --- Look for the break: a BODY CLOSE crossing the level. -------
            broke_up = (
                prev_close <= level + min_break and candle.close > level + min_break
            )
            broke_down = (
                prev_close >= level - min_break and candle.close < level - min_break
            )

            if direction is Direction.BUY:
                broke_down = False
            elif direction is Direction.SELL:
                broke_up = False

            if broke_up or broke_down:
                signal.status = "broken"
                signal.direction = Direction.BUY if broke_up else Direction.SELL
                signal.break_index = i
                signal.break_time = candle.time
                signal.break_close = candle.close
                signal.notes = [
                    f"Break: body close {candle.close:g} cleared {level_label or 'level'} "
                    f"{level:g} to the {'upside' if broke_up else 'downside'}."
                ]

        elif signal.status == "broken":
            # --- Then look for the retest. ----------------------------------
            elapsed = i - (signal.break_index or 0)

            if elapsed > config.BREAK_RETEST.max_candles_to_retest:
                signal.status = "invalidated"
                signal.notes.append(
                    f"No retest within {config.BREAK_RETEST.max_candles_to_retest} "
                    f"candles - setup went stale."
                )

            # A close back through the level means the break was a fakeout.
            elif signal.direction is Direction.BUY and candle.close < level - invalidate:
                signal.status = "invalidated"
                signal.notes.append(
                    f"Invalidated: closed {candle.close:g} back below {level:g}."
                )
            elif signal.direction is Direction.SELL and candle.close > level + invalidate:
                signal.status = "invalidated"
                signal.notes.append(
                    f"Invalidated: closed {candle.close:g} back above {level:g}."
                )
            else:
                # The retest itself: price returns to the level and holds.
                if signal.direction is Direction.BUY:
                    touched = candle.low <= level + retest_tol
                    held = candle.close >= level - min_break
                else:
                    touched = candle.high >= level - retest_tol
                    held = candle.close <= level + min_break

                if touched and held and elapsed >= 1:
                    signal.status = "armed"
                    signal.retest_index = i
                    signal.retest_time = candle.time
                    signal.retest_price = level
                    signal.candles_to_retest = elapsed
                    signal.notes.append(
                        f"Retest confirmed {elapsed} candle(s) after the break - "
                        f"setup armed for a {signal.direction.value}."
                    )

        prev_close = candle.close

    return signal


def scan_for_trigger(
    candles: List[Candle],
    symbol: str,
    structure: StructureResult,
    aoi_zones: Optional[List[AOIZone]] = None,
    bias: Trend = Trend.UNDETERMINED,
) -> BreakRetestSignal:
    """Find the best available entry trigger across AOI edges and structure points.

    Levels are tried in priority order - AOI boundaries first (the notes trade
    the upside or downside *of the AOI*), then the structure points whose break
    would shift the trend. The first armed signal wins; otherwise the furthest
    along signal is returned so the UI can show "broken, waiting for retest".

    Trend is your friend: when ``bias`` is known, only levels that would
    produce a trade *with* the bias are considered. A bullish read never
    returns a sell trigger, however clean the break looks.

    Args:
        candles: series for the entry timeframe.
        symbol: pair.
        structure: structure read for the same series.
        aoi_zones: validated zones from the Weekly/Daily scan.
        bias: the top-down directional bias.

    Returns:
        The best :class:`BreakRetestSignal` found.
    """
    candidates: List[tuple] = []
    wanted = {
        Trend.BULLISH: Direction.BUY,
        Trend.BEARISH: Direction.SELL,
    }.get(bias)

    for zone in aoi_zones or []:
        if not zone.valid:
            continue
        tag = f"{zone.timeframe} AOI ({zone.golden_rule_tag})"
        # Golden Rule: buy at support, sell at resistance.
        if zone.zone_type.value == "support":
            candidates.append((zone.lower, f"{tag} lower", Direction.BUY))
            candidates.append((zone.upper, f"{tag} upper", Direction.BUY))
        else:
            candidates.append((zone.upper, f"{tag} upper", Direction.SELL))
            candidates.append((zone.lower, f"{tag} lower", Direction.SELL))

    if structure.trend is Trend.BULLISH and structure.last_hh:
        candidates.append((structure.last_hh.price, "HH", Direction.BUY))
    if structure.trend is Trend.BEARISH and structure.last_ll:
        candidates.append((structure.last_ll.price, "LL", Direction.SELL))
    if structure.last_valid_hl:
        candidates.append((structure.last_valid_hl.price, "HL", wanted))
    if structure.last_valid_lh:
        candidates.append((structure.last_valid_lh.price, "LH", wanted))

    if wanted is not None:
        candidates = [c for c in candidates if c[2] is wanted]

    best = BreakRetestSignal()
    rank = {"none": 0, "invalidated": 1, "broken": 2, "armed": 3}

    for level, label, direction in candidates:
        signal = detect_break_retest(candles, level, symbol, label, direction)
        if rank[signal.status] > rank[best.status]:
            best = signal
        elif (
            rank[signal.status] == rank[best.status] == 3
            and (signal.retest_index or 0) > (best.retest_index or 0)
        ):
            best = signal

    if best.status != "armed":
        best.notes.append(config.GUARDRAIL_MESSAGES["no_trigger"])
    return best
