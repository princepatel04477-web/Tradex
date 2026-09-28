"""Alert engine tests: crossing semantics (fire once on transition, not while price holds)."""

import asyncio
from decimal import Decimal

from app.schemas.alerts import AlertCreate
from app.services.alert_service import AlertService
from app.services.market_service import market_service


def _set_mid(symbol: str, mid: str) -> None:
    market_service.prices[symbol]["mid"] = Decimal(mid)


def test_price_above_fires_once_on_crossing_and_not_while_holding():
    svc = AlertService()
    _set_mid("EUR_USD", "1.0800")
    alert = svc.create_alert("u1", AlertCreate(symbol="EUR_USD", alert_type="price_above", threshold_value=1.0850))

    assert asyncio.run(svc.check_alerts_on_tick()) == []  # still below

    _set_mid("EUR_USD", "1.0860")
    events = asyncio.run(svc.check_alerts_on_tick())
    assert len(events) == 1 and events[0].alert.id == alert.id

    _set_mid("EUR_USD", "1.0870")
    assert asyncio.run(svc.check_alerts_on_tick()) == []  # holding beyond threshold does not re-fire
    assert len(svc.get_notifications("u1")) == 1
    assert svc.events_since(0)[0][0] == 1


def test_alert_created_beyond_threshold_does_not_fire_immediately():
    svc = AlertService()
    _set_mid("GBP_USD", "1.2800")
    svc.create_alert("u2", AlertCreate(symbol="GBP_USD", alert_type="price_above", threshold_value=1.2700))
    assert asyncio.run(svc.check_alerts_on_tick()) == []


def test_price_below_crossing_and_isolation_between_users():
    svc = AlertService()
    _set_mid("USD_JPY", "155.00")
    svc.create_alert("alice", AlertCreate(symbol="USD_JPY", alert_type="price_below", threshold_value=154.50))
    _set_mid("USD_JPY", "154.40")
    assert len(asyncio.run(svc.check_alerts_on_tick())) == 1
    assert svc.get_notifications("bob") == []
    assert svc.list_alerts("bob") == []


def test_latest_ticks_does_not_advance_feed():
    before = {k: v["mid"] for k, v in market_service.prices.items()}
    ticks = market_service.latest_ticks()
    after = {k: v["mid"] for k, v in market_service.prices.items()}
    assert before == after
    assert len(ticks) == 15
    assert all(t.ask > t.bid for t in ticks.values())
