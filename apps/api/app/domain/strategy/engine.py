"""End-to-end orchestrator - the top-down pass in one call.

Runs the full sequence the notes describe, in order:

    trend (1W/1D/4H)  ->  AOI (1W/1D only)  ->  break & retest  ->
    candlestick / H&S pattern  ->  confluence score  ->  sized trade plan

Every stage is a real computation over the supplied candles. When a stage
fails its rule the pass stops producing a trade and returns the matching
discipline message instead - that refusal is a feature, not an error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from . import config
from .aoi import AOIScan, detect_aoi_zones
from .break_retest import scan_for_trigger
from .confluence import ConfluenceInputs, evaluate, guardrail_message
from .head_shoulders import detect_head_shoulders
from .indicators import EMAState, compute_ema
from .patterns import actionable, detect_patterns
from .pips import from_pips, round_price
from .risk import build_trade_plan, suggest_take_profit, weekly_pace
from .sessions import SessionClock, session_clock
from .structure import analyse_structure, trace_last_valid_structure_point
from .topdown import TopDownView, build_top_down_view
from .types import (
    AOIZone,
    BreakRetestSignal,
    Candle,
    ConfluenceResult,
    Direction,
    HeadShouldersPattern,
    PatternMatch,
    StructureResult,
    TradePlan,
    Trend,
    ZoneType,
)

#: Extra room beyond the AOI edge when placing the stop.
STOP_BUFFER_PIPS = 5.0


@dataclass
class StrategyAnalysis:
    """The complete top-down read for one pair."""

    symbol: str
    generated_at: datetime
    entry_timeframe: str
    current_price: float

    top_down: TopDownView
    aoi_scans: Dict[str, AOIScan] = field(default_factory=dict)
    valid_zones: List[AOIZone] = field(default_factory=list)
    active_zone: Optional[AOIZone] = None

    trigger: Optional[BreakRetestSignal] = None
    patterns: Dict[str, List[PatternMatch]] = field(default_factory=dict)
    actionable_patterns: List[PatternMatch] = field(default_factory=list)
    head_shoulders: Dict[str, List[HeadShouldersPattern]] = field(default_factory=dict)
    ema: Optional[EMAState] = None
    snake_trace: Dict[str, Optional[float]] = field(default_factory=dict)

    confluence: Optional[ConfluenceResult] = None
    trade_plan: Optional[TradePlan] = None
    session: Optional[SessionClock] = None

    tradeable: bool = False
    guardrails: List[str] = field(default_factory=list)
    narrative: List[str] = field(default_factory=list)

    @property
    def bias(self) -> Trend:
        return self.top_down.bias


def analyse(
    symbol: str,
    candles_by_timeframe: Dict[str, List[Candle]],
    account_size: float = 10_000.0,
    entry_timeframe: str = "1H",
    trade_times: Optional[List[datetime]] = None,
    now: Optional[datetime] = None,
) -> StrategyAnalysis:
    """Run the whole strategy over a pair's multi-timeframe candles.

    Args:
        symbol: pair, e.g. ``EUR_USD``.
        candles_by_timeframe: OHLC series keyed by timeframe label. Weekly and
            Daily are required for AOI; the entry timeframe is required for the
            trigger.
        account_size: balance used to size the plan.
        entry_timeframe: which lower timeframe carries the entry trigger.
        trade_times: previously placed trades, for the weekly pacer.
        now: evaluation instant (UTC). Defaults to now.

    Returns:
        A :class:`StrategyAnalysis`. ``trade_plan`` is populated only when all
        four core pillars pass *and* the plan clears the 1:2 RR floor.
    """
    now = now or datetime.now(timezone.utc)

    # --- 1. Trend: structure across every timeframe, then the sync gate ----
    top_down = build_top_down_view(symbol, candles_by_timeframe)

    reference_series = (
        candles_by_timeframe.get(entry_timeframe)
        or candles_by_timeframe.get("1D")
        or next(iter(candles_by_timeframe.values()), [])
    )
    current_price = reference_series[-1].close if reference_series else 0.0

    analysis = StrategyAnalysis(
        symbol=symbol,
        generated_at=now,
        entry_timeframe=entry_timeframe,
        current_price=current_price,
        top_down=top_down,
        session=session_clock(now),
    )

    # The "snake trick" backtrace, reported per trend timeframe.
    for tf, structure in top_down.trend_layer.items():
        point = trace_last_valid_structure_point(structure.swings, structure.trend)
        analysis.snake_trace[tf] = point.price if point else None

    if top_down.trend_layer:
        analysis.narrative.append(
            "Trend: "
            + "; ".join(
                f"{tf} {res.trend.value}" for tf, res in top_down.trend_layer.items()
            )
            + f" -> {top_down.sync.explanation}"
        )

    # --- 2. AOI: Weekly and Daily only ------------------------------------
    for tf in config.AOI_TIMEFRAMES:
        candles = candles_by_timeframe.get(tf)
        if not candles:
            continue
        scan = detect_aoi_zones(
            candles, tf, symbol, top_down.trend_layer.get(tf)
        )
        analysis.aoi_scans[tf] = scan
        analysis.valid_zones.extend(scan.zones)

    analysis.valid_zones.sort(key=lambda z: z.confidence, reverse=True)
    for zone in analysis.valid_zones:
        if zone.contains(current_price):
            analysis.active_zone = zone
            break

    if analysis.valid_zones:
        best = analysis.valid_zones[0]
        analysis.narrative.append(
            f"AOI: {best.timeframe} {best.golden_rule_tag} "
            f"{best.lower:g}-{best.upper:g} ({best.width_pips:g} pips, "
            f"{best.touches} touches, confidence {best.confidence:.0%})."
        )
    else:
        analysis.narrative.append("AOI: none valid on Weekly or Daily.")

    # --- 3. Entry trigger: break & retest ---------------------------------
    entry_structure = top_down.entry_layer.get(entry_timeframe)
    if entry_structure is None and reference_series:
        entry_structure = analyse_structure(reference_series, entry_timeframe)

    if reference_series and entry_structure:
        analysis.trigger = scan_for_trigger(
            reference_series,
            symbol,
            entry_structure,
            analysis.valid_zones,
            bias=top_down.bias,
        )
        analysis.narrative.append(
            f"Trigger ({entry_timeframe}): {analysis.trigger.status}"
            + (
                f" - {analysis.trigger.notes[-1]}"
                if analysis.trigger.notes
                else ""
            )
        )

    # --- 4. Patterns: candlesticks and Head & Shoulders --------------------
    pattern_timeframes = list(config.TREND_TIMEFRAMES) + [entry_timeframe]
    for tf in dict.fromkeys(pattern_timeframes):
        candles = candles_by_timeframe.get(tf)
        if not candles:
            continue

        zones = [z for z in analysis.valid_zones]
        analysis.patterns[tf] = detect_patterns(
            candles, tf, symbol, zones, scan_last=60
        )

        structure = top_down.trend_layer.get(tf) or top_down.entry_layer.get(tf)
        if structure is None:
            structure = analyse_structure(candles, tf)
        analysis.head_shoulders[tf] = detect_head_shoulders(
            candles, structure.swings, tf, symbol
        )

    analysis.actionable_patterns = [
        p for matches in analysis.patterns.values() for p in actionable(matches)
    ]
    # Only a pattern pointing the same way as the bias supports the setup - a
    # bullish engulfing does nothing for a short.
    with_bias = [p for p in analysis.actionable_patterns if p.bias is top_down.bias]
    if with_bias:
        best_pattern = max(with_bias, key=lambda p: p.weighted_strength)
        analysis.narrative.append(
            f"Pattern: {best_pattern.name} on {best_pattern.timeframe} at the AOI "
            f"(weighted strength {best_pattern.weighted_strength:.2f})."
        )
    elif analysis.actionable_patterns:
        analysis.narrative.append(
            f"Pattern: {len(analysis.actionable_patterns)} formation(s) at an AOI, "
            f"but none agreeing with the {top_down.bias.value} bias."
        )
    else:
        analysis.narrative.append("Pattern: nothing actionable at an AOI.")

    # --- 5. EMA (supplementary only) --------------------------------------
    daily = candles_by_timeframe.get("1D")
    if daily:
        analysis.ema = compute_ema(daily)

    # --- 6. Confluence ----------------------------------------------------
    analysis.confluence = evaluate(
        ConfluenceInputs(
            bias=top_down.bias,
            sync=top_down.sync,
            aoi_scan=_merged_scan(analysis),
            current_price=current_price,
            trigger=analysis.trigger,
            patterns=analysis.actionable_patterns,
            head_shoulders=analysis.head_shoulders,
            ema=analysis.ema,
            daily_structure=top_down.trend_layer.get("1D"),
        )
    )

    message = guardrail_message(analysis.confluence)
    if message:
        analysis.guardrails.append(message)

    # --- 7. Trade plan ----------------------------------------------------
    if analysis.confluence.eligible:
        analysis.trade_plan = _build_plan(analysis, symbol, account_size)
        if analysis.trade_plan and not analysis.trade_plan.meets_min_rr:
            analysis.guardrails.append(
                f"Plan rejected: reward:risk 1:{analysis.trade_plan.reward_risk:.2f} "
                f"is below the 1:{config.MIN_REWARD_RISK:g} floor."
            )
            analysis.trade_plan = None

    analysis.tradeable = analysis.trade_plan is not None

    # --- 8. Weekly pace ---------------------------------------------------
    pace = weekly_pace(trade_times or [], now)
    if pace.at_limit and analysis.tradeable:
        analysis.guardrails.append(pace.message)

    if analysis.tradeable and analysis.trade_plan:
        plan = analysis.trade_plan
        analysis.narrative.append(
            f"Plan: {plan.direction.value} {plan.position_size_lots:g} lots at "
            f"{plan.entry:g}, stop {plan.stop_loss:g}, target {plan.take_profit:g} "
            f"(1:{plan.reward_risk:g} RR)."
        )

    return analysis


def _merged_scan(analysis: StrategyAnalysis) -> AOIScan:
    """Collapse the Weekly and Daily scans into one view for the scorer."""
    merged = AOIScan(timeframe="1W+1D", allowed=True)
    merged.zones = list(analysis.valid_zones)
    for scan in analysis.aoi_scans.values():
        merged.rejected.extend(scan.rejected)
    merged.message = (
        analysis.aoi_scans.get("1D", analysis.aoi_scans.get("1W")).message
        if analysis.aoi_scans
        else config.GUARDRAIL_MESSAGES["no_aoi"]
    )
    return merged


def _build_plan(
    analysis: StrategyAnalysis, symbol: str, account_size: float
) -> Optional[TradePlan]:
    """Turn an eligible setup into a sized, RR-checked plan.

    Entry is the retest level (never mid-zone). The stop sits just beyond the
    far edge of the AOI, and the target is the 1:4 projection unless a Head &
    Shoulders measured move sits closer - in which case the measured move is
    used, because it is the level price is actually reaching for.
    """
    trigger = analysis.trigger
    if trigger is None or not trigger.is_armed or trigger.direction is None:
        return None

    direction = trigger.direction
    zone = analysis.active_zone or _zone_for(analysis, direction)
    entry = trigger.retest_price or analysis.current_price
    buffer = from_pips(STOP_BUFFER_PIPS, symbol)

    if zone is not None:
        # The stop sits beyond the FAR edge of the zone, so the whole area of
        # interest is inside the trade. Entering at one edge must not leave a
        # stop only a buffer's width away.
        stop = (
            min(zone.lower, entry) - buffer
            if direction is Direction.BUY
            else max(zone.upper, entry) + buffer
        )
    else:
        structure = analysis.top_down.trend_layer.get("1D")
        anchor = None
        if structure:
            anchor = (
                structure.last_valid_hl
                if direction is Direction.BUY
                else structure.last_valid_lh
            )
        if anchor is None:
            return None
        stop = anchor.price - buffer if direction is Direction.BUY else anchor.price + buffer

    # Never let the stop sit inside spread-and-noise range of the entry.
    floor = from_pips(config.MIN_STOP_DISTANCE_PIPS, symbol)
    if direction is Direction.BUY:
        stop = min(stop, entry - floor)
    else:
        stop = max(stop, entry + floor)

    if (direction is Direction.BUY and stop >= entry) or (
        direction is Direction.SELL and stop <= entry
    ):
        return None

    target = suggest_take_profit(entry, stop, config.TARGET_REWARD_RISK)

    # Prefer a Head & Shoulders measured move when it is nearer than the 1:4
    # projection - a target price will not reach is not a target.
    for patterns in analysis.head_shoulders.values():
        for pattern in patterns:
            if not pattern.is_valid_signal or pattern.bias is not analysis.bias:
                continue
            if pattern.target_price is None:
                continue
            if direction is Direction.BUY and entry < pattern.target_price < target:
                target = pattern.target_price
            elif direction is Direction.SELL and target < pattern.target_price < entry:
                target = pattern.target_price

    return build_trade_plan(
        symbol=symbol,
        direction=direction,
        entry=round_price(entry, symbol),
        stop_loss=round_price(stop, symbol),
        account_size=account_size,
        take_profit=round_price(target, symbol),
    )


def _zone_for(
    analysis: StrategyAnalysis, direction: Direction
) -> Optional[AOIZone]:
    """Best zone matching the trade direction - support to buy, resistance to sell."""
    want = ZoneType.SUPPORT if direction is Direction.BUY else ZoneType.RESISTANCE
    for zone in analysis.valid_zones:
        if zone.zone_type is want:
            return zone
    return analysis.valid_zones[0] if analysis.valid_zones else None
