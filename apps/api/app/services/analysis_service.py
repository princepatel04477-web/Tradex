"""Analysis Service: orchestrates indicator computation and composite directional bias (FG-2, AI-3)."""

from decimal import Decimal
from typing import List, Optional
from app.domain.indicators import compute_all_indicators
from app.domain.signals import compute_composite_bias
from app.schemas.market import IndicatorSnapshot, DirectionalBias, IndicatorBreakdownItem
from app.services.market_service import market_service


class AnalysisService:
    def get_indicators(self, symbol: str, timeframe: str = "H1") -> IndicatorSnapshot:
        candles = market_service.get_candles(symbol, timeframe, limit=250)
        closes = [Decimal(str(c.close)) for c in candles]
        highs = [Decimal(str(c.high)) for c in candles]
        lows = [Decimal(str(c.low)) for c in candles]

        ind = compute_all_indicators(closes, highs, lows)
        curr_price = closes[-1] if closes else Decimal("1.0")
        bias = compute_composite_bias(curr_price, ind)

        fib_dict = {k: float(v) for k, v in ind.fib_levels.items()}

        return IndicatorSnapshot(
            symbol=symbol,
            timeframe=timeframe,
            rsi_14=float(ind.rsi_14) if ind.rsi_14 is not None else 50.0,
            macd_line=float(ind.macd_line) if ind.macd_line is not None else 0.0,
            macd_signal=float(ind.macd_signal) if ind.macd_signal is not None else 0.0,
            macd_hist=float(ind.macd_hist) if ind.macd_hist is not None else 0.0,
            bb_upper=float(ind.bb_upper) if ind.bb_upper is not None else float(curr_price),
            bb_middle=float(ind.bb_middle) if ind.bb_middle is not None else float(curr_price),
            bb_lower=float(ind.bb_lower) if ind.bb_lower is not None else float(curr_price),
            atr_14=float(ind.atr_14) if ind.atr_14 is not None else 0.001,
            ema_9=float(ind.ema_9) if ind.ema_9 is not None else float(curr_price),
            ema_21=float(ind.ema_21) if ind.ema_21 is not None else float(curr_price),
            ema_50=float(ind.ema_50) if ind.ema_50 is not None else float(curr_price),
            sma_200=float(ind.sma_200) if ind.sma_200 is not None else float(curr_price),
            fib_levels=fib_dict,
            macd_crossover=ind.macd_crossover,
            rsi_condition=ind.rsi_condition,
            bb_squeeze=ind.bb_squeeze,
            bias_score=float(bias.bias_score),
            bias_label=bias.bias_label,
            bias_breakdown=[
                IndicatorBreakdownItem(
                    name=k,
                    contribution=float(v),
                    description=next((r for r in bias.reasons if k in r or r.startswith("Bullish") or r.startswith("Bearish")), "Contributing factor"),
                    direction="bullish" if v > 0 else ("bearish" if v < 0 else "neutral")
                )
                for k, v in bias.contributions.items()
            ],
            reasoning=bias.reasons,
        )

    def get_bias(self, symbol: str, timeframe: str = "H1") -> DirectionalBias:
        snapshot = self.get_indicators(symbol, timeframe)
        return DirectionalBias(
            symbol=symbol,
            timeframe=timeframe,
            bias=snapshot.bias_label,
            score=snapshot.bias_score,
            breakdown=snapshot.bias_breakdown,
            reasons=snapshot.reasoning,
            timestamp=snapshot.timestamp,
        )


analysis_service = AnalysisService()
