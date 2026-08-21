"""Pure Forex pip arithmetic using Python Decimal (DI-5 compliance).

Rules:
- Standard pairs (4 decimal places): 1 pip = Decimal("0.0001")
- JPY pairs (2 decimal places): 1 pip = Decimal("0.01")
- 1 standard lot = 100,000 units
- 1 mini lot = 10,000 units
- 1 micro lot = 1,000 units
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple, Optional

STANDARD_PIP_SIZE = Decimal("0.0001")
JPY_PIP_SIZE = Decimal("0.01")
UNITS_PER_STANDARD_LOT = Decimal("100000")


def normalize_symbol(symbol: str) -> str:
    """Normalize 'eur/usd', 'EUR_USD', 'EURUSD' -> 'EUR_USD'."""
    s = symbol.strip().upper().replace("/", "_").replace("-", "_")
    if "_" not in s and len(s) == 6:
        s = f"{s[:3]}_{s[3:]}"
    return s


def split_symbol(symbol: str) -> Tuple[str, str]:
    """Return (base_currency, quote_currency) from normalized symbol."""
    norm = normalize_symbol(symbol)
    parts = norm.split("_")
    if len(parts) != 2 or len(parts[0]) != 3 or len(parts[1]) != 3:
        raise ValueError(f"Invalid currency pair symbol: {symbol}")
    return parts[0], parts[1]


def get_pip_size(symbol: str) -> Decimal:
    """Return Decimal pip size (0.01 for JPY pairs, 0.0001 otherwise)."""
    _, quote = split_symbol(symbol)
    return JPY_PIP_SIZE if quote == "JPY" else STANDARD_PIP_SIZE


def get_pip_decimal_places(symbol: str) -> int:
    """Return pip decimal places (2 for JPY pairs, 4 otherwise)."""
    _, quote = split_symbol(symbol)
    return 2 if quote == "JPY" else 4


def price_diff_to_pips(price_delta: Decimal, symbol: str) -> Decimal:
    """Convert raw price delta into pips with 1 decimal place precision."""
    pip_sz = get_pip_size(symbol)
    if pip_sz == 0:
        return Decimal("0.0")
    pips = price_delta / pip_sz
    return pips.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def pips_to_price_diff(pips: Decimal, symbol: str) -> Decimal:
    """Convert pips into raw price delta."""
    pip_sz = get_pip_size(symbol)
    return pips * pip_sz


def calculate_pip_value(
    symbol: str,
    lot_size: Decimal,
    current_price: Decimal,
    account_currency: str = "USD",
    quote_to_account_rate: Optional[Decimal] = None,
) -> Decimal:
    """
    Calculate the monetary value of 1 pip in account currency for the given lot size.

    Worked examples (SRS TC-1):
    1) EUR/USD, 1.0 lot, rate 1.0850, USD account:
       units = 100,000 -> 100,000 * 0.0001 = $10.00 / pip
    2) USD/JPY, 0.1 lot, rate 154.50, USD account:
       units = 10,000 -> 10,000 * 0.01 = 100 JPY / 154.50 = $0.6472 / pip
    """
    base, quote = split_symbol(symbol)
    units = lot_size * UNITS_PER_STANDARD_LOT
    pip_sz = get_pip_size(symbol)
    value_in_quote = units * pip_sz

    if quote == account_currency:
        return value_in_quote.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    if base == account_currency:
        if current_price <= Decimal("0"):
            raise ValueError("current_price must be positive for base currency conversion")
        val = value_in_quote / current_price
        return val.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    # Cross currency pair where neither is account currency
    if quote_to_account_rate is None:
        raise ValueError(f"Cross pair {symbol} requires quote_to_account_rate ({quote}->{account_currency})")
    val = value_in_quote * quote_to_account_rate
    return val.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
