"""Technical analysis and directional bias router."""

from fastapi import APIRouter, Query
from app.core.envelope import ApiResponse
from app.schemas.market import DirectionalBias, IndicatorSnapshot
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/analysis", tags=["Technical Analysis"])


@router.get("/indicators/{symbol}", response_model=ApiResponse[IndicatorSnapshot])
async def get_indicators(
    symbol: str,
    timeframe: str = Query(default="H1", description="M1, M5, M15, M30, H1, H4, D1"),
) -> ApiResponse[IndicatorSnapshot]:
    indicators = analysis_service.get_indicators(symbol, timeframe)
    return ApiResponse.success(indicators)


@router.get("/bias/{symbol}", response_model=ApiResponse[DirectionalBias])
async def get_bias(
    symbol: str,
    timeframe: str = Query(default="H1", description="M1, M5, M15, M30, H1, H4, D1"),
) -> ApiResponse[DirectionalBias]:
    bias = analysis_service.get_bias(symbol, timeframe)
    return ApiResponse.success(bias)
