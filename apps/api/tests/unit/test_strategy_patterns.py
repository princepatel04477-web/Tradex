"""Candlestick recognizer: exact OHLC geometry, body-not-wick engulfing, AOI gating."""

from datetime import datetime, timedelta, timezone

import pytest

from app.strategy import config
from app.strategy.patterns import (
    actionable,
    detect_doji,
    detect_engulfing,
    detect_hammer,
    detect_inverted_hammer,
    detect_patterns,
    detect_spinning_top,
    detect_star,
    strongest,
)
from app.strategy.types import AOIZone, Candle, Trend, ZoneType

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
SYMBOL = "EUR_USD"


def c(o, h, l, cl, i=0):
    return Candle(time=BASE + timedelta(hours=i), open=o, high=h, low=l, close=cl)


class TestDoji:
    def test_detects_equal_open_and_close(self):
        candles = [c(1.1000, 1.1030, 1.0970, 1.1001)]
        match = detect_doji(candles, 0, SYMBOL)

        assert match is not None
        assert match.name == "Doji"
        assert match.bias is Trend.UNDETERMINED

    def test_rejects_a_full_bodied_candle(self):
        candles = [c(1.1000, 1.1055, 1.0995, 1.1050)]
        assert detect_doji(candles, 0, SYMBOL) is None

    def test_rejects_a_candle_below_the_noise_floor(self):
        # Range under min_candle_range_pips - too small to mean anything.
        candles = [c(1.10000, 1.10003, 1.09997, 1.10000)]
        assert detect_doji(candles, 0, SYMBOL) is None


class TestSpinningTop:
    def test_small_body_between_two_wicks(self):
        candles = [c(1.1000, 1.1040, 1.0960, 1.1010)]
        match = detect_spinning_top(candles, 0, SYMBOL)

        assert match is not None
        assert match.name == "Spinning Top"

    def test_a_doji_is_not_reported_as_a_spinning_top(self):
        candles = [c(1.1000, 1.1030, 1.0970, 1.1001)]
        assert detect_spinning_top(candles, 0, SYMBOL) is None


class TestHammer:
    def test_long_lower_wick_is_bullish(self):
        candles = [c(1.1040, 1.1045, 1.0960, 1.1042)]
        match = detect_hammer(candles, 0, SYMBOL)

        assert match is not None
        assert match.bias is Trend.BULLISH

    def test_long_upper_wick_is_an_inverted_hammer(self):
        candles = [c(1.0962, 1.1050, 1.0958, 1.0960)]
        match = detect_inverted_hammer(candles, 0, SYMBOL)

        assert match is not None
        assert match.bias is Trend.BEARISH

    def test_a_hammer_is_not_also_an_inverted_hammer(self):
        candles = [c(1.1040, 1.1045, 1.0960, 1.1042)]
        assert detect_inverted_hammer(candles, 0, SYMBOL) is None


class TestEngulfing:
    def test_bullish_engulfing_covers_the_prior_body(self):
        candles = [
            c(1.1020, 1.1025, 1.0995, 1.1000, 0),   # bearish
            c(1.0995, 1.1050, 1.0990, 1.1040, 1),   # bullish, covers it
        ]
        match = detect_engulfing(candles, 1, SYMBOL)

        assert match is not None
        assert match.name == "Bullish Engulfing"
        assert match.bias is Trend.BULLISH

    def test_bearish_engulfing_covers_the_prior_body(self):
        candles = [
            c(1.1000, 1.1025, 1.0995, 1.1020, 0),   # bullish
            c(1.1030, 1.1035, 1.0980, 1.0990, 1),   # bearish, covers it
        ]
        match = detect_engulfing(candles, 1, SYMBOL)

        assert match is not None
        assert match.name == "Bearish Engulfing"

    def test_engulfing_the_wick_but_not_the_body_does_not_count(self):
        """The rule is body-over-body. Covering only the wick is not engulfing."""
        candles = [
            c(1.1020, 1.1060, 1.0960, 1.1000, 0),   # bearish, long wicks
            c(1.1005, 1.1030, 1.1002, 1.1015, 1),   # inside the prior body
        ]
        assert detect_engulfing(candles, 1, SYMBOL) is None

    def test_strength_accounts_for_the_last_two_bodies_together(self):
        two_bodies = [
            c(1.1030, 1.1035, 1.1018, 1.1020, 0),
            c(1.1020, 1.1025, 1.0998, 1.1000, 1),
            c(1.0995, 1.1060, 1.0990, 1.1050, 2),   # covers BOTH prior bodies
        ]
        one_body = [
            c(1.1000, 1.1005, 1.0995, 1.1002, 0),
            c(1.1020, 1.1025, 1.0998, 1.1000, 1),
            c(1.0997, 1.1030, 1.0995, 1.1025, 2),   # covers only the last body
        ]

        wide = detect_engulfing(two_bodies, 2, SYMBOL)
        narrow = detect_engulfing(one_body, 2, SYMBOL)

        assert wide is not None and narrow is not None
        assert "both preceding bodies" in wide.detail
        assert wide.strength >= narrow.strength

    def test_same_direction_candles_are_not_engulfing(self):
        candles = [
            c(1.1000, 1.1015, 1.0998, 1.1010, 0),
            c(1.0995, 1.1050, 1.0990, 1.1040, 1),   # bullish after bullish
        ]
        assert detect_engulfing(candles, 1, SYMBOL) is None


class TestStars:
    def test_morning_star_is_bullish(self):
        candles = [
            c(1.1050, 1.1055, 1.0995, 1.1000, 0),   # decisive down
            c(1.0995, 1.1000, 1.0980, 1.0990, 1),   # small stall
            c(1.0995, 1.1050, 1.0992, 1.1045, 2),   # closes back into candle 1
        ]
        match = detect_star(candles, 2, SYMBOL)

        assert match is not None
        assert match.name == "Morning Star"
        assert match.bias is Trend.BULLISH

    def test_evening_star_is_bearish(self):
        candles = [
            c(1.1000, 1.1055, 1.0995, 1.1050, 0),   # decisive up
            c(1.1055, 1.1070, 1.1050, 1.1060, 1),   # small stall
            c(1.1055, 1.1058, 1.1000, 1.1005, 2),   # closes back into candle 1
        ]
        match = detect_star(candles, 2, SYMBOL)

        assert match is not None
        assert match.name == "Evening Star"
        assert match.bias is Trend.BEARISH

    def test_a_large_middle_body_disqualifies_the_pattern(self):
        candles = [
            c(1.1050, 1.1055, 1.0995, 1.1000, 0),
            c(1.0995, 1.1060, 1.0980, 1.1055, 1),   # middle body far too big
            c(1.1050, 1.1080, 1.1045, 1.1075, 2),
        ]
        assert detect_star(candles, 2, SYMBOL) is None


class TestAOIGating:
    def _series(self):
        return [
            c(1.1020, 1.1025, 1.0995, 1.1000, 0),
            c(1.0995, 1.1050, 1.0990, 1.1040, 1),
        ]

    def _zone(self, lower, upper):
        return AOIZone(
            timeframe="1D",
            lower=lower,
            upper=upper,
            zone_type=ZoneType.SUPPORT,
            touches=3,
            valid=True,
        )

    def test_pattern_inside_a_zone_is_actionable(self):
        matches = detect_patterns(
            self._series(), "1D", SYMBOL, [self._zone(1.0990, 1.1010)]
        )
        assert any(m.at_aoi for m in matches)
        assert actionable(matches)

    def test_pattern_away_from_any_zone_is_detected_but_not_actionable(self):
        matches = detect_patterns(
            self._series(), "1D", SYMBOL, [self._zone(1.2000, 1.2020)]
        )
        assert matches, "detection still runs everywhere"
        assert not actionable(matches), "but nothing off-AOI is tradeable"

    def test_no_zones_means_nothing_is_actionable(self):
        matches = detect_patterns(self._series(), "1D", SYMBOL, [])
        assert not actionable(matches)


class TestTimeframeWeighting:
    def test_higher_timeframe_scores_higher_for_the_same_geometry(self):
        series = [
            c(1.1020, 1.1025, 1.0995, 1.1000, 0),
            c(1.0995, 1.1050, 1.0990, 1.1040, 1),
        ]
        zone = [
            AOIZone("1D", 1.0990, 1.1010, ZoneType.SUPPORT, 3, valid=True)
        ]

        weekly = detect_patterns(series, "1W", SYMBOL, zone)
        m15 = detect_patterns(series, "15M", SYMBOL, zone)

        assert weekly[0].strength == m15[0].strength
        assert weekly[0].weighted_strength > m15[0].weighted_strength
        assert config.PATTERN_TIMEFRAME_WEIGHT["1W"] > config.PATTERN_TIMEFRAME_WEIGHT["15M"]

    def test_strongest_filters_by_bias(self):
        series = [
            c(1.1020, 1.1025, 1.0995, 1.1000, 0),
            c(1.0995, 1.1050, 1.0990, 1.1040, 1),
        ]
        zone = [AOIZone("1D", 1.0990, 1.1010, ZoneType.SUPPORT, 3, valid=True)]
        matches = detect_patterns(series, "1D", SYMBOL, zone)

        assert strongest(matches, Trend.BULLISH) is not None
        assert strongest(matches, Trend.BEARISH) is None


def test_empty_series_returns_no_matches():
    assert detect_patterns([], "1D", SYMBOL) == []
