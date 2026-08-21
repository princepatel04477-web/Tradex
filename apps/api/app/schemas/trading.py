"""Trading schemas for orders, positions, accounts, and performance analytics."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"


class CreateOrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    lot_size: float = Field(gt=0, description="1.0 standard, 0.1 mini, 0.01 micro")
    leverage: int = Field(default=30, description="1, 10, 30, 50, 100")
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop_pips: Optional[float] = None


class Position(BaseModel):
    id: str
    symbol: str
    side: OrderSide
    lot_size: float
    units: float
    leverage: int
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop_pips: Optional[float] = None
    floating_pnl: float = 0.0
    floating_pnl_pips: float = 0.0
    margin_used: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClosedTrade(BaseModel):
    id: str
    symbol: str
    side: OrderSide
    lot_size: float
    units: float
    leverage: int
    entry_price: float
    exit_price: float
    realized_pnl: float
    realized_pnl_pips: float
    close_reason: str
    opened_at: datetime
    closed_at: datetime
    duration_minutes: int = 1
    notes: Optional[str] = None
    tags: List[str] = []


class PaperAccount(BaseModel):
    balance: float
    equity: float
    used_margin: float
    free_margin: float
    margin_level_pct: float
    floating_pnl: float
    currency: str = "USD"
    open_positions_count: int = 0
    closed_trades_count: int = 0


class DrawdownInfo(BaseModel):
    max_drawdown_amount: float = 0.0
    max_drawdown_pct: float = 0.0
    current_drawdown_amount: float = 0.0
    current_drawdown_pct: float = 0.0
    peak_balance: float = 10000.0


class PairPerformance(BaseModel):
    symbol: str
    trades: int
    pnl: float
    win_rate: float


class SessionPerformance(BaseModel):
    session: str
    trades: int
    pnl: float


class PerformanceAnalytics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    total_realized_pnl: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    avg_risk_reward_ratio: float
    drawdown: DrawdownInfo
    pair_performance: List[PairPerformance] = []
    session_performance: List[SessionPerformance] = []


class TradingSummary(BaseModel):
    account: PaperAccount
    positions: List[Position]
    recent_trades: List[ClosedTrade]
