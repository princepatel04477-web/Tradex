"""Paper trading router: account state, order execution, position closing, analytics."""

from typing import List
from fastapi import APIRouter, Depends
from app.core.envelope import ApiResponse
from app.schemas.trading import (
    ClosedTrade,
    CreateOrderRequest,
    PaperAccount,
    PerformanceAnalytics,
    Position,
)
from app.services.trading_service import trading_service

router = APIRouter(prefix="/trading", tags=["Paper Trading"])


@router.get("/account", response_model=ApiResponse[PaperAccount])
@router.get("/metrics")
async def get_paper_account():
    account = trading_service.get_account()
    return ApiResponse.success(account)


@router.post("/orders", response_model=ApiResponse[Position])
async def create_order(req: CreateOrderRequest) -> ApiResponse[Position]:
    pos = trading_service.create_order(req)
    return ApiResponse.success(pos)


@router.get("/positions", response_model=ApiResponse[List[Position]])
async def list_positions() -> ApiResponse[List[Position]]:
    positions = list(trading_service.positions.values())
    return ApiResponse.success(positions)


@router.post("/positions/{position_id}/close", response_model=ApiResponse[ClosedTrade])
async def close_position(position_id: str) -> ApiResponse[ClosedTrade]:
    trade = trading_service.close_position(position_id, reason="manual")
    return ApiResponse.success(trade)


@router.get("/trades", response_model=ApiResponse[List[ClosedTrade]])
async def list_closed_trades() -> ApiResponse[List[ClosedTrade]]:
    trades = trading_service.closed_trades
    return ApiResponse.success(trades)


@router.post("/account/reset", response_model=ApiResponse[PaperAccount])
async def reset_account() -> ApiResponse[PaperAccount]:
    account = trading_service.reset_account()
    return ApiResponse.success(account)


@router.get("/analytics", response_model=ApiResponse[PerformanceAnalytics])
async def get_performance_analytics() -> ApiResponse[PerformanceAnalytics]:
    analytics = trading_service.get_analytics()
    return ApiResponse.success(analytics)
