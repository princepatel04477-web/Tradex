"""Multi-agent analysis router (Month 4 roadmap)."""

from typing import List
from fastapi import APIRouter
from app.core.envelope import ApiResponse
from app.schemas.agents import AgentAnalyseRequest, AgentRunOut
from app.services.agent_service import agent_service

router = APIRouter(prefix="/agents", tags=["Multi-Agent Analysis"])


@router.post("/analyse", response_model=ApiResponse[AgentRunOut])
async def analyse(req: AgentAnalyseRequest) -> ApiResponse[AgentRunOut]:
    run = await agent_service.analyse(req)
    return ApiResponse.success(run)


@router.get("/runs", response_model=ApiResponse[List[AgentRunOut]])
async def list_runs() -> ApiResponse[List[AgentRunOut]]:
    return ApiResponse.success(agent_service.list_runs())
