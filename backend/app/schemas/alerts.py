from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AlertCreate(BaseModel):
    symbol: str
    alert_type: str  # price_above, price_below, rsi_overbought, rsi_oversold, macd_crossover, bb_breakout
    threshold_value: Optional[float] = None
    timeframe: Optional[str] = "H1"
    note: Optional[str] = None
    email_notification: bool = False

class AlertItem(BaseModel):
    id: str
    symbol: str
    alert_type: str
    threshold_value: Optional[float] = None
    timeframe: Optional[str] = "H1"
    note: Optional[str] = None
    is_active: bool = True
    is_triggered: bool = False
    triggered_at: Optional[datetime] = None
    created_at: datetime
