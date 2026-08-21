"""AI schemas for RAG query, sentiment overview, and economic calendar."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class CitationSource(BaseModel):
    id: str
    title: str
    source: str
    url: Optional[str] = None
    snippet: str
    published_at: str


class NewsHeadline(BaseModel):
    id: str
    title: str
    source: str
    url: Optional[str] = None
    published_at: str
    snippet: str
    currencies: List[str] = []


class RAGQueryRequest(BaseModel):
    query: str
    symbol: Optional[str] = None
    currency_pair: Optional[str] = None


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[CitationSource] = []
    model_used: str = "Tradly-Grounded-RAG"
    relevance_score: float = 0.0
    disclaimer: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CurrencySentiment(BaseModel):
    currency: str
    score: float  # -1.0 to +1.0
    label: str    # Bullish, Bearish, Neutral
    article_count: int = 0
    sample_headline: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SentimentOverview(BaseModel):
    currencies: List[CurrencySentiment] = []
    overall_market_bias: str = "Neutral"
    total_articles_analyzed: int = 0
    model_version: str = "ProsusAI/finbert-forex-v1"
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EconomicCalendarEvent(BaseModel):
    id: str
    title: str
    country: str
    currency: str
    scheduled_at: datetime
    impact: str  # High, Medium, Low
    previous: Optional[str] = None
    consensus: Optional[str] = None
    actual: Optional[str] = None
    ai_briefing: Optional[str] = None
    historical_pip_volatility: Optional[str] = None
