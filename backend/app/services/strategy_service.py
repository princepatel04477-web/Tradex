"""Strategy service - the bridge between the pure engine and the HTTP layer.

The engine in ``app/strategy`` knows nothing about FastAPI. Everything in this
module is either serialisation or request orchestration; no trading rule is
implemented here, so the rules can only ever live in one place.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.schemas import strategy as api
from app.strategy import config, engine, reference, sample_data
from app.strategy.aoi import AOIScan, detect_aoi_zones
from app.strategy.data_input import fetch_live_candles, live_data_enabled, parse_ohlc_csv
from app.strategy.indicators import EMAState, compute_ema
from app.strategy.journal import JournalEntry, journal_store
from app.strategy.risk import (
    WeeklyPace,
    build_trade_plan,
    risk_table,
    weekly_pace,
)
from app.strategy.sessions import SessionClock, session_clock
from app.strategy.structure import (
    analyse_structure,
    describe,
    trace_last_valid_structure_point,
)
from app.strategy.types import (
    AOIZone,
    BreakRetestSignal,
    Candle,
    ConfluenceResult,
    Direction,
    HeadShouldersPattern,
    PatternMatch,
    StructureResult,
    SwingPoint,
    TradePlan,
)


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------


def candle_out(candle: Candle) -> api.CandleOut:
    return api.CandleOut(
        time=candle.time,
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        volume=candle.volume,
    )


def swing_out(swing: Optional[SwingPoint]) -> Optional[api.SwingPointOut]:
    if swing is None:
        return None
    return api.SwingPointOut(
        index=swing.index,
        time=swing.time,
        price=swing.price,
        kind=swing.kind.value,
        label=swing.label.value if swing.label else None,
        broken=swing.broken,
        broken_time=swing.broken_time,
        broken_reason=swing.broken_reason,
    )


def structure_out(
    result: StructureResult, snake_price: Optional[float] = None
) -> api.StructureOut:
    rng = result.structural_range
    return api.StructureOut(
        timeframe=result.timeframe,
        trend=result.trend.value,
        swings=[swing_out(s) for s in result.swings],
        live_swing_count=len(result.live_swings),
        choch_events=[
            api.ChochOut(
                index=e.index,
                time=e.time,
                close=e.close,
                broken_level=e.broken_level,
                broken_label=e.broken_label.value,
                from_trend=e.from_trend.value,
                to_trend=e.to_trend.value,
                description=e.description,
            )
            for e in result.choch_events
        ],
        last_valid_hl=swing_out(result.last_valid_hl),
        last_valid_lh=swing_out(result.last_valid_lh),
        last_hh=swing_out(result.last_hh),
        last_ll=swing_out(result.last_ll),
        structural_range=list(rng) if rng else None,
        candles_analysed=result.candles_analysed,
        summary=describe(result),
        snake_trace_price=snake_price,
    )


def zone_out(zone: AOIZone) -> api.AOIZoneOut:
    return api.AOIZoneOut(
        timeframe=zone.timeframe,
        lower=zone.lower,
        upper=zone.upper,
        mid=zone.mid,
        zone_type=zone.zone_type.value,
        golden_rule_tag=zone.golden_rule_tag,
        touches=zone.touches,
        touch_times=zone.touch_times,
        width_pips=zone.width_pips,
        valid=zone.valid,
        confidence=zone.confidence,
        rejection_reasons=zone.rejection_reasons,
    )


def scan_out(scan: AOIScan) -> api.AOIScanOut:
    return api.AOIScanOut(
        timeframe=scan.timeframe,
        allowed=scan.allowed,
        zones=[zone_out(z) for z in scan.zones],
        rejected=[zone_out(z) for z in scan.rejected],
        message=scan.message,
        has_valid_aoi=scan.has_valid_aoi,
    )


def trigger_out(signal: Optional[BreakRetestSignal]) -> Optional[api.TriggerOut]:
    if signal is None:
        return None
    return api.TriggerOut(
        status=signal.status,
        direction=signal.direction.value if signal.direction else None,
        level=signal.level,
        level_label=signal.level_label,
        break_time=signal.break_time,
        break_close=signal.break_close,
        retest_time=signal.retest_time,
        retest_price=signal.retest_price,
        candles_to_retest=signal.candles_to_retest,
        is_armed=signal.is_armed,
        notes=signal.notes,
    )


def pattern_out(match: PatternMatch) -> api.PatternOut:
    return api.PatternOut(
        name=match.name,
        index=match.index,
        time=match.time,
        timeframe=match.timeframe,
        bias=match.bias.value,
        strength=match.strength,
        weighted_strength=match.weighted_strength,
        at_aoi=match.at_aoi,
        detail=match.detail,
    )


def hs_out(pattern: HeadShouldersPattern) -> api.HeadShouldersOut:
    return api.HeadShouldersOut(
        kind=pattern.kind,
        timeframe=pattern.timeframe,
        bias=pattern.bias.value,
        left_shoulder=swing_out(pattern.left_shoulder),
        head=swing_out(pattern.head),
        right_shoulder=swing_out(pattern.right_shoulder),
        neckline_start=swing_out(pattern.neckline_start),
        neckline_end=swing_out(pattern.neckline_end),
        neckline_broken=pattern.neckline_broken,
        neckline_retested=pattern.neckline_retested,
        target_price=pattern.target_price,
        is_valid_signal=pattern.is_valid_signal,
        early_entry_risk=pattern.early_entry_risk,
        notes=pattern.notes,
    )


def ema_out(state: Optional[EMAState]) -> Optional[api.EMAOut]:
    if state is None:
        return None
    return api.EMAOut(
        period=state.period,
        value=state.value,
        price=state.price,
        alignment=state.alignment.value,
        slope=state.slope,
        # Only the tail is useful for an overlay, and it keeps payloads small.
        series=state.series[-300:],
    )


def confluence_out(result: Optional[ConfluenceResult]) -> Optional[api.ConfluenceOut]:
    if result is None:
        return None
    return api.ConfluenceOut(
        core_pillars=result.core_pillars,
        core_complete=result.core_complete,
        missing_core=result.missing_core,
        expanded=result.expanded,
        score=result.score,
        max_score=result.max_score,
        low_risk_high_reward=result.low_risk_high_reward,
        reasons=result.reasons,
    )


def plan_out(plan: Optional[TradePlan]) -> Optional[api.TradePlanOut]:
    if plan is None:
        return None
    return api.TradePlanOut(
        symbol=plan.symbol,
        direction=plan.direction.value,
        entry=plan.entry,
        stop_loss=plan.stop_loss,
        take_profit=plan.take_profit,
        stop_distance_pips=plan.stop_distance_pips,
        target_distance_pips=plan.target_distance_pips,
        reward_risk=plan.reward_risk,
        account_size=plan.account_size,
        risk_pct=plan.risk_pct,
        risk_amount=plan.risk_amount,
        pip_value_per_lot=plan.pip_value_per_lot,
        position_size_lots=plan.position_size_lots,
        position_size_units=plan.position_size_units,
        meets_min_rr=plan.meets_min_rr,
        meets_target_rr=plan.meets_target_rr,
        risk_tier_unconfirmed=plan.risk_tier_unconfirmed,
        warnings=plan.warnings,
    )


def clock_out(clock: SessionClock) -> api.SessionClockOut:
    return api.SessionClockOut(
        now_utc=clock.now_utc,
        now_ist=clock.now_ist,
        sessions=[
            api.SessionWindowOut(
                name=s.name,
                open_ist=s.open_ist,
                close_ist=s.close_ist,
                open_utc=s.open_utc,
                close_utc=s.close_utc,
                is_active=s.is_active,
                crosses_midnight=s.crosses_midnight,
                minutes_until_open=s.minutes_until_open,
                minutes_until_close=s.minutes_until_close,
            )
            for s in clock.sessions
        ],
        active_sessions=clock.active_sessions,
        overlap=clock.overlap,
        in_primary_window=clock.in_primary_window,
        primary_window_ist=clock.primary_window_ist,
        minutes_until_primary_open=clock.minutes_until_primary_open,
        minutes_until_primary_close=clock.minutes_until_primary_close,
        message=clock.message,
    )


def pace_out(pace: WeeklyPace) -> api.WeeklyPaceOut:
    return api.WeeklyPaceOut(
        week_start=pace.week_start,
        week_end=pace.week_end,
        trades_this_week=pace.trades_this_week,
        limit=pace.limit,
        remaining=pace.remaining,
        at_limit=pace.at_limit,
        message=pace.message,
    )


def journal_out(entry: JournalEntry) -> api.JournalEntryOut:
    return api.JournalEntryOut(
        id=entry.id,
        symbol=entry.symbol,
        direction=entry.direction,
        placed_at=entry.placed_at,
        week_key=entry.week_key,
        sync_state=entry.sync_state,
        sync_timeframes=entry.sync_timeframes,
        aoi_zone=entry.aoi_zone,
        aoi_timeframe=entry.aoi_timeframe,
        aoi_touches=entry.aoi_touches,
        patterns=entry.patterns,
        confluence_score=entry.confluence_score,
        confluence_max=entry.confluence_max,
        low_risk_high_reward=entry.low_risk_high_reward,
        entry=entry.entry,
        stop_loss=entry.stop_loss,
        take_profit=entry.take_profit,
        planned_rr=entry.planned_rr,
        position_size_lots=entry.position_size_lots,
        risk_amount=entry.risk_amount,
        outcome=entry.outcome,
        exit_price=entry.exit_price,
        closed_at=entry.closed_at,
        realised_rr=entry.realised_rr,
        pnl=entry.pnl,
        notes=entry.notes,
        tags=entry.tags,
        is_placed=entry.is_placed,
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class StrategyService:
    """Orchestrates data loading and calls into the engine."""

    # -- data ------------------------------------------------------------

    def scenarios(self) -> List[api.ScenarioOut]:
        return [api.ScenarioOut(**s) for s in sample_data.list_scenarios()]

    def load_candles(
        self, scenario_key: str, timeframes: Optional[List[str]] = None
    ) -> Dict[str, List[Candle]]:
        """Candles for a scenario - live data when enabled, sample otherwise."""
        scenario = sample_data.get_scenario(scenario_key)
        tfs = timeframes or list(sample_data.TIMEFRAME_HOURS.keys())

        if live_data_enabled():
            live: Dict[str, List[Candle]] = {}
            for tf in tfs:
                fetched = fetch_live_candles(scenario.symbol, tf)
                if fetched:
                    live[tf] = fetched
            if len(live) == len(tfs):
                return live
            # Partial live data is worse than none - fall through to sample.

        return sample_data.generate_all_timeframes(scenario_key, tfs)

    def candle_series(
        self, scenario_key: str, timeframe: str, limit: int = 300
    ) -> api.CandleSeries:
        scenario = sample_data.get_scenario(scenario_key)
        candles = self.load_candles(scenario_key, [timeframe])[timeframe]
        tail = candles[-limit:]
        return api.CandleSeries(
            symbol=scenario.symbol,
            timeframe=timeframe,
            candles=[candle_out(c) for c in tail],
            count=len(tail),
        )

    def candles_csv(self, scenario_key: str, timeframe: str) -> str:
        candles = self.load_candles(scenario_key, [timeframe])[timeframe]
        return sample_data.candles_to_csv(candles)

    # -- analysis --------------------------------------------------------

    def analyse_scenario(
        self,
        scenario_key: str,
        account_size: float = 10_000.0,
        entry_timeframe: str = "1H",
    ) -> api.AnalysisOut:
        """Full top-down pass over a bundled sample scenario."""
        scenario = sample_data.get_scenario(scenario_key)
        candles = self.load_candles(scenario_key)
        return self._analyse(
            scenario.symbol, candles, account_size, entry_timeframe
        )

    def analyse_uploaded(self, request: api.AnalysisRequest) -> api.AnalysisOut:
        """Full top-down pass over pasted or uploaded CSV data.

        Raises:
            ValueError: if a timeframe's CSV cannot be parsed, or Weekly and
                Daily are both absent (AOI needs at least one of them).
        """
        candles: Dict[str, List[Candle]] = {}
        for timeframe, text in request.csv_by_timeframe.items():
            if timeframe not in config.TIMEFRAMES:
                raise ValueError(
                    f"Unknown timeframe {timeframe!r}. "
                    f"Expected one of: {', '.join(config.TIMEFRAMES)}"
                )
            candles[timeframe] = parse_ohlc_csv(text)

        if not ({"1W", "1D"} & set(candles)):
            raise ValueError(
                "Supply Weekly or Daily data - AOI is only ever computed on "
                "those timeframes, and without one there is no setup to find."
            )

        return self._analyse(
            request.symbol,
            candles,
            request.account_size,
            request.entry_timeframe,
        )

    def _analyse(
        self,
        symbol: str,
        candles: Dict[str, List[Candle]],
        account_size: float,
        entry_timeframe: str,
    ) -> api.AnalysisOut:
        # The weekly pacer reads real logged trades, so the guardrail reflects
        # what the trader has actually done this week.
        trade_times = [e.placed_at for e in journal_store.all()]

        result = engine.analyse(
            symbol,
            candles,
            account_size=account_size,
            entry_timeframe=entry_timeframe,
            trade_times=trade_times,
        )

        return api.AnalysisOut(
            symbol=result.symbol,
            generated_at=result.generated_at,
            entry_timeframe=result.entry_timeframe,
            current_price=result.current_price,
            bias=result.bias.value,
            tradeable=result.tradeable,
            top_down=api.TopDownOut(
                symbol=result.top_down.symbol,
                trend_layer={
                    tf: structure_out(res, result.snake_trace.get(tf))
                    for tf, res in result.top_down.trend_layer.items()
                },
                entry_layer={
                    tf: structure_out(res)
                    for tf, res in result.top_down.entry_layer.items()
                },
                sync=(
                    api.SyncOut(
                        in_sync=result.top_down.sync.in_sync,
                        rule=result.top_down.sync.rule,
                        direction=result.top_down.sync.direction.value,
                        agreeing_timeframes=result.top_down.sync.agreeing_timeframes,
                        explanation=result.top_down.sync.explanation,
                        rule_is_unconfirmed=result.top_down.sync.rule_is_unconfirmed,
                        rule_note=result.top_down.sync.rule_note,
                    )
                    if result.top_down.sync
                    else None
                ),
                trend_is_your_friend=result.top_down.trend_is_your_friend,
                bias=result.top_down.bias.value,
                messages=result.top_down.messages,
            ),
            aoi_scans={tf: scan_out(s) for tf, s in result.aoi_scans.items()},
            valid_zones=[zone_out(z) for z in result.valid_zones],
            active_zone=zone_out(result.active_zone) if result.active_zone else None,
            trigger=trigger_out(result.trigger),
            patterns={
                tf: [pattern_out(p) for p in matches]
                for tf, matches in result.patterns.items()
            },
            actionable_patterns=[
                pattern_out(p) for p in result.actionable_patterns
            ],
            head_shoulders={
                tf: [hs_out(p) for p in patterns]
                for tf, patterns in result.head_shoulders.items()
            },
            ema=ema_out(result.ema),
            confluence=confluence_out(result.confluence),
            trade_plan=plan_out(result.trade_plan),
            session=clock_out(result.session) if result.session else None,
            weekly_pace=pace_out(weekly_pace(trade_times, result.generated_at)),
            guardrails=result.guardrails,
            narrative=result.narrative,
        )

    # -- individual modules ----------------------------------------------

    def structure_for(self, scenario_key: str, timeframe: str) -> api.StructureOut:
        candles = self.load_candles(scenario_key, [timeframe])[timeframe]
        result = analyse_structure(candles, timeframe)
        point = trace_last_valid_structure_point(result.swings, result.trend)
        return structure_out(result, point.price if point else None)

    def aoi_for(self, scenario_key: str, timeframe: str) -> api.AOIScanOut:
        scenario = sample_data.get_scenario(scenario_key)
        candles = self.load_candles(scenario_key, [timeframe])[timeframe]
        structure = analyse_structure(candles, timeframe)
        return scan_out(
            detect_aoi_zones(candles, timeframe, scenario.symbol, structure)
        )

    def ema_for(self, scenario_key: str, timeframe: str, period: int) -> api.EMAOut:
        candles = self.load_candles(scenario_key, [timeframe])[timeframe]
        return ema_out(compute_ema(candles, period))

    def sessions(self) -> api.SessionClockOut:
        return clock_out(session_clock())

    # -- risk ------------------------------------------------------------

    def risk_table(self) -> api.RiskTableOut:
        return api.RiskTableOut(
            tiers=[api.RiskTierOut(**row) for row in risk_table()],
            min_reward_risk=config.MIN_REWARD_RISK,
            target_reward_risk=config.TARGET_REWARD_RISK,
            max_trades_per_week=config.MAX_TRADES_PER_WEEK,
            note=config.RISK_TABLE_NOTE,
        )

    def trade_plan(self, request: api.TradePlanRequest) -> api.TradePlanOut:
        plan = build_trade_plan(
            symbol=request.symbol,
            direction=Direction(request.direction),
            entry=request.entry,
            stop_loss=request.stop_loss,
            account_size=request.account_size,
            take_profit=request.take_profit,
            risk_pct_override=request.risk_pct_override,
            quote_to_account_rate=request.quote_to_account_rate,
        )
        return plan_out(plan)

    # -- reference -------------------------------------------------------

    def reference(self) -> api.ReferenceOut:
        return api.ReferenceOut(
            majors=[s.replace("_", "/") for s in reference.MAJOR_PAIRS],
            chart_types=list(reference.CHART_TYPES),
            tools=reference.TOOLS,
            brokers=reference.BROKERS,
            guiding_principle=reference.GUIDING_PRINCIPLE,
            golden_rules=reference.GOLDEN_RULES,
            flagged_for_confirmation=[
                api.FlaggedItemOut(**item)
                for item in reference.flagged_for_confirmation()
            ],
        )

    def explain_pair(
        self, symbol: str, rate: Optional[float] = None
    ) -> api.PairExplainerOut:
        info = reference.explain_pair(symbol, rate)
        return api.PairExplainerOut(**info.__dict__)

    # -- journal ---------------------------------------------------------

    def log_trade(self, request: api.JournalLogRequest) -> api.JournalEntryOut:
        entry = journal_store.log(**request.model_dump())
        return journal_out(entry)

    def journal(self) -> List[api.JournalEntryOut]:
        return [journal_out(e) for e in journal_store.all()]

    def close_trade(
        self, entry_id: str, request: api.JournalCloseRequest
    ) -> api.JournalEntryOut:
        entry = journal_store.close(
            entry_id,
            exit_price=request.exit_price,
            outcome=request.outcome,
            pnl=request.pnl,
        )
        return journal_out(entry)

    def edit_levels(
        self, entry_id: str, request: api.JournalEditRequest
    ) -> api.JournalEditResponse:
        entry, notice = journal_store.edit_levels(
            entry_id,
            entry_price=request.entry,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            acknowledge_set_and_forget=request.acknowledge_set_and_forget,
        )
        return api.JournalEditResponse(
            entry=journal_out(entry), notice=notice, applied=not notice
        )

    def delete_trade(self, entry_id: str) -> bool:
        return journal_store.delete(entry_id)

    def journal_weeks(self) -> List[api.JournalWeekOut]:
        return [
            api.JournalWeekOut(
                week=bucket["week"],
                trade_count=bucket["trade_count"],
                limit=bucket["limit"],
                over_limit=bucket["over_limit"],
                trades=[journal_out(e) for e in bucket["trades"]],
            )
            for bucket in journal_store.weekly_view()
        ]

    def journal_stats(self) -> api.JournalStatsOut:
        return api.JournalStatsOut(**journal_store.stats())

    def pace(self) -> api.WeeklyPaceOut:
        return pace_out(journal_store.pace())

    # -- TradingAgents bridge --------------------------------------------

    def bridge_status(self) -> api.BridgeStatusOut:
        """Whether the optional LLM second opinion is configured."""
        from app.services.tradingagents_bridge import tradingagents_bridge

        return api.BridgeStatusOut(**tradingagents_bridge.status().__dict__)

    def review_scenario(
        self,
        scenario_key: str,
        account_size: float = 10_000.0,
        entry_timeframe: str = "1H",
    ) -> api.SetupReviewOut:
        """Run the engine, then ask the LLM layer to argue both sides of it."""
        from app.services.tradingagents_bridge import tradingagents_bridge

        analysis = self.analyse_scenario(scenario_key, account_size, entry_timeframe)
        review = tradingagents_bridge.review(analysis.model_dump(mode="json"))
        return api.SetupReviewOut(**review.__dict__)


#: Process-wide singleton, matching the other services.
strategy_service = StrategyService()
