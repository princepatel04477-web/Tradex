"""Alert Service: price crossing checks, indicator alerts, in-app notifications (FG-6)."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from app.core.errors import ResourceNotFoundError, ValidationError
from app.providers.base import EmailProvider
from app.providers.fakes import FakeEmailProvider
from app.schemas.alerts import Alert, AlertCreate, AlertTriggerEvent, Notification, NotificationChannel
from app.services.market_service import market_service


class AlertService:
    def __init__(self, email_provider: Optional[EmailProvider] = None):
        self.email_provider = email_provider or FakeEmailProvider()
        self.alerts: Dict[str, Alert] = {}
        self.notifications: List[Notification] = []

    def create_alert(self, user_id: str, req: AlertCreate) -> Alert:
        if len([a for a in self.alerts.values() if a.user_id == user_id]) >= 50:
            raise ValidationError("Alert cap reached (maximum 50 active alerts per user)")

        alert_id = str(uuid.uuid4())[:8]
        alert = Alert(
            id=alert_id,
            user_id=user_id,
            symbol=req.symbol,
            alert_type=req.alert_type,
            threshold_value=req.threshold_value,
            timeframe=req.timeframe,
            note=req.note,
            is_active=True,
            is_triggered=False,
            created_at=datetime.now(timezone.utc),
            last_triggered_at=None,
        )
        self.alerts[alert_id] = alert
        return alert

    def list_alerts(self, user_id: str) -> List[Alert]:
        return [a for a in self.alerts.values() if a.user_id == user_id]

    def delete_alert(self, user_id: str, alert_id: str) -> bool:
        if alert_id in self.alerts and self.alerts[alert_id].user_id == user_id:
            del self.alerts[alert_id]
            return True
        raise ResourceNotFoundError(f"Alert {alert_id} not found")

    def toggle_alert(self, user_id: str, alert_id: str) -> Alert:
        if alert_id in self.alerts and self.alerts[alert_id].user_id == user_id:
            a = self.alerts[alert_id]
            a.is_active = not a.is_active
            return a
        raise ResourceNotFoundError(f"Alert {alert_id} not found")

    async def check_alerts_on_tick(self) -> List[AlertTriggerEvent]:
        triggered_events = []
        for alert in list(self.alerts.values()):
            if not alert.is_active or alert.is_triggered:
                continue

            pair = market_service.prices.get(alert.symbol)
            if not pair:
                continue

            curr_price = float(pair["mid"])
            thresh = alert.threshold_value
            is_hit = False

            if alert.alert_type == "price_above" and curr_price >= thresh:
                is_hit = True
            elif alert.alert_type == "price_below" and curr_price <= thresh:
                is_hit = True

            if is_hit:
                alert.is_triggered = True
                alert.last_triggered_at = datetime.now(timezone.utc)
                event = AlertTriggerEvent(
                    alert=alert,
                    current_price=curr_price,
                    triggered_at=datetime.now(timezone.utc),
                    message=f"Alert: {alert.symbol} reached {curr_price} (Target: {thresh})",
                )
                triggered_events.append(event)
                # create notification
                self.notifications.append(
                    Notification(
                        id=str(uuid.uuid4())[:8],
                        user_id=alert.user_id,
                        alert_id=alert.id,
                        title=f"Price Alert: {alert.symbol}",
                        message=event.message,
                        channel=NotificationChannel.IN_APP,
                        is_read=False,
                        created_at=datetime.now(timezone.utc),
                    )
                )
        return triggered_events

    def get_notifications(self, user_id: str) -> List[Notification]:
        return [n for n in self.notifications if n.user_id == user_id]


alert_service = AlertService()
