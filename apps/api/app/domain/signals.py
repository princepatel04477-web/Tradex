"""Composite directional bias signal generation (SRS §6.3, AI-3.1, AI-3.2, AI-3.3).

Rule-based ensemble:
- EMA-9 vs EMA-21 (Weight 0.25)
- Price vs SMA-200 (Weight 0.20)
- MACD Histogram (Weight 0.20)
- RSI-14 (Weight 0.15)
- Bollinger Band Position (Weight 0.10)
- Sentiment Score (Weight 0.10)

Score mapping:
- >= +0.60: Strong Bullish
- +0.20 to +0.60: Bullish
- -0.20 to +0.20: Neutral
- -0.60 to -0.20: Bearish
- <= -0.60: Strong Bearish
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, NamedTuple, Optional
from app.domain.indicators import IndicatorResult


DEFAULT_WEIGHTS = {
    "ema_cross": Decimal("0.25"),
    "sma_200": Decimal("0.20"),
    "macd_hist": Decimal("0.20"),
    "rsi_14": Decimal("0.15"),
    "bb_position": Decimal("0.10"),
    "sentiment": Decimal("0.10"),
}


class CompositeBiasResult(NamedTuple):
    bias_label: str
    bias_score: Decimal
    contributions: Dict[str, Decimal]
    reasons: List[str]


def compute_composite_bias(
    current_price: Decimal,
    indicators: IndicatorResult,
    sentiment_score: Decimal = Decimal("0.0"),
    weights: Optional[Dict[str, Decimal]] = None,
) -> CompositeBiasResult:
    """Compute explainable composite directional bias from indicators and sentiment."""
    w = weights or DEFAULT_WEIGHTS
    contributions: Dict[str, Decimal] = {}
    reasons: List[str] = []

    # 1. EMA-9 vs EMA-21
    if indicators.ema_9 and indicators.ema_21:
        if indicators.ema_9 > indicators.ema_21:
            contributions["EMA 9/21 Alignment"] = w.get("ema_cross", Decimal("0.25"))
            reasons.append(f"Bullish: Short-term EMA-9 ({indicators.ema_9}) trades above EMA-21 ({indicators.ema_21})")
        else:
            contributions["EMA 9/21 Alignment"] = -w.get("ema_cross", Decimal("0.25"))
            reasons.append(f"Bearish: Short-term EMA-9 ({indicators.ema_9}) trades below EMA-21 ({indicators.ema_21})")
    else:
        contributions["EMA 9/21 Alignment"] = Decimal("0.00")

    # 2. Price vs SMA-200
    if indicators.sma_200:
        if current_price > indicators.sma_200:
            contributions["Price vs SMA-200"] = w.get("sma_200", Decimal("0.20"))
            reasons.append(f"Bullish: Price ({current_price}) is above 200-period baseline ({indicators.sma_200})")
        else:
            contributions["Price vs SMA-200"] = -w.get("sma_200", Decimal("0.20"))
            reasons.append(f"Bearish: Price ({current_price}) is below 200-period baseline ({indicators.sma_200})")
    else:
        contributions["Price vs SMA-200"] = Decimal("0.00")

    # 3. MACD Histogram
    if indicators.macd_hist is not None:
        if indicators.macd_hist > Decimal("0"):
            contributions["MACD Momentum"] = w.get("macd_hist", Decimal("0.20"))
            reasons.append(f"Bullish: MACD histogram is positive (+{indicators.macd_hist})")
        else:
            contributions["MACD Momentum"] = -w.get("macd_hist", Decimal("0.20"))
            reasons.append(f"Bearish: MACD histogram is negative ({indicators.macd_hist})")
    else:
        contributions["MACD Momentum"] = Decimal("0.00")

    # 4. RSI-14
    if indicators.rsi_14 is not None:
        if Decimal("50.0") <= indicators.rsi_14 < Decimal("70.0"):
            contributions["RSI Oscillator"] = w.get("rsi_14", Decimal("0.15"))
            reasons.append(f"Bullish: RSI-14 ({indicators.rsi_14}) demonstrates solid upward momentum")
        elif indicators.rsi_14 >= Decimal("70.0"):
            contributions["RSI Oscillator"] = Decimal("0.05")
            reasons.append(f"Caution: RSI-14 ({indicators.rsi_14}) is in overbought territory (>70)")
        elif Decimal("30.0") < indicators.rsi_14 < Decimal("50.0"):
            contributions["RSI Oscillator"] = -w.get("rsi_14", Decimal("0.15"))
            reasons.append(f"Bearish: RSI-14 ({indicators.rsi_14}) indicates downward pressure")
        else:
            contributions["RSI Oscillator"] = -Decimal("0.05")
            reasons.append(f"Caution: RSI-14 ({indicators.rsi_14}) is in oversold territory (<30)")
    else:
        contributions["RSI Oscillator"] = Decimal("0.00")

    # 5. Bollinger Band Position
    if indicators.bb_middle:
        if current_price >= indicators.bb_middle:
            contributions["Bollinger Band Position"] = w.get("bb_position", Decimal("0.10"))
            reasons.append("Bullish: Price trades in the upper Bollinger Band half")
        else:
            contributions["Bollinger Band Position"] = -w.get("bb_position", Decimal("0.10"))
            reasons.append("Bearish: Price trades in the lower Bollinger Band half")
    else:
        contributions["Bollinger Band Position"] = Decimal("0.00")

    # 6. Global News Sentiment Score
    if sentiment_score > Decimal("0.20"):
        contributions["News Sentiment"] = w.get("sentiment", Decimal("0.10"))
        reasons.append(f"Bullish: Macro news sentiment is positive (+{sentiment_score})")
    elif sentiment_score < -Decimal("0.20"):
        contributions["News Sentiment"] = -w.get("sentiment", Decimal("0.10"))
        reasons.append(f"Bearish: Macro news sentiment is negative ({sentiment_score})")
    else:
        contributions["News Sentiment"] = Decimal("0.00")
        reasons.append(f"Neutral: Macro news sentiment is balanced ({sentiment_score})")

    total_score = sum(contributions.values(), Decimal("0.00"))
    total_score = max(Decimal("-1.00"), min(Decimal("1.00"), total_score))
    total_score = total_score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if total_score >= Decimal("0.60"):
        label = "Strong Bullish"
    elif total_score >= Decimal("0.20"):
        label = "Bullish"
    elif total_score > Decimal("-0.20"):
        label = "Neutral"
    elif total_score > Decimal("-0.60"):
        label = "Bearish"
    else:
        label = "Strong Bearish"

    return CompositeBiasResult(
        bias_label=label,
        bias_score=total_score,
        contributions=contributions,
        reasons=reasons,
    )
