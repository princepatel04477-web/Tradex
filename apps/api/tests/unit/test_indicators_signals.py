"""Unit tests for technical indicators and composite directional bias signals."""

from decimal import Decimal
from app.domain.indicators import compute_all_indicators, calculate_rsi, calculate_macd
from app.domain.signals import compute_composite_bias


def test_indicator_calculations():
    # 50 prices in steady uptrend
    closes = [Decimal(str(round(1.0800 + i * 0.0005, 5))) for i in range(50)]
    highs = [p + Decimal("0.0003") for p in closes]
    lows = [p - Decimal("0.0003") for p in closes]

    ind = compute_all_indicators(closes, highs, lows)
    assert ind.rsi_14 is not None
    assert ind.rsi_14 > Decimal("50.0")  # Uptrend RSI should be high
    assert ind.macd_line is not None
    assert ind.bb_upper is not None
    assert ind.bb_middle is not None
    assert ind.bb_lower is not None
    assert ind.bb_upper > ind.bb_middle > ind.bb_lower


def test_composite_bias_generation():
    closes = [Decimal(str(round(1.0800 + i * 0.0005, 5))) for i in range(60)]
    highs = [p + Decimal("0.0003") for p in closes]
    lows = [p - Decimal("0.0003") for p in closes]

    ind = compute_all_indicators(closes, highs, lows)
    current_p = closes[-1]
    bias = compute_composite_bias(current_p, ind, sentiment_score=Decimal("0.50"))

    assert bias.bias_label in ["Strong Bullish", "Bullish"]
    assert bias.bias_score > Decimal("0.20")
    assert len(bias.contributions) > 0
    assert len(bias.reasons) > 0
