import pytest
from app.schemas.trading import OrderRequest
from app.services.trading_service import TradingService

def test_insufficient_margin_rejection():
    # TC-2: Order exceeding free margin must be rejected with explicit message
    service = TradingService(initial_balance=100.0)  # Very small balance
    order = OrderRequest(
        symbol="EUR_USD",
        direction="buy",
        lot_size=10.0,  # Huge position (1,000,000 units)
        leverage=1
    )
    with pytest.raises(ValueError) as excinfo:
        service.place_order(order)
    assert "Insufficient Free Margin" in str(excinfo.value)

def test_margin_call_and_liquidation():
    # TC-3: Auto-liquidation when margin level falls below 50%
    service = TradingService(initial_balance=1000.0)
    order = OrderRequest(
        symbol="EUR_USD",
        direction="buy",
        lot_size=0.2,  # 20,000 units, margin ~ $723 at 1:30 leverage
        leverage=30
    )
    pos = service.place_order(order)
    assert pos.status == "open"

    # Simulate catastrophic price plunge (15% drop)
    pos.current_price = pos.entry_price * 0.85
    pnl, pnl_pips = service._calc_position_pnl(pos, pos.current_price)
    pos.unrealized_pnl = pnl
    pos.unrealized_pnl_pips = pnl_pips
    
    metrics = service.update_positions_and_check_liquidation()
    # Positions should have been auto-liquidated
    assert len(service.positions) == 0
    assert len(service.closed_trades) == 1
    assert service.closed_trades[0].close_reason == "liquidation"
