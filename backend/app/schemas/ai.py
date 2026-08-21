from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Citation(BaseModel):
    id: str
    title: str
    source: str
    url: Optional[str] = None
    published_at: str
    snippet: str
    relevance_score: float

class RAGQueryRequest(BaseModel):
    query: str
    currency_pair: Optional[str] = None

class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
    is_insufficient_context: bool = False
    disclaimer: str
    model_used: str
    timestamp: datetime

class CurrencySentiment(BaseModel):
    currency: str
    score: float  # -1.0 (bearish) to +1.0 (bullish)
    label: str    # Bullish, Bearish, Neutral
    article_count: int
    top_headlines: List[str]

class HeadlineSentiment(BaseModel):
    title: str
    source: str
    published_at: str
    sentiment_label: str  # Bullish, Bearish, Neutral
    confidence: float
    affected_currencies: List[str]

class EconomicEvent(BaseModel):
    id: str
    title: str
    country: str
    currency: str
    scheduled_at: datetime
    impact: str  # High, Medium, Low
    previous: str
    consensus: str
    actual: Optional[str] = None
    ai_briefing: Optional[str] = None
    historical_pip_volatility: Optional[str] = None
