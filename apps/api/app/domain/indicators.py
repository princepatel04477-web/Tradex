"""Pure Technical Analysis Indicator calculations (SRS FG-2 & Appendix D).

All algorithms implemented using Decimal/standard floating math and outputting Decimal quantities.
Warm-up constraints:
- SMA-200 requires at least 200 candles (returns None / fallback if fewer)
- MACD requires at least 35 candles
- RSI requires at least 15 candles
"""

from decimal import Decimal, ROUND_HALF_UP
import math
from typing import Dict, List, Optional, Tuple, NamedTuple


class IndicatorResult(NamedTuple):
    rsi_14: Optional[Decimal]
    macd_line: Optional[Decimal]
    macd_signal: Optional[Decimal]
    macd_hist: Optional[Decimal]
    bb_upper: Optional[Decimal]
    bb_middle: Optional[Decimal]
    bb_lower: Optional[Decimal]
    atr_14: Optional[Decimal]
    ema_9: Optional[Decimal]
    ema_21: Optional[Decimal]
    ema_50: Optional[Decimal]
    sma_200: Optional[Decimal]
    fib_levels: Dict[str, Decimal]
    macd_crossover: Optional[str]  # 'bullish', 'bearish', or None
    rsi_condition: str            # 'overbought', 'oversold', 'neutral'
    bb_squeeze: bool


def calculate_sma(prices: List[Decimal], period: int) -> Optional[Decimal]:
    if len(prices) < period:
        return None
    window = prices[-period:]
    return (sum(window) / Decimal(period)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def calculate_ema_series(prices: List[Decimal], period: int) -> List[Decimal]:
    if not prices:
        return []
    multiplier = Decimal("2") / (Decimal(period) + Decimal("1"))
    ema = prices[0]
    result = [ema]
    for p in prices[1:]:
        ema = (p - ema) * multiplier + ema
        result.append(ema)
    return result


def calculate_rsi(prices: List[Decimal], period: int = 14) -> Optional[Decimal]:
    if len(prices) <= period:
        return None

    gains: List[Decimal] = []
    losses: List[Decimal] = []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        if delta > Decimal("0"):
            gains.append(delta)
            losses.append(Decimal("0"))
        else:
            gains.append(Decimal("0"))
            losses.append(abs(delta))

    avg_gain = sum(gains[:period]) / Decimal(period)
    avg_loss = sum(losses[:period]) / Decimal(period)

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * Decimal(period - 1) + gains[i]) / Decimal(period)
        avg_loss = (avg_loss * Decimal(period - 1) + losses[i]) / Decimal(period)

    if avg_loss == Decimal("0"):
        return Decimal("100.00")
    rs = avg_gain / avg_loss
    rsi = Decimal("100.0") - (Decimal("100.0") / (Decimal("1.0") + rs))
    return rsi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_macd(
    prices: List[Decimal],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
    if len(prices) < slow + signal:
        return None, None, None

    fast_ema = calculate_ema_series(prices, fast)
    slow_ema = calculate_ema_series(prices, slow)
    macd_series = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_series = calculate_ema_series(macd_series, signal)

    macd_line = macd_series[-1].quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    signal_line = signal_series[-1].quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    hist = (macd_line - signal_line).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    return macd_line, signal_line, hist


def calculate_bollinger_bands(
    prices: List[Decimal],
    period: int = 20,
    std_dev_multiplier: Decimal = Decimal("2.0"),
) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
    if len(prices) < period:
        return None, None, None
    window = [float(p) for p in prices[-period:]]
    mean = sum(window) / period
    variance = sum((x - mean) ** 2 for x in window) / period
    std_dev = math.sqrt(variance)

    mid = Decimal(str(round(mean, 6)))
    offset = Decimal(str(round(float(std_dev_multiplier) * std_dev, 6)))
    upper = (mid + offset).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    lower = (mid - offset).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    return upper, mid, lower


def calculate_atr(
    highs: List[Decimal],
    lows: List[Decimal],
    closes: List[Decimal],
    period: int = 14,
) -> Optional[Decimal]:
    if len(closes) < period + 1:
        return None
    tr_list: List[Decimal] = []
    for i in range(1, len(closes)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr_list.append(max(hl, hc, lc))

    atr = sum(tr_list[-period:]) / Decimal(period)
    return atr.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def calculate_fibonacci_levels(high: Decimal, low: Decimal) -> Dict[str, Decimal]:
    diff = high - low
    return {
        "0.0% (Low)": low.quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP),
        "23.6%": (low + diff * Decimal("0.236")).quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP),
        "38.2%": (low + diff * Decimal("0.382")).quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP),
        "50.0%": (low + diff * Decimal("0.500")).quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP),
        "61.8%": (low + diff * Decimal("0.618")).quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP),
        "78.6%": (low + diff * Decimal("0.786")).quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP),
        "100.0% (High)": high.quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP),
    }


def compute_all_indicators(
    closes: List[Decimal],
    highs: List[Decimal],
    lows: List[Decimal],
) -> IndicatorResult:
    """Compute the complete indicator suite for a series of OHLC prices."""
    rsi = calculate_rsi(closes, 14)
    macd_l, macd_s, macd_h = calculate_macd(closes, 12, 26, 9)
    bb_u, bb_m, bb_l = calculate_bollinger_bands(closes, 20, Decimal("2.0"))
    atr = calculate_atr(highs, lows, closes, 14)

    ema_9 = calculate_ema_series(closes, 9)[-1] if len(closes) >= 9 else (closes[-1] if closes else None)
    ema_21 = calculate_ema_series(closes, 21)[-1] if len(closes) >= 21 else (closes[-1] if closes else None)
    ema_50 = calculate_ema_series(closes, 50)[-1] if len(closes) >= 50 else (closes[-1] if closes else None)
    sma_200 = calculate_sma(closes, 200) or (calculate_sma(closes, len(closes)) if closes else None)

    recent_high = max(highs[-50:]) if len(highs) >= 50 else (max(highs) if highs else Decimal("1.0"))
    recent_low = min(lows[-50:]) if len(lows) >= 50 else (min(lows) if lows else Decimal("1.0"))
    fibs = calculate_fibonacci_levels(recent_high, recent_low)

    # Detect conditions
    rsi_cond = "neutral"
    if rsi is not None:
        if rsi >= Decimal("70.0"):
            rsi_cond = "overbought"
        elif rsi <= Decimal("30.0"):
            rsi_cond = "oversold"

    bb_squeeze = False
    if bb_u and bb_m and bb_l and bb_m > Decimal("0"):
        width = (bb_u - bb_l) / bb_m
        bb_squeeze = width < Decimal("0.0050")

    macd_cross = None
    if len(closes) >= 36:
        prev_m, prev_s, _ = calculate_macd(closes[:-1], 12, 26, 9)
        if prev_m is not None and prev_s is not None and macd_l is not None and macd_s is not None:
            if prev_m <= prev_s and macd_l > macd_s:
                macd_cross = "bullish"
            elif prev_m >= prev_s and macd_l < macd_s:
                macd_cross = "bearish"

    return IndicatorResult(
        rsi_14=rsi,
        macd_line=macd_l,
        macd_signal=macd_s,
        macd_hist=macd_h,
        bb_upper=bb_u,
        bb_middle=bb_m,
        bb_lower=bb_l,
        atr_14=atr,
        ema_9=ema_9.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP) if ema_9 else None,
        ema_21=ema_21.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP) if ema_21 else None,
        ema_50=ema_50.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP) if ema_50 else None,
        sma_200=sma_200.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP) if sma_200 else None,
        fib_levels=fibs,
        macd_crossover=macd_cross,
        rsi_condition=rsi_cond,
        bb_squeeze=bb_squeeze,
    )
