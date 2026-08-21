import random
import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from app.schemas.market import CurrencyPair, Tick, Candle, MarketSession, MarketSessionOverview

PAIRS_CONFIG = [
    # Majors
    {"symbol": "EUR_USD", "name": "EUR/USD", "base": "EUR", "quote": "USD", "pip_decimals": 4, "category": "major", "base_price": 1.0850, "spread_pips": 1.2},
    {"symbol": "GBP_USD", "name": "GBP/USD", "base": "GBP", "quote": "USD", "pip_decimals": 4, "category": "major", "base_price": 1.2720, "spread_pips": 1.5},
    {"symbol": "USD_JPY", "name": "USD/JPY", "base": "USD", "quote": "JPY", "pip_decimals": 2, "category": "major", "base_price": 154.50, "spread_pips": 1.3},
    {"symbol": "USD_CHF", "name": "USD/CHF", "base": "USD", "quote": "CHF", "pip_decimals": 4, "category": "major", "base_price": 0.8980, "spread_pips": 1.6},
    {"symbol": "AUD_USD", "name": "AUD/USD", "base": "AUD", "quote": "USD", "pip_decimals": 4, "category": "major", "base_price": 0.6580, "spread_pips": 1.4},
    {"symbol": "NZD_USD", "name": "NZD/USD", "base": "NZD", "quote": "USD", "pip_decimals": 4, "category": "major", "base_price": 0.6020, "spread_pips": 1.8},
    {"symbol": "USD_CAD", "name": "USD/CAD", "base": "USD", "quote": "CAD", "pip_decimals": 4, "category": "major", "base_price": 1.3650, "spread_pips": 1.5},
    # Minors
    {"symbol": "EUR_GBP", "name": "EUR/GBP", "base": "EUR", "quote": "GBP", "pip_decimals": 4, "category": "minor", "base_price": 0.8530, "spread_pips": 1.7},
    {"symbol": "EUR_JPY", "name": "EUR/JPY", "base": "EUR", "quote": "JPY", "pip_decimals": 2, "category": "minor", "base_price": 167.60, "spread_pips": 1.8},
    {"symbol": "GBP_JPY", "name": "GBP/JPY", "base": "GBP", "quote": "JPY", "pip_decimals": 2, "category": "minor", "base_price": 196.50, "spread_pips": 2.1},
    {"symbol": "AUD_JPY", "name": "AUD/JPY", "base": "AUD", "quote": "JPY", "pip_decimals": 2, "category": "minor", "base_price": 101.60, "spread_pips": 2.0},
    {"symbol": "EUR_AUD", "name": "EUR/AUD", "base": "EUR", "quote": "AUD", "pip_decimals": 4, "category": "minor", "base_price": 1.6480, "spread_pips": 2.2},
    # Exotics
    {"symbol": "USD_INR", "name": "USD/INR", "base": "USD", "quote": "INR", "pip_decimals": 4, "category": "exotic", "base_price": 83.9500, "spread_pips": 3.5},
    {"symbol": "USD_SGD", "name": "USD/SGD", "base": "USD", "quote": "SGD", "pip_decimals": 4, "category": "exotic", "base_price": 1.3480, "spread_pips": 2.5},
    {"symbol": "USD_MXN", "name": "USD/MXN", "base": "USD", "quote": "MXN", "pip_decimals": 4, "category": "exotic", "base_price": 18.2500, "spread_pips": 5.0},
]

class MarketService:
    def __init__(self):
        self.prices: Dict[str, Dict] = {}
        self.candles_cache: Dict[str, Dict[str, List[Candle]]] = {}
        self._init_market_state()

    def _init_market_state(self):
        for cfg in PAIRS_CONFIG:
            symbol = cfg["symbol"]
            pip_size = 0.01 if cfg["pip_decimals"] == 2 else 0.0001
            mid_price = cfg["base_price"]
            half_spread = (cfg["spread_pips"] * pip_size) / 2.0
            bid = round(mid_price - half_spread, cfg["pip_decimals"] + 1)
            ask = round(mid_price + half_spread, cfg["pip_decimals"] + 1)
            
            self.prices[symbol] = {
                "config": cfg,
                "mid": mid_price,
                "bid": bid,
                "ask": ask,
                "pip_size": pip_size,
                "high_24h": round(mid_price * 1.006, cfg["pip_decimals"] + 1),
                "low_24h": round(mid_price * 0.994, cfg["pip_decimals"] + 1),
                "open_24h": mid_price,
                "last_update": datetime.now(timezone.utc)
            }
            
            self.candles_cache[symbol] = {}
            for tf in ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]:
                self.candles_cache[symbol][tf] = self._generate_historical_candles(symbol, tf)

    def get_all_pairs(self) -> List[CurrencyPair]:
        result = []
        now = datetime.now(timezone.utc)
        for symbol, data in self.prices.items():
            cfg = data["config"]
            mid = data["mid"]
            open_24h = data["open_24h"]
            change_pct = round(((mid - open_24h) / open_24h) * 100, 2)
            spread_pips = cfg["spread_pips"]

            result.append(CurrencyPair(
                symbol=symbol,
                name=cfg["name"],
                base_currency=cfg["base"],
                quote_currency=cfg["quote"],
                pip_decimal_places=cfg["pip_decimals"],
                category=cfg["category"],
                pip_size=data["pip_size"],
                bid=data["bid"],
                ask=data["ask"],
                spread_pips=spread_pips,
                change_24h_pct=change_pct,
                high_24h=data["high_24h"],
                low_24h=data["low_24h"],
                timestamp=now
            ))
        return result

    def get_pair(self, symbol: str) -> Optional[CurrencyPair]:
        all_pairs = self.get_all_pairs()
        for p in all_pairs:
            if p.symbol == symbol or p.symbol.replace("_", "/") == symbol:
                return p
        return None

    def update_ticks(self) -> Dict[str, Tick]:
        """Simulate realistic tick movement for all pairs."""
        now = datetime.now(timezone.utc)
        ticks = {}
        for symbol, data in self.prices.items():
            cfg = data["config"]
            pip_size = data["pip_size"]
            pip_decimals = cfg["pip_decimals"]
            
            # Small Brownian motion shift (-2 to +2 pips)
            pip_shift = random.uniform(-1.5, 1.5) * pip_size
            new_mid = round(data["mid"] + pip_shift, pip_decimals + 1)
            
            half_spread = (cfg["spread_pips"] * pip_size) / 2.0
            bid = round(new_mid - half_spread, pip_decimals + 1)
            ask = round(new_mid + half_spread, pip_decimals + 1)
            
            data["mid"] = new_mid
            data["bid"] = bid
            data["ask"] = ask
            data["high_24h"] = max(data["high_24h"], new_mid)
            data["low_24h"] = min(data["low_24h"], new_mid)
            data["last_update"] = now
            
            ticks[symbol] = Tick(
                symbol=symbol,
                bid=bid,
                ask=ask,
                spread_pips=cfg["spread_pips"],
                timestamp=now
            )
            
            # Also update the latest M1 candle close
            if symbol in self.candles_cache and "M1" in self.candles_cache[symbol]:
                m1_candles = self.candles_cache[symbol]["M1"]
                if m1_candles:
                    latest = m1_candles[-1]
                    latest.close = new_mid
                    latest.high = max(latest.high, new_mid)
                    latest.low = min(latest.low, new_mid)

        return ticks

    def get_candles(self, symbol: str, timeframe: str = "H1", limit: int = 100) -> List[Candle]:
        symbol = symbol.replace("/", "_")
        if symbol not in self.candles_cache or timeframe not in self.candles_cache[symbol]:
            return self._generate_historical_candles(symbol, timeframe, count=limit)
        return self.candles_cache[symbol][timeframe][-limit:]

    def _generate_historical_candles(self, symbol: str, timeframe: str, count: int = 200) -> List[Candle]:
        cfg = next((c for c in PAIRS_CONFIG if c["symbol"] == symbol), PAIRS_CONFIG[0])
        pip_decimals = cfg["pip_decimals"]
        pip_size = 0.01 if pip_decimals == 2 else 0.0001
        base_price = cfg["base_price"]
        
        minutes_map = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
        step_minutes = minutes_map.get(timeframe, 60)
        
        now = datetime.now(timezone.utc)
        candles = []
        curr_price = base_price
        
        for i in range(count, 0, -1):
            c_time = now - timedelta(minutes=i * step_minutes)
            volatility = random.uniform(5, 25) * pip_size
            change = random.uniform(-volatility, volatility)
            
            c_open = round(curr_price, pip_decimals + 1)
            c_close = round(curr_price + change, pip_decimals + 1)
            c_high = round(max(c_open, c_close) + random.uniform(0, volatility * 0.8), pip_decimals + 1)
            c_low = round(min(c_open, c_close) - random.uniform(0, volatility * 0.8), pip_decimals + 1)
            
            # Satisfy DI-1: low <= open/close <= high
            c_high = max(c_high, c_open, c_close)
            c_low = min(c_low, c_open, c_close)
            
            volume = random.randint(300, 4500)
            
            candles.append(Candle(
                symbol=symbol,
                timeframe=timeframe,
                open_time=c_time,
                open=c_open,
                high=c_high,
                low=c_low,
                close=c_close,
                volume=volume
            ))
            curr_price = c_close
            
        return candles

    def get_market_sessions(self) -> MarketSessionOverview:
        now = datetime.now(timezone.utc)
        cur_hour = now.hour + (now.minute / 60.0)
        
        # Session UTC hours
        sessions = [
            MarketSession(name="Sydney", is_active=(21.0 <= cur_hour or cur_hour < 6.0), open_utc="21:00", close_utc="06:00", description="Lower volatility; AUD/NZD pairs active"),
            MarketSession(name="Tokyo", is_active=(0.0 <= cur_hour < 9.0), open_utc="00:00", close_utc="09:00", description="JPY pairs active; range-bound trading"),
            MarketSession(name="London", is_active=(7.0 <= cur_hour < 16.0), open_utc="07:00", close_utc="16:00", description="Highest liquidity & volume window"),
            MarketSession(name="New York", is_active=(12.0 <= cur_hour < 21.0), open_utc="12:00", close_utc="21:00", description="High volatility; USD pairs dominant")
        ]
        
        overlap = None
        if 12.0 <= cur_hour < 16.0:
            overlap = "London-New York Overlap (Peak Volatility & Liquidity Window)"
        elif 0.0 <= cur_hour < 6.0:
            overlap = "Sydney-Tokyo Overlap"
        
        return MarketSessionOverview(
            sessions=sessions,
            active_overlap=overlap,
            current_utc_time=now.strftime("%Y-%m-%d %H:%M:%S UTC")
        )

# Global singleton instance
market_service = MarketService()
