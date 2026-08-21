"""Risk calculator: table lookup, pip value, position sizing, RR floor, weekly pace."""

from datetime import datetime, timedelta, timezone

import pytest

from app.strategy import config
from app.strategy.pips import pip_size, pip_value, to_pips
from app.strategy.risk import (
    build_trade_plan,
    risk_table,
    risk_tier_for,
    set_and_forget_notice,
    suggest_take_profit,
    weekly_pace,
)
from app.strategy.types import Direction

MONDAY = datetime(2026, 8, 17, 9, 0, tzinfo=timezone.utc)


class TestRiskTable:
    @pytest.mark.parametrize(
        "balance,expected",
        [
            (100, 100.0),
            (400, 400.0),
            (3_200, 3_200.0),
            (8_000, 8_000.0),
            (15_000, 15_000.0),
            (17_000, 17_000.0),
            (30_000, 30_000.0),
            (1_000_000, 1_000_000.0),
        ],
    )
    def test_exact_balances_hit_their_own_tier(self, balance, expected):
        assert risk_tier_for(balance).account_size == expected

    def test_between_tiers_uses_the_lower_one(self):
        assert risk_tier_for(5_000).account_size == 3_200.0

    def test_below_the_smallest_tier_falls_back_to_it(self):
        assert risk_tier_for(50).account_size == 100.0

    def test_above_the_largest_tier_stays_on_it(self):
        assert risk_tier_for(5_000_000).account_size == 1_000_000.0

    def test_the_17000_row_is_present_and_flagged(self):
        """FLAGGED QUESTION #2 - transcribed as written, marked unconfirmed."""
        row = next(r for r in risk_table() if r["account_size"] == 17_000.0)

        assert row["unconfirmed"] is True
        assert "ascending order" in row["note"]

    def test_table_is_returned_in_ascending_order(self):
        sizes = [r["account_size"] for r in risk_table()]
        assert sizes == sorted(sizes)

    def test_risk_percentage_uses_the_midpoint_of_a_range(self):
        tier = risk_tier_for(3_200)  # 50-60%
        assert tier.risk_pct == pytest.approx(55.0)


class TestPipValue:
    def test_standard_pair_one_lot_is_ten_dollars(self):
        assert pip_value("EUR_USD", 1.0, 1.0850) == pytest.approx(10.0)

    def test_mini_lot_is_one_dollar(self):
        assert pip_value("EUR_USD", 0.1, 1.0850) == pytest.approx(1.0)

    def test_jpy_pair_uses_a_two_decimal_pip(self):
        assert pip_size("USD_JPY") == pytest.approx(0.01)
        assert pip_size("EUR_USD") == pytest.approx(0.0001)

    def test_jpy_pip_value_divides_by_the_rate(self):
        value = pip_value("USD_JPY", 1.0, 154.50)
        assert value == pytest.approx(100_000 * 0.01 / 154.50)
        assert value != pytest.approx(10.0)

    def test_a_cross_without_a_conversion_rate_is_an_error(self):
        with pytest.raises(ValueError, match="cross"):
            pip_value("EUR_GBP", 1.0, 0.8530)

    def test_a_cross_with_a_conversion_rate_works(self):
        value = pip_value("EUR_GBP", 1.0, 0.8530, quote_to_account_rate=1.27)
        assert value == pytest.approx(100_000 * 0.0001 * 1.27)


class TestTradePlan:
    def test_position_size_matches_the_risk_amount(self):
        plan = build_trade_plan(
            "EUR_USD", Direction.BUY, entry=1.1000, stop_loss=1.0950,
            account_size=10_000, take_profit=1.1200,
        )
        # Losing the trade must cost exactly the risk amount.
        loss = plan.position_size_lots * plan.stop_distance_pips * plan.pip_value_per_lot
        assert loss == pytest.approx(plan.risk_amount, rel=0.01)

    def test_default_target_is_the_1_to_4_projection(self):
        plan = build_trade_plan(
            "EUR_USD", Direction.BUY, entry=1.1000, stop_loss=1.0950,
            account_size=10_000,
        )
        assert plan.reward_risk == pytest.approx(config.TARGET_REWARD_RISK)
        assert plan.meets_target_rr is True

    def test_below_1_to_2_is_flagged_as_not_valid(self):
        plan = build_trade_plan(
            "EUR_USD", Direction.BUY, entry=1.1000, stop_loss=1.0950,
            account_size=10_000, take_profit=1.1050,   # only 1:1
        )
        assert plan.reward_risk == pytest.approx(1.0)
        assert plan.meets_min_rr is False
        assert any("below the 1:2 minimum" in w for w in plan.warnings)

    def test_exactly_1_to_2_is_acceptable(self):
        plan = build_trade_plan(
            "EUR_USD", Direction.BUY, entry=1.1000, stop_loss=1.0950,
            account_size=10_000, take_profit=1.1100,
        )
        assert plan.reward_risk == pytest.approx(2.0)
        assert plan.meets_min_rr is True
        assert plan.meets_target_rr is False

    def test_stop_on_the_wrong_side_of_a_buy_is_an_error(self):
        with pytest.raises(ValueError, match="below the entry"):
            build_trade_plan(
                "EUR_USD", Direction.BUY, entry=1.1000, stop_loss=1.1050,
                account_size=10_000,
            )

    def test_stop_on_the_wrong_side_of_a_sell_is_an_error(self):
        with pytest.raises(ValueError, match="above the entry"):
            build_trade_plan(
                "EUR_USD", Direction.SELL, entry=1.1000, stop_loss=1.0950,
                account_size=10_000,
            )

    def test_zero_stop_distance_is_an_error(self):
        with pytest.raises(ValueError, match="differ from entry"):
            build_trade_plan(
                "EUR_USD", Direction.BUY, entry=1.1000, stop_loss=1.1000,
                account_size=10_000,
            )

    def test_unconfirmed_tier_is_surfaced_on_the_plan(self):
        plan = build_trade_plan(
            "EUR_USD", Direction.BUY, entry=1.1000, stop_loss=1.0950,
            account_size=17_000,
        )
        assert plan.risk_tier_unconfirmed is True
        assert any("UNCONFIRMED" in w for w in plan.warnings)

    def test_jpy_pair_sizes_differently_from_a_standard_pair(self):
        jpy = build_trade_plan(
            "USD_JPY", Direction.BUY, entry=154.50, stop_loss=154.00,
            account_size=10_000,
        )
        assert jpy.stop_distance_pips == pytest.approx(50.0)
        assert jpy.pip_value_per_lot != pytest.approx(10.0)

    def test_suggest_take_profit_respects_direction(self):
        assert suggest_take_profit(1.1000, 1.0950, 2.0) == pytest.approx(1.1100)
        assert suggest_take_profit(1.1000, 1.1050, 2.0) == pytest.approx(1.0900)


class TestWeeklyPace:
    def test_no_trades_leaves_the_week_open(self):
        pace = weekly_pace([], now=MONDAY)
        assert pace.trades_this_week == 0
        assert pace.at_limit is False
        assert pace.remaining == config.MAX_TRADES_PER_WEEK

    def test_one_trade_hits_the_weekly_limit(self):
        pace = weekly_pace([MONDAY - timedelta(hours=2)], now=MONDAY)
        assert pace.trades_this_week == 1
        assert pace.at_limit is True
        assert pace.message == config.GUARDRAIL_MESSAGES["weekly_pace"]

    def test_last_weeks_trade_does_not_count(self):
        pace = weekly_pace([MONDAY - timedelta(days=8)], now=MONDAY)
        assert pace.trades_this_week == 0
        assert pace.at_limit is False

    def test_week_runs_monday_to_monday(self):
        pace = weekly_pace([], now=MONDAY)
        assert pace.week_start.weekday() == 0
        assert (pace.week_end - pace.week_start) == timedelta(days=7)

    def test_naive_timestamps_are_treated_as_utc(self):
        naive = datetime(2026, 8, 17, 10, 0)
        pace = weekly_pace([naive], now=MONDAY)
        assert pace.trades_this_week == 1


class TestSetAndForget:
    def test_placed_trade_gets_a_friction_notice(self):
        notice = set_and_forget_notice(True)
        assert notice and "Set & Forget" in notice

    def test_unplaced_trade_has_no_notice(self):
        assert set_and_forget_notice(False) is None
