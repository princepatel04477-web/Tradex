"""Module 10 - Confluence scoring engine.

Two linked layers, exactly as the notes describe them:

**Core 4 pillars** (all mandatory)
    Trend confirmed -> AOI valid -> Entry trigger (break & retest) confirmed ->
    Pattern confirmed.

**Expanded checklist** (scored only once all four core pillars are true)
    directional bias, at a valid AOI, Morning/Evening Star, Head & Shoulders,
    EMA alignment, break & retest, Daily trend confirmation, Engulfing,
    4H Head & Shoulders, break & retest of the H&S neckline.

The score is a plain count of confirmed expanded items. It is never computed
while a core pillar is missing, and no trade is ever suggested in that state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import config
from .aoi import AOIScan
from .indicators import EMAState, ema_confluence
from .topdown import SyncVerdict
from .types import (
    BreakRetestSignal,
    ConfluenceResult,
    HeadShouldersPattern,
    PatternMatch,
    StructureResult,
    Trend,
)


@dataclass
class ConfluenceInputs:
    """Everything the scorer needs, gathered by the engine."""

    bias: Trend
    sync: SyncVerdict
    aoi_scan: Optional[AOIScan] = None
    current_price: float = 0.0
    trigger: Optional[BreakRetestSignal] = None
    #: Actionable candlestick matches (already filtered to at-AOI).
    patterns: List[PatternMatch] = field(default_factory=list)
    #: Head & Shoulders patterns keyed by the timeframe they were found on.
    head_shoulders: Dict[str, List[HeadShouldersPattern]] = field(default_factory=dict)
    ema: Optional[EMAState] = None
    daily_structure: Optional[StructureResult] = None


def _has_pattern(patterns: List[PatternMatch], names: tuple, bias: Trend) -> bool:
    """Any at-AOI pattern from ``names`` agreeing with the bias."""
    return any(
        p.at_aoi and p.bias is bias and p.name in names for p in patterns
    )


def _hs_matching(
    inputs: ConfluenceInputs, timeframes: Optional[tuple] = None
) -> List[HeadShouldersPattern]:
    """Head & Shoulders patterns that agree with the bias and have broken."""
    out: List[HeadShouldersPattern] = []
    for tf, patterns in inputs.head_shoulders.items():
        if timeframes and tf not in timeframes:
            continue
        for pattern in patterns:
            if pattern.is_valid_signal and pattern.bias is inputs.bias:
                out.append(pattern)
    return out


def evaluate(inputs: ConfluenceInputs) -> ConfluenceResult:
    """Score a setup.

    Args:
        inputs: gathered evidence for one pair.

    Returns:
        A :class:`ConfluenceResult`. When ``core_complete`` is false the score
        stays at 0 and ``missing_core`` names what is absent.
    """
    result = ConfluenceResult(max_score=len(config.EXPANDED_CHECKLIST))
    bias = inputs.bias

    at_aoi_zone = None
    if inputs.aoi_scan:
        for zone in inputs.aoi_scan.zones:
            if zone.contains(inputs.current_price):
                at_aoi_zone = zone
                break

    trigger_armed = bool(inputs.trigger and inputs.trigger.is_armed)
    hs_valid = _hs_matching(inputs)
    hs_retested = [p for p in hs_valid if p.neckline_retested]
    candle_pattern = any(p.at_aoi and p.bias is bias for p in inputs.patterns)

    # ---- Layer 1: the mandatory core 4 -----------------------------------
    result.core_pillars = {
        "trend_confirmed": bool(inputs.sync and inputs.sync.in_sync),
        "aoi_valid": bool(inputs.aoi_scan and inputs.aoi_scan.has_valid_aoi),
        "entry_trigger_confirmed": trigger_armed,
        "pattern_confirmed": candle_pattern or bool(hs_valid),
    }
    result.missing_core = [k for k, v in result.core_pillars.items() if not v]
    result.core_complete = not result.missing_core

    if result.core_pillars["trend_confirmed"] and inputs.sync:
        result.reasons.append(f"Trend: {inputs.sync.explanation}")
    if result.core_pillars["aoi_valid"] and inputs.aoi_scan:
        result.reasons.append(f"AOI: {inputs.aoi_scan.message}")
    if trigger_armed and inputs.trigger:
        result.reasons.append(
            f"Trigger: break & retest armed at {inputs.trigger.level_label} "
            f"({inputs.trigger.level:g})."
        )

    if not result.core_complete:
        result.reasons.append(
            "Core 4 incomplete - no score, no trade. Missing: "
            + ", ".join(result.missing_core)
        )
        return result

    # ---- Layer 2: the expanded checklist ---------------------------------
    result.expanded = {
        "directional_bias": bias is not Trend.UNDETERMINED,
        "at_valid_aoi": at_aoi_zone is not None,
        "star_pattern": _has_pattern(
            inputs.patterns, ("Morning Star", "Evening Star"), bias
        ),
        "head_and_shoulders": bool(hs_valid),
        "ema_alignment": bool(inputs.ema and ema_confluence(inputs.ema, bias)),
        "break_and_retest": trigger_armed,
        "daily_trend_confirmation": bool(
            inputs.daily_structure and inputs.daily_structure.trend is bias
        ),
        "engulfing": _has_pattern(
            inputs.patterns, ("Bullish Engulfing", "Bearish Engulfing"), bias
        ),
        "h4_head_and_shoulders": bool(_hs_matching(inputs, ("4H",))),
        "hs_neckline_break_retest": bool(hs_retested),
    }

    result.score = sum(1 for v in result.expanded.values() if v)
    result.low_risk_high_reward = (
        result.score >= config.LOW_RISK_HIGH_REWARD_THRESHOLD
    )

    confirmed = [k.replace("_", " ") for k, v in result.expanded.items() if v]
    result.reasons.append(
        f"Expanded checklist {result.score}/{result.max_score}: "
        + ", ".join(confirmed)
    )
    if result.low_risk_high_reward:
        result.reasons.append(
            f"Low Risk / High Reward - score is at or above the "
            f"{config.LOW_RISK_HIGH_REWARD_THRESHOLD} threshold."
        )
    else:
        result.reasons.append(
            f"Below the Low Risk / High Reward threshold of "
            f"{config.LOW_RISK_HIGH_REWARD_THRESHOLD}."
        )

    return result


def guardrail_message(result: ConfluenceResult) -> Optional[str]:
    """The discipline message to show when a setup is not eligible.

    Returns ``None`` when the setup passed - the UI shows the plan instead.
    """
    if result.core_complete:
        return None
    if "aoi_valid" in result.missing_core:
        return config.GUARDRAIL_MESSAGES["no_aoi"]
    if "trend_confirmed" in result.missing_core:
        return config.GUARDRAIL_MESSAGES["no_sync"]
    if "entry_trigger_confirmed" in result.missing_core:
        return config.GUARDRAIL_MESSAGES["no_trigger"]
    return config.GUARDRAIL_MESSAGES["no_setup"]
