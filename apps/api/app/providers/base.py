"""Abstract Base Classes (ABCs) for all external service providers (SRS §7.2, ADR-0004)."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import AsyncGenerator, Dict, List, Optional
from pydantic import BaseModel


class MarketTick(BaseModel):
    symbol: str
    bid: Decimal
    ask: Decimal
    spread_pips: Decimal
    timestamp: str


class HistoricalCandle(BaseModel):
    symbol: str
    timeframe: str
    open_time: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class NewsArticle(BaseModel):
    id: str
    title: str
    source: str
    url: Optional[str] = None
    published_at: str
    snippet: str
    currencies: List[str]


class MarketDataProvider(ABC):
    """ABC for Forex market data providers (OANDA v20, TwelveData, or Fake)."""

    @abstractmethod
    async def get_live_ticks(self, symbols: List[str]) -> List[MarketTick]:
        """Fetch latest bid/ask quotes for symbols."""
        pass

    @abstractmethod
    async def get_historical_candles(
        self, symbol: str, timeframe: str, count: int = 100
    ) -> List[HistoricalCandle]:
        """Fetch historical OHLCV candles."""
        pass

    @abstractmethod
    async def stream_ticks(self, symbols: List[str]) -> AsyncGenerator[MarketTick, None]:
        """Stream real-time price ticks."""
        pass


class NewsProvider(ABC):
    """ABC for macroeconomic news and central bank statements."""

    @abstractmethod
    async def fetch_latest_news(self, query: str = "forex", limit: int = 20) -> List[NewsArticle]:
        """Fetch recent Forex news articles."""
        pass


class LLMProvider(ABC):
    """ABC for Large Language Model generation (Groq, Perplexity, or Fake)."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> str:
        """Generate response text from LLM."""
        pass


class EmbeddingProvider(ABC):
    """ABC for text embedding generation (OpenAI text-embedding-3-small or Fake)."""

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for input texts."""
        pass


class EmailProvider(ABC):
    """ABC for transactional email alerts (Resend or Fake)."""

    @abstractmethod
    async def send_email(self, to: str, subject: str, body_html: str) -> bool:
        """Send transactional email notification."""
        pass
