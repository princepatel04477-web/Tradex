from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OrderRequest(BaseModel):
    symbol: str
    order_type: str = "market"  # market, limit, stop
    direction: str  # buy, sell
    lot_size: float = Field(gt=0, description="1.0 standard, 0.1 mini, 0.01 micro")
    leverage: int = Field(default=30, description="1, 10, 30, 50, 100")
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop_pips: Optional[float] = None
    limit_price: Optional[float] = None

class Position(BaseModel):
    id: str
    symbol: str
    direction: str  # long, short
    lot_size: float
    units: float
    leverage: int
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop_pips: Optional[float] = None
    unrealized_pnl: float
    unrealized_pnl_pips: float
    required_margin: float
    opened_at: datetime
    status: str = "open"  # open, closed, liquidated

class AccountMetrics(BaseModel):
    balance: float
    equity: float
    used_margin: float
    free_margin: float
    margin_level_pct: float
    floating_pnl: float
    open_positions_count: int

class ClosedTrade(BaseModel):
    id: str
    symbol: str
    direction: str
    lot_size: float
    units: float
    entry_price: float
    exit_price: float
    realized_pnl: float
    realized_pnl_pips: float
    opened_at: datetime
    closed_at: datetime
    close_reason: str  # manual, stop_loss, take_profit, liquidation
    notes: Optional[str] = None
    tags: List[str] = []

class TradeJournalUpdate(BaseModel):
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

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
    max_drawdown_amount: float
    max_drawdown_pct: float
    equity_curve: List[dict]
    pair_performance: List[dict]
    session_performance: List[dict]
