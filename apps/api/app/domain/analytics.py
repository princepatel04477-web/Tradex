"""Performance analytics and trade journal calculations (SRS FG-5).

Formulas:
- Win Rate % = (Winning Trades / Total Trades) * 100
- Profit Factor = Gross Profits / Gross Losses (if Gross Losses > 0 else Gross Profits)
- Average Win / Average Loss
- Average Risk:Reward = Avg Win / Avg Loss
- Max Drawdown (Absolute & Percentage) over equity snapshot curve
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, NamedTuple, Optional


class ClosedTradeItem(NamedTuple):
    symbol: str
    realized_pnl: Decimal
    realized_pnl_pips: Decimal
    session: Optional[str] = None


class EquityPoint(NamedTuple):
    timestamp: str
    balance: Decimal
    equity: Decimal


class AnalyticsResult(NamedTuple):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: Decimal
    total_realized_pnl: Decimal
    profit_factor: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    avg_risk_reward_ratio: Decimal
    max_drawdown_amount: Decimal
    max_drawdown_pct: Decimal
    pair_performance: List[Dict[str, any]]
    session_performance: List[Dict[str, any]]


def calculate_performance_analytics(
    trades: List[ClosedTradeItem],
    equity_history: List[EquityPoint],
    initial_balance: Decimal = Decimal("10000.00"),
) -> AnalyticsResult:
    total = len(trades)
    if total == 0:
        return AnalyticsResult(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate_pct=Decimal("0.0"),
            total_realized_pnl=Decimal("0.00"),
            profit_factor=Decimal("0.00"),
            avg_win=Decimal("0.00"),
            avg_loss=Decimal("0.00"),
            avg_risk_reward_ratio=Decimal("0.00"),
            max_drawdown_amount=Decimal("0.00"),
            max_drawdown_pct=Decimal("0.0"),
            pair_performance=[],
            session_performance=[],
        )

    wins = [t for t in trades if t.realized_pnl > Decimal("0")]
    losses = [t for t in trades if t.realized_pnl <= Decimal("0")]

    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (Decimal(win_count) / Decimal(total) * Decimal("100.0")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    gross_profit = sum((t.realized_pnl for t in wins), Decimal("0.00"))
    gross_loss = abs(sum((t.realized_pnl for t in losses), Decimal("0.00")))

    if gross_loss > Decimal("0"):
        profit_factor = (gross_profit / gross_loss).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        profit_factor = gross_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if gross_profit > Decimal("0") else Decimal("1.00")

    avg_win = (gross_profit / Decimal(win_count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if win_count > 0 else Decimal("0.00")
    avg_loss = (gross_loss / Decimal(loss_count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if loss_count > 0 else Decimal("0.00")
    rr_ratio = (avg_win / avg_loss).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if avg_loss > Decimal("0") else Decimal("0.00")

    total_pnl = sum((t.realized_pnl for t in trades), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Max Drawdown
    peak = initial_balance
    max_dd_amount = Decimal("0.00")
    max_dd_pct = Decimal("0.0")

    for pt in equity_history:
        if pt.equity > peak:
            peak = pt.equity
        dd = peak - pt.equity
        if dd > max_dd_amount:
            max_dd_amount = dd
            if peak > Decimal("0"):
                max_dd_pct = (dd / peak * Decimal("100.0")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    # Pair Performance Breakdown
    pair_dict: Dict[str, dict] = {}
    for t in trades:
        if t.symbol not in pair_dict:
            pair_dict[t.symbol] = {"symbol": t.symbol, "trades": 0, "pnl": Decimal("0.00"), "wins": 0}
        pair_dict[t.symbol]["trades"] += 1
        pair_dict[t.symbol]["pnl"] += t.realized_pnl
        if t.realized_pnl > Decimal("0"):
            pair_dict[t.symbol]["wins"] += 1

    pair_perf = [
        {
            "symbol": v["symbol"],
            "trades": v["trades"],
            "pnl": float(v["pnl"]),
            "win_rate": round(v["wins"] / v["trades"] * 100, 1) if v["trades"] > 0 else 0.0,
        }
        for v in pair_dict.values()
    ]

    # Session Performance Breakdown
    session_dict: Dict[str, dict] = {}
    for t in trades:
        sess = t.session or "London"
        if sess not in session_dict:
            session_dict[sess] = {"session": sess, "trades": 0, "pnl": Decimal("0.00")}
        session_dict[sess]["trades"] += 1
        session_dict[sess]["pnl"] += t.realized_pnl

    session_perf = [
        {"session": k, "trades": v["trades"], "pnl": float(v["pnl"])}
        for k, v in session_dict.items()
    ]

    return AnalyticsResult(
        total_trades=total,
        winning_trades=win_count,
        losing_trades=loss_count,
        win_rate_pct=win_rate,
        total_realized_pnl=total_pnl,
        profit_factor=profit_factor,
        avg_win=avg_win,
        avg_loss=avg_loss,
        avg_risk_reward_ratio=rr_ratio,
        max_drawdown_amount=max_dd_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        max_drawdown_pct=max_dd_pct,
        pair_performance=pair_perf,
        session_performance=session_perf,
    )
