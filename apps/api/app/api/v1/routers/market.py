"""Market data router: thin presentation layer wrapping MarketService."""

from typing import List
from fastapi import APIRouter, Query
from app.core.envelope import ApiResponse
from app.schemas.market import Candle, CurrencyPair, MarketSessionOverview, Tick
from app.services.market_service import market_service

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/pairs", response_model=ApiResponse[List[CurrencyPair]])
async def list_currency_pairs() -> ApiResponse[List[CurrencyPair]]:
    pairs = market_service.get_all_pairs()
    return ApiResponse.success(pairs)


@router.get("/pairs/{symbol}", response_model=ApiResponse[CurrencyPair])
async def get_pair(symbol: str) -> ApiResponse[CurrencyPair]:
    pair = market_service.get_pair(symbol)
    if not pair:
        return ApiResponse.fail(code="NOT_FOUND", message=f"Currency pair {symbol} not found")
    return ApiResponse.success(pair)


@router.get("/ticks", response_model=ApiResponse[dict])
async def get_live_ticks() -> ApiResponse[dict]:
    ticks = market_service.update_ticks()
    return ApiResponse.success(ticks)


@router.get("/candles/{symbol}", response_model=ApiResponse[List[Candle]])
async def get_candles(
    symbol: str,
    timeframe: str = Query(default="H1", description="M1, M5, M15, M30, H1, H4, D1"),
    limit: int = Query(default=100, ge=1, le=500),
) -> ApiResponse[List[Candle]]:
    candles = market_service.get_candles(symbol, timeframe, limit)
    return ApiResponse.success(candles)


@router.get("/sessions", response_model=ApiResponse[MarketSessionOverview])
async def get_sessions() -> ApiResponse[MarketSessionOverview]:
    sessions = market_service.get_market_sessions()
    return ApiResponse.success(sessions)
