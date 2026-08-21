"""Module 9 - EMA overlay.

The notes name exactly one indicator: the 50 EMA. It is treated as a
**supplementary confluence only**. Structure is the primary trend signal, and
nothing here may override the structure engine's trend call - "no indicator
tells you the market trend".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from . import config
from .types import Candle, Trend


@dataclass
class EMAState:
    """Where price sits relative to the EMA right now."""

    period: int
    value: Optional[float]
    price: float
    #: Price above the EMA reads bullish, below bearish. Advisory only.
    alignment: Trend
    slope: float
    series: List[Optional[float]]

    @property
    def aligns_with(self) -> Trend:
        return self.alignment


def ema_series(values: List[float], period: int) -> List[Optional[float]]:
    """Exponential moving average, seeded with an SMA of the first ``period``.

    Returns a list the same length as ``values``; entries before the EMA can be
    seeded are ``None``.
    """
    if period <= 0:
        raise ValueError("EMA period must be positive")
    out: List[Optional[float]] = [None] * len(values)
    if len(values) < period:
        return out

    multiplier = 2.0 / (period + 1.0)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    ema = seed
    for i in range(period, len(values)):
        ema = (values[i] - ema) * multiplier + ema
        out[i] = ema
    return out


def compute_ema(
    candles: List[Candle], period: Optional[int] = None
) -> EMAState:
    """EMA state for a candle series.

    Args:
        candles: OHLC series (closes are used).
        period: defaults to ``config.EMA_PERIOD`` (50).

    Returns:
        An :class:`EMAState`. ``alignment`` is ``UNDETERMINED`` when there are
        not enough candles to seed the average - it never guesses.
    """
    p = period or config.EMA_PERIOD
    closes = [c.close for c in candles]
    series = ema_series(closes, p)

    price = closes[-1] if closes else 0.0
    value = series[-1] if series else None

    if value is None:
        return EMAState(p, None, price, Trend.UNDETERMINED, 0.0, series)

    alignment = Trend.BULLISH if price > value else Trend.BEARISH

    slope = 0.0
    prior = series[-2] if len(series) > 1 else None
    if prior is not None:
        slope = value - prior

    return EMAState(p, value, price, alignment, slope, series)


def ema_confluence(state: EMAState, bias: Trend) -> bool:
    """True when the EMA agrees with the structural bias.

    This is a tick on the expanded checklist, nothing more - disagreement never
    cancels a structurally valid setup.
    """
    if state.value is None or bias is Trend.UNDETERMINED:
        return False
    return state.alignment is bias
