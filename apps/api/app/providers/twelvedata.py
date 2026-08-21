"""Twelve Data Market Data Provider (800 Free API Requests/Day, Batch Multi-Pair Support)."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncGenerator, List, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.domain.pips import price_diff_to_pips
from app.providers.base import HistoricalCandle, MarketDataProvider, MarketTick


class TwelveDataProvider(MarketDataProvider):
    """Twelve Data Forex Adapter.
    
    Provides institutional Forex spot prices and multi-timeframe candles.
    Supports batch querying up to 15 currency pairs in a single HTTP request.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "TWELVEDATA_API_KEY", "")
        self.base_url = "https://api.twelvedata.com"

    def _format_symbol(self, symbol: str) -> str:
        # e.g., EUR_USD -> EUR/USD
        return symbol.replace("_", "/")

    async def get_live_ticks(self, symbols: List[str]) -> List[MarketTick]:
        if not self.api_key:
            logger.warning("TWELVEDATA_API_KEY is not configured")
            return []

        # Batch all symbols into a comma-separated query string
        formatted_symbols = [self._format_symbol(s) for s in symbols]
        sym_param = ",".join(formatted_symbols)
        url = f"{self.base_url}/quote?symbol={sym_param}&apikey={self.api_key}"

        results: List[MarketTick] = []
        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                res = await client.get(url)
                if res.status_code != 200:
                    logger.error(f"Twelve Data quote error: {res.status_code} {res.text}")
                    return []

                data = res.json()
                # If querying single symbol, data is a dict; if multiple, data is dict of symbol keys
                payload = data if len(symbols) > 1 else {formatted_symbols[0]: data}

                for orig_sym in symbols:
                    key = self._format_symbol(orig_sym)
                    quote_data = payload.get(key)
                    if not quote_data or "close" not in quote_data:
                        continue

                    close_str = quote_data.get("close")
                    if not close_str:
                        continue

                    price = Decimal(str(close_str))
                    # Standard spread ~ 1.2 pips
                    spread_delta = Decimal("0.00012") if "JPY" not in orig_sym else Decimal("0.012")
                    bid = price - (spread_delta / Decimal("2"))
                    ask = price + (spread_delta / Decimal("2"))
                    spread_pips = price_diff_to_pips(ask - bid, orig_sym)

                    results.append(
                        MarketTick(
                            symbol=orig_sym.replace("/", "_"),
                            bid=bid,
                            ask=ask,
                            spread_pips=spread_pips,
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        )
                    )
            except Exception as e:
                logger.error(f"Twelve Data tick fetch exception: {e}")
        return results

    async def get_historical_candles(
        self, symbol: str, timeframe: str, count: int = 100
    ) -> List[HistoricalCandle]:
        if not self.api_key:
            return []

        interval_map = {
            "M1": "1min",
            "M5": "5min",
            "M15": "15min",
            "M30": "30min",
            "H1": "1h",
            "H4": "4h",
            "D1": "1day",
        }
        interval = interval_map.get(timeframe.upper(), "1h")
        sym_fmt = self._format_symbol(symbol)
        url = f"{self.base_url}/time_series?symbol={sym_fmt}&interval={interval}&outputsize={min(count, 500)}&apikey={self.api_key}"

        candles: List[HistoricalCandle] = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.get(url)
                if res.status_code != 200:
                    return []

                data = res.json()
                values = data.get("values", [])
                for val in reversed(values):
                    candles.append(
                        HistoricalCandle(
                            symbol=symbol.replace("/", "_"),
                            timeframe=timeframe,
                            open_time=val.get("datetime", ""),
                            open=Decimal(str(val.get("open", "0.0"))),
                            high=Decimal(str(val.get("high", "0.0"))),
                            low=Decimal(str(val.get("low", "0.0"))),
                            close=Decimal(str(val.get("close", "0.0"))),
                            volume=int(val.get("volume", 0) or 0),
                        )
                    )
            except Exception as e:
                logger.error(f"Twelve Data candles fetch exception: {e}")
        return candles

    async def stream_ticks(self, symbols: List[str]) -> AsyncGenerator[MarketTick, None]:
        while True:
            ticks = await self.get_live_ticks(symbols)
            for tick in ticks:
                yield tick
            await asyncio.sleep(2.0)
