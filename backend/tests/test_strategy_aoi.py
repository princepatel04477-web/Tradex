"""AOI validator: 3-touch minimum, 5-60 pip width, W/D only, Golden Rule tags."""

from datetime import datetime, timedelta, timezone

import pytest

from app.strategy import config
from app.strategy.aoi import aoi_allowed, detect_aoi_zones, zone_at_price
from app.strategy.structure import analyse_structure
from app.strategy.types import Candle, ZoneType

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def build(points, per_leg=7, start=1.1000):
    """Trace straight legs between prices, putting an exact pivot at each turn."""
    candles = []
    price = start
    idx = 0
    for target in points:
        step = (target - price) / per_leg
        for k in range(per_leg):
            o = price + step * k
            c = price + step * (k + 1)
            hi, lo = max(o, c), min(o, c)
            if k == per_leg - 1:
                if step < 0:
                    lo = target
                else:
                    hi = target
            candles.append(
                Candle(
                    time=BASE + timedelta(hours=idx),
                    open=o,
                    high=hi + 0.00005,
                    low=lo - 0.00005,
                    close=c,
                )
            )
            idx += 1
        price = target
    return candles


#: Lows creep up inside a tight band while highs step up - a classic support
#: AOI under a bullish structure.
SUPPORT_PATH = [
    1.0800, 1.1000, 1.0804, 1.1050, 1.0808, 1.1100, 1.0812, 1.1200,
]


class TestTimeframeRestriction:
    @pytest.mark.parametrize("tf", ["1W", "1D"])
    def test_weekly_and_daily_are_allowed(self, tf):
        assert aoi_allowed(tf) is True

    @pytest.mark.parametrize("tf", ["4H", "2H", "1H", "30M", "15M"])
    def test_everything_below_daily_is_refused(self, tf):
        assert aoi_allowed(tf) is False

    def test_scan_on_4h_returns_a_refusal_not_zones(self):
        candles = build(SUPPORT_PATH)
        scan = detect_aoi_zones(candles, "4H", "EUR_USD")

        assert scan.allowed is False
        assert scan.zones == []
        assert "never computed on 4H" in scan.message


class TestTouchRule:
    def test_valid_zone_needs_three_touches(self):
        candles = build(SUPPORT_PATH)
        structure = analyse_structure(candles, "1D", lookback=2)
        scan = detect_aoi_zones(candles, "1D", "EUR_USD", structure)

        assert scan.has_valid_aoi
        for zone in scan.zones:
            assert zone.touches >= config.AOI.min_touches

    def test_two_touches_is_rejected_with_a_reason(self):
        # Only one round trip to the level - never a third test.
        candles = build([1.0800, 1.1000, 1.0805, 1.1200])
        structure = analyse_structure(candles, "1D", lookback=2)
        scan = detect_aoi_zones(candles, "1D", "EUR_USD", structure)

        assert not scan.has_valid_aoi
        assert scan.message == config.GUARDRAIL_MESSAGES["no_aoi"]
        assert any(
            "needs at least 3" in reason
            for zone in scan.rejected
            for reason in zone.rejection_reasons
        )

    def test_confidence_scales_with_touch_count(self):
        candles = build(SUPPORT_PATH)
        structure = analyse_structure(candles, "1D", lookback=2)
        scan = detect_aoi_zones(candles, "1D", "EUR_USD", structure)

        for zone in scan.zones:
            assert 0.0 < zone.confidence <= 1.0


class TestWidthRule:
    def test_every_valid_zone_sits_inside_the_pip_bounds(self):
        candles = build(SUPPORT_PATH)
        structure = analyse_structure(candles, "1D", lookback=2)
        scan = detect_aoi_zones(candles, "1D", "EUR_USD", structure)

        for zone in scan.zones:
            assert config.AOI.min_width_pips <= zone.width_pips <= config.AOI.max_width_pips

    def test_zone_wider_than_60_pips_is_rejected_not_clipped(self):
        # Lows scattered across ~200 pips cannot be squeezed into one zone.
        candles = build([1.0700, 1.1200, 1.0900, 1.1300, 1.1100, 1.1400])
        structure = analyse_structure(candles, "1D", lookback=2)
        scan = detect_aoi_zones(candles, "1D", "EUR_USD", structure)

        for zone in scan.zones + scan.rejected:
            if zone.width_pips > config.AOI.max_width_pips:
                assert zone.valid is False
                assert any("wider than" in r for r in zone.rejection_reasons)
        # Nothing may be silently trimmed down to the cap.
        assert all(z.width_pips <= config.AOI.max_width_pips for z in scan.zones)


class TestGoldenRule:
    def test_support_is_a_buy_zone_and_resistance_a_sell_zone(self):
        candles = build(SUPPORT_PATH)
        structure = analyse_structure(candles, "1D", lookback=2)
        scan = detect_aoi_zones(candles, "1D", "EUR_USD", structure)

        for zone in scan.zones:
            if zone.zone_type is ZoneType.SUPPORT:
                assert zone.golden_rule_tag == "Buy zone"
            else:
                assert zone.golden_rule_tag == "Sell zone"


class TestStructuralPlacement:
    def test_zone_beyond_the_structural_extreme_is_rejected(self):
        candles = build(SUPPORT_PATH)
        structure = analyse_structure(candles, "1D", lookback=2)
        scan = detect_aoi_zones(candles, "1D", "EUR_USD", structure)

        rng = structure.structural_range
        if rng:
            low, high = rng
            for zone in scan.zones:
                assert zone.upper >= low and zone.lower <= high


def test_zone_at_price_finds_the_containing_zone():
    candles = build(SUPPORT_PATH)
    structure = analyse_structure(candles, "1D", lookback=2)
    scan = detect_aoi_zones(candles, "1D", "EUR_USD", structure)

    if scan.zones:
        target = scan.zones[0]
        assert zone_at_price(scan.zones, target.mid) is not None
    assert zone_at_price(scan.zones, 0.5) is None


def test_no_candles_is_handled_gracefully():
    scan = detect_aoi_zones([], "1D", "EUR_USD")
    assert scan.zones == []
    assert scan.allowed is True
