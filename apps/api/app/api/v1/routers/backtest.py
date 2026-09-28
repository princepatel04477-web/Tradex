"""Historical backtesting router (Month 3 roadmap)."""

from typing import List, Optional
from fastapi import APIRouter, Depends
from app.core.deps import CurrentUser, get_optional_user
from app.core.envelope import ApiResponse
from app.schemas.backtest import BacktestRequest, BacktestRunOut, BacktestRunSummary, StrategyInfo
from app.services.backtest_service import backtest_service

router = APIRouter(prefix="/backtest", tags=["Backtesting"])


@router.get("/strategies", response_model=ApiResponse[List[StrategyInfo]])
async def list_strategies() -> ApiResponse[List[StrategyInfo]]:
    return ApiResponse.success(backtest_service.list_strategies())


@router.post("/run", response_model=ApiResponse[BacktestRunOut])
async def run_backtest(
    req: BacktestRequest,
    user: Optional[CurrentUser] = Depends(get_optional_user),
) -> ApiResponse[BacktestRunOut]:
    run = backtest_service.run(req, user.user_id if user else None)
    return ApiResponse.success(run)


@router.get("/runs", response_model=ApiResponse[List[BacktestRunSummary]])
async def list_runs() -> ApiResponse[List[BacktestRunSummary]]:
    return ApiResponse.success(backtest_service.list_runs())


@router.get("/runs/{run_id}", response_model=ApiResponse[BacktestRunOut])
async def get_run(run_id: str) -> ApiResponse[BacktestRunOut]:
    return ApiResponse.success(backtest_service.get_run(run_id))
