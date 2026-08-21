"""Break & retest, Head & Shoulders, sessions, CSV import, and the full pass."""

from datetime import datetime, timedelta, timezone

import pytest

from app.strategy import config, engine, sample_data
from app.strategy.break_retest import detect_break_retest
from app.strategy.data_input import parse_ohlc_csv, parse_time
from app.strategy.head_shoulders import detect_head_shoulders, valid_signals
from app.strategy.indicators import compute_ema, ema_series
from app.strategy.reference import explain_pair, flagged_for_confirmation
from app.strategy.sessions import session_clock
from app.strategy.structure import analyse_structure
from app.strategy.topdown import evaluate_sync
from app.strategy.types import Candle, Direction, StructureResult, Trend

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
SYMBOL = "EUR_USD"


def bars(prices, wick=0.0003):
    """One candle per close price, with modest wicks."""
    out = []
    prev = prices[0]
    for i, close in enumerate(prices):
        o = prev
        out.append(
            Candle(
                time=BASE + timedelta(hours=i),
                open=o,
                high=max(o, close) + wick,
                low=min(o, close) - wick,
                close=close,
            )
        )
        prev = close
    return out


class TestBreakRetest:
    LEVEL = 1.1000

    def test_close_beyond_the_level_registers_a_break(self):
        candles = bars([1.0950, 1.0970, 1.0990, 1.1030])
        signal = detect_break_retest(candles, self.LEVEL, SYMBOL, "AOI upper")

        assert signal.status == "broken"
        assert signal.direction is Direction.BUY

    def test_a_wick_through_the_level_is_not_a_break(self):
        """The break rule is a body close, so a wick alone does nothing."""
        candles = bars([1.0950, 1.0970, 1.0990])
        last = candles[-1]
        candles[-1] = Candle(
            time=last.time, open=last.open, high=1.1050, low=last.low, close=1.0990
        )
        signal = detect_break_retest(candles, self.LEVEL, SYMBOL, "AOI upper")

        assert signal.status == "none"

    def test_break_then_return_to_the_level_arms_the_setup(self):
        candles = bars([1.0950, 1.0990, 1.1030, 1.1040, 1.1002, 1.1020])
        signal = detect_break_retest(candles, self.LEVEL, SYMBOL, "AOI upper")

        assert signal.is_armed
        assert signal.retest_index is not None
        assert signal.candles_to_retest >= 1

    def test_the_break_candle_itself_never_arms_the_setup(self):
        candles = bars([1.0950, 1.0990, 1.1030])
        signal = detect_break_retest(candles, self.LEVEL, SYMBOL)

        assert signal.status == "broken"
        assert not signal.is_armed

    def test_closing_back_through_invalidates_the_break(self):
        candles = bars([1.0950, 1.0990, 1.1030, 1.0980, 1.0960])
        signal = detect_break_retest(candles, self.LEVEL, SYMBOL)

        assert signal.status == "invalidated"

    def test_no_retest_within_the_window_goes_stale(self):
        prices = [1.0990, 1.1030] + [1.1100 + i * 0.0005 for i in range(40)]
        signal = detect_break_retest(bars(prices), self.LEVEL, SYMBOL)

        assert signal.status == "invalidated"
        assert any("stale" in n for n in signal.notes)

    def test_direction_filter_ignores_the_opposite_break(self):
        candles = bars([1.1050, 1.1020, 1.0960])
        signal = detect_break_retest(
            candles, self.LEVEL, SYMBOL, direction=Direction.BUY
        )
        assert signal.status == "none"


class TestHeadShoulders:
    def _pattern_series(self):
        path = [
            1.2400, 1.2700,   # left shoulder
            1.2550,           # neckline A
            1.2900,           # head
            1.2560,           # neckline B
            1.2720,           # right shoulder
            1.2450,           # neckline break
            1.2555,           # retest
            1.2300,
        ]
        prices = []
        current = path[0]
        for target in path[1:]:
            for k in range(1, 9):
                prices.append(current + (target - current) * k / 8)
            current = target
        return bars(prices, wick=0.0002)

    def test_detects_the_pattern_from_swing_structure(self):
        candles = self._pattern_series()
        structure = analyse_structure(candles, "4H", lookback=3)
        patterns = detect_head_shoulders(candles, structure.swings, "4H", "GBP_USD")

        assert patterns, "expected a head and shoulders in this path"
        assert patterns[0].kind == "head_and_shoulders"
        assert patterns[0].bias is Trend.BEARISH

    def test_neckline_is_built_from_the_two_troughs(self):
        candles = self._pattern_series()
        structure = analyse_structure(candles, "4H", lookback=3)
        pattern = detect_head_shoulders(candles, structure.swings, "4H", "GBP_USD")[0]

        assert pattern.neckline_start.price == pytest.approx(1.2550, abs=0.003)
        assert pattern.neckline_end.price == pytest.approx(1.2560, abs=0.003)
        # Interpolating between the anchors stays between their prices.
        mid = pattern.neckline_price_at(
            (pattern.neckline_start.index + pattern.neckline_end.index) // 2
        )
        assert min(pattern.neckline_start.price, pattern.neckline_end.price) - 0.001 <= mid

    def test_broken_neckline_makes_the_pattern_a_valid_signal(self):
        candles = self._pattern_series()
        structure = analyse_structure(candles, "4H", lookback=3)
        patterns = detect_head_shoulders(candles, structure.swings, "4H", "GBP_USD")

        assert valid_signals(patterns), "the neckline breaks in this path"
        assert patterns[0].target_price is not None
        assert patterns[0].target_price < patterns[0].neckline_start.price

    def test_pattern_without_a_neckline_break_is_not_a_signal(self):
        # Stop the series at the right shoulder - the neckline never breaks.
        candles = self._pattern_series()[:48]
        structure = analyse_structure(candles, "4H", lookback=3)
        patterns = detect_head_shoulders(candles, structure.swings, "4H", "GBP_USD")

        for pattern in patterns:
            if not pattern.neckline_broken:
                assert pattern.is_valid_signal is False
                assert pattern.early_entry_risk is True
                assert any("HIGH RISK" in n for n in pattern.notes)

    def test_too_few_swings_finds_nothing(self):
        assert detect_head_shoulders(bars([1.1, 1.2]), [], "4H", SYMBOL) == []


class TestSyncRule:
    def _layer(self, w, d, h):
        return {
            "1W": StructureResult("1W", w),
            "1D": StructureResult("1D", d),
            "4H": StructureResult("4H", h),
        }

    def test_weekly_and_daily_agreeing_passes_the_default_rule(self):
        verdict = evaluate_sync(
            self._layer(Trend.BULLISH, Trend.BULLISH, Trend.BEARISH)
        )
        assert verdict.in_sync is True
        assert verdict.direction is Trend.BULLISH

    def test_weekly_and_daily_disagreeing_fails_the_default_rule(self):
        verdict = evaluate_sync(
            self._layer(Trend.BEARISH, Trend.BULLISH, Trend.BULLISH)
        )
        assert verdict.in_sync is False
        assert verdict.direction is Trend.UNDETERMINED

    def test_the_rule_is_reported_as_unconfirmed(self):
        verdict = evaluate_sync(
            self._layer(Trend.BULLISH, Trend.BULLISH, Trend.BULLISH)
        )
        assert verdict.rule_is_unconfirmed is True
        assert "UNCONFIRMED" in verdict.rule_note

    def test_the_alternate_reading_is_selectable(self, monkeypatch):
        """The notes' own examples imply 'any two consecutive' - both are built."""
        monkeypatch.setattr(config, "REQUIRED_SYNC_TIMEFRAMES", "any_two_consecutive")

        # W down / D up / 4H up: valid under this rule, invalid under the default.
        verdict = evaluate_sync(
            self._layer(Trend.BEARISH, Trend.BULLISH, Trend.BULLISH)
        )
        assert verdict.in_sync is True
        assert verdict.agreeing_timeframes == ["1D", "4H"]

        # W down / D up / 4H down: no adjacent pair agrees.
        assert not evaluate_sync(
            self._layer(Trend.BEARISH, Trend.BULLISH, Trend.BEARISH)
        ).in_sync


class TestSessionClock:
    def test_london_is_open_inside_the_primary_window(self):
        # 14:00 IST == 08:30 UTC
        clock = session_clock(datetime(2026, 8, 20, 8, 30, tzinfo=timezone.utc))

        assert "London" in clock.active_sessions
        assert clock.in_primary_window is True

    def test_outside_the_window_reports_time_until_it_opens(self):
        # 06:00 IST == 00:30 UTC
        clock = session_clock(datetime(2026, 8, 20, 0, 30, tzinfo=timezone.utc))

        assert clock.in_primary_window is False
        assert clock.minutes_until_primary_open > 0

    def test_new_york_window_wraps_past_midnight(self):
        ny = next(s for s in session_clock().sessions if s.name == "New York")
        assert ny.crosses_midnight is True

    def test_overlaps_are_named(self):
        # 12:00 IST == 06:30 UTC - Sydney and Tokyo both open.
        clock = session_clock(datetime(2026, 8, 20, 6, 30, tzinfo=timezone.utc))
        assert len(clock.active_sessions) > 1
        assert clock.overlap is not None

    def test_naive_datetimes_are_treated_as_utc(self):
        assert session_clock(datetime(2026, 8, 20, 8, 30)).in_primary_window is True


class TestEMA:
    def test_ema_is_seeded_and_tracks_price(self):
        values = [1.0 + i * 0.001 for i in range(60)]
        series = ema_series(values, 50)

        assert series[48] is None, "not enough data to seed yet"
        assert series[49] is not None
        assert series[-1] < values[-1], "a rising series leaves the EMA behind"

    def test_short_series_yields_no_value(self):
        state = compute_ema(bars([1.1, 1.2, 1.3]))
        assert state.value is None
        assert state.alignment is Trend.UNDETERMINED

    def test_alignment_follows_price_position(self):
        rising = compute_ema(bars([1.0 + i * 0.001 for i in range(80)]))
        assert rising.alignment is Trend.BULLISH


class TestCSVImport:
    def test_parses_a_standard_export(self):
        csv_text = (
            "time,open,high,low,close,volume\n"
            "2026-01-01T00:00:00Z,1.1000,1.1020,1.0990,1.1010,1500\n"
            "2026-01-01T01:00:00Z,1.1010,1.1030,1.1005,1.1025,1600\n"
        )
        candles = parse_ohlc_csv(csv_text)

        assert len(candles) == 2
        assert candles[0].close == pytest.approx(1.1010)
        assert candles[0].time < candles[1].time

    def test_accepts_alternative_headers_and_semicolons(self):
        csv_text = (
            "Date;O;H;L;C\n"
            "2026-01-01;1.1000;1.1020;1.0990;1.1010\n"
            "2026-01-02;1.1010;1.1030;1.1005;1.1025\n"
        )
        assert len(parse_ohlc_csv(csv_text)) == 2

    def test_missing_a_required_column_is_an_error(self):
        with pytest.raises(ValueError, match="Missing required column"):
            parse_ohlc_csv("time,open,high\n2026-01-01,1.1,1.2\n")

    def test_bad_rows_are_skipped_not_fatal(self):
        csv_text = (
            "time,open,high,low,close\n"
            "2026-01-01,1.1000,1.1020,1.0990,1.1010\n"
            "garbage,x,y,z,w\n"
            "2026-01-02,1.1010,1.1030,1.1005,1.1025\n"
        )
        assert len(parse_ohlc_csv(csv_text)) == 2

    def test_empty_input_is_an_error(self):
        with pytest.raises(ValueError):
            parse_ohlc_csv("   ")

    def test_epoch_timestamps_are_understood(self):
        assert parse_time("1767225600").year == 2026

    def test_round_trip_through_the_csv_writer(self):
        original = sample_data.generate_series(
            sample_data.get_scenario("eurusd_bullish_aoi"), "1D"
        )
        restored = parse_ohlc_csv(sample_data.candles_to_csv(original))

        assert len(restored) == len(original)
        assert restored[0].close == pytest.approx(original[0].close)


class TestReference:
    def test_explains_base_and_quote(self):
        info = explain_pair("EUR_USD", 1.10)

        assert info.base == "EUR" and info.quote == "USD"
        assert "1 EUR = 1.1 USD" in info.quote_example
        assert "EUR (the base) is getting stronger" in info.up_means
        assert info.is_major is True

    def test_jpy_pairs_report_the_larger_pip(self):
        assert explain_pair("USD_JPY").pip_size == pytest.approx(0.01)

    def test_unconfirmed_values_are_all_surfaced(self):
        flags = {f["id"] for f in flagged_for_confirmation()}
        assert {"sync_rule", "risk_table", "structure_lookback", "snake_trick"} <= flags


class TestEndToEnd:
    """The definition of done: load data, watch every stage actually run."""

    END = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)

    def _run(self, key, **kwargs):
        scenario = sample_data.get_scenario(key)
        data = sample_data.generate_all_timeframes(key, end_time=self.END)
        return scenario, engine.analyse(
            scenario.symbol, data, account_size=10_000.0, now=self.END, **kwargs
        )

    def test_bullish_scenario_produces_a_complete_sized_plan(self):
        _, analysis = self._run("eurusd_bullish_aoi")

        assert analysis.bias is Trend.BULLISH
        assert analysis.top_down.trend_layer["1W"].trend is Trend.BULLISH
        assert analysis.valid_zones, "expected a validated AOI"
        assert analysis.trigger.is_armed
        assert analysis.confluence.core_complete
        assert analysis.tradeable

        plan = analysis.trade_plan
        assert plan.direction is Direction.BUY, "trade must follow the bias"
        assert plan.meets_min_rr
        assert plan.position_size_lots > 0

    def test_head_shoulders_scenario_breaks_and_retests_its_neckline(self):
        _, analysis = self._run("gbpusd_head_shoulders")

        assert analysis.bias is Trend.BEARISH
        daily = analysis.head_shoulders.get("1D", [])
        assert daily and daily[0].neckline_broken
        assert daily[0].neckline_retested
        assert analysis.confluence.expanded["hs_neckline_break_retest"] is True
        assert analysis.trade_plan.direction is Direction.SELL

    def test_no_setup_scenario_refuses_and_explains_itself(self):
        _, analysis = self._run("usdjpy_no_setup")

        assert analysis.valid_zones == []
        assert analysis.tradeable is False
        assert analysis.trade_plan is None
        assert config.GUARDRAIL_MESSAGES["no_aoi"] in analysis.guardrails

    def test_weekly_pace_warns_once_the_limit_is_used(self):
        _, analysis = self._run(
            "eurusd_bullish_aoi", trade_times=[self.END - timedelta(days=1)]
        )
        assert any("this week" in g for g in analysis.guardrails)

    def test_aoi_is_never_computed_below_the_daily(self):
        _, analysis = self._run("eurusd_bullish_aoi")

        assert set(analysis.aoi_scans) <= set(config.AOI_TIMEFRAMES)
        assert all(z.timeframe in config.AOI_TIMEFRAMES for z in analysis.valid_zones)

    def test_the_snake_trace_reports_a_level_per_trend_timeframe(self):
        _, analysis = self._run("eurusd_bullish_aoi")

        assert set(analysis.snake_trace) == set(config.TREND_TIMEFRAMES)
        assert any(v is not None for v in analysis.snake_trace.values())

    def test_analysis_is_deterministic(self):
        _, first = self._run("eurusd_bullish_aoi")
        _, second = self._run("eurusd_bullish_aoi")

        assert first.confluence.score == second.confluence.score
        assert first.current_price == second.current_price

    def test_every_scenario_runs_without_error(self):
        for key in sample_data.SCENARIOS:
            _, analysis = self._run(key)
            assert analysis.confluence is not None
            assert analysis.session is not None


class TestSampleDataIntegrity:
    """Generated bars must be valid candles - every module reads them."""

    def test_every_bar_is_internally_consistent(self):
        for key in sample_data.SCENARIOS:
            for tf, candles in sample_data.generate_all_timeframes(key).items():
                assert candles, f"{key}/{tf} produced no candles"
                for i, c in enumerate(candles):
                    assert c.high >= c.low, f"{key}/{tf}[{i}]: high below low"
                    assert c.high >= c.open, f"{key}/{tf}[{i}]: high below open"
                    assert c.high >= c.close, f"{key}/{tf}[{i}]: high below close"
                    assert c.low <= c.open, f"{key}/{tf}[{i}]: low above open"
                    assert c.low <= c.close, f"{key}/{tf}[{i}]: low above close"

    def test_candles_are_chronological(self):
        for key in sample_data.SCENARIOS:
            for tf, candles in sample_data.generate_all_timeframes(key).items():
                times = [c.time for c in candles]
                assert times == sorted(times), f"{key}/{tf} is out of order"

    def test_the_same_scenario_renders_identically_twice(self):
        first = sample_data.generate_series(
            sample_data.get_scenario("eurusd_bullish_aoi"), "1D", end_time=BASE
        )
        second = sample_data.generate_series(
            sample_data.get_scenario("eurusd_bullish_aoi"), "1D", end_time=BASE
        )
        assert [c.close for c in first] == [c.close for c in second]
