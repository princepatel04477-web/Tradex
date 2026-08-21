import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional
from app.schemas.alerts import AlertCreate, AlertItem

class AlertService:
    def __init__(self):
        self.alerts: Dict[str, AlertItem] = {}

    def create_alert(self, request: AlertCreate) -> AlertItem:
        if len(self.alerts) >= 50:
            raise ValueError("Alert limit reached (maximum 50 active alerts per user).")

        alert_id = str(uuid.uuid4())[:8]
        item = AlertItem(
            id=alert_id,
            symbol=request.symbol.replace("/", "_"),
            alert_type=request.alert_type,
            threshold_value=request.threshold_value,
            timeframe=request.timeframe or "H1",
            note=request.note,
            is_active=True,
            is_triggered=False,
            created_at=datetime.now(timezone.utc)
        )
        self.alerts[alert_id] = item
        return item

    def get_alerts(self) -> List[AlertItem]:
        return list(self.alerts.values())

    def delete_alert(self, alert_id: str) -> bool:
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            return True
        return False

# Global singleton
alert_service = AlertService()
