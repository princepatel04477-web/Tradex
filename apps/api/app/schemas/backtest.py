"""Backtesting request / response schemas (Month 3 roadmap — Historical Backtesting Engine)."""

from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

StrategyName = Literal["ema_crossover", "rsi_reversion", "macd_momentum"]
BacktestTimeframe = Literal["M30", "H1", "H4", "D1"]


class BacktestRequest(BaseModel):
    symbol: str = Field(default="EUR_USD", description="Currency pair, e.g. EUR_USD")
    timeframe: BacktestTimeframe = "H4"
    strategy: StrategyName = "ema_crossover"
    bars: int = Field(default=1500, ge=200, le=3000, description="Number of historical bars to test")
    initial_balance: float = Field(default=10000.0, ge=100, le=10_000_000)
    risk_per_trade_pct: float = Field(default=1.0, gt=0, le=5)
    sl_atr_mult: float = Field(default=1.5, gt=0, le=10)
    tp_atr_mult: float = Field(default=3.0, gt=0, le=20)
    fast_period: int = Field(default=9, ge=2, le=100)
    slow_period: int = Field(default=21, ge=3, le=300)
    rsi_period: int = Field(default=14, ge=2, le=50)
    rsi_lower: float = Field(default=30, ge=5, le=50)
    rsi_upper: float = Field(default=70, ge=50, le=95)
    allow_short: bool = True


class StrategyInfo(BaseModel):
    id: str
    name: str
    description: str
    parameters: List[str]


class BacktestTradeOut(BaseModel):
    trade_no: int
    direction: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    units: int
    stop_loss: float
    take_profit: float
    pnl: float
    pnl_pips: float
    r_multiple: float
    exit_reason: str
    bars_held: int


class EquityPointOut(BaseModel):
    time: str
    equity: float
    drawdown_pct: float


class BacktestMetrics(BaseModel):
    initial_balance: float
    final_balance: float
    net_profit: float
    total_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    expectancy: float
    avg_r_multiple: float
    max_drawdown_pct: float
    max_drawdown_amount: float
    sharpe_ratio: float
    exposure_pct: float
    bars_tested: int


class BacktestRunOut(BaseModel):
    run_id: str
    status: str = "completed"
    request: BacktestRequest
    period_start: str
    period_end: str
    spread_pips: float
    data_source: str
    runtime_ms: float
    metrics: BacktestMetrics
    equity_curve: List[EquityPointOut]
    trades: List[BacktestTradeOut]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None


class BacktestRunSummary(BaseModel):
    run_id: str
    symbol: str
    timeframe: str
    strategy: str
    total_trades: int
    net_profit: float
    total_return_pct: float
    win_rate_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    created_at: datetime
