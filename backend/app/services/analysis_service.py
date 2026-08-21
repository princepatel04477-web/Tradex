import math
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Optional
from app.schemas.market import Candle, IndicatorSnapshot, CompositeBias
from app.services.market_service import market_service

class AnalysisService:
    def compute_indicators(self, symbol: str, timeframe: str = "H1") -> IndicatorSnapshot:
        symbol = symbol.replace("/", "_")
        candles = market_service.get_candles(symbol, timeframe, limit=250)
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        
        if len(closes) < 30:
            # Fallback if insufficient candles
            now = datetime.now(timezone.utc)
            return IndicatorSnapshot(
                symbol=symbol,
                timeframe=timeframe,
                rsi_14=50.0,
                macd_line=0.0,
                macd_signal=0.0,
                macd_histogram=0.0,
                bb_upper=closes[-1] * 1.01,
                bb_middle=closes[-1],
                bb_lower=closes[-1] * 0.99,
                atr_14=0.001,
                ema_9=closes[-1],
                ema_21=closes[-1],
                ema_50=closes[-1],
                sma_200=closes[-1],
                fib_levels={},
                timestamp=now
            )
            
        rsi_14 = self._calc_rsi(closes, 14)
        macd_line, macd_signal, macd_hist = self._calc_macd(closes, 12, 26, 9)
        bb_upper, bb_mid, bb_lower = self._calc_bollinger_bands(closes, 20, 2.0)
        atr_14 = self._calc_atr(highs, lows, closes, 14)
        ema_9 = self._calc_ema(closes, 9)
        ema_21 = self._calc_ema(closes, 21)
        ema_50 = self._calc_ema(closes, 50)
        sma_200 = self._calc_sma(closes, min(200, len(closes)))
        
        # Fibonacci levels from recent swing high & low
        recent_high = max(highs[-50:])
        recent_low = min(lows[-50:])
        diff = recent_high - recent_low
        fib_levels = {
            "0.0% (Low)": round(recent_low, 4),
            "23.6%": round(recent_low + diff * 0.236, 4),
            "38.2%": round(recent_low + diff * 0.382, 4),
            "50.0%": round(recent_low + diff * 0.500, 4),
            "61.8%": round(recent_low + diff * 0.618, 4),
            "78.6%": round(recent_low + diff * 0.786, 4),
            "100.0% (High)": round(recent_high, 4),
        }
        
        # Crossover & conditions
        macd_crossover = None
        if len(closes) > 2:
            prev_macd, prev_sig, _ = self._calc_macd(closes[:-1], 12, 26, 9)
            if prev_macd < prev_sig and macd_line > macd_signal:
                macd_crossover = "bullish"
            elif prev_macd > prev_sig and macd_line < macd_signal:
                macd_crossover = "bearish"
                
        rsi_cond = "neutral"
        if rsi_14 > 70:
            rsi_cond = "overbought"
        elif rsi_14 < 30:
            rsi_cond = "oversold"
            
        bb_width = (bb_upper - bb_lower) / bb_mid if bb_mid != 0 else 0
        bb_squeeze = bb_width < 0.005
        
        return IndicatorSnapshot(
            symbol=symbol,
            timeframe=timeframe,
            rsi_14=round(rsi_14, 2),
            macd_line=round(macd_line, 5),
            macd_signal=round(macd_signal, 5),
            macd_histogram=round(macd_hist, 5),
            bb_upper=round(bb_upper, 4),
            bb_middle=round(bb_mid, 4),
            bb_lower=round(bb_lower, 4),
            atr_14=round(atr_14, 5),
            ema_9=round(ema_9, 4),
            ema_21=round(ema_21, 4),
            ema_50=round(ema_50, 4),
            sma_200=round(sma_200, 4),
            fib_levels=fib_levels,
            macd_crossover=macd_crossover,
            rsi_condition=rsi_cond,
            bb_squeeze=bb_squeeze,
            timestamp=datetime.now(timezone.utc)
        )

    def compute_composite_bias(self, symbol: str, timeframe: str = "H1", sentiment_score: float = 0.0) -> CompositeBias:
        snapshot = self.compute_indicators(symbol, timeframe)
        pair = market_service.get_pair(symbol)
        price = pair.ask if pair else snapshot.bb_middle
        
        contributions = {}
        reasons = []
        
        # 1. EMA-9 vs EMA-21 (Weight 0.25)
        if snapshot.ema_9 > snapshot.ema_21:
            contributions["EMA 9/21 Alignment"] = 0.25
            reasons.append(f"Bullish: Short-term momentum (EMA-9: {snapshot.ema_9}) is trading above EMA-21 ({snapshot.ema_21})")
        else:
            contributions["EMA 9/21 Alignment"] = -0.25
            reasons.append(f"Bearish: Short-term momentum (EMA-9: {snapshot.ema_9}) is trading below EMA-21 ({snapshot.ema_21})")
            
        # 2. Price vs SMA-200 (Weight 0.20)
        if price > snapshot.sma_200:
            contributions["Price vs SMA-200"] = 0.20
            reasons.append(f"Bullish: Price ({price}) is above the 200-period baseline ({snapshot.sma_200})")
        else:
            contributions["Price vs SMA-200"] = -0.20
            reasons.append(f"Bearish: Price ({price}) is below the 200-period baseline ({snapshot.sma_200})")
            
        # 3. MACD Histogram (Weight 0.20)
        if snapshot.macd_histogram > 0:
            contributions["MACD Momentum"] = 0.20
            reasons.append(f"Bullish: MACD histogram is positive (+{snapshot.macd_histogram})")
        else:
            contributions["MACD Momentum"] = -0.20
            reasons.append(f"Bearish: MACD histogram is negative ({snapshot.macd_histogram})")
            
        # 4. RSI-14 (Weight 0.15)
        if 50 <= snapshot.rsi_14 < 70:
            contributions["RSI Oscillator"] = 0.15
            reasons.append(f"Bullish: RSI-14 at {snapshot.rsi_14} shows healthy bullish momentum without overbought stress")
        elif snapshot.rsi_14 >= 70:
            contributions["RSI Oscillator"] = 0.05
            reasons.append(f"Neutral/Caution: RSI-14 at {snapshot.rsi_14} is in overbought territory (>70)")
        elif 30 < snapshot.rsi_14 < 50:
            contributions["RSI Oscillator"] = -0.15
            reasons.append(f"Bearish: RSI-14 at {snapshot.rsi_14} indicates bearish momentum")
        else:
            contributions["RSI Oscillator"] = -0.05
            reasons.append(f"Neutral/Caution: RSI-14 at {snapshot.rsi_14} is in oversold territory (<30)")
            
        # 5. Bollinger Position (Weight 0.10)
        if price >= snapshot.bb_middle:
            contributions["Bollinger Band Position"] = 0.10
            reasons.append(f"Bullish: Price is in the upper Bollinger Band section")
        else:
            contributions["Bollinger Band Position"] = -0.10
            reasons.append(f"Bearish: Price is in the lower Bollinger Band section")
            
        # 6. Sentiment Score (Weight 0.10)
        if sentiment_score > 0.2:
            contributions["Global News Sentiment"] = 0.10
            reasons.append(f"Bullish: Positive market news sentiment score ({sentiment_score:+.2f})")
        elif sentiment_score < -0.2:
            contributions["Global News Sentiment"] = -0.10
            reasons.append(f"Bearish: Negative market news sentiment score ({sentiment_score:+.2f})")
        else:
            contributions["Global News Sentiment"] = 0.0
            reasons.append(f"Neutral: News sentiment score is balanced ({sentiment_score:+.2f})")

        total_score = sum(contributions.values())
        total_score = max(-1.0, min(1.0, total_score))
        
        # SRS 6.3 score thresholds
        if total_score >= 0.6:
            label = "Strong Bullish"
        elif total_score >= 0.2:
            label = "Bullish"
        elif total_score > -0.2:
            label = "Neutral"
        elif total_score > -0.6:
            label = "Bearish"
        else:
            label = "Strong Bearish"
            
        return CompositeBias(
            symbol=symbol,
            timeframe=timeframe,
            bias=label,
            score=round(total_score, 2),
            indicator_contributions=contributions,
            reasons=reasons,
            timestamp=datetime.now(timezone.utc)
        )

    def _calc_sma(self, data: List[float], period: int) -> float:
        if len(data) < period:
            return data[-1]
        return float(np.mean(data[-period:]))

    def _calc_ema(self, data: List[float], period: int) -> float:
        if len(data) == 0:
            return 0.0
        multiplier = 2 / (period + 1)
        ema = data[0]
        for val in data[1:]:
            ema = (val - ema) * multiplier + ema
        return float(ema)

    def _calc_rsi(self, data: List[float], period: int = 14) -> float:
        if len(data) <= period:
            return 50.0
        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return float(100.0 - (100.0 / (1.0 + rs)))

    def _calc_macd(self, data: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = self._calc_ema(data, fast)
        ema_slow = self._calc_ema(data, slow)
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line over recent macd points
        macd_series = []
        for i in range(max(1, len(data) - 20), len(data) + 1):
            sub = data[:i]
            macd_series.append(self._calc_ema(sub, fast) - self._calc_ema(sub, slow))
            
        macd_signal = self._calc_ema(macd_series, signal)
        macd_hist = macd_line - macd_signal
        return macd_line, macd_signal, macd_hist

    def _calc_bollinger_bands(self, data: List[float], period: int = 20, num_std: float = 2.0):
        if len(data) < period:
            mid = data[-1]
            return mid * 1.01, mid, mid * 0.99
        sub = data[-period:]
        mid = float(np.mean(sub))
        std = float(np.std(sub))
        upper = mid + (num_std * std)
        lower = mid - (num_std * std)
        return upper, mid, lower

    def _calc_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        if len(closes) < 2:
            return 0.0010
        tr_list = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_list.append(tr)
        return float(np.mean(tr_list[-period:]))

# Global singleton
analysis_service = AnalysisService()
