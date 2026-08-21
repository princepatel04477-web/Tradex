"""Module 4 - Top-down trend dashboard and the timeframe sync gate.

Weekly / Daily / 4H are the **trend + AOI** layer. 2H / 1H / 30M / 15M are the
**entry-signal** layer and are deliberately kept in a separate panel so a 15M
wiggle never colours the bias.

The sync gate decides whether a pair is worth looking at at all. Two readings
of the notes are implemented; ``config.REQUIRED_SYNC_TIMEFRAMES`` selects one.
See FLAGGED QUESTION #1 in ``config.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import config
from .structure import analyse_structure
from .types import Candle, StructureResult, Trend


@dataclass
class SyncVerdict:
    """Whether the trend timeframes agree well enough to trade the pair."""

    in_sync: bool
    rule: str
    direction: Trend
    agreeing_timeframes: List[str] = field(default_factory=list)
    explanation: str = ""
    rule_is_unconfirmed: bool = True
    rule_note: str = ""


@dataclass
class TopDownView:
    """The full top-down read for one pair."""

    symbol: str
    #: Weekly / Daily / 4H - trend and AOI.
    trend_layer: Dict[str, StructureResult] = field(default_factory=dict)
    #: 2H / 1H / 30M / 15M - entry timing only.
    entry_layer: Dict[str, StructureResult] = field(default_factory=dict)
    sync: Optional[SyncVerdict] = None
    #: "Trend is your friend" banner state.
    trend_is_your_friend: bool = False
    bias: Trend = Trend.UNDETERMINED
    messages: List[str] = field(default_factory=list)


def evaluate_sync(trend_layer: Dict[str, StructureResult]) -> SyncVerdict:
    """Apply the configured sync rule to the Weekly/Daily/4H trends.

    Args:
        trend_layer: structure results keyed by timeframe (``1W``/``1D``/``4H``).

    Returns:
        A :class:`SyncVerdict`. ``direction`` is the bias to trade when
        ``in_sync`` is true, and ``Trend.UNDETERMINED`` otherwise.
    """
    rule = config.REQUIRED_SYNC_TIMEFRAMES
    weekly = trend_layer.get("1W")
    daily = trend_layer.get("1D")
    h4 = trend_layer.get("4H")

    def direction_of(res: Optional[StructureResult]) -> Trend:
        return res.trend if res else Trend.UNDETERMINED

    w, d, h = direction_of(weekly), direction_of(daily), direction_of(h4)

    if rule == "any_two_consecutive":
        # W+D or D+4H agreeing is enough (matches the notes' worked examples).
        if w is d and w is not Trend.UNDETERMINED:
            return SyncVerdict(
                True,
                rule,
                w,
                ["1W", "1D"],
                f"Weekly and Daily are both {w.value} - consecutive pair in sync.",
                config.SYNC_RULE_IS_UNCONFIRMED,
                config.SYNC_RULE_NOTE,
            )
        if d is h and d is not Trend.UNDETERMINED:
            return SyncVerdict(
                True,
                rule,
                d,
                ["1D", "4H"],
                f"Daily and 4H are both {d.value} - consecutive pair in sync.",
                config.SYNC_RULE_IS_UNCONFIRMED,
                config.SYNC_RULE_NOTE,
            )
        return SyncVerdict(
            False,
            rule,
            Trend.UNDETERMINED,
            [],
            f"No two consecutive timeframes agree (W {w.value} / D {d.value} / 4H {h.value}).",
            config.SYNC_RULE_IS_UNCONFIRMED,
            config.SYNC_RULE_NOTE,
        )

    # Default: "weekly_daily_must_agree" - 4H may diverge, it is entry timing.
    if w is d and w is not Trend.UNDETERMINED:
        agreeing = ["1W", "1D"] + (["4H"] if h is w else [])
        note = f"Weekly and Daily are both {w.value}."
        if h is not w and h is not Trend.UNDETERMINED:
            note += f" 4H is {h.value}, which is allowed - 4H is entry timing, not bias."
        return SyncVerdict(
            True,
            rule,
            w,
            agreeing,
            note,
            config.SYNC_RULE_IS_UNCONFIRMED,
            config.SYNC_RULE_NOTE,
        )

    return SyncVerdict(
        False,
        rule,
        Trend.UNDETERMINED,
        [],
        f"Weekly ({w.value}) and Daily ({d.value}) disagree - no bias to trade.",
        config.SYNC_RULE_IS_UNCONFIRMED,
        config.SYNC_RULE_NOTE,
    )


def build_top_down_view(
    symbol: str,
    candles_by_timeframe: Dict[str, List[Candle]],
) -> TopDownView:
    """Run the structure engine across every supplied timeframe and gate it.

    Args:
        symbol: e.g. ``EUR_USD``.
        candles_by_timeframe: OHLC series keyed by timeframe label.

    Returns:
        A :class:`TopDownView` with the two layers kept separate, the sync
        verdict, and the resulting bias.
    """
    view = TopDownView(symbol=symbol)

    for tf in config.TREND_TIMEFRAMES:
        candles = candles_by_timeframe.get(tf)
        if candles:
            view.trend_layer[tf] = analyse_structure(candles, tf)

    for tf in config.ENTRY_TIMEFRAMES:
        candles = candles_by_timeframe.get(tf)
        if candles:
            view.entry_layer[tf] = analyse_structure(candles, tf)

    view.sync = evaluate_sync(view.trend_layer)
    view.bias = view.sync.direction

    # "Trend is your friend" lights up only when all three trend timeframes
    # point the same way - a stricter, purely informational banner.
    directions = [r.trend for r in view.trend_layer.values()]
    view.trend_is_your_friend = (
        len(directions) == len(config.TREND_TIMEFRAMES)
        and len(set(directions)) == 1
        and directions[0] is not Trend.UNDETERMINED
    )

    if view.trend_is_your_friend:
        view.messages.append(
            f"Trend is your friend - Weekly, Daily and 4H are all {view.bias.value}."
        )
    if not view.sync.in_sync:
        view.messages.append(config.GUARDRAIL_MESSAGES["no_sync"])

    return view
