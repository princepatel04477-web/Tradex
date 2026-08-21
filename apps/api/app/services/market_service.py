"""Market Service: manages live tick streaming, OHLCV candles, and session clock (FG-1)."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
import random

from app.domain.pips import get_pip_size, price_diff_to_pips
from app.domain.sessions import get_market_sessions_overview
from app.core.config import settings
from app.providers.base import MarketDataProvider, MarketTick
from app.providers.fakes import FakeMarketDataProvider, BASE_PRICES
from app.providers.yfinance_provider import YahooFinanceProvider
from app.providers.finnhub import FinnhubProvider
from app.schemas.market import Candle, CurrencyPair, MarketSessionOverview, Tick

PAIRS_METADATA = [
    {"symbol": "EUR_USD", "name": "EUR/USD", "base": "EUR", "quote": "USD", "pip_decimals": 4, "category": "major", "base_price": Decimal("1.0850"), "spread_pips": Decimal("1.2")},
    {"symbol": "GBP_USD", "name": "GBP/USD", "base": "GBP", "quote": "USD", "pip_decimals": 4, "category": "major", "base_price": Decimal("1.2720"), "spread_pips": Decimal("1.5")},
    {"symbol": "USD_JPY", "name": "USD/JPY", "base": "USD", "quote": "JPY", "pip_decimals": 2, "category": "major", "base_price": Decimal("154.50"), "spread_pips": Decimal("1.3")},
    {"symbol": "USD_CHF", "name": "USD/CHF", "base": "USD", "quote": "CHF", "pip_decimals": 4, "category": "major", "base_price": Decimal("0.8980"), "spread_pips": Decimal("1.6")},
    {"symbol": "AUD_USD", "name": "AUD/USD", "base": "AUD", "quote": "USD", "pip_decimals": 4, "category": "major", "base_price": Decimal("0.6580"), "spread_pips": Decimal("1.4")},
    {"symbol": "NZD_USD", "name": "NZD/USD", "base": "NZD", "quote": "USD", "pip_decimals": 4, "category": "major", "base_price": Decimal("0.6020"), "spread_pips": Decimal("1.8")},
    {"symbol": "USD_CAD", "name": "USD/CAD", "base": "USD", "quote": "CAD", "pip_decimals": 4, "category": "major", "base_price": Decimal("1.3650"), "spread_pips": Decimal("1.5")},
    {"symbol": "EUR_GBP", "name": "EUR/GBP", "base": "EUR", "quote": "GBP", "pip_decimals": 4, "category": "minor", "base_price": Decimal("0.8530"), "spread_pips": Decimal("1.7")},
    {"symbol": "EUR_JPY", "name": "EUR/JPY", "base": "EUR", "quote": "JPY", "pip_decimals": 2, "category": "minor", "base_price": Decimal("167.60"), "spread_pips": Decimal("1.8")},
    {"symbol": "GBP_JPY", "name": "GBP/JPY", "base": "GBP", "quote": "JPY", "pip_decimals": 2, "category": "minor", "base_price": Decimal("196.50"), "spread_pips": Decimal("2.1")},
    {"symbol": "AUD_JPY", "name": "AUD/JPY", "base": "AUD", "quote": "JPY", "pip_decimals": 2, "category": "minor", "base_price": Decimal("101.60"), "spread_pips": Decimal("2.0")},
    {"symbol": "EUR_AUD", "name": "EUR/AUD", "base": "EUR", "quote": "AUD", "pip_decimals": 4, "category": "minor", "base_price": Decimal("1.6480"), "spread_pips": Decimal("2.2")},
    {"symbol": "USD_INR", "name": "USD/INR", "base": "USD", "quote": "INR", "pip_decimals": 4, "category": "exotic", "base_price": Decimal("83.9500"), "spread_pips": Decimal("3.5")},
    {"symbol": "USD_SGD", "name": "USD/SGD", "base": "USD", "quote": "SGD", "pip_decimals": 4, "category": "exotic", "base_price": Decimal("1.3480"), "spread_pips": Decimal("2.5")},
    {"symbol": "USD_MXN", "name": "USD/MXN", "base": "USD", "quote": "MXN", "pip_decimals": 4, "category": "exotic", "base_price": Decimal("18.2500"), "spread_pips": Decimal("5.0")},
]


class MarketService:
    def __init__(self, provider: Optional[MarketDataProvider] = None):
        if provider:
            self.provider = provider
        elif settings.MARKET_DATA_PROVIDER == "yahoo":
            self.provider = YahooFinanceProvider()
        elif settings.MARKET_DATA_PROVIDER == "finnhub":
            self.provider = FinnhubProvider()
        else:
            self.provider = FakeMarketDataProvider()
        self.prices: Dict[str, dict] = {}
        self.candles_cache: Dict[str, Dict[str, List[Candle]]] = {}
        self._init_market_state()

    def _init_market_state(self):
        for cfg in PAIRS_METADATA:
            sym = cfg["symbol"]
            pip_sz = get_pip_size(sym)
            mid = cfg["base_price"]
            spread = cfg["spread_pips"] * pip_sz
            bid = mid - (spread / Decimal("2"))
            ask = mid + (spread / Decimal("2"))
            self.prices[sym] = {
                "config": cfg,
                "mid": mid,
                "bid": bid,
                "ask": ask,
                "pip_size": pip_sz,
                "high_24h": mid * Decimal("1.006"),
                "low_24h": mid * Decimal("0.994"),
                "open_24h": mid,
                "last_update": datetime.now(timezone.utc),
            }
            self.candles_cache[sym] = {}
            for tf in ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]:
                self.candles_cache[sym][tf] = self._generate_seed_candles(sym, tf)

    def get_all_pairs(self) -> List[CurrencyPair]:
        result = []
        now = datetime.now(timezone.utc)
        for sym, d in self.prices.items():
            cfg = d["config"]
            mid = d["mid"]
            open_24h = d["open_24h"]
            chg = round(float((mid - open_24h) / open_24h * 100), 2)
            result.append(
                CurrencyPair(
                    symbol=sym,
                    name=cfg["name"],
                    base_currency=cfg["base"],
                    quote_currency=cfg["quote"],
                    pip_decimal_places=cfg["pip_decimals"],
                    category=cfg["category"],
                    pip_size=float(d["pip_size"]),
                    bid=float(d["bid"]),
                    ask=float(d["ask"]),
                    spread_pips=float(cfg["spread_pips"]),
                    change_24h_pct=chg,
                    high_24h=float(d["high_24h"]),
                    low_24h=float(d["low_24h"]),
                    timestamp=now,
                )
            )
        return result

    def get_pair(self, symbol: str) -> Optional[CurrencyPair]:
        all_p = self.get_all_pairs()
        sym_norm = symbol.replace("/", "_")
        for p in all_p:
            if p.symbol == sym_norm:
                return p
        return None

    def update_ticks(self) -> Dict[str, Tick]:
        now = datetime.now(timezone.utc)
        ticks = {}
        for sym, d in self.prices.items():
            cfg = d["config"]
            pip_sz = d["pip_size"]
            shift = Decimal(str(round(random.uniform(-1.2, 1.2), 4))) * pip_sz
            new_mid = d["mid"] + shift
            half_spread = (cfg["spread_pips"] * pip_sz) / Decimal("2")
            bid = new_mid - half_spread
            ask = new_mid + half_spread
            d["mid"] = new_mid
            d["bid"] = bid
            d["ask"] = ask
            d["high_24h"] = max(d["high_24h"], new_mid)
            d["low_24h"] = min(d["low_24h"], new_mid)
            d["last_update"] = now

            ticks[sym] = Tick(
                symbol=sym,
                bid=float(bid),
                ask=float(ask),
                spread_pips=float(cfg["spread_pips"]),
                timestamp=now,
            )
        return ticks

    def get_candles(self, symbol: str, timeframe: str = "H1", limit: int = 100) -> List[Candle]:
        sym = symbol.replace("/", "_")
        if sym not in self.candles_cache or timeframe not in self.candles_cache[sym]:
            return self._generate_seed_candles(sym, timeframe, count=limit)
        return self.candles_cache[sym][timeframe][-limit:]

    def _generate_seed_candles(self, symbol: str, timeframe: str, count: int = 200) -> List[Candle]:
        cfg = next((c for c in PAIRS_METADATA if c["symbol"] == symbol), PAIRS_METADATA[0])
        pip_sz = float(get_pip_size(symbol))
        base_p = float(cfg["base_price"])
        now = datetime.now(timezone.utc)
        candles = []
        curr = base_p

        minutes_map = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
        step = minutes_map.get(timeframe, 60)

        for i in range(count, 0, -1):
            t = now - (count - i) * (now - (now - (now - now)))  # time step
            vol = random.uniform(5, 20) * pip_sz
            chg = random.uniform(-vol, vol)
            c_open = curr
            c_close = curr + chg
            c_high = max(c_open, c_close) + random.uniform(0, vol * 0.7)
            c_low = min(c_open, c_close) - random.uniform(0, vol * 0.7)

            candles.append(
                Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    open_time=now - (i * (now - (now - (now - now)))),
                    open=round(c_open, cfg["pip_decimals"] + 1),
                    high=round(c_high, cfg["pip_decimals"] + 1),
                    low=round(c_low, cfg["pip_decimals"] + 1),
                    close=round(c_close, cfg["pip_decimals"] + 1),
                    volume=random.randint(500, 3000),
                )
            )
            curr = c_close
        return candles

    def get_market_sessions(self) -> MarketSessionOverview:
        data = get_market_sessions_overview()
        from app.schemas.market import MarketSession
        return MarketSessionOverview(
            sessions=[MarketSession(**s) for s in data["sessions"]],
            active_overlap=data["active_overlap"],
            current_utc_time=data["current_utc_time"],
        )


market_service = MarketService()
