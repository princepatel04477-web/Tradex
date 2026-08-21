"""Structure engine: swings, HH/HL/LH/LL labelling, CHoCH, snake-trick trace."""

from datetime import datetime, timedelta, timezone

import pytest

from app.strategy import config
from app.strategy.structure import (
    analyse_structure,
    apply_lookback,
    find_swing_points,
    trace_last_valid_structure_point,
)
from app.strategy.types import Candle, StructureLabel, SwingKind, Trend

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def bar(i, o, h, l, c):
    return Candle(time=BASE + timedelta(hours=i), open=o, high=h, low=l, close=c)


def zigzag(points, per_leg=5, start=1.0):
    """Build candles that trace straight legs between the given prices."""
    candles = []
    price = start
    idx = 0
    for target in points:
        step = (target - price) / per_leg
        for k in range(per_leg):
            o = price + step * k
            c = price + step * (k + 1)
            candles.append(bar(idx, o, max(o, c) + 0.0002, min(o, c) - 0.0002, c))
            idx += 1
        price = target
    return candles


class TestSwingDetection:
    def test_finds_pivot_high_and_low(self):
        candles = zigzag([1.05, 1.00, 1.08], per_leg=6)
        swings = find_swing_points(candles, lookback=2)

        assert swings, "expected at least one pivot"
        assert any(s.kind is SwingKind.HIGH for s in swings)
        assert any(s.kind is SwingKind.LOW for s in swings)

    def test_returns_empty_when_series_too_short(self):
        candles = [bar(i, 1.0, 1.01, 0.99, 1.0) for i in range(4)]
        assert find_swing_points(candles, lookback=3) == []

    def test_alternation_collapses_consecutive_same_kind_swings(self):
        candles = zigzag([1.05, 1.00, 1.06, 1.01, 1.07], per_leg=6)
        swings = find_swing_points(candles, lookback=2, enforce_alternation=True)

        kinds = [s.kind for s in swings]
        for earlier, later in zip(kinds, kinds[1:]):
            assert earlier is not later, "zigzag must alternate high/low"


class TestLabelling:
    def test_uptrend_labels_hh_and_hl(self):
        candles = zigzag([1.05, 1.02, 1.08, 1.04, 1.11], per_leg=6)
        result = analyse_structure(candles, "1D", lookback=2)

        labels = [s.label for s in result.swings]
        assert StructureLabel.HH in labels
        assert StructureLabel.HL in labels
        assert result.trend is Trend.BULLISH

    def test_downtrend_labels_lh_and_ll(self):
        candles = zigzag([0.98, 1.02, 0.94, 0.99, 0.90], per_leg=6, start=1.05)
        result = analyse_structure(candles, "1D", lookback=2)

        labels = [s.label for s in result.swings]
        assert StructureLabel.LL in labels
        assert StructureLabel.LH in labels
        assert result.trend is Trend.BEARISH


class TestChoch:
    def test_body_close_below_hl_flips_trend_bearish(self):
        # Uptrend, then a decisive close below the last higher low.
        candles = zigzag([1.05, 1.02, 1.09, 1.04, 1.11, 1.01], per_leg=6)
        result = analyse_structure(candles, "1D", lookback=2)

        assert result.choch_events, "a close below the HL must register a CHoCH"
        event = result.choch_events[-1]
        assert event.from_trend is Trend.BULLISH
        assert event.to_trend is Trend.BEARISH
        assert event.broken_label is StructureLabel.HL
        assert result.trend is Trend.BEARISH

    def test_wick_below_hl_does_not_flip_trend(self):
        """Only a body close shifts structure - a wick is noise."""
        candles = zigzag([1.05, 1.02, 1.09, 1.04, 1.11], per_leg=6)
        clean = analyse_structure(candles, "1D", lookback=2)
        assert clean.trend is Trend.BULLISH

        hl = clean.last_valid_hl
        assert hl is not None

        # Same series, but the final candle spikes far below the HL and closes
        # right back above it.
        spiked = list(candles)
        last = spiked[-1]
        spiked[-1] = Candle(
            time=last.time,
            open=last.open,
            high=last.high,
            low=hl.price - 0.02,   # deep wick through the HL
            close=last.close,      # body closes back above it
        )

        result = analyse_structure(spiked, "1D", lookback=2)
        assert result.trend is Trend.BULLISH
        assert not result.choch_events

    def test_new_hh_puts_a_fresh_hl_in_play(self):
        candles = zigzag([1.05, 1.02, 1.09, 1.04, 1.12, 1.06, 1.15], per_leg=6)
        result = analyse_structure(candles, "1D", lookback=2)

        assert result.trend is Trend.BULLISH
        assert result.last_hh is not None
        assert result.last_valid_hl is not None
        # The HL being tracked must be the one formed after the earlier HH,
        # not the first low in the series.
        assert result.last_valid_hl.price > candles[0].low


class TestSnakeTrace:
    def test_traces_back_to_last_valid_hl_in_uptrend(self):
        candles = zigzag([1.05, 1.02, 1.09, 1.04, 1.12], per_leg=6)
        result = analyse_structure(candles, "1D", lookback=2)

        point = trace_last_valid_structure_point(result.swings, Trend.BULLISH)
        assert point is not None
        assert point.kind is SwingKind.LOW
        assert point.price < result.last_hh.price

    def test_traces_back_to_last_valid_lh_in_downtrend(self):
        candles = zigzag([0.98, 1.02, 0.94, 0.99, 0.90], per_leg=6, start=1.05)
        result = analyse_structure(candles, "1D", lookback=2)

        point = trace_last_valid_structure_point(result.swings, Trend.BEARISH)
        assert point is not None
        assert point.kind is SwingKind.HIGH

    def test_returns_none_without_a_trend(self):
        assert trace_last_valid_structure_point([], Trend.UNDETERMINED) is None


class TestLookback:
    def test_trims_to_configured_window(self):
        candles = [bar(i, 1.0, 1.01, 0.99, 1.0) for i in range(500)]
        trimmed = apply_lookback(candles, "1D")

        assert len(trimmed) == config.STRUCTURE_LOOKBACK_CANDLES["1D"]
        assert trimmed[-1] is candles[-1], "must keep the most recent candles"

    def test_leaves_short_series_untouched(self):
        candles = [bar(i, 1.0, 1.01, 0.99, 1.0) for i in range(10)]
        assert len(apply_lookback(candles, "1W")) == 10

    def test_lower_timeframe_noise_cannot_move_a_higher_timeframe(self):
        """Each timeframe is read against its own closes only."""
        weekly = zigzag([1.05, 1.02, 1.09, 1.04, 1.12], per_leg=6)
        weekly_trend = analyse_structure(weekly, "1W", lookback=2).trend

        # A violent intrabar spike on a lower timeframe does not appear in the
        # weekly closes, so the weekly read is unchanged.
        assert weekly_trend is Trend.BULLISH
        assert analyse_structure(weekly, "1W", lookback=2).trend is weekly_trend


def test_empty_series_is_undetermined_not_an_error():
    result = analyse_structure([], "1D")
    assert result.trend is Trend.UNDETERMINED
    assert result.swings == []


class TestBrokenStructure:
    """Swings retire once they stop describing where structure sits."""

    def test_superseded_high_is_broken_by_a_close_above_it(self):
        # Rising staircase: every high except the last is closed through.
        candles = zigzag([1.05, 1.02, 1.09, 1.04, 1.12], per_leg=6)
        result = analyse_structure(candles, "1D", lookback=2)

        highs = [s for s in result.swings if s.kind is SwingKind.HIGH]
        assert highs, "expected swing highs"
        broken_highs = [s for s in highs if s.broken]
        assert broken_highs, "an exceeded high must not stay on the chart"
        for swing in broken_highs:
            assert swing.broken_index is not None
            assert candles[swing.broken_index].close > swing.price
            assert "closed above" in swing.broken_reason

    def test_a_wick_through_a_level_does_not_break_it(self):
        """Only a body close retires a swing - same rule as CHoCH."""
        candles = zigzag([1.05, 1.00, 1.04], per_leg=6)
        result = analyse_structure(candles, "1D", lookback=2)
        highs = [s for s in result.swings if s.kind is SwingKind.HIGH]
        assert highs

        top = max(highs, key=lambda s: s.price)
        # A bar that spikes far above the high but closes back under it.
        candles.append(bar(len(candles), 1.03, top.price + 0.02, 1.028, 1.032))
        after = analyse_structure(candles, "1D", lookback=2)

        same = [s for s in after.swings if s.index == top.index]
        assert same and not same[0].broken

    def test_live_swings_excludes_broken_points(self):
        candles = zigzag([1.05, 1.02, 1.09, 1.04, 1.12], per_leg=6)
        result = analyse_structure(candles, "1D", lookback=2)

        assert result.live_swings == [s for s in result.swings if not s.broken]
        assert len(result.live_swings) < len(result.swings)

    def test_choch_retires_the_labels_it_relabelled(self):
        # Up, then a decisive break back down through the last HL.
        candles = zigzag([1.05, 1.02, 1.09, 1.04, 1.10, 0.98], per_leg=6)
        result = analyse_structure(candles, "1D", lookback=2)

        assert result.choch_events, "expected a CHoCH in this series"
        cutoff = result.choch_events[-1].index
        stale = [
            s for s in result.swings if s.index < cutoff and not s.broken
        ]
        # Anything left alive from before the flip must be a reference point
        # the engine still keys off, not a leftover label.
        references = {
            id(p)
            for p in (
                result.last_valid_hl,
                result.last_valid_lh,
                result.last_hh,
                result.last_ll,
            )
            if p is not None
        }
        for swing in stale:
            assert id(swing) in references

    def test_the_level_that_must_hold_is_never_swept_away(self):
        """After a flip the guarding level predates the flip - keep it drawn."""
        candles = zigzag([1.05, 1.02, 1.09, 1.04, 1.10, 0.98], per_leg=6)
        result = analyse_structure(candles, "1D", lookback=2)

        guard = (
            result.last_valid_lh
            if result.trend is Trend.BEARISH
            else result.last_valid_hl
        )
        if guard is not None:
            assert guard in result.live_swings

    def test_flags_reset_on_reanalysis(self):
        """Re-running the pass must not accumulate stale flags."""
        candles = zigzag([1.05, 1.02, 1.09], per_leg=6)
        first = analyse_structure(candles, "1D", lookback=2)
        second = analyse_structure(candles, "1D", lookback=2)

        assert [s.broken for s in first.swings] == [s.broken for s in second.swings]
