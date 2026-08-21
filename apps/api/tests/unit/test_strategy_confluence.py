"""Confluence scorer: the core 4 gate, the expanded checklist, the LRHR badge."""

from datetime import datetime, timezone

import pytest

from app.strategy import config
from app.strategy.aoi import AOIScan
from app.strategy.confluence import ConfluenceInputs, evaluate, guardrail_message
from app.strategy.indicators import EMAState
from app.strategy.topdown import SyncVerdict
from app.strategy.types import (
    AOIZone,
    BreakRetestSignal,
    Direction,
    HeadShouldersPattern,
    PatternMatch,
    StructureResult,
    SwingKind,
    SwingPoint,
    Trend,
    ZoneType,
)

NOW = datetime(2026, 8, 20, tzinfo=timezone.utc)


def zone(lower=1.0800, upper=1.0820):
    return AOIZone("1D", lower, upper, ZoneType.SUPPORT, touches=4, valid=True, confidence=0.75)


def scan(valid=True):
    s = AOIScan("1D", allowed=True)
    if valid:
        s.zones = [zone()]
    s.message = "AOI ok" if valid else config.GUARDRAIL_MESSAGES["no_aoi"]
    return s


def sync(in_sync=True, direction=Trend.BULLISH):
    return SyncVerdict(
        in_sync=in_sync,
        rule=config.REQUIRED_SYNC_TIMEFRAMES,
        direction=direction if in_sync else Trend.UNDETERMINED,
        agreeing_timeframes=["1W", "1D"] if in_sync else [],
        explanation="Weekly and Daily agree." if in_sync else "They disagree.",
    )


def armed_trigger():
    return BreakRetestSignal(
        status="armed", direction=Direction.BUY, level=1.0820, level_label="1D AOI upper"
    )


def pattern(name="Bullish Engulfing", bias=Trend.BULLISH, at_aoi=True):
    return PatternMatch(
        name=name, index=10, time=NOW, bias=bias, strength=0.8,
        timeframe="1D", weighted_strength=2.0, at_aoi=at_aoi,
    )


def hs(timeframe="4H", broken=True, retested=True):
    swing = lambda i, p, k: SwingPoint(i, NOW, p, k)
    pat = HeadShouldersPattern(
        kind="inverse_head_and_shoulders",
        timeframe=timeframe,
        left_shoulder=swing(0, 1.08, SwingKind.LOW),
        head=swing(2, 1.07, SwingKind.LOW),
        right_shoulder=swing(4, 1.081, SwingKind.LOW),
        neckline_start=swing(1, 1.09, SwingKind.HIGH),
        neckline_end=swing(3, 1.091, SwingKind.HIGH),
    )
    pat.neckline_broken = broken
    pat.neckline_retested = retested
    return pat


def full_inputs(**overrides):
    base = dict(
        bias=Trend.BULLISH,
        sync=sync(),
        aoi_scan=scan(),
        current_price=1.0810,
        trigger=armed_trigger(),
        patterns=[pattern(), pattern("Morning Star")],
        head_shoulders={"4H": [hs()], "1D": [hs("1D")]},
        ema=EMAState(50, 1.0790, 1.0810, Trend.BULLISH, 0.0001, []),
        daily_structure=StructureResult("1D", Trend.BULLISH),
    )
    base.update(overrides)
    return ConfluenceInputs(**base)


class TestCorePillars:
    def test_all_four_present_makes_the_setup_eligible(self):
        result = evaluate(full_inputs())

        assert result.core_complete is True
        assert result.eligible is True
        assert result.missing_core == []
        assert all(result.core_pillars.values())

    @pytest.mark.parametrize(
        "override,missing",
        [
            ({"sync": sync(in_sync=False)}, "trend_confirmed"),
            ({"aoi_scan": scan(valid=False)}, "aoi_valid"),
            ({"trigger": BreakRetestSignal(status="broken")}, "entry_trigger_confirmed"),
        ],
    )
    def test_any_missing_pillar_blocks_eligibility(self, override, missing):
        result = evaluate(full_inputs(**override))

        assert result.core_complete is False
        assert missing in result.missing_core
        assert result.score == 0, "no score is computed while a pillar is missing"

    def test_missing_pattern_blocks_eligibility(self):
        result = evaluate(full_inputs(patterns=[], head_shoulders={}))

        assert result.core_complete is False
        assert "pattern_confirmed" in result.missing_core

    def test_a_pattern_away_from_the_aoi_does_not_satisfy_the_pillar(self):
        result = evaluate(
            full_inputs(patterns=[pattern(at_aoi=False)], head_shoulders={})
        )
        assert "pattern_confirmed" in result.missing_core

    def test_a_pattern_against_the_bias_does_not_satisfy_the_pillar(self):
        result = evaluate(
            full_inputs(
                patterns=[pattern("Bearish Engulfing", Trend.BEARISH)],
                head_shoulders={},
            )
        )
        assert "pattern_confirmed" in result.missing_core


class TestExpandedChecklist:
    def test_checklist_has_the_ten_items_from_the_notes(self):
        result = evaluate(full_inputs())

        assert result.max_score == 10
        assert set(result.expanded) == set(config.EXPANDED_CHECKLIST)

    def test_score_counts_confirmed_items(self):
        result = evaluate(full_inputs())
        assert result.score == sum(1 for v in result.expanded.values() if v)

    def test_a_full_stack_earns_the_low_risk_high_reward_badge(self):
        result = evaluate(full_inputs())

        assert result.score >= config.LOW_RISK_HIGH_REWARD_THRESHOLD
        assert result.low_risk_high_reward is True

    def test_a_thin_stack_does_not_earn_the_badge(self):
        result = evaluate(
            full_inputs(
                patterns=[pattern()],
                head_shoulders={},
                ema=EMAState(50, 1.0900, 1.0810, Trend.BEARISH, 0.0, []),
                daily_structure=StructureResult("1D", Trend.BEARISH),
            )
        )
        assert result.core_complete is True
        assert result.low_risk_high_reward is False

    def test_h4_head_and_shoulders_is_scored_separately(self):
        with_h4 = evaluate(full_inputs())
        without_h4 = evaluate(full_inputs(head_shoulders={"1D": [hs("1D")]}))

        assert with_h4.expanded["h4_head_and_shoulders"] is True
        assert without_h4.expanded["h4_head_and_shoulders"] is False

    def test_unretested_neckline_does_not_tick_the_retest_item(self):
        result = evaluate(full_inputs(head_shoulders={"4H": [hs(retested=False)]}))

        assert result.expanded["head_and_shoulders"] is True
        assert result.expanded["hs_neckline_break_retest"] is False

    def test_unbroken_neckline_is_not_a_head_and_shoulders_signal(self):
        result = evaluate(
            full_inputs(head_shoulders={"4H": [hs(broken=False, retested=False)]})
        )
        assert result.expanded["head_and_shoulders"] is False


class TestGuardrails:
    def test_eligible_setups_get_no_guardrail(self):
        assert guardrail_message(evaluate(full_inputs())) is None

    def test_missing_aoi_gets_the_aoi_message(self):
        result = evaluate(full_inputs(aoi_scan=scan(valid=False)))
        assert guardrail_message(result) == config.GUARDRAIL_MESSAGES["no_aoi"]

    def test_missing_sync_gets_the_sync_message(self):
        result = evaluate(full_inputs(sync=sync(in_sync=False)))
        assert guardrail_message(result) == config.GUARDRAIL_MESSAGES["no_sync"]

    def test_missing_trigger_gets_the_trigger_message(self):
        result = evaluate(full_inputs(trigger=BreakRetestSignal(status="broken")))
        assert guardrail_message(result) == config.GUARDRAIL_MESSAGES["no_trigger"]

    def test_missing_pattern_gets_the_general_message(self):
        result = evaluate(full_inputs(patterns=[], head_shoulders={}))
        assert guardrail_message(result) == config.GUARDRAIL_MESSAGES["no_setup"]
