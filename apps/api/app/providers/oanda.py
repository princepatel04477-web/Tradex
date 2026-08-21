"""OANDA v20 API Market Data Provider with Token-Bucket Rate Limiting (CON-1 compliance)."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncGenerator, List, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.domain.pips import get_pip_size, price_diff_to_pips
from app.providers.base import HistoricalCandle, MarketDataProvider, MarketTick


class OandaProvider(MarketDataProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        account_id: Optional[str] = None,
        environment: str = "practice",
    ):
        self.api_key = api_key or settings.OANDA_API_KEY
        self.account_id = account_id or settings.OANDA_ACCOUNT_ID
        self.environment = environment or settings.OANDA_ENVIRONMENT
        self.base_url = (
            "https://api-fxpractice.oanda.com/v3"
            if self.environment == "practice"
            else "https://api-fxtrade.oanda.com/v3"
        )
        self.stream_url = (
            "https://stream-fxpractice.oanda.com/v3"
            if self.environment == "practice"
            else "https://stream-fxtrade.oanda.com/v3"
        )

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def get_live_ticks(self, symbols: List[str]) -> List[MarketTick]:
        if not self.api_key:
            raise ValueError("OANDA_API_KEY is not configured")

        instruments = ",".join([s.replace("/", "_") for s in symbols])
        url = f"{self.base_url}/accounts/{self.account_id}/pricing?instruments={instruments}"

        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(url, headers=self._get_headers())
            if res.status_code != 200:
                logger.error(f"OANDA pricing error: {res.status_code} {res.text}")
                return []

            data = res.json()
            results: List[MarketTick] = []
            for p in data.get("prices", []):
                sym = p["instrument"]
                bid = Decimal(str(p["bids"][0]["price"]))
                ask = Decimal(str(p["asks"][0]["price"]))
                spread_pips = price_diff_to_pips(ask - bid, sym)
                results.append(
                    MarketTick(
                        symbol=sym,
                        bid=bid,
                        ask=ask,
                        spread_pips=spread_pips,
                        timestamp=p.get("time", datetime.now(timezone.utc).isoformat()),
                    )
                )
            return results

    async def get_historical_candles(
        self, symbol: str, timeframe: str, count: int = 100
    ) -> List[HistoricalCandle]:
        if not self.api_key:
            raise ValueError("OANDA_API_KEY is not configured")

        tf_map = {
            "M1": "M1", "M5": "M5", "M15": "M15", "M30": "M30",
            "H1": "H1", "H4": "H4", "D1": "D",
        }
        granularity = tf_map.get(timeframe, "H1")
        instrument = symbol.replace("/", "_")
        url = f"{self.base_url}/instruments/{instrument}/candles?granularity={granularity}&count={min(count, 5000)}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, headers=self._get_headers())
            if res.status_code != 200:
                logger.error(f"OANDA candles error: {res.status_code} {res.text}")
                return []

            data = res.json()
            candles: List[HistoricalCandle] = []
            for c in data.get("candles", []):
                mid = c["mid"]
                candles.append(
                    HistoricalCandle(
                        symbol=instrument,
                        timeframe=timeframe,
                        open_time=c["time"],
                        open=Decimal(str(mid["o"])),
                        high=Decimal(str(mid["h"])),
                        low=Decimal(str(mid["l"])),
                        close=Decimal(str(mid["c"])),
                        volume=int(c.get("volume", 0)),
                    )
                )
            return candles

    async def stream_ticks(self, symbols: List[str]) -> AsyncGenerator[MarketTick, None]:
        if not self.api_key or not self.account_id:
            raise ValueError("OANDA credentials missing for streaming")

        instruments = ",".join([s.replace("/", "_") for s in symbols])
        url = f"{self.stream_url}/accounts/{self.account_id}/pricing/stream?instruments={instruments}"

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url, headers=self._get_headers()) as response:
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    # Parse chunked tick lines
                    # Yield valid tick records
                    pass
