"""Live FX market data feed (Yahoo Finance primary, Twelve Data fallback).

Synchronous on purpose: callers run it from worker threads (``asyncio.to_thread`` or sync FastAPI
routes), and the existing services consume candles synchronously.

* ``fetch_quotes`` - one batched request for every pair's latest mid price and previous close.
* ``fetch_candles`` - real OHLC bars for a pair/timeframe, cached with a timeframe-aware TTL.
  H4 bars are built from real H1 bars aligned to 4-hour UTC boundaries, since Yahoo has no 4h interval.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional, Tuple

import httpx

from app.core.config import settings
from app.core.logging import logger

YAHOO_HOSTS = ("https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}

# (yahoo interval, yahoo range) per timeframe for the chart view (a few hundred bars).
CHART_PARAMS: Dict[str, Tuple[str, str]] = {
    "M1": ("1m", "5d"),
    "M5": ("5m", "1mo"),
    "M15": ("15m", "1mo"),
    "M30": ("30m", "1mo"),
    "H1": ("60m", "3mo"),
    "H4": ("60m", "1y"),
    "D1": ("1d", "2y"),
}

# Deeper history for the backtest engine (Yahoo limits: intraday <= 60d, hourly <= 730d).
HISTORY_PARAMS: Dict[str, Tuple[str, str]] = {
    "M15": ("15m", "60d"),
    "M30": ("30m", "60d"),
    "H1": ("60m", "730d"),
    "H4": ("60m", "730d"),
    "D1": ("1d", "15y"),
}

# Seconds a cached candle series stays fresh.
CANDLE_TTL: Dict[str, int] = {"M1": 20, "M5": 45, "M15": 60, "M30": 90, "H1": 120, "H4": 300, "D1": 900}

INTERVAL_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "60m": 60, "1d": 1440}

TWELVEDATA_INTERVAL = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h", "H4": "4h", "D1": "1day"}


@dataclass
class Quote:
    symbol: str  # EUR_USD
    price: float
    previous_close: Optional[float]
    day_high: Optional[float]
    day_low: Optional[float]
    market_time: datetime


@dataclass
class OHLC:
    time: datetime  # bar open, UTC
    open: float
    high: float
    low: float
    close: float
    volume: int


class LiveDataUnavailable(RuntimeError):
    """Raised when no live provider could return data and nothing is cached."""


def to_yahoo(symbol: str) -> str:
    return symbol.replace("/", "").replace("_", "") + "=X"


def from_yahoo(ticker: str) -> str:
    raw = ticker.replace("=X", "")
    return f"{raw[:3]}_{raw[3:]}"


class LiveFeed:
    def __init__(self) -> None:
        self._client = httpx.Client(timeout=httpx.Timeout(6.0, connect=4.0), headers=HEADERS, follow_redirects=True)
        self._cache: Dict[Tuple[str, str, str], Tuple[float, List[OHLC]]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ HTTP
    def _yahoo_get(self, path: str, params: dict) -> Optional[dict]:
        for host in YAHOO_HOSTS:
            try:
                res = self._client.get(f"{host}{path}", params=params)
                if res.status_code == 200:
                    return res.json()
                logger.warning(f"Yahoo {path} -> HTTP {res.status_code}")
            except Exception as exc:  # network / JSON errors: try next host
                logger.warning(f"Yahoo {path} failed on {host}: {exc}")
        return None

    # ---------------------------------------------------------------- quotes
    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Latest mid price per pair in a single batched Yahoo request (falls back to Twelve Data)."""
        quotes: Dict[str, Quote] = {}
        data = self._yahoo_get(
            "/v8/finance/spark",
            {"symbols": ",".join(to_yahoo(s) for s in symbols), "range": "1d", "interval": "5m"},
        )
        if data:
            for ticker, row in data.items():
                try:
                    closes = [c for c in (row.get("close") or []) if c is not None]
                    stamps = row.get("timestamp") or []
                    if not closes:
                        continue
                    sym = from_yahoo(ticker)
                    quotes[sym] = Quote(
                        symbol=sym,
                        price=float(closes[-1]),
                        previous_close=row.get("previousClose") or row.get("chartPreviousClose"),
                        day_high=max(closes),
                        day_low=min(closes),
                        market_time=datetime.fromtimestamp(stamps[-1], tz=timezone.utc) if stamps else datetime.now(timezone.utc),
                    )
                except Exception as exc:
                    logger.warning(f"Bad spark row for {ticker}: {exc}")

        missing = [s for s in symbols if s not in quotes]
        if missing and settings.TWELVEDATA_API_KEY:
            quotes.update(self._twelvedata_quotes(missing))
        return quotes

    def _twelvedata_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        out: Dict[str, Quote] = {}
        try:
            res = self._client.get(
                "https://api.twelvedata.com/quote",
                params={"symbol": ",".join(s.replace("_", "/") for s in symbols), "apikey": settings.TWELVEDATA_API_KEY},
            )
            payload = res.json()
            if len(symbols) == 1:
                payload = {symbols[0].replace("_", "/"): payload}
            for sym in symbols:
                row = payload.get(sym.replace("_", "/")) or {}
                if "close" not in row:
                    continue
                out[sym] = Quote(
                    symbol=sym,
                    price=float(row["close"]),
                    previous_close=float(row["previous_close"]) if row.get("previous_close") else None,
                    day_high=float(row["high"]) if row.get("high") else None,
                    day_low=float(row["low"]) if row.get("low") else None,
                    market_time=datetime.now(timezone.utc),
                )
        except Exception as exc:
            logger.warning(f"Twelve Data quote fallback failed: {exc}")
        return out

    # --------------------------------------------------------------- candles
    def fetch_candles(self, symbol: str, timeframe: str, history: bool = False) -> List[OHLC]:
        """Real OHLC bars, oldest first. ``history=True`` pulls the deepest range (for backtests)."""
        tf = timeframe.upper()
        params_map = HISTORY_PARAMS if history else CHART_PARAMS
        if tf not in params_map:
            raise LiveDataUnavailable(f"Timeframe {tf} is not supported for live data")
        key = (symbol, tf, "hist" if history else "chart")
        ttl = CANDLE_TTL.get(tf, 120) * (5 if history else 1)

        cached = self._cache.get(key)
        if cached and time.time() - cached[0] < ttl:
            return cached[1]

        with self._lock:
            cached = self._cache.get(key)
            if cached and time.time() - cached[0] < ttl:
                return cached[1]
            bars = self._yahoo_candles(symbol, tf, *params_map[tf])
            if not bars and settings.TWELVEDATA_API_KEY:
                bars = self._twelvedata_candles(symbol, tf)
            if bars:
                self._cache[key] = (time.time(), bars)
                return bars
        if cached:
            logger.warning(f"Serving stale cached candles for {symbol} {tf}")
            return cached[1]
        raise LiveDataUnavailable(f"No live candle data available for {symbol} {tf}")

    def _yahoo_candles(self, symbol: str, tf: str, interval: str, rng: str) -> List[OHLC]:
        data = self._yahoo_get(f"/v8/finance/chart/{to_yahoo(symbol)}", {"interval": interval, "range": rng})
        try:
            result = data["chart"]["result"][0]  # type: ignore[index]
            stamps = result.get("timestamp") or []
            q = result["indicators"]["quote"][0]
        except Exception:
            return []
        bars: List[OHLC] = []
        for i, ts in enumerate(stamps):
            o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
            if None in (o, h, l, c) or o <= 0:
                continue
            bars.append(
                OHLC(
                    time=datetime.fromtimestamp(ts, tz=timezone.utc),
                    open=float(o),
                    high=float(max(h, o, c)),
                    low=float(min(l, o, c)),
                    close=float(c),
                    volume=int((q.get("volume") or [0] * len(stamps))[i] or 0),
                )
            )
        # Yahoo appends the live quote as an extra point with a raw timestamp; bucketing merges it
        # into the bar it belongs to.
        if tf == "D1":
            # Daily FX bars are stamped at the London midnight (22:00/23:00 UTC of the prior day).
            return merge_buckets(bars, lambda t: datetime.combine((t + timedelta(hours=2)).date(), datetime.min.time(), tzinfo=timezone.utc))
        minutes = 240 if tf == "H4" else INTERVAL_MINUTES[interval]
        return resample(bars, minutes)

    def _twelvedata_candles(self, symbol: str, tf: str) -> List[OHLC]:
        try:
            res = self._client.get(
                "https://api.twelvedata.com/time_series",
                params={
                    "symbol": symbol.replace("_", "/"),
                    "interval": TWELVEDATA_INTERVAL[tf],
                    "outputsize": 500,
                    "timezone": "UTC",
                    "apikey": settings.TWELVEDATA_API_KEY,
                },
            )
            values = res.json().get("values") or []
            bars = []
            for v in reversed(values):
                t = datetime.fromisoformat(v["datetime"])
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                bars.append(OHLC(t, float(v["open"]), float(v["high"]), float(v["low"]), float(v["close"]), 0))
            return bars
        except Exception as exc:
            logger.warning(f"Twelve Data candle fallback failed for {symbol} {tf}: {exc}")
            return []


def resample(bars: List[OHLC], minutes: int) -> List[OHLC]:
    """Aggregate bars into ``minutes``-long buckets aligned to UTC epoch boundaries."""
    span = minutes * 60
    return merge_buckets(bars, lambda t: datetime.fromtimestamp(int(t.timestamp()) // span * span, tz=timezone.utc))


def merge_buckets(bars: List[OHLC], bucket_of: Callable[[datetime], datetime]) -> List[OHLC]:
    """Merge consecutive bars that map to the same bucket start into one OHLC bar."""
    out: List[OHLC] = []
    for b in bars:
        start = bucket_of(b.time)
        if out and out[-1].time == start:
            last = out[-1]
            last.high = max(last.high, b.high)
            last.low = min(last.low, b.low)
            last.close = b.close
            last.volume += b.volume
        else:
            out.append(OHLC(start, b.open, b.high, b.low, b.close, b.volume))
    return out


live_feed = LiveFeed()
