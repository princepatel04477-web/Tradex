"""Alerts and notification schemas."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"


class AlertCreate(BaseModel):
    symbol: str
    alert_type: str  # price_above, price_below, rsi_overbought, rsi_oversold, macd_crossover, bb_squeeze
    threshold_value: float
    timeframe: Optional[str] = "H1"
    note: Optional[str] = None
    email_notification: bool = False


class Alert(BaseModel):
    id: str
    user_id: str = "user-demo-001"
    symbol: str
    alert_type: str
    threshold_value: float
    timeframe: Optional[str] = "H1"
    note: Optional[str] = None
    is_active: bool = True
    is_triggered: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered_at: Optional[datetime] = None


class AlertItem(Alert):
    pass


class AlertTriggerEvent(BaseModel):
    alert: Alert
    current_price: float
    triggered_at: datetime
    message: str


class Notification(BaseModel):
    id: str
    user_id: str
    alert_id: Optional[str] = None
    title: str
    message: str
    channel: NotificationChannel = NotificationChannel.IN_APP
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
