"""Finnhub.io Market Data Provider (Free Tier: 60 API req/min, Real-time Forex FX)."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncGenerator, List, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.domain.pips import price_diff_to_pips
from app.providers.base import HistoricalCandle, MarketDataProvider, MarketTick


class FinnhubProvider(MarketDataProvider):
    """Finnhub Forex Market Data Adapter.
    
    Free tier offers 60 requests/minute for real-time and historical Forex quotes.
    Get a free API key at https://finnhub.io.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "FINNHUB_API_KEY", "")
        self.base_url = "https://finnhub.io/api/v1"

    def _convert_symbol(self, symbol: str) -> str:
        # e.g., EUR_USD -> OANDA:EUR_USD
        clean = symbol.replace("/", "_")
        return f"OANDA:{clean}"

    async def get_live_ticks(self, symbols: List[str]) -> List[MarketTick]:
        if not self.api_key:
            logger.warning("FINNHUB_API_KEY is not set; skipping live tick fetch")
            return []

        results: List[MarketTick] = []
        async with httpx.AsyncClient(timeout=5.0) as client:
            for sym in symbols:
                fh_sym = self._convert_symbol(sym)
                url = f"{self.base_url}/quote?symbol={fh_sym}&token={self.api_key}"
                try:
                    res = await client.get(url)
                    if res.status_code == 200:
                        data = res.json()
                        current_price = Decimal(str(data.get("c", 0.0)))
                        if current_price > 0:
                            # Typical standard spread approx 1.2 pips
                            bid = current_price - Decimal("0.00006")
                            ask = current_price + Decimal("0.00006")
                            spread_pips = price_diff_to_pips(sym, ask - bid)
                            results.append(
                                MarketTick(
                                    symbol=sym.replace("/", "_"),
                                    bid=bid,
                                    ask=ask,
                                    spread_pips=spread_pips,
                                    timestamp=datetime.now(timezone.utc).isoformat(),
                                )
                            )
                except Exception as e:
                    logger.warning(f"Finnhub quote error for {sym}: {e}")
        return results

    async def get_historical_candles(
        self, symbol: str, timeframe: str, count: int = 100
    ) -> List[HistoricalCandle]:
        if not self.api_key:
            return []

        resolution_map = {"M1": "1", "M5": "5", "M15": "15", "M30": "30", "H1": "60", "H4": "D", "D1": "D"}
        resolution = resolution_map.get(timeframe.upper(), "60")
        fh_sym = self._convert_symbol(symbol)
        now_ts = int(datetime.now(timezone.utc).timestamp())
        from_ts = now_ts - (count * 3600 * (1 if resolution == "60" else 24))

        url = f"{self.base_url}/forex/candle?symbol={fh_sym}&resolution={resolution}&from={from_ts}&to={now_ts}&token={self.api_key}"

        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url)
            if res.status_code != 200:
                logger.error(f"Finnhub candle error: {res.status_code} {res.text}")
                return []
            data = res.json()
            if data.get("s") != "ok":
                return []

            candles: List[HistoricalCandle] = []
            for i in range(len(data.get("t", []))):
                candles.append(
                    HistoricalCandle(
                        symbol=symbol.replace("/", "_"),
                        timeframe=timeframe,
                        open_time=datetime.fromtimestamp(data["t"][i], tz=timezone.utc).isoformat(),
                        open=Decimal(str(data["o"][i])),
                        high=Decimal(str(data["h"][i])),
                        low=Decimal(str(data["l"][i])),
                        close=Decimal(str(data["c"][i])),
                        volume=int(data.get("v", [0])[i] if "v" in data else 0),
                    )
                )
            return candles

    async def stream_ticks(self, symbols: List[str]) -> AsyncGenerator[MarketTick, None]:
        while True:
            ticks = await self.get_live_ticks(symbols)
            for tick in ticks:
                yield tick
            await asyncio.sleep(1.0)
