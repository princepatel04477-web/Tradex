"""Alerts and notifications router."""

from typing import List
from fastapi import APIRouter, Depends
from app.core.deps import CurrentUser, get_current_user
from app.core.envelope import ApiResponse
from app.schemas.alerts import Alert, AlertCreate, Notification
from app.services.alert_service import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])


@router.post("", response_model=ApiResponse[Alert])
async def create_alert(
    req: AlertCreate,
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[Alert]:
    alert = alert_service.create_alert(user.user_id, req)
    return ApiResponse.success(alert)


@router.get("", response_model=ApiResponse[List[Alert]])
async def list_alerts(
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[List[Alert]]:
    alerts = alert_service.list_alerts(user.user_id)
    return ApiResponse.success(alerts)


@router.delete("/{alert_id}", response_model=ApiResponse[bool])
async def delete_alert(
    alert_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[bool]:
    alert_service.delete_alert(user.user_id, alert_id)
    return ApiResponse.success(True)


@router.post("/{alert_id}/toggle", response_model=ApiResponse[Alert])
async def toggle_alert(
    alert_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[Alert]:
    alert = alert_service.toggle_alert(user.user_id, alert_id)
    return ApiResponse.success(alert)


@router.get("/notifications", response_model=ApiResponse[List[Notification]])
async def list_notifications(
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[List[Notification]]:
    notifications = alert_service.get_notifications(user.user_id)
    return ApiResponse.success(notifications)
