"""Market Service: manages live tick streaming, OHLCV candles, and session clock (FG-1)."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional
import random

from app.domain.pips import get_pip_size, price_diff_to_pips
from app.domain.sessions import get_market_sessions_overview
from app.core.config import settings
from app.core.errors import ProviderUnavailableError
from app.core.logging import logger
from app.providers.base import MarketDataProvider
from app.providers.live_feed import OHLC, LiveDataUnavailable, live_feed
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
    """Market state backed by real FX quotes and candles (Yahoo Finance, Twelve Data fallback).

    ``prices`` holds the latest real mid per pair; bid/ask are the mid +/- the pair's typical retail spread.
    When ``settings.LIVE_MARKET_DATA`` is off (offline test runs) prices stay at the registry reference
    levels and candles come from a local generator.
    """

    def __init__(self, provider: Optional[MarketDataProvider] = None, live: Optional[bool] = None):
        self.provider = provider
        self.live = settings.LIVE_MARKET_DATA if live is None else live
        self.prices: Dict[str, dict] = {}
        self.candles_cache: Dict[str, Dict[str, List[Candle]]] = {}
        self.last_quote_refresh: Optional[datetime] = None
        self.last_quote_error: Optional[str] = None
        self._init_market_state()
        if self.live:
            self.refresh_quotes()

    def _init_market_state(self):
        for cfg in PAIRS_METADATA:
            sym = cfg["symbol"]
            pip_sz = get_pip_size(sym)
            mid = cfg["base_price"]
            self.prices[sym] = {
                "config": cfg,
                "mid": mid,
                "bid": mid,
                "ask": mid,
                "pip_size": pip_sz,
                "high_24h": mid,
                "low_24h": mid,
                "open_24h": mid,
                "last_update": datetime.now(timezone.utc),
                "market_time": None,
            }
            self._set_mid(sym, mid)
            self.candles_cache[sym] = {}

    def _set_mid(self, sym: str, mid: Decimal) -> None:
        d = self.prices[sym]
        half_spread = (d["config"]["spread_pips"] * d["pip_size"]) / Decimal("2")
        d["mid"] = mid
        d["bid"] = mid - half_spread
        d["ask"] = mid + half_spread

    # ------------------------------------------------------------------ live quotes
    def refresh_quotes(self) -> int:
        """Pull the latest real quotes for every pair. Blocking - run it from a worker thread."""
        try:
            quotes = live_feed.fetch_quotes(list(self.prices.keys()))
        except Exception as exc:  # never let a provider hiccup kill the heartbeat
            self.last_quote_error = str(exc)
            logger.warning(f"Live quote refresh failed: {exc}")
            return 0
        now = datetime.now(timezone.utc)
        for sym, q in quotes.items():
            if sym not in self.prices or q.price <= 0:
                continue
            d = self.prices[sym]
            decimals = d["config"]["pip_decimals"] + 1
            mid = Decimal(str(round(q.price, decimals)))
            self._set_mid(sym, mid)
            if q.previous_close:
                d["open_24h"] = Decimal(str(q.previous_close))
            elif d["market_time"] is None:
                d["open_24h"] = mid
            d["high_24h"] = Decimal(str(max(q.day_high or q.price, q.price)))
            d["low_24h"] = Decimal(str(min(q.day_low or q.price, q.price)))
            d["last_update"] = now
            d["market_time"] = q.market_time
        if quotes:
            self.last_quote_refresh = now
            self.last_quote_error = None
        else:
            self.last_quote_error = "No quotes returned by live providers"
        return len(quotes)

    def data_status(self) -> dict:
        return {
            "mode": "live" if self.live else "offline",
            "source": "Yahoo Finance (Twelve Data fallback)" if self.live else "offline test generator",
            "last_quote_refresh": self.last_quote_refresh.isoformat() if self.last_quote_refresh else None,
            "pairs_with_live_quotes": sum(1 for d in self.prices.values() if d["market_time"] is not None),
            "last_error": self.last_quote_error,
        }

    def get_all_pairs(self) -> List[CurrencyPair]:
        result = []
        now = datetime.now(timezone.utc)
        for sym, d in self.prices.items():
            cfg = d["config"]
            mid = d["mid"]
            open_24h = d["open_24h"]
            chg = round(float((mid - open_24h) / open_24h * 100), 2) if open_24h else 0.0
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
                    timestamp=d["market_time"] or now,
                )
            )
        return result

    def get_pair(self, symbol: str) -> Optional[CurrencyPair]:
        all_p = self.get_all_pairs()
        sym_norm = symbol.replace("/", "_").upper()
        for p in all_p:
            if p.symbol == sym_norm:
                return p
        return None

    def update_ticks(self) -> Dict[str, Tick]:
        """Current real quotes. Prices change only when the live refresh pulls a new quote."""
        return self.latest_ticks()

    def latest_ticks(self) -> Dict[str, Tick]:
        """Current bid/ask per pair (read-only snapshot)."""
        return {
            sym: Tick(
                symbol=sym,
                bid=float(d["bid"]),
                ask=float(d["ask"]),
                spread_pips=float(d["config"]["spread_pips"]),
                timestamp=d["last_update"],
            )
            for sym, d in self.prices.items()
        }

    def get_candles(self, symbol: str, timeframe: str = "H1", limit: int = 100) -> List[Candle]:
        sym = symbol.replace("/", "_").upper()
        tf = timeframe.upper()
        if not self.live:
            if sym not in self.candles_cache:
                self.candles_cache[sym] = {}
            if tf not in self.candles_cache[sym] or len(self.candles_cache[sym][tf]) < limit:
                self.candles_cache[sym][tf] = self._generate_offline_candles(sym, tf, count=max(limit, 200))
            return self.candles_cache[sym][tf][-limit:]

        try:
            bars = live_feed.fetch_candles(sym, tf)
        except LiveDataUnavailable as exc:
            raise ProviderUnavailableError("Live market data", str(exc)) from exc
        decimals = (2 if "JPY" in sym else 4) + 1
        candles = [
            Candle(
                symbol=sym,
                timeframe=tf,
                open_time=b.time,
                open=round(b.open, decimals),
                high=round(b.high, decimals),
                low=round(b.low, decimals),
                close=round(b.close, decimals),
                volume=b.volume,
            )
            for b in bars[-limit:]
        ]
        # Fold the latest real quote into the forming bar so charts track the live price between refreshes.
        d = self.prices.get(sym)
        if candles and d and d["market_time"] is not None and d["market_time"] >= candles[-1].open_time:
            last = candles[-1]
            mid = float(d["mid"])
            candles[-1] = last.model_copy(update={"close": mid, "high": max(last.high, mid), "low": min(last.low, mid)})
        return candles

    def get_history_bars(self, symbol: str, timeframe: str) -> List[OHLC]:
        """Deep real history for the backtest engine."""
        try:
            return live_feed.fetch_candles(symbol.replace("/", "_").upper(), timeframe.upper(), history=True)
        except LiveDataUnavailable as exc:
            raise ProviderUnavailableError("Live market data", str(exc)) from exc

    def _generate_offline_candles(self, symbol: str, timeframe: str, count: int = 200) -> List[Candle]:
        """Offline-only generator used when LIVE_MARKET_DATA is disabled (unit tests / CI without network)."""
        cfg = next((c for c in PAIRS_METADATA if c["symbol"] == symbol), PAIRS_METADATA[0])
        pip_sz = float(get_pip_size(symbol))
        base_p = float(cfg["base_price"])
        now = datetime.now(timezone.utc)
        rng = random.Random(f"{symbol}|{timeframe}")
        candles = []
        curr = base_p

        minutes_map = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
        step = minutes_map.get(timeframe, 60)
        step_delta = timedelta(minutes=step)
        epoch_min = int(now.timestamp() // 60)
        last_open = datetime.fromtimestamp((epoch_min - epoch_min % step) * 60, tz=timezone.utc)
        vol_scale = (step / 60) ** 0.5

        for i in range(count, 0, -1):
            vol = rng.uniform(5, 20) * pip_sz * vol_scale
            chg = rng.uniform(-vol, vol)
            c_open = curr
            c_close = curr + chg
            c_high = max(c_open, c_close) + rng.uniform(0, vol * 0.7)
            c_low = min(c_open, c_close) - rng.uniform(0, vol * 0.7)
            candles.append(
                Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    open_time=last_open - (i - 1) * step_delta,
                    open=round(c_open, cfg["pip_decimals"] + 1),
                    high=round(c_high, cfg["pip_decimals"] + 1),
                    low=round(c_low, cfg["pip_decimals"] + 1),
                    close=round(c_close, cfg["pip_decimals"] + 1),
                    volume=rng.randint(500, 3000),
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
