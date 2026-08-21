"""Module 8 - Head & Shoulders detector (and the inverse).

Built from swing structure, not from curve fitting: five alternating swing
points make the shoulders, head and the two neckline anchors.

The notes' rules are enforced strictly:

* the pattern is **invalid until the neckline is broken** - it is never
  surfaced as a signal beforehand;
* a **break and retest** of the neckline is required before it is a trigger,
  and that neckline retest *is* the AOI retest - the same event;
* trading off the right shoulder before any neckline break is flagged
  separately as high-risk / early entry, never as a primary signal.
"""

from __future__ import annotations

from typing import List, Optional

from . import config
from .pips import from_pips
from .types import (
    Candle,
    HeadShouldersPattern,
    SwingKind,
    SwingPoint,
    Trend,
)


def detect_head_shoulders(
    candles: List[Candle],
    swings: List[SwingPoint],
    timeframe: str,
    symbol: str,
) -> List[HeadShouldersPattern]:
    """Find every Head & Shoulders and inverse Head & Shoulders in the series.

    Args:
        candles: OHLC series.
        swings: alternating swing points from the structure engine.
        timeframe: label carried onto the result.
        symbol: pair, for pip tolerances.

    Returns:
        Patterns in chronological order. Check ``is_valid_signal`` before
        treating one as tradeable - an unbroken neckline means no signal.
    """
    if len(swings) < 5 or not candles:
        return []

    patterns: List[HeadShouldersPattern] = []

    for i in range(len(swings) - 4):
        window = swings[i : i + 5]
        kinds = [s.kind for s in window]

        # Regular H&S: high, low, high, low, high (a top formation).
        if kinds == [
            SwingKind.HIGH,
            SwingKind.LOW,
            SwingKind.HIGH,
            SwingKind.LOW,
            SwingKind.HIGH,
        ]:
            pattern = _build(window, "head_and_shoulders", timeframe)
        # Inverse H&S: low, high, low, high, low (a bottom formation).
        elif kinds == [
            SwingKind.LOW,
            SwingKind.HIGH,
            SwingKind.LOW,
            SwingKind.HIGH,
            SwingKind.LOW,
        ]:
            pattern = _build(window, "inverse_head_and_shoulders", timeframe)
        else:
            continue

        if pattern is None:
            continue

        _evaluate_neckline(pattern, candles, symbol)
        patterns.append(pattern)

    return patterns


def _build(
    window: List[SwingPoint], kind: str, timeframe: str
) -> Optional[HeadShouldersPattern]:
    """Validate the geometry of five swings and assemble the pattern."""
    left_shoulder, neck_a, head, neck_b, right_shoulder = window
    inverse = kind == "inverse_head_and_shoulders"

    # 1. The head must be the extreme of the three peaks (or troughs).
    if inverse:
        if not (head.price < left_shoulder.price and head.price < right_shoulder.price):
            return None
    else:
        if not (head.price > left_shoulder.price and head.price > right_shoulder.price):
            return None

    neckline_mid = (neck_a.price + neck_b.price) / 2.0
    height = abs(head.price - neckline_mid)
    if height <= 0:
        return None

    # 2. The head must stand clear of the taller shoulder.
    tallest_shoulder = (
        min(left_shoulder.price, right_shoulder.price)
        if inverse
        else max(left_shoulder.price, right_shoulder.price)
    )
    prominence = abs(head.price - tallest_shoulder) / height
    if prominence < config.HEAD_SHOULDERS.min_head_prominence:
        return None

    # 3. The shoulders must roughly match each other, measured from the neckline.
    left_h = abs(left_shoulder.price - neckline_mid)
    right_h = abs(right_shoulder.price - neckline_mid)
    if max(left_h, right_h) <= 0:
        return None
    asymmetry = abs(left_h - right_h) / max(left_h, right_h)
    if asymmetry > config.HEAD_SHOULDERS.shoulder_symmetry_tolerance:
        return None

    # 4. The neckline must not be wildly sloped.
    slope_ratio = abs(neck_a.price - neck_b.price) / height
    if slope_ratio > config.HEAD_SHOULDERS.max_neckline_slope_ratio:
        return None

    pattern = HeadShouldersPattern(
        kind=kind,
        timeframe=timeframe,
        left_shoulder=left_shoulder,
        head=head,
        right_shoulder=right_shoulder,
        neckline_start=neck_a,
        neckline_end=neck_b,
    )
    pattern.notes.append(
        f"Shoulders match within {asymmetry:.0%}; head stands "
        f"{prominence:.0%} of pattern height clear of the taller shoulder."
    )
    return pattern


def _evaluate_neckline(
    pattern: HeadShouldersPattern, candles: List[Candle], symbol: str
) -> None:
    """Walk forward from the right shoulder looking for a break, then a retest."""
    inverse = pattern.kind == "inverse_head_and_shoulders"
    min_break = from_pips(config.BREAK_RETEST.min_break_pips, symbol)
    retest_tol = from_pips(config.BREAK_RETEST.retest_tolerance_pips, symbol)

    start = pattern.right_shoulder.index + 1
    for i in range(start, len(candles)):
        candle = candles[i]
        neckline = pattern.neckline_price_at(i)

        if not pattern.neckline_broken:
            # A body close through the neckline, never a wick.
            broke = (
                candle.close > neckline + min_break
                if inverse
                else candle.close < neckline - min_break
            )
            if broke:
                pattern.neckline_broken = True
                pattern.neckline_break_index = i
                height = abs(pattern.head.price - neckline)
                pattern.target_price = (
                    neckline + height if inverse else neckline - height
                )
                pattern.notes.append(
                    f"Neckline broken on a body close at {candle.close:g} "
                    f"(neckline {neckline:g}). Measured target {pattern.target_price:g}."
                )
            continue

        # Break confirmed - now the retest. The neckline retest IS the AOI retest.
        if not pattern.neckline_retested:
            if inverse:
                touched = candle.low <= neckline + retest_tol
                held = candle.close >= neckline - min_break
            else:
                touched = candle.high >= neckline - retest_tol
                held = candle.close <= neckline + min_break

            if touched and held:
                pattern.neckline_retested = True
                pattern.neckline_retest_index = i
                pattern.notes.append(
                    "Neckline retested and held - this retest is the AOI retest; "
                    "treat them as one event."
                )
                return

    if not pattern.neckline_broken:
        pattern.early_entry_risk = True
        pattern.notes.append(
            "HIGH RISK / EARLY ENTRY: right shoulder formed but the neckline has "
            "not broken. The pattern is not valid yet - wait for the break, then "
            "the retest."
        )


def valid_signals(patterns: List[HeadShouldersPattern]) -> List[HeadShouldersPattern]:
    """Only patterns whose neckline has actually broken."""
    return [p for p in patterns if p.is_valid_signal]


def tradeable_signals(
    patterns: List[HeadShouldersPattern],
) -> List[HeadShouldersPattern]:
    """Broken **and** retested - the only state the notes will enter on."""
    return [p for p in patterns if p.neckline_broken and p.neckline_retested]


def latest(
    patterns: List[HeadShouldersPattern], bias: Optional[Trend] = None
) -> Optional[HeadShouldersPattern]:
    """Most recent pattern, optionally filtered to one directional bias."""
    pool = patterns if bias is None else [p for p in patterns if p.bias is bias]
    if not pool:
        return None
    return max(pool, key=lambda p: p.right_shoulder.index)
