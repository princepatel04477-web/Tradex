"""Market data repository for currency pairs and candle persistence."""

from decimal import Decimal
from typing import List, Optional
from app.domain.pips import split_symbol
from app.providers.base import HistoricalCandle
from app.repositories.base import get_db_pool


class MarketRepository:
    async def get_active_pairs(self) -> List[dict]:
        pool = get_db_pool()
        if not pool:
            return []
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM currency_pairs WHERE is_active = TRUE ORDER BY symbol")
            return [dict(r) for r in rows]

    async def save_candle(self, candle: HistoricalCandle, pair_id: str) -> None:
        pool = get_db_pool()
        if not pool:
            return
        query = """
        INSERT INTO candles (pair_id, timeframe, open_time, open, high, low, close, volume)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (pair_id, timeframe, open_time) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume;
        """
        async with pool.acquire() as conn:
            await conn.execute(
                query,
                pair_id,
                candle.timeframe,
                candle.open_time,
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume,
            )

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> List[dict]:
        pool = get_db_pool()
        if not pool:
            return []
        query = """
        SELECT c.*, p.symbol 
        FROM candles c
        JOIN currency_pairs p ON c.pair_id = p.id
        WHERE p.symbol = $1 AND c.timeframe = $2
        ORDER BY c.open_time DESC
        LIMIT $3;
        """
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, symbol.replace("/", "_"), timeframe, limit)
            return [dict(r) for r in reversed(rows)]


market_repo = MarketRepository()
