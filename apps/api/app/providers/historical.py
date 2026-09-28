"""Deterministic historical OHLC dataset used by the backtesting engine.

The dataset is a seeded, regime-switching geometric random walk per (pair, timeframe), so every
backtest is exactly reproducible for grading and regression testing. Bar timestamps follow the
Forex trading week (Sunday 17:00 to Friday 17:00 America/New_York) and D1 bars open at
17:00 New York time, with daylight-saving handled by the timezone database rather than a fixed offset.

When a live historical provider (OANDA / Twelve Data) is configured it can replace this adapter
without changing the backtest engine, which only consumes ``List[Bar]``.
"""

from __future__ import annotations

import math
import random
import zlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from typing import List, Tuple
from zoneinfo import ZoneInfo

from app.domain.backtest import Bar
from app.domain.pips import get_pip_decimal_places, get_pip_size

NEW_YORK = ZoneInfo("America/New_York")

TIMEFRAME_MINUTES = {"M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}

# Typical one-bar standard deviation in pips per timeframe.
BAR_VOL_PIPS = {"M15": Decimal("6"), "M30": Decimal("8"), "H1": Decimal("12"), "H4": Decimal("24"), "D1": Decimal("65")}


def _is_market_open(ts_utc: datetime) -> bool:
    """True when the timestamp lies inside the FX trading week (Sun 17:00 – Fri 17:00 New York)."""
    ny = ts_utc.astimezone(NEW_YORK)
    wd = ny.weekday()  # Mon=0 … Sun=6
    if wd == 5:
        return False
    if wd == 4 and ny.hour >= 17:
        return False
    if wd == 6 and ny.hour < 17:
        return False
    return True


def bar_open_times(timeframe: str, count: int, end: datetime) -> List[datetime]:
    """Return ``count`` bar open times (ascending, UTC) for closed bars ending at or before ``end``."""
    if timeframe not in TIMEFRAME_MINUTES:
        raise ValueError(f"Unsupported timeframe {timeframe}")
    times: List[datetime] = []
    if timeframe == "D1":
        ny_end = end.astimezone(NEW_YORK)
        day = ny_end.date() - timedelta(days=2)
        while len(times) < count:
            local_open = datetime(day.year, day.month, day.day, 17, 0, tzinfo=NEW_YORK)
            # D1 bars open Sun–Thu 17:00 NY (the Sunday open starts Monday's trading day).
            if local_open.weekday() in (6, 0, 1, 2, 3):
                times.append(local_open.astimezone(timezone.utc))
            day -= timedelta(days=1)
    else:
        step = timedelta(minutes=TIMEFRAME_MINUTES[timeframe])
        epoch_minutes = int(end.timestamp() // 60)
        floored = datetime.fromtimestamp((epoch_minutes - epoch_minutes % TIMEFRAME_MINUTES[timeframe]) * 60, tz=timezone.utc)
        t = floored - step
        while len(times) < count:
            if _is_market_open(t):
                times.append(t)
            t -= step
    times.reverse()
    return times


@lru_cache(maxsize=64)
def _cached_history(symbol: str, timeframe: str, count: int, base_price: str, day_key: str) -> Tuple[Bar, ...]:
    seed = zlib.crc32(f"{symbol}|{timeframe}|tradly-history-v1".encode())
    rng = random.Random(seed)
    pip = get_pip_size(symbol)
    decimals = get_pip_decimal_places(symbol) + 1
    quant = Decimal(1).scaleb(-decimals)
    anchor = float(base_price)
    sigma = float(BAR_VOL_PIPS[timeframe] * pip) / anchor  # log-return std per bar

    end = datetime.fromisoformat(day_key)
    times = bar_open_times(timeframe, count, end)

    # Walk forward from a start price near the anchor with persistent regimes.
    price = anchor * math.exp(rng.gauss(0, 12 * sigma))
    drift = 0.0
    regime_left = 0
    bars: List[Bar] = []
    for t in times:
        if regime_left <= 0:
            drift = rng.choice([-1.0, -0.5, 0.0, 0.0, 0.5, 1.0]) * 0.18 * sigma
            regime_left = rng.randint(40, 160)
        regime_left -= 1
        pull = -0.004 * math.log(price / anchor)  # weak mean reversion keeps prices realistic
        ret = drift + pull + rng.gauss(0, sigma)
        o = price
        c = price * math.exp(ret)
        wick = abs(rng.gauss(0, sigma * 0.6))
        h = max(o, c) * math.exp(wick)
        l = min(o, c) * math.exp(-abs(rng.gauss(0, sigma * 0.6)))
        bars.append(
            Bar(
                time=t.isoformat(),
                open=Decimal(repr(o)).quantize(quant, rounding=ROUND_HALF_UP),
                high=Decimal(repr(h)).quantize(quant, rounding=ROUND_HALF_UP),
                low=Decimal(repr(l)).quantize(quant, rounding=ROUND_HALF_UP),
                close=Decimal(repr(c)).quantize(quant, rounding=ROUND_HALF_UP),
            )
        )
        price = c
    return tuple(bars)


def generate_history(symbol: str, timeframe: str, count: int, base_price: Decimal) -> List[Bar]:
    """Deterministic OHLC history for one pair/timeframe; identical for every call on the same UTC day."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return list(_cached_history(symbol, timeframe, count, str(base_price), today.isoformat()))
