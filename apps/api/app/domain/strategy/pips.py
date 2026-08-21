"""Pip arithmetic - the unit every rule in the notes is expressed in.

AOI widths, break tolerances and stop distances are all stated in pips, so
every module converts through here rather than doing its own decimal maths.
"""

from __future__ import annotations

from typing import Optional

#: A pip is 0.01 on JPY-quoted pairs and 0.0001 everywhere else.
JPY_PIP_SIZE = 0.01
STANDARD_PIP_SIZE = 0.0001

#: 1 standard lot = 100,000 units of the base currency.
UNITS_PER_STANDARD_LOT = 100_000.0


def normalise_symbol(symbol: str) -> str:
    """``eur/usd``, ``EUR_USD`` and ``EURUSD`` all become ``EUR_USD``."""
    s = symbol.strip().upper().replace("/", "_").replace("-", "_")
    if "_" not in s and len(s) == 6:
        s = f"{s[:3]}_{s[3:]}"
    return s


def split_pair(symbol: str) -> tuple[str, str]:
    """Return ``(base, quote)`` - EUR/USD -> ``("EUR", "USD")``."""
    s = normalise_symbol(symbol)
    parts = s.split("_")
    if len(parts) != 2 or not all(len(p) == 3 for p in parts):
        raise ValueError(f"Unrecognised currency pair: {symbol!r}")
    return parts[0], parts[1]


def pip_size(symbol: str) -> float:
    """Price increment of one pip for this pair."""
    _, quote = split_pair(symbol)
    return JPY_PIP_SIZE if quote == "JPY" else STANDARD_PIP_SIZE


def price_decimals(symbol: str) -> int:
    """Display precision: 3 for JPY pairs, 5 otherwise (fractional pip)."""
    _, quote = split_pair(symbol)
    return 3 if quote == "JPY" else 5


def to_pips(price_delta: float, symbol: str) -> float:
    """Convert a raw price difference into pips."""
    return price_delta / pip_size(symbol)


def from_pips(pips: float, symbol: str) -> float:
    """Convert a pip count into a raw price difference."""
    return pips * pip_size(symbol)


def pip_value(
    symbol: str,
    lot_size: float,
    current_price: float,
    account_currency: str = "USD",
    quote_to_account_rate: Optional[float] = None,
) -> float:
    """Value of one pip, in the account currency, for ``lot_size`` lots.

    Args:
        symbol: e.g. ``EUR_USD``.
        lot_size: 1.0 standard, 0.1 mini, 0.01 micro.
        current_price: current rate for the pair, used for USD-base conversion.
        account_currency: defaults to USD.
        quote_to_account_rate: rate converting the QUOTE currency into the
            account currency. Only needed for crosses where neither leg is the
            account currency (e.g. EUR/GBP on a USD account).

    Returns:
        Pip value in the account currency.

    Raises:
        ValueError: if a cross needs a conversion rate that was not supplied.
    """
    base, quote = split_pair(symbol)
    units = lot_size * UNITS_PER_STANDARD_LOT
    value_in_quote = units * pip_size(symbol)

    if quote == account_currency:
        # e.g. EUR/USD on a USD account - already in account currency.
        return value_in_quote

    if base == account_currency:
        # e.g. USD/JPY on a USD account - divide by the current rate.
        if current_price <= 0:
            raise ValueError("current_price must be positive to convert pip value")
        return value_in_quote / current_price

    if quote_to_account_rate is None:
        raise ValueError(
            f"{symbol} is a cross for a {account_currency} account; supply "
            f"quote_to_account_rate ({quote}->{account_currency})"
        )
    return value_in_quote * quote_to_account_rate


def round_price(price: float, symbol: str) -> float:
    """Round a price to the pair's display precision."""
    return round(price, price_decimals(symbol))


def round_pips(pips: float) -> float:
    """Pip counts are quoted to one decimal place."""
    return round(pips, 1)
