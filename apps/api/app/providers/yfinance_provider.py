"""Yahoo Finance / Open FX Market Data Provider (100% Free, Zero API Key Required)."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncGenerator, List
import httpx

from app.core.logging import logger
from app.domain.pips import price_diff_to_pips
from app.providers.base import HistoricalCandle, MarketDataProvider, MarketTick


class YahooFinanceProvider(MarketDataProvider):
    """Yahoo Finance Open Forex Adapter.
    
    100% Free, no sign-up, no API key required.
    Fetches real-time spot FX rates and historical multi-timeframe candles.
    """

    def _convert_symbol(self, symbol: str) -> str:
        clean = symbol.replace("/", "").replace("_", "")
        return f"{clean}=X"

    async def get_live_ticks(self, symbols: List[str]) -> List[MarketTick]:
        results: List[MarketTick] = []
        async with httpx.AsyncClient(timeout=6.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
            for sym in symbols:
                ticker = self._convert_symbol(sym)
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
                try:
                    res = await client.get(url)
                    if res.status_code == 200:
                        data = res.json()
                        meta = data["chart"]["result"][0]["meta"]
                        price = Decimal(str(meta.get("regularMarketPrice", 0.0)))
                        if price > 0:
                            spread_delta = Decimal("0.00012") if "JPY" not in sym else Decimal("0.012")
                            bid = price - (spread_delta / Decimal("2"))
                            ask = price + (spread_delta / Decimal("2"))
                            spread_pips = price_diff_to_pips(ask - bid, sym)
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
                    logger.debug(f"Yahoo finance tick error for {sym}: {e}")
        return results

    async def get_historical_candles(
        self, symbol: str, timeframe: str, count: int = 100
    ) -> List[HistoricalCandle]:
        ticker = self._convert_symbol(symbol)
        interval_map = {
            "M1": "1m",
            "M5": "5m",
            "M15": "15m",
            "M30": "30m",
            "H1": "1h",
            "H4": "1h",
            "D1": "1d",
        }
        interval = interval_map.get(timeframe.upper(), "1h")
        range_str = "5d" if interval in ("1m", "5m", "15m", "30m") else "1mo"

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range={range_str}"

        async with httpx.AsyncClient(timeout=8.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
            try:
                res = await client.get(url)
                if res.status_code != 200:
                    return []
                data = res.json()
                result = data["chart"]["result"][0]
                timestamps = result.get("timestamp", [])
                quotes = result["indicators"]["quote"][0]

                candles: List[HistoricalCandle] = []
                for i in range(len(timestamps)):
                    if quotes["open"][i] is None or quotes["close"][i] is None:
                        continue
                    candles.append(
                        HistoricalCandle(
                            symbol=symbol.replace("/", "_"),
                            timeframe=timeframe,
                            open_time=datetime.fromtimestamp(timestamps[i], tz=timezone.utc).isoformat(),
                            open=Decimal(str(quotes["open"][i])),
                            high=Decimal(str(quotes["high"][i])),
                            low=Decimal(str(quotes["low"][i])),
                            close=Decimal(str(quotes["close"][i])),
                            volume=int(quotes.get("volume", [0])[i] or 0),
                        )
                    )
                return candles[-count:] if len(candles) > count else candles
            except Exception as e:
                logger.warning(f"Yahoo finance candle fetch error: {e}")
                return []

    async def stream_ticks(self, symbols: List[str]) -> AsyncGenerator[MarketTick, None]:
        while True:
            ticks = await self.get_live_ticks(symbols)
            for tick in ticks:
                yield tick
            await asyncio.sleep(1.0)
