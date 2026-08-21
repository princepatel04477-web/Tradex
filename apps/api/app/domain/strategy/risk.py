"""Module 11 - Risk management calculator.

Account-size -> risk-% comes from ``config.RISK_TIERS`` and nowhere else, so
the whole table is a one-file edit. Position size is derived from the stop
distance and the pair's real pip value (JPY pairs included).

Hard rules from the notes:

* minimum acceptable reward:risk is **1:2** - a plan below it is never valid;
* **1:4** is the target the tool aims for and highlights;
* **1 trade a week**;
* **Set & Forget** - once placed, editing entry/stop/target is discouraged.

NOTE: the transcribed risk percentages (35-100% of account per trade) are far
above any conventional risk standard. ``config.RISK_TABLE_NOTE`` carries that
caveat through to the API and UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Sequence

from . import config
from .config import RiskTier
from .pips import pip_value, round_price, to_pips
from .types import Direction, TradePlan


def risk_tier_for(account_size: float) -> RiskTier:
    """The tier that applies to an account balance.

    Uses the highest tier whose threshold the account has reached. Balances
    below the smallest tier fall back to it.

    Args:
        account_size: account balance in the account currency.

    Returns:
        The matching :class:`RiskTier`.
    """
    if not config.RISK_TIERS:
        raise ValueError("RISK_TIERS is empty - check config.py")

    tiers = sorted(config.RISK_TIERS, key=lambda t: t.account_size)
    chosen = tiers[0]
    for tier in tiers:
        if account_size >= tier.account_size:
            chosen = tier
        else:
            break
    return chosen


def risk_table() -> List[dict]:
    """The full table, ready for display, with the unconfirmed rows flagged."""
    return [
        {
            "account_size": t.account_size,
            "risk_pct_min": t.risk_pct_min,
            "risk_pct_max": t.risk_pct_max,
            "risk_pct_used": t.risk_pct,
            "unconfirmed": t.unconfirmed,
            "note": t.note,
        }
        for t in sorted(config.RISK_TIERS, key=lambda t: t.account_size)
    ]


def suggest_take_profit(
    entry: float, stop_loss: float, reward_risk: Optional[float] = None
) -> float:
    """Project a take-profit at a given reward:risk from entry and stop.

    Args:
        entry: entry price.
        stop_loss: stop price. Its side of the entry decides direction.
        reward_risk: defaults to ``config.TARGET_REWARD_RISK`` (1:4).

    Returns:
        The take-profit price.
    """
    rr = reward_risk or config.TARGET_REWARD_RISK
    distance = abs(entry - stop_loss)
    if distance <= 0:
        raise ValueError("Stop loss must differ from entry")
    return entry + distance * rr if stop_loss < entry else entry - distance * rr


def build_trade_plan(
    symbol: str,
    direction: Direction,
    entry: float,
    stop_loss: float,
    account_size: float,
    take_profit: Optional[float] = None,
    risk_pct_override: Optional[float] = None,
    quote_to_account_rate: Optional[float] = None,
) -> TradePlan:
    """Size a trade and validate its reward:risk.

    Args:
        symbol: pair, e.g. ``EUR_USD``.
        direction: BUY or SELL.
        entry: intended entry price.
        stop_loss: stop price - must sit on the losing side of the entry.
        account_size: account balance.
        take_profit: optional. Defaults to the 1:4 target projection.
        risk_pct_override: bypass the table with an explicit risk percentage.
        quote_to_account_rate: needed only for crosses (neither leg is USD).

    Returns:
        A :class:`TradePlan`. Check ``meets_min_rr`` before showing it -
        anything below 1:2 must not be rendered as a plan.

    Raises:
        ValueError: on a zero stop distance or a stop on the wrong side.
    """
    if account_size <= 0:
        raise ValueError("Account size must be positive")

    stop_distance = abs(entry - stop_loss)
    if stop_distance <= 0:
        raise ValueError("Stop loss must differ from entry")

    if direction is Direction.BUY and stop_loss >= entry:
        raise ValueError("A buy's stop loss must sit below the entry")
    if direction is Direction.SELL and stop_loss <= entry:
        raise ValueError("A sell's stop loss must sit above the entry")

    if take_profit is None:
        take_profit = suggest_take_profit(entry, stop_loss, config.TARGET_REWARD_RISK)

    target_distance = abs(take_profit - entry)
    reward_risk = target_distance / stop_distance

    tier = risk_tier_for(account_size)
    risk_pct = risk_pct_override if risk_pct_override is not None else tier.risk_pct
    risk_amount = account_size * (risk_pct / 100.0)

    pip_val_per_lot = pip_value(
        symbol,
        lot_size=1.0,
        current_price=entry,
        quote_to_account_rate=quote_to_account_rate,
    )
    stop_pips = to_pips(stop_distance, symbol)
    target_pips = to_pips(target_distance, symbol)

    lots = 0.0
    if stop_pips > 0 and pip_val_per_lot > 0:
        lots = risk_amount / (stop_pips * pip_val_per_lot)

    warnings: List[str] = []
    # Compare with a tolerance: 1:2 computed in binary floating point lands a
    # hair under 2.0, and a plan that is exactly at the floor must pass it.
    epsilon = 1e-9
    meets_min = reward_risk >= config.MIN_REWARD_RISK - epsilon
    meets_target = reward_risk >= config.TARGET_REWARD_RISK - epsilon

    if not meets_min:
        warnings.append(
            f"Reward:risk is 1:{reward_risk:.2f} - below the 1:"
            f"{config.MIN_REWARD_RISK:g} minimum. This plan is not valid; move "
            f"the target to at least "
            f"{round_price(suggest_take_profit(entry, stop_loss, config.MIN_REWARD_RISK), symbol)} "
            f"or skip the trade."
        )
    elif not meets_target:
        warnings.append(
            f"Reward:risk is 1:{reward_risk:.2f}. Acceptable, but the target "
            f"ratio is 1:{config.TARGET_REWARD_RISK:g} - "
            f"{round_price(suggest_take_profit(entry, stop_loss, config.TARGET_REWARD_RISK), symbol)}."
        )

    if tier.unconfirmed:
        warnings.append(
            f"Risk tier ${tier.account_size:,.0f} is UNCONFIRMED. {tier.note} "
            f"{config.RISK_TABLE_NOTE}"
        )
    if risk_pct >= 35.0:
        warnings.append(
            f"Risking {risk_pct:.0f}% of the account on one position. A short "
            f"losing run at this size ends the account - confirm this is really "
            f"the intended table."
        )

    if stop_pips < config.MIN_STOP_DISTANCE_PIPS:
        warnings.append(
            f"Stop is only {stop_pips:.1f} pips from entry - inside normal "
            f"spread-and-noise range, and it inflates the position size. "
            f"Minimum is {config.MIN_STOP_DISTANCE_PIPS:g} pips."
        )

    notional = lots * 100_000 * (1.0 if pip_val_per_lot else 0.0)
    if account_size > 0 and notional / account_size > config.NOTIONAL_LEVERAGE_WARNING:
        warnings.append(
            f"Position notional is {notional / account_size:.0f}x the account "
            f"balance. No retail broker will allow this - the risk table, the "
            f"stop distance, or both need revisiting."
        )

    return TradePlan(
        symbol=symbol,
        direction=direction,
        entry=round_price(entry, symbol),
        stop_loss=round_price(stop_loss, symbol),
        take_profit=round_price(take_profit, symbol),
        stop_distance_pips=round(stop_pips, 1),
        target_distance_pips=round(target_pips, 1),
        reward_risk=round(reward_risk, 2),
        account_size=account_size,
        risk_pct=risk_pct,
        risk_amount=round(risk_amount, 2),
        pip_value_per_lot=round(pip_val_per_lot, 4),
        position_size_lots=round(lots, 2),
        position_size_units=round(lots * 100_000, 0),
        meets_min_rr=meets_min,
        meets_target_rr=meets_target,
        warnings=warnings,
        risk_tier_unconfirmed=tier.unconfirmed,
    )


# ---------------------------------------------------------------------------
# "1 trade a week" pace tracker
# ---------------------------------------------------------------------------


@dataclass
class WeeklyPace:
    """How many trades have been taken in the current week."""

    week_start: datetime
    week_end: datetime
    trades_this_week: int
    limit: int
    remaining: int
    at_limit: bool
    message: str = ""
    trade_times: List[datetime] = field(default_factory=list)


def week_bounds(now: Optional[datetime] = None) -> tuple:
    """(Monday 00:00, next Monday 00:00) in UTC for the week containing ``now``."""
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    start = now.astimezone(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=now.astimezone(timezone.utc).weekday())
    return start, start + timedelta(days=7)


def weekly_pace(
    trade_times: Sequence[datetime], now: Optional[datetime] = None
) -> WeeklyPace:
    """Track the "1 trade a week" rule.

    Args:
        trade_times: when each trade was placed.
        now: evaluation instant; defaults to now (UTC).

    Returns:
        A :class:`WeeklyPace`. At the limit the message discourages a second
        trade - it is friction, not a block.
    """
    start, end = week_bounds(now)
    in_week = [
        t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t.astimezone(timezone.utc)
        for t in trade_times
    ]
    in_week = [t for t in in_week if start <= t < end]

    count = len(in_week)
    limit = config.MAX_TRADES_PER_WEEK
    remaining = max(0, limit - count)
    at_limit = count >= limit

    if at_limit:
        message = config.GUARDRAIL_MESSAGES["weekly_pace"]
    elif count == 0:
        message = f"No trades yet this week. {limit} available."
    else:
        message = f"{count} trade(s) taken this week, {remaining} remaining."

    return WeeklyPace(
        week_start=start,
        week_end=end,
        trades_this_week=count,
        limit=limit,
        remaining=remaining,
        at_limit=at_limit,
        message=message,
        trade_times=sorted(in_week),
    )


def set_and_forget_notice(is_placed: bool) -> Optional[str]:
    """Friction message shown when editing a placed trade's levels."""
    if not (is_placed and config.SET_AND_FORGET_LOCK):
        return None
    return (
        "Set & Forget: this trade is already placed. Editing the entry, stop or "
        "target now is exactly the habit the rule exists to prevent. Change it "
        "only if the original plan was mis-entered."
    )
