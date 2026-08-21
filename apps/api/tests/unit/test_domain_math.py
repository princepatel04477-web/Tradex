"""Unit tests for pure Forex domain math (SRS TC-1, TC-9, DI-5)."""

from decimal import Decimal
import pytest
from app.domain.pips import (
    calculate_pip_value,
    get_pip_decimal_places,
    get_pip_size,
    normalize_symbol,
    price_diff_to_pips,
    split_symbol,
)
from app.domain.margin import (
    PositionMarginItem,
    calculate_account_equity,
    calculate_margin_metrics,
    calculate_required_margin,
)
from app.domain.pnl import calculate_position_pnl


def test_symbol_normalization():
    assert normalize_symbol("eur/usd") == "EUR_USD"
    assert normalize_symbol("USD_JPY") == "USD_JPY"
    assert normalize_symbol("gbpjpy") == "GBP_JPY"
    assert split_symbol("EUR_USD") == ("EUR", "USD")
    assert split_symbol("USD_JPY") == ("USD", "JPY")


def test_pip_size_and_decimals():
    # Standard pairs: 4 decimal places, pip size = 0.0001
    assert get_pip_size("EUR_USD") == Decimal("0.0001")
    assert get_pip_decimal_places("EUR_USD") == 4

    # JPY pairs: 2 decimal places, pip size = 0.01
    assert get_pip_size("USD_JPY") == Decimal("0.01")
    assert get_pip_decimal_places("USD_JPY") == 2
    assert get_pip_size("GBP_JPY") == Decimal("0.01")
    assert get_pip_decimal_places("GBP_JPY") == 2


def test_pip_value_tc1_worked_examples():
    """
    SRS TC-1: Pip value verification against worked examples.
    1) EUR/USD, 1.0 lot, USD account -> 100,000 * 0.0001 = $10.00 / pip
    2) USD/JPY, 0.1 lot, USD account, rate 154.50 -> 10,000 * 0.01 = 100 JPY / 154.50 = $0.6472 / pip
    """
    # 1. EUR/USD (1.0 standard lot)
    pip_val_eurusd = calculate_pip_value(
        symbol="EUR_USD",
        lot_size=Decimal("1.0"),
        current_price=Decimal("1.0850"),
        account_currency="USD",
    )
    assert pip_val_eurusd == Decimal("10.0000")

    # 2. USD/JPY (0.1 mini lot at 154.50)
    pip_val_usdjpy = calculate_pip_value(
        symbol="USD_JPY",
        lot_size=Decimal("0.1"),
        current_price=Decimal("154.50"),
        account_currency="USD",
    )
    assert pip_val_usdjpy == Decimal("0.6472")

    # 3. GBP/USD (0.01 micro lot)
    pip_val_gbpusd = calculate_pip_value(
        symbol="GBP_USD",
        lot_size=Decimal("0.01"),
        current_price=Decimal("1.2720"),
        account_currency="USD",
    )
    assert pip_val_gbpusd == Decimal("0.1000")


def test_required_margin_calculations():
    # 1.0 lot EUR/USD at 1.0850 with 1:100 leverage -> (100,000 * 1.0850) / 100 = $1,085.00
    units = Decimal("100000")
    margin_100x = calculate_required_margin(
        units=units,
        entry_price=Decimal("1.0850"),
        leverage=Decimal("100"),
    )
    assert margin_100x == Decimal("1085.00")

    # With 1:30 leverage -> (100,000 * 1.0850) / 30 = $3,616.67
    margin_30x = calculate_required_margin(
        units=units,
        entry_price=Decimal("1.0850"),
        leverage=Decimal("30"),
    )
    assert margin_30x == Decimal("3616.67")


def test_margin_metrics_and_liquidation_trigger():
    balance = Decimal("10000.00")
    positions = [
        PositionMarginItem(
            units=Decimal("100000"),
            entry_price=Decimal("1.0850"),
            leverage=Decimal("100"),
            unrealized_pnl=Decimal("-500.00"),
        )
    ]

    metrics = calculate_margin_metrics(balance, positions)
    assert metrics["equity"] == Decimal("9500.00")
    assert metrics["used_margin"] == Decimal("1085.00")
    assert metrics["free_margin"] == Decimal("8415.00")
    # Margin level = (9500 / 1085) * 100 = 875.6%
    assert metrics["margin_level_pct"] == Decimal("875.6")
    assert not metrics["is_margin_call"]
    assert not metrics["is_liquidation_required"]

    # Test extreme loss triggering liquidation (margin level < 50%)
    positions_loss = [
        PositionMarginItem(
            units=Decimal("100000"),
            entry_price=Decimal("1.0850"),
            leverage=Decimal("100"),
            unrealized_pnl=Decimal("-9600.00"),  # equity = 400 < 542.5 (50% of 1085)
        )
    ]
    metrics_loss = calculate_margin_metrics(balance, positions_loss)
    assert metrics_loss["equity"] == Decimal("400.00")
    assert metrics_loss["margin_level_pct"] == Decimal("36.9")
    assert metrics_loss["is_margin_call"] is True
    assert metrics_loss["is_liquidation_required"] is True


def test_position_pnl_long_and_short():
    # Long 1.0 lot EUR/USD bought at 1.0850, current bid 1.0870 (+20 pips -> +$200)
    pnl_usd, pnl_pips = calculate_position_pnl(
        symbol="EUR_USD",
        direction="long",
        lot_size=Decimal("1.0"),
        entry_price=Decimal("1.0850"),
        current_bid=Decimal("1.0870"),
        current_ask=Decimal("1.0872"),
    )
    assert pnl_pips == Decimal("20.0")
    assert pnl_usd == Decimal("200.00")

    # Short 1.0 lot EUR/USD sold at 1.0850, current ask 1.0830 (+20 pips -> +$200)
    pnl_usd_s, pnl_pips_s = calculate_position_pnl(
        symbol="EUR_USD",
        direction="short",
        lot_size=Decimal("1.0"),
        entry_price=Decimal("1.0850"),
        current_bid=Decimal("1.0828"),
        current_ask=Decimal("1.0830"),
    )
    assert pnl_pips_s == Decimal("20.0")
    assert pnl_usd_s == Decimal("200.00")
