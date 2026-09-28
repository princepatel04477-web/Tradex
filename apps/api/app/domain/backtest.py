"""Pure, deterministic bar-by-bar backtesting engine (Month 3 roadmap, SRS FG-4 / Phase 5).

Design rules enforced here:
- No look-ahead: every indicator series is causal (value at index i depends only on bars 0..i),
  the signal is evaluated on the CLOSE of bar i and filled at the OPEN of bar i+1.
- Fills use bid/ask, never mid: buys fill at ask (mid + half spread), sells at bid (mid - half spread);
  longs exit on the bid, shorts exit on the ask.
- Money and prices are Decimal throughout; only derived statistics (Sharpe) use float math.
- Stops are evaluated intrabar with the conservative rule: if a bar touches both SL and TP,
  the stop-loss is assumed to have been hit first.

This module performs no I/O and has no side effects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, NamedTuple, Optional, Sequence

from app.domain.indicators import calculate_ema_series
from app.domain.pips import get_pip_size, split_symbol

ZERO = Decimal("0")
TWO = Decimal("2")
CENT = Decimal("0.01")


class Bar(NamedTuple):
    """One OHLC bar quoted at mid; the engine applies half the spread on each side."""

    time: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal


@dataclass(frozen=True)
class StrategyConfig:
    """User-configurable strategy parameters."""

    strategy: str = "ema_crossover"
    fast_period: int = 9
    slow_period: int = 21
    rsi_period: int = 14
    rsi_lower: Decimal = Decimal("30")
    rsi_upper: Decimal = Decimal("70")
    atr_period: int = 14
    sl_atr_mult: Decimal = Decimal("1.5")
    tp_atr_mult: Decimal = Decimal("3.0")
    risk_per_trade_pct: Decimal = Decimal("1.0")
    allow_short: bool = True


@dataclass
class BacktestTrade:
    """A single closed trade in the backtest ledger."""

    trade_no: int
    direction: str
    entry_time: str
    exit_time: str
    entry_price: Decimal
    exit_price: Decimal
    units: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    pnl: Decimal
    pnl_pips: Decimal
    r_multiple: Decimal
    exit_reason: str
    bars_held: int


@dataclass
class EquitySample:
    """Mark-to-market equity at the close of a bar."""

    time: str
    equity: Decimal
    drawdown_pct: Decimal


@dataclass
class BacktestResult:
    """Full backtest output: summary statistics, equity curve and trade ledger."""

    initial_balance: Decimal
    final_balance: Decimal
    net_profit: Decimal
    total_return_pct: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: Decimal
    profit_factor: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    expectancy: Decimal
    avg_r_multiple: Decimal
    max_drawdown_pct: Decimal
    max_drawdown_amount: Decimal
    sharpe_ratio: Decimal
    exposure_pct: Decimal
    bars_tested: int
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[EquitySample] = field(default_factory=list)


BARS_PER_YEAR: Dict[str, int] = {
    "M15": 24 * 4 * 260,
    "M30": 24 * 2 * 260,
    "H1": 24 * 260,
    "H4": 6 * 260,
    "D1": 260,
}

SUPPORTED_STRATEGIES: Dict[str, str] = {
    "ema_crossover": "EMA fast/slow crossover trend-following",
    "rsi_reversion": "RSI mean-reversion (re-entry from oversold / overbought)",
    "macd_momentum": "MACD line / signal line momentum crossover",
}


# ---------------------------------------------------------------------------
# Causal indicator series (value[i] uses only data[0..i]) — the look-ahead guard.
# ---------------------------------------------------------------------------


def rsi_series(closes: Sequence[Decimal], period: int = 14) -> List[Optional[Decimal]]:
    """Wilder RSI as a causal series; identical to domain.indicators.calculate_rsi on each prefix."""
    out: List[Optional[Decimal]] = [None] * len(closes)
    if len(closes) <= period:
        return out
    gains: List[Decimal] = []
    losses: List[Decimal] = []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(delta if delta > ZERO else ZERO)
        losses.append(-delta if delta < ZERO else ZERO)

    p = Decimal(period)
    avg_gain = sum(gains[:period], ZERO) / p
    avg_loss = sum(losses[:period], ZERO) / p
    out[period] = _rsi_value(avg_gain, avg_loss)
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * Decimal(period - 1) + gains[i]) / p
        avg_loss = (avg_loss * Decimal(period - 1) + losses[i]) / p
        out[i + 1] = _rsi_value(avg_gain, avg_loss)
    return out


def _rsi_value(avg_gain: Decimal, avg_loss: Decimal) -> Decimal:
    if avg_loss == ZERO:
        return Decimal("100.00")
    rs = avg_gain / avg_loss
    return (Decimal("100.0") - Decimal("100.0") / (Decimal("1.0") + rs)).quantize(CENT, rounding=ROUND_HALF_UP)


def atr_series(bars: Sequence[Bar], period: int = 14) -> List[Optional[Decimal]]:
    """Simple-mean ATR as a causal series; matches domain.indicators.calculate_atr on each prefix."""
    out: List[Optional[Decimal]] = [None] * len(bars)
    trs: List[Decimal] = []
    for i in range(1, len(bars)):
        hl = bars[i].high - bars[i].low
        hc = abs(bars[i].high - bars[i - 1].close)
        lc = abs(bars[i].low - bars[i - 1].close)
        trs.append(max(hl, hc, lc))
        if len(trs) >= period:
            window = trs[-period:]
            out[i] = (sum(window, ZERO) / Decimal(period)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    return out


def macd_series(
    closes: Sequence[Decimal], fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[List[Decimal], List[Decimal]]:
    """Causal MACD line and signal line series."""
    fast_ema = calculate_ema_series(list(closes), fast)
    slow_ema = calculate_ema_series(list(closes), slow)
    line = [f - s for f, s in zip(fast_ema, slow_ema)]
    sig = calculate_ema_series(line, signal)
    return line, sig


# ---------------------------------------------------------------------------
# Signal generation
# ---------------------------------------------------------------------------


def generate_signals(bars: Sequence[Bar], cfg: StrategyConfig) -> List[int]:
    """Return +1 (long), -1 (short) or 0 (no new signal) evaluated on the close of each bar."""
    closes = [b.close for b in bars]
    n = len(closes)
    signals = [0] * n
    if cfg.strategy == "ema_crossover":
        fast = calculate_ema_series(closes, cfg.fast_period)
        slow = calculate_ema_series(closes, cfg.slow_period)
        warmup = cfg.slow_period
        for i in range(max(1, warmup), n):
            if fast[i - 1] <= slow[i - 1] and fast[i] > slow[i]:
                signals[i] = 1
            elif fast[i - 1] >= slow[i - 1] and fast[i] < slow[i]:
                signals[i] = -1
    elif cfg.strategy == "rsi_reversion":
        rsi = rsi_series(closes, cfg.rsi_period)
        for i in range(1, n):
            prev, cur = rsi[i - 1], rsi[i]
            if prev is None or cur is None:
                continue
            if prev < cfg.rsi_lower <= cur:
                signals[i] = 1
            elif prev > cfg.rsi_upper >= cur:
                signals[i] = -1
    elif cfg.strategy == "macd_momentum":
        line, sig = macd_series(closes)
        for i in range(35, n):
            if line[i - 1] <= sig[i - 1] and line[i] > sig[i]:
                signals[i] = 1
            elif line[i - 1] >= sig[i - 1] and line[i] < sig[i]:
                signals[i] = -1
    else:
        raise ValueError(f"Unsupported strategy '{cfg.strategy}'")
    if not cfg.allow_short:
        signals = [s if s > 0 else 0 for s in signals]
    return signals


# ---------------------------------------------------------------------------
# Execution loop
# ---------------------------------------------------------------------------


def quote_to_usd(symbol: str, price: Decimal, usd_rates: Dict[str, Decimal]) -> Decimal:
    """Rate that converts 1 unit of the pair's quote currency into USD."""
    base, quote = split_symbol(symbol)
    if quote == "USD":
        return Decimal("1")
    if base == "USD":
        return Decimal("1") / price
    rate = usd_rates.get(quote)
    if rate is None:
        raise ValueError(f"No USD conversion rate for {quote}")
    return rate


@dataclass
class _OpenPosition:
    direction: int
    entry_index: int
    entry_time: str
    entry_price: Decimal
    units: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    risk_amount: Decimal


def run_backtest(
    symbol: str,
    bars: Sequence[Bar],
    spread_pips: Decimal,
    cfg: StrategyConfig,
    initial_balance: Decimal = Decimal("10000"),
    usd_rates: Optional[Dict[str, Decimal]] = None,
    timeframe: str = "H1",
) -> BacktestResult:
    """Run a deterministic bar-by-bar backtest and return statistics, equity curve and ledger."""
    if len(bars) < 60:
        raise ValueError("At least 60 bars are required for a backtest")
    if initial_balance <= ZERO:
        raise ValueError("initial_balance must be positive")

    rates = usd_rates or {}
    pip = get_pip_size(symbol)
    half_spread = spread_pips * pip / TWO
    signals = generate_signals(bars, cfg)
    atrs = atr_series(bars, cfg.atr_period)

    balance = initial_balance
    position: Optional[_OpenPosition] = None
    trades: List[BacktestTrade] = []
    equity_curve: List[EquitySample] = []
    peak = initial_balance
    max_dd_amount = ZERO
    max_dd_pct = ZERO
    bars_in_market = 0
    pending_signal = 0

    def close_position(pos: _OpenPosition, exit_price: Decimal, idx: int, reason: str) -> None:
        """Close at an already side-adjusted price (longs exit on bid, shorts on ask)."""
        nonlocal balance
        move = (exit_price - pos.entry_price) * Decimal(pos.direction)
        pnl = (move * pos.units * quote_to_usd(symbol, exit_price, rates)).quantize(CENT, rounding=ROUND_HALF_UP)
        balance += pnl
        r_mult = (pnl / pos.risk_amount).quantize(CENT, rounding=ROUND_HALF_UP) if pos.risk_amount > ZERO else ZERO
        trades.append(
            BacktestTrade(
                trade_no=len(trades) + 1,
                direction="long" if pos.direction > 0 else "short",
                entry_time=pos.entry_time,
                exit_time=bars[idx].time,
                entry_price=pos.entry_price,
                exit_price=exit_price,
                units=pos.units,
                stop_loss=pos.stop_loss,
                take_profit=pos.take_profit,
                pnl=pnl,
                pnl_pips=(move / pip).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
                r_multiple=r_mult,
                exit_reason=reason,
                bars_held=idx - pos.entry_index,
            )
        )

    def exit_side_price(direction: int, mid: Decimal) -> Decimal:
        return mid - half_spread if direction > 0 else mid + half_spread

    for i, bar in enumerate(bars):
        # 1) Execute the signal produced on the previous close at this bar's open.
        if pending_signal != 0:
            if position is not None and position.direction != pending_signal:
                close_position(position, exit_side_price(position.direction, bar.open), i, "signal_reversal")
                position = None
            atr_prev = atrs[i - 1] if i > 0 else None
            if position is None and atr_prev is not None and atr_prev > ZERO:
                direction = pending_signal
                entry = bar.open + half_spread if direction > 0 else bar.open - half_spread
                stop_dist = atr_prev * cfg.sl_atr_mult
                risk_amount = (balance * cfg.risk_per_trade_pct / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
                conv = quote_to_usd(symbol, entry, rates)
                units = (risk_amount / (stop_dist * conv)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                if units > ZERO:
                    sl = entry - stop_dist if direction > 0 else entry + stop_dist
                    tp = entry + atr_prev * cfg.tp_atr_mult if direction > 0 else entry - atr_prev * cfg.tp_atr_mult
                    position = _OpenPosition(direction, i, bar.time, entry, units, sl, tp, risk_amount)
            pending_signal = 0

        # 2) Intrabar stop / target evaluation on the exit side of the book.
        #    Conservative rule: when a bar touches both levels the stop is assumed first.
        if position is not None:
            d = position.direction
            side_open = exit_side_price(d, bar.open)
            side_high = exit_side_price(d, bar.high)
            side_low = exit_side_price(d, bar.low)
            if d > 0:
                if side_low <= position.stop_loss:
                    close_position(position, min(position.stop_loss, side_open), i, "stop_loss")
                    position = None
                elif side_high >= position.take_profit:
                    close_position(position, max(position.take_profit, side_open), i, "take_profit")
                    position = None
            else:
                if side_high >= position.stop_loss:
                    close_position(position, max(position.stop_loss, side_open), i, "stop_loss")
                    position = None
                elif side_low <= position.take_profit:
                    close_position(position, min(position.take_profit, side_open), i, "take_profit")
                    position = None

        # 3) Mark-to-market equity (equity derived, never stored).
        floating = ZERO
        if position is not None:
            bars_in_market += 1
            exit_px = exit_side_price(position.direction, bar.close)
            move = (exit_px - position.entry_price) * Decimal(position.direction)
            floating = move * position.units * quote_to_usd(symbol, exit_px, rates)
        equity = (balance + floating).quantize(CENT, rounding=ROUND_HALF_UP)
        peak = max(peak, equity)
        dd_amount = peak - equity
        dd_pct = (dd_amount / peak * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP) if peak > ZERO else ZERO
        max_dd_amount = max(max_dd_amount, dd_amount)
        max_dd_pct = max(max_dd_pct, dd_pct)
        equity_curve.append(EquitySample(time=bar.time, equity=equity, drawdown_pct=dd_pct))

        # 4) Signal on this close becomes an order for the next bar's open.
        if i < len(bars) - 1:
            pending_signal = signals[i]

    if position is not None:
        close_position(position, exit_side_price(position.direction, bars[-1].close), len(bars) - 1, "end_of_test")
        position = None
        equity_curve[-1] = EquitySample(time=bars[-1].time, equity=balance, drawdown_pct=equity_curve[-1].drawdown_pct)

    return _summarise(initial_balance, balance, trades, equity_curve, max_dd_amount, max_dd_pct, bars_in_market, len(bars), timeframe)


def _summarise(
    initial_balance: Decimal,
    final_balance: Decimal,
    trades: List[BacktestTrade],
    equity_curve: List[EquitySample],
    max_dd_amount: Decimal,
    max_dd_pct: Decimal,
    bars_in_market: int,
    bars_tested: int,
    timeframe: str,
) -> BacktestResult:
    wins = [t for t in trades if t.pnl > ZERO]
    losses = [t for t in trades if t.pnl <= ZERO]
    gross_win = sum((t.pnl for t in wins), ZERO)
    gross_loss = -sum((t.pnl for t in losses), ZERO)
    n = len(trades)

    profit_factor = (gross_win / gross_loss).quantize(CENT, rounding=ROUND_HALF_UP) if gross_loss > ZERO else (
        Decimal("99.99") if gross_win > ZERO else ZERO
    )
    avg_win = (gross_win / len(wins)).quantize(CENT, rounding=ROUND_HALF_UP) if wins else ZERO
    avg_loss = (-gross_loss / len(losses)).quantize(CENT, rounding=ROUND_HALF_UP) if losses else ZERO
    net = (final_balance - initial_balance).quantize(CENT, rounding=ROUND_HALF_UP)
    expectancy = (net / n).quantize(CENT, rounding=ROUND_HALF_UP) if n else ZERO
    avg_r = (sum((t.r_multiple for t in trades), ZERO) / n).quantize(CENT, rounding=ROUND_HALF_UP) if n else ZERO

    returns: List[float] = []
    for prev, cur in zip(equity_curve, equity_curve[1:]):
        if prev.equity > ZERO:
            returns.append(float((cur.equity - prev.equity) / prev.equity))
    sharpe = 0.0
    if len(returns) > 2:
        mean = sum(returns) / len(returns)
        var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        std = math.sqrt(var)
        if std > 0:
            sharpe = mean / std * math.sqrt(BARS_PER_YEAR.get(timeframe, 24 * 260))

    return BacktestResult(
        initial_balance=initial_balance,
        final_balance=final_balance.quantize(CENT, rounding=ROUND_HALF_UP),
        net_profit=net,
        total_return_pct=(net / initial_balance * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP),
        total_trades=n,
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate_pct=(Decimal(len(wins)) / Decimal(n) * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP) if n else ZERO,
        profit_factor=profit_factor,
        avg_win=avg_win,
        avg_loss=avg_loss,
        expectancy=expectancy,
        avg_r_multiple=avg_r,
        max_drawdown_pct=max_dd_pct,
        max_drawdown_amount=max_dd_amount.quantize(CENT, rounding=ROUND_HALF_UP),
        sharpe_ratio=Decimal(str(round(sharpe, 2))),
        exposure_pct=(Decimal(bars_in_market) / Decimal(bars_tested) * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
        if bars_tested
        else ZERO,
        bars_tested=bars_tested,
        trades=trades,
        equity_curve=equity_curve,
    )
