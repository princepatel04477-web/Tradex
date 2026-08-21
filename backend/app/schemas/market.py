from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class CurrencyPair(BaseModel):
    symbol: str
    name: str
    base_currency: str
    quote_currency: str
    pip_decimal_places: int  # 4 for standard, 2 for JPY pairs
    category: str  # major, minor, exotic
    pip_size: float
    bid: float
    ask: float
    spread_pips: float
    change_24h_pct: float
    high_24h: float
    low_24h: float
    timestamp: datetime

class Tick(BaseModel):
    symbol: str
    bid: float
    ask: float
    spread_pips: float
    timestamp: datetime

class Candle(BaseModel):
    symbol: str
    timeframe: str  # M1, M5, M15, M30, H1, H4, D1
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class IndicatorSnapshot(BaseModel):
    symbol: str
    timeframe: str
    rsi_14: float
    macd_line: float
    macd_signal: float
    macd_histogram: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    atr_14: float
    ema_9: float
    ema_21: float
    ema_50: float
    sma_200: float
    fib_levels: Dict[str, float]
    macd_crossover: Optional[str] = None  # bullish, bearish, None
    rsi_condition: Optional[str] = None   # overbought, oversold, neutral
    bb_squeeze: bool = False
    timestamp: datetime

class CompositeBias(BaseModel):
    symbol: str
    timeframe: str
    bias: str  # Strong Bullish, Bullish, Neutral, Bearish, Strong Bearish
    score: float  # -1.0 to +1.0
    indicator_contributions: Dict[str, float]
    reasons: List[str]
    timestamp: datetime

class MarketSession(BaseModel):
    name: str  # Sydney, Tokyo, London, New York
    is_active: bool
    open_utc: str
    close_utc: str
    description: str

class MarketSessionOverview(BaseModel):
    sessions: List[MarketSession]
    active_overlap: Optional[str] = None  # e.g., "London-NY Overlap"
    current_utc_time: str
