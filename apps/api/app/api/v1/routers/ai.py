"""AI Intelligence router: Grounded RAG query, sentiment heatmap, economic calendar."""

from typing import List
from fastapi import APIRouter
from app.core.envelope import ApiResponse
from app.schemas.ai import EconomicCalendarEvent, RAGQueryRequest, RAGQueryResponse, SentimentOverview
from app.services.ai_service import ai_service

router = APIRouter(prefix="/ai", tags=["AI Market Intelligence"])


@router.post("/rag/query", response_model=ApiResponse[RAGQueryResponse])
async def query_rag(req: RAGQueryRequest) -> ApiResponse[RAGQueryResponse]:
    response = await ai_service.query_rag(req)
    return ApiResponse.success(response)


@router.get("/sentiment", response_model=ApiResponse[SentimentOverview])
async def get_sentiment_overview() -> ApiResponse[SentimentOverview]:
    overview = ai_service.get_sentiment_overview()
    return ApiResponse.success(overview)


@router.get("/calendar", response_model=ApiResponse[List[EconomicCalendarEvent]])
async def get_economic_calendar() -> ApiResponse[List[EconomicCalendarEvent]]:
    calendar = ai_service.get_economic_calendar()
    return ApiResponse.success(calendar)
