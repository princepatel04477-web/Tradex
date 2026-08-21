"""Pure Forex P&L arithmetic using Python Decimal (DI-5 compliance).

Formulas:
- Long P&L = (Current Bid - Entry Price) / Pip Size * Pip Value
- Short P&L = (Entry Price - Current Ask) / Pip Size * Pip Value
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple, Optional
from app.domain.pips import price_diff_to_pips, calculate_pip_value, get_pip_size


def calculate_position_pnl(
    symbol: str,
    direction: str,
    lot_size: Decimal,
    entry_price: Decimal,
    current_bid: Decimal,
    current_ask: Decimal,
    account_currency: str = "USD",
    quote_to_account_rate: Optional[Decimal] = None,
) -> Tuple[Decimal, Decimal]:
    """
    Calculate (pnl_usd, pnl_pips) for an open or closing position.
    
    Long trades exit at current_bid.
    Short trades exit at current_ask.
    """
    dir_lower = direction.lower().strip()
    if dir_lower in ("long", "buy"):
        exit_price = current_bid
        price_diff = exit_price - entry_price
    elif dir_lower in ("short", "sell"):
        exit_price = current_ask
        price_diff = entry_price - exit_price
    else:
        raise ValueError(f"Invalid position direction: {direction}")

    pnl_pips = price_diff_to_pips(price_diff, symbol)
    pip_val = calculate_pip_value(
        symbol=symbol,
        lot_size=lot_size,
        current_price=exit_price,
        account_currency=account_currency,
        quote_to_account_rate=quote_to_account_rate,
    )
    pnl_usd = (pnl_pips * pip_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return pnl_usd, pnl_pips
