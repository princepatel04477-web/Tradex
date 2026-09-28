"""Backtesting engine tests: look-ahead guard, bid/ask fills, ledger identity, reproducibility."""

from decimal import Decimal

import pytest

from app.domain.backtest import (
    Bar,
    StrategyConfig,
    atr_series,
    generate_signals,
    rsi_series,
    run_backtest,
)
from app.domain.indicators import calculate_atr, calculate_rsi
from app.domain.pips import get_pip_size
from app.providers.historical import _is_market_open, bar_open_times, generate_history
from app.schemas.backtest import BacktestRequest
from app.services.backtest_service import _usd_rates, backtest_service

EURUSD_BARS = generate_history("EUR_USD", "H4", 600, Decimal("1.0850"))


def test_history_is_deterministic_and_ohlc_valid():
    again = generate_history("EUR_USD", "H4", 600, Decimal("1.0850"))
    assert again == EURUSD_BARS
    for b in EURUSD_BARS:
        assert b.high >= max(b.open, b.close)
        assert b.low <= min(b.open, b.close)
        assert b.low > 0


def test_history_respects_fx_trading_week():
    from datetime import datetime, timezone

    times = bar_open_times("H1", 300, datetime(2026, 9, 28, tzinfo=timezone.utc))
    assert all(_is_market_open(t) for t in times)
    assert times == sorted(times)


def test_d1_bars_open_at_17_new_york_across_dst():
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    ny = ZoneInfo("America/New_York")
    times = bar_open_times("D1", 400, datetime(2026, 9, 28, tzinfo=timezone.utc))
    assert all(t.astimezone(ny).hour == 17 for t in times)
    # Summer (EDT) opens at 21:00 UTC, winter (EST) at 22:00 UTC — handled by tz, not a fixed offset.
    assert {t.hour for t in times} == {21, 22}


def test_rsi_series_matches_domain_rsi_on_every_prefix():
    closes = [b.close for b in EURUSD_BARS[:120]]
    series = rsi_series(closes, 14)
    for i in (15, 40, 80, 119):
        assert series[i] == calculate_rsi(closes[: i + 1], 14)


def test_atr_series_matches_domain_atr_on_every_prefix():
    bars = EURUSD_BARS[:120]
    series = atr_series(bars, 14)
    for i in (15, 60, 119):
        prefix = bars[: i + 1]
        assert series[i] == calculate_atr([b.high for b in prefix], [b.low for b in prefix], [b.close for b in prefix], 14)


@pytest.mark.parametrize("strategy", ["ema_crossover", "rsi_reversion", "macd_momentum"])
def test_no_look_ahead_signals_on_prefix_equal_full_run(strategy):
    cfg = StrategyConfig(strategy=strategy)
    full = generate_signals(EURUSD_BARS, cfg)
    for k in (100, 250, 400):
        assert generate_signals(EURUSD_BARS[:k], cfg) == full[:k]


def test_fills_use_ask_for_buys_and_bid_for_sells():
    spread = Decimal("1.2")
    half = spread * get_pip_size("EUR_USD") / 2
    result = run_backtest("EUR_USD", EURUSD_BARS, spread, StrategyConfig(), Decimal("10000"), _usd_rates(), "H4")
    assert result.total_trades > 0
    by_time = {b.time: b for b in EURUSD_BARS}
    for t in result.trades:
        bar = by_time[t.entry_time]
        expected = bar.open + half if t.direction == "long" else bar.open - half
        assert t.entry_price == expected


def test_ledger_identity_and_stats():
    result = run_backtest("EUR_USD", EURUSD_BARS, Decimal("1.2"), StrategyConfig(), Decimal("10000"), _usd_rates(), "H4")
    assert result.final_balance == Decimal("10000") + sum((t.pnl for t in result.trades), Decimal("0"))
    assert result.winning_trades + result.losing_trades == result.total_trades
    assert Decimal("0") <= result.win_rate_pct <= Decimal("100")
    assert result.max_drawdown_pct >= 0
    assert result.equity_curve[-1].equity == result.final_balance


def test_stop_loss_limits_loss_to_about_one_r():
    result = run_backtest("EUR_USD", EURUSD_BARS, Decimal("1.2"), StrategyConfig(), Decimal("10000"), _usd_rates(), "H4")
    stops = [t for t in result.trades if t.exit_reason == "stop_loss"]
    assert stops
    # Gaps can exceed the stop slightly, but a stopped trade should cost roughly one risk unit.
    assert all(Decimal("-1.6") <= t.r_multiple <= Decimal("0.1") for t in stops)


def test_service_run_is_reproducible_and_stored():
    req = BacktestRequest(symbol="USD_JPY", timeframe="D1", strategy="ema_crossover", bars=800)
    a = backtest_service.run(req)
    b = backtest_service.run(req)
    assert a.metrics == b.metrics
    assert backtest_service.get_run(a.run_id).run_id == a.run_id
    assert len(a.equity_curve) <= 402


def test_service_rejects_bad_parameters():
    from app.core.errors import ValidationError

    with pytest.raises(ValidationError):
        backtest_service.run(BacktestRequest(symbol="EUR_USD", fast_period=30, slow_period=20))
    with pytest.raises(ValidationError):
        backtest_service.run(BacktestRequest(symbol="XAU_BTC"))


def test_too_few_bars_rejected():
    with pytest.raises(ValueError):
        run_backtest("EUR_USD", EURUSD_BARS[:30], Decimal("1"), StrategyConfig())


def test_cross_pair_uses_usd_conversion():
    req = BacktestRequest(symbol="EUR_GBP", timeframe="H1", strategy="ema_crossover", bars=600)
    run = backtest_service.run(req)
    assert run.metrics.total_trades > 0
