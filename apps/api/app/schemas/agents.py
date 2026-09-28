"""Multi-agent analysis schemas (Month 4 roadmap — LangGraph-style Technical / Macro / Risk / Synthesis squad)."""

from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

AgentName = Literal["technical", "macro", "risk", "synthesis"]
AgentStatus = Literal["ok", "insufficient_context", "failed"]


class AgentAnalyseRequest(BaseModel):
    symbol: str = Field(default="EUR_USD")
    timeframe: Literal["M15", "M30", "H1", "H4", "D1"] = "H1"
    use_llm: bool = Field(default=True, description="Allow the Groq LLM to phrase the synthesis narrative")


class Evidence(BaseModel):
    id: str
    kind: Literal["indicator", "document", "sentiment", "account", "calendar", "volatility", "timeframe"]
    label: str
    value: str
    url: Optional[str] = None


class AgentClaim(BaseModel):
    text: str
    stance: float = Field(ge=-1, le=1, description="-1 bearish … +1 bullish; 0 for non-directional")
    evidence_ids: List[str] = []


class AgentReport(BaseModel):
    agent: AgentName
    title: str
    status: AgentStatus
    stance: float = 0.0
    confidence: float = Field(default=0.0, ge=0, le=1)
    summary: str
    claims: List[AgentClaim] = []
    evidence: List[Evidence] = []
    model_used: str
    duration_ms: float = 0.0
    error: Optional[str] = None


class DiscardedClaim(BaseModel):
    agent: AgentName
    text: str
    reason: str


class AgentVerdict(BaseModel):
    label: str
    tilt: Literal["bullish", "bearish", "neutral"]
    score: float
    confidence: float
    risk_level: str
    narrative: str
    narrative_source: str
    accepted_claims: int
    discarded_claims: List[DiscardedClaim] = []


class AgentRunOut(BaseModel):
    run_id: str
    symbol: str
    timeframe: str
    verdict: AgentVerdict
    agents: List[AgentReport]
    disclaimer: str
    total_duration_ms: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
