"""Integration tests for Paper Trading Service (SRS TC-2, TC-3)."""

from decimal import Decimal
import pytest
from app.core.errors import InsufficientMarginError
from app.schemas.trading import CreateOrderRequest, OrderSide
from app.services.market_service import market_service
from app.services.trading_service import TradingService


def test_paper_trading_lifecycle():
    ts = TradingService(initial_balance=Decimal("10000.00"))
    acc = ts.get_account()
    assert acc.balance == 10000.0
    assert acc.free_margin == 10000.0

    # Place long 0.1 lot EUR/USD order
    req = CreateOrderRequest(
        symbol="EUR_USD",
        side=OrderSide.BUY,
        lot_size=0.1,
        leverage=100,
        stop_loss=1.0500,
        take_profit=1.1200,
    )
    pos = ts.create_order(req)
    assert pos.id is not None
    assert pos.symbol == "EUR_USD"
    assert pos.units == 10000.0
    assert pos.margin_used > 0.0

    # Close position
    trade = ts.close_position(pos.id, reason="manual")
    assert trade.id == pos.id
    assert trade.close_reason == "manual"
    assert len(ts.closed_trades) == 1


def test_tc2_insufficient_margin_rejection():
    """SRS TC-2: Attempting to open position exceeding free margin must fail."""
    ts = TradingService(initial_balance=Decimal("500.00"))
    # 1.0 lot at 1:1 leverage requires > $100,000 margin
    req = CreateOrderRequest(
        symbol="EUR_USD",
        side=OrderSide.BUY,
        lot_size=1.0,
        leverage=1,
    )
    with pytest.raises(InsufficientMarginError) as exc_info:
        ts.create_order(req)
    assert "Insufficient Free Margin" in str(exc_info.value)


def test_tc3_auto_liquidation_trigger():
    """SRS TC-3: Margin level < 50% must trigger auto-liquidation of open positions."""
    ts = TradingService(initial_balance=Decimal("1000.00"))
    # Open long position with 1:100 leverage
    req = CreateOrderRequest(
        symbol="EUR_USD",
        side=OrderSide.BUY,
        lot_size=0.8,
        leverage=100,
    )
    pos = ts.create_order(req)
    assert len(ts.positions) == 1

    # Simulate market crash: EUR/USD drops by 120 pips -> loss of ~$960, leaving equity < $40 (Margin level < 5%)
    orig_bid = market_service.prices["EUR_USD"]["bid"]
    orig_ask = market_service.prices["EUR_USD"]["ask"]
    try:
        market_service.prices["EUR_USD"]["bid"] = orig_bid - Decimal("0.0120")
        market_service.prices["EUR_USD"]["ask"] = orig_ask - Decimal("0.0120")

        ts.update_positions_on_tick()

        # Position must have been auto-liquidated
        assert len(ts.positions) == 0
        assert len(ts.closed_trades) == 1
        assert ts.closed_trades[0].close_reason == "liquidation"
    finally:
        market_service.prices["EUR_USD"]["bid"] = orig_bid
        market_service.prices["EUR_USD"]["ask"] = orig_ask
