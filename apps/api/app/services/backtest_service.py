"""Backtest Service: orchestrates historical data, the pure engine and run storage (Month 3 roadmap)."""

from __future__ import annotations

import time
import uuid
from collections import OrderedDict
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from app.core.errors import ResourceNotFoundError, ValidationError
from app.domain.backtest import SUPPORTED_STRATEGIES, Bar, StrategyConfig, run_backtest
from app.domain.pips import get_pip_decimal_places, normalize_symbol, split_symbol
from app.providers.historical import generate_history
from app.schemas.backtest import (
    BacktestMetrics,
    BacktestRequest,
    BacktestRunOut,
    BacktestRunSummary,
    BacktestTradeOut,
    EquityPointOut,
    StrategyInfo,
)
from app.services.market_service import PAIRS_METADATA, market_service

MAX_STORED_RUNS = 50
MAX_CURVE_POINTS = 400

STRATEGY_PARAMETERS: Dict[str, List[str]] = {
    "ema_crossover": ["fast_period", "slow_period"],
    "rsi_reversion": ["rsi_period", "rsi_lower", "rsi_upper"],
    "macd_momentum": [],
}

STRATEGY_TITLES: Dict[str, str] = {
    "ema_crossover": "EMA Crossover",
    "rsi_reversion": "RSI Mean Reversion",
    "macd_momentum": "MACD Momentum",
}


def _usd_rates() -> Dict[str, Decimal]:
    """Quote->USD conversion rates from the current market mids."""
    rates: Dict[str, Decimal] = {"USD": Decimal("1")}
    for cfg in PAIRS_METADATA:
        base, quote = cfg["base"], cfg["quote"]
        price: Decimal = market_service.prices[cfg["symbol"]]["mid"]
        if quote == "USD":
            rates[base] = price
        elif base == "USD":
            rates[quote] = Decimal("1") / price
    return rates


def _load_bars(symbol: str, timeframe: str, count: int, base_price: Decimal) -> Tuple[List[Bar], str]:
    """Most recent ``count`` closed bars of real market history (offline generator only when live data is off)."""
    if not market_service.live:
        return generate_history(symbol, timeframe, count, base_price), "Offline generated dataset (live data disabled)"
    raw = market_service.get_history_bars(symbol, timeframe)
    closed = raw[:-1]  # the last bar is still forming
    decimals = get_pip_decimal_places(symbol) + 1
    quant = Decimal(1).scaleb(-decimals)

    def q(x: float) -> Decimal:
        return Decimal(repr(x)).quantize(quant)

    bars = [Bar(time=b.time.isoformat(), open=q(b.open), high=q(b.high), low=q(b.low), close=q(b.close)) for b in closed[-count:]]
    if len(bars) < 200:
        raise ValidationError(f"Only {len(bars)} real {timeframe} bars are available for {symbol}; need at least 200")
    return bars, "Real market history - Yahoo Finance FX (mid prices)"


class BacktestService:
    def __init__(self) -> None:
        self._runs: "OrderedDict[str, BacktestRunOut]" = OrderedDict()

    @staticmethod
    def list_strategies() -> List[StrategyInfo]:
        return [
            StrategyInfo(id=k, name=STRATEGY_TITLES[k], description=v, parameters=STRATEGY_PARAMETERS[k])
            for k, v in SUPPORTED_STRATEGIES.items()
        ]

    def run(self, req: BacktestRequest, user_id: Optional[str] = None) -> BacktestRunOut:
        symbol = normalize_symbol(req.symbol)
        try:
            split_symbol(symbol)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        cfg_row = next((c for c in PAIRS_METADATA if c["symbol"] == symbol), None)
        if cfg_row is None:
            raise ValidationError(f"Pair {symbol} is not in the Tradly pair registry")
        if req.strategy == "ema_crossover" and req.fast_period >= req.slow_period:
            raise ValidationError("fast_period must be smaller than slow_period")

        cfg = StrategyConfig(
            strategy=req.strategy,
            fast_period=req.fast_period,
            slow_period=req.slow_period,
            rsi_period=req.rsi_period,
            rsi_lower=Decimal(str(req.rsi_lower)),
            rsi_upper=Decimal(str(req.rsi_upper)),
            sl_atr_mult=Decimal(str(req.sl_atr_mult)),
            tp_atr_mult=Decimal(str(req.tp_atr_mult)),
            risk_per_trade_pct=Decimal(str(req.risk_per_trade_pct)),
            allow_short=req.allow_short,
        )

        started = time.perf_counter()
        bars, data_source = _load_bars(symbol, req.timeframe, req.bars, cfg_row["base_price"])
        try:
            result = run_backtest(
                symbol=symbol,
                bars=bars,
                spread_pips=cfg_row["spread_pips"],
                cfg=cfg,
                initial_balance=Decimal(str(req.initial_balance)),
                usd_rates=_usd_rates(),
                timeframe=req.timeframe,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        runtime_ms = round((time.perf_counter() - started) * 1000, 1)

        step = max(1, len(result.equity_curve) // MAX_CURVE_POINTS)
        curve = result.equity_curve[::step]
        if curve[-1] is not result.equity_curve[-1]:
            curve.append(result.equity_curve[-1])

        run = BacktestRunOut(
            run_id=str(uuid.uuid4())[:12],
            request=req.model_copy(update={"symbol": symbol}),
            period_start=bars[0].time,
            period_end=bars[-1].time,
            spread_pips=float(cfg_row["spread_pips"]),
            data_source=data_source,
            runtime_ms=runtime_ms,
            metrics=BacktestMetrics(
                initial_balance=float(result.initial_balance),
                final_balance=float(result.final_balance),
                net_profit=float(result.net_profit),
                total_return_pct=float(result.total_return_pct),
                total_trades=result.total_trades,
                winning_trades=result.winning_trades,
                losing_trades=result.losing_trades,
                win_rate_pct=float(result.win_rate_pct),
                profit_factor=float(result.profit_factor),
                avg_win=float(result.avg_win),
                avg_loss=float(result.avg_loss),
                expectancy=float(result.expectancy),
                avg_r_multiple=float(result.avg_r_multiple),
                max_drawdown_pct=float(result.max_drawdown_pct),
                max_drawdown_amount=float(result.max_drawdown_amount),
                sharpe_ratio=float(result.sharpe_ratio),
                exposure_pct=float(result.exposure_pct),
                bars_tested=result.bars_tested,
            ),
            equity_curve=[
                EquityPointOut(time=p.time, equity=float(p.equity), drawdown_pct=float(p.drawdown_pct)) for p in curve
            ],
            trades=[
                BacktestTradeOut(
                    trade_no=t.trade_no,
                    direction=t.direction,
                    entry_time=t.entry_time,
                    exit_time=t.exit_time,
                    entry_price=float(t.entry_price),
                    exit_price=float(t.exit_price),
                    units=int(t.units),
                    stop_loss=float(t.stop_loss),
                    take_profit=float(t.take_profit),
                    pnl=float(t.pnl),
                    pnl_pips=float(t.pnl_pips),
                    r_multiple=float(t.r_multiple),
                    exit_reason=t.exit_reason,
                    bars_held=t.bars_held,
                )
                for t in result.trades
            ],
            user_id=user_id,
        )
        self._runs[run.run_id] = run
        while len(self._runs) > MAX_STORED_RUNS:
            self._runs.popitem(last=False)
        return run

    def get_run(self, run_id: str) -> BacktestRunOut:
        run = self._runs.get(run_id)
        if run is None:
            raise ResourceNotFoundError(f"Backtest run {run_id} not found")
        return run

    def list_runs(self) -> List[BacktestRunSummary]:
        return [
            BacktestRunSummary(
                run_id=r.run_id,
                symbol=r.request.symbol,
                timeframe=r.request.timeframe,
                strategy=r.request.strategy,
                total_trades=r.metrics.total_trades,
                net_profit=r.metrics.net_profit,
                total_return_pct=r.metrics.total_return_pct,
                win_rate_pct=r.metrics.win_rate_pct,
                sharpe_ratio=r.metrics.sharpe_ratio,
                max_drawdown_pct=r.metrics.max_drawdown_pct,
                created_at=r.created_at,
            )
            for r in reversed(self._runs.values())
        ]


backtest_service = BacktestService()
