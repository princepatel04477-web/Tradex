"""Deterministic Test Fakes for all external providers (for offline testing & CI)."""

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import AsyncGenerator, Dict, List, Optional

from app.domain.pips import get_pip_size, price_diff_to_pips
from app.providers.base import (
    EmbeddingProvider,
    EmailProvider,
    HistoricalCandle,
    LLMProvider,
    MarketDataProvider,
    MarketTick,
    NewsArticle,
    NewsProvider,
)

BASE_PRICES: Dict[str, Decimal] = {
    "EUR_USD": Decimal("1.0850"),
    "GBP_USD": Decimal("1.2720"),
    "USD_JPY": Decimal("154.50"),
    "USD_CHF": Decimal("0.8980"),
    "AUD_USD": Decimal("0.6580"),
    "NZD_USD": Decimal("0.6020"),
    "USD_CAD": Decimal("1.3650"),
    "EUR_GBP": Decimal("0.8530"),
    "EUR_JPY": Decimal("167.60"),
    "GBP_JPY": Decimal("196.50"),
    "AUD_JPY": Decimal("101.60"),
    "EUR_AUD": Decimal("1.6480"),
    "USD_INR": Decimal("83.9500"),
    "USD_SGD": Decimal("1.3480"),
    "USD_MXN": Decimal("18.2500"),
}


class FakeMarketDataProvider(MarketDataProvider):
    def __init__(self):
        self.prices = {k: v for k, v in BASE_PRICES.items()}

    async def get_live_ticks(self, symbols: List[str]) -> List[MarketTick]:
        now = datetime.now(timezone.utc).isoformat()
        results: List[MarketTick] = []
        for s in symbols:
            sym = s.replace("/", "_")
            mid = self.prices.get(sym, Decimal("1.0000"))
            pip_sz = get_pip_size(sym)
            spread = Decimal("1.5") * pip_sz
            bid = mid - (spread / Decimal("2"))
            ask = mid + (spread / Decimal("2"))
            spread_pips = price_diff_to_pips(ask - bid, sym)
            results.append(
                MarketTick(
                    symbol=sym,
                    bid=bid,
                    ask=ask,
                    spread_pips=spread_pips,
                    timestamp=now,
                )
            )
        return results

    async def get_historical_candles(
        self, symbol: str, timeframe: str, count: int = 100
    ) -> List[HistoricalCandle]:
        sym = symbol.replace("/", "_")
        base = self.prices.get(sym, Decimal("1.0000"))
        now = datetime.now(timezone.utc)
        pip_sz = get_pip_size(sym)
        candles: List[HistoricalCandle] = []

        for i in range(count, 0, -1):
            t = now - timedelta(hours=i)
            # deterministic slight oscillation
            offset = Decimal(str(math_sin := (i % 10 - 5))) * pip_sz * Decimal("3")
            open_p = base + offset
            close_p = open_p + Decimal("2") * pip_sz
            high_p = max(open_p, close_p) + Decimal("4") * pip_sz
            low_p = min(open_p, close_p) - Decimal("4") * pip_sz

            candles.append(
                HistoricalCandle(
                    symbol=sym,
                    timeframe=timeframe,
                    open_time=t.isoformat(),
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=1000 + (i * 10),
                )
            )
        return candles

    async def stream_ticks(self, symbols: List[str]) -> AsyncGenerator[MarketTick, None]:
        while True:
            ticks = await self.get_live_ticks(symbols)
            for t in ticks:
                yield t
            await asyncio.sleep(1.0)


class FakeNewsProvider(NewsProvider):
    async def fetch_latest_news(self, query: str = "forex", limit: int = 20) -> List[NewsArticle]:
        return [
            NewsArticle(
                id="fake-news-1",
                title="Federal Reserve Signals Prolonged Higher Rate Stance Amid Sticky CPI",
                source="Federal Reserve Statement",
                url="https://federalreserve.gov/sample",
                published_at=datetime.now(timezone.utc).isoformat(),
                snippet="FOMC Chair emphasized that persistent core service inflation warrants restrictive policy.",
                currencies=["USD"],
            ),
            NewsArticle(
                id="fake-news-2",
                title="ECB Prepares for Potential Rate Cut as Eurozone Composite PMI Contracts",
                source="ECB Bulletin",
                url="https://ecb.europa.eu/sample",
                published_at=datetime.now(timezone.utc).isoformat(),
                snippet="Eurozone manufacturing activity registered a slowdown, highlighting downside risks.",
                currencies=["EUR"],
            ),
        ]


class FakeLLMProvider(LLMProvider):
    def __init__(self, fixed_response: Optional[str] = None):
        self.fixed_response = fixed_response

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> str:
        if self.fixed_response:
            return self.fixed_response
        return "Based on verified macroeconomic context [doc-001], monetary policy trends support current price action."


class FakeEmbeddingProvider(EmbeddingProvider):
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # Return dummy 1536-dimensional vectors
        return [[0.05] * 1536 for _ in texts]


class FakeEmailProvider(EmailProvider):
    def __init__(self):
        self.sent_emails: List[dict] = []

    async def send_email(self, to: str, subject: str, body_html: str) -> bool:
        self.sent_emails.append({"to": to, "subject": subject, "body": body_html})
        return True
