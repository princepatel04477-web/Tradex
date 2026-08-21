"""Pure Forex margin arithmetic using Python Decimal (DI-5 compliance).

Formulas:
- Required Margin = (Units * Entry Price) / Leverage
- Account Equity = Balance + sum(Floating P&L) [Derived per ADR-0006]
- Used Margin = sum(Required Margin of open positions)
- Free Margin = max(0, Equity - Used Margin)
- Margin Level % = (Equity / Used Margin) * 100 (if Used Margin > 0 else 9999.0%)
- Margin Call Warning: Margin Level < 100%
- Auto-Liquidation: Margin Level < 50%
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, NamedTuple, Optional
from app.domain.pips import UNITS_PER_STANDARD_LOT


class PositionMarginItem(NamedTuple):
    units: Decimal
    entry_price: Decimal
    leverage: Decimal
    unrealized_pnl: Decimal


def calculate_required_margin(
    units: Decimal,
    entry_price: Decimal,
    leverage: Decimal,
    base_to_account_rate: Decimal = Decimal("1.0"),
) -> Decimal:
    """Compute required margin in account currency."""
    if leverage <= Decimal("0"):
        raise ValueError("Leverage must be positive")
    notional = units * entry_price * base_to_account_rate
    req = notional / leverage
    return req.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_account_equity(balance: Decimal, open_positions_pnl: Decimal) -> Decimal:
    """Account equity = balance + sum(floating pnl). Never stored directly (ADR-0006)."""
    return (balance + open_positions_pnl).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_margin_metrics(
    balance: Decimal,
    positions: List[PositionMarginItem],
) -> dict:
    """
    Compute full margin metrics snapshot.
    Returns: {
        'balance': Decimal,
        'equity': Decimal,
        'used_margin': Decimal,
        'free_margin': Decimal,
        'margin_level_pct': Decimal,
        'is_margin_call': bool,
        'is_liquidation_required': bool
    }
    """
    total_floating_pnl = sum((p.unrealized_pnl for p in positions), Decimal("0.00"))
    equity = calculate_account_equity(balance, total_floating_pnl)
    
    used_margin = sum((
        calculate_required_margin(p.units, p.entry_price, p.leverage)
        for p in positions
    ), Decimal("0.00"))

    free_margin = max(Decimal("0.00"), equity - used_margin)

    if used_margin > Decimal("0"):
        margin_level_pct = (equity / used_margin * Decimal("100.0")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    else:
        margin_level_pct = Decimal("9999.0")

    is_margin_call = (used_margin > Decimal("0")) and (margin_level_pct < Decimal("100.0"))
    is_liquidation = (used_margin > Decimal("0")) and (margin_level_pct < Decimal("50.0"))

    return {
        "balance": balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "equity": equity,
        "used_margin": used_margin,
        "free_margin": free_margin,
        "margin_level_pct": margin_level_pct,
        "is_margin_call": is_margin_call,
        "is_liquidation_required": is_liquidation,
    }
