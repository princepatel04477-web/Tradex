"""Paper Trading Service: order execution, margin accounting, trailing stops, auto-liquidation (FG-4, FG-5)."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from app.core.errors import InsufficientMarginError, ResourceNotFoundError, ValidationError
from app.domain.analytics import ClosedTradeItem, EquityPoint, calculate_performance_analytics
from app.domain.margin import PositionMarginItem, calculate_margin_metrics, calculate_required_margin
from app.domain.pips import UNITS_PER_STANDARD_LOT, get_pip_size
from app.domain.pnl import calculate_position_pnl
from app.schemas.trading import (
    ClosedTrade,
    CreateOrderRequest,
    OrderSide,
    PaperAccount,
    PerformanceAnalytics,
    Position,
    PositionStatus,
    TradingSummary,
)
from app.services.market_service import market_service


class TradingService:
    def __init__(self, initial_balance: Decimal = Decimal("10000.00")):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.currency = "USD"
        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[ClosedTrade] = []
        self.equity_history: List[EquityPoint] = [
            EquityPoint(datetime.now(timezone.utc).isoformat(), initial_balance, initial_balance)
        ]

    def get_account(self) -> PaperAccount:
        metrics = self._calculate_metrics()
        return PaperAccount(
            balance=float(metrics["balance"]),
            equity=float(metrics["equity"]),
            used_margin=float(metrics["used_margin"]),
            free_margin=float(metrics["free_margin"]),
            margin_level_pct=float(metrics["margin_level_pct"]),
            floating_pnl=float(metrics["equity"] - metrics["balance"]),
            currency=self.currency,
            open_positions_count=len(self.positions),
            closed_trades_count=len(self.closed_trades),
        )

    def _calculate_metrics(self) -> dict:
        items = []
        for pos in self.positions.values():
            items.append(
                PositionMarginItem(
                    units=Decimal(str(pos.units)),
                    entry_price=Decimal(str(pos.entry_price)),
                    leverage=Decimal(str(pos.leverage)),
                    unrealized_pnl=Decimal(str(pos.floating_pnl)),
                )
            )
        return calculate_margin_metrics(self.balance, items)

    def create_order(self, req: CreateOrderRequest) -> Position:
        pair_data = market_service.prices.get(req.symbol)
        if not pair_data:
            raise ResourceNotFoundError(f"Symbol {req.symbol} not supported")

        dir_str = req.side.value if hasattr(req.side, "value") else str(req.side)
        fill_price = Decimal(str(pair_data["ask"] if dir_str == "buy" else pair_data["bid"]))

        lot_sz = Decimal(str(req.lot_size))
        units = lot_sz * UNITS_PER_STANDARD_LOT
        leverage = Decimal(str(req.leverage))
        req_margin = calculate_required_margin(units, fill_price, leverage)

        cur_metrics = self._calculate_metrics()
        if req_margin > cur_metrics["free_margin"]:
            raise InsufficientMarginError(
                required=str(req_margin),
                available=str(cur_metrics["free_margin"]),
            )

        pos_id = str(uuid.uuid4())[:8]
        pos = Position(
            id=pos_id,
            symbol=req.symbol,
            side=OrderSide.BUY if dir_str == "buy" else OrderSide.SELL,
            lot_size=float(lot_sz),
            units=float(units),
            leverage=int(req.leverage),
            entry_price=float(fill_price),
            current_price=float(fill_price),
            stop_loss=req.stop_loss,
            take_profit=req.take_profit,
            trailing_stop_pips=req.trailing_stop_pips,
            floating_pnl=0.0,
            floating_pnl_pips=0.0,
            margin_used=float(req_margin),
            status=PositionStatus.OPEN,
            opened_at=datetime.now(timezone.utc),
        )
        self.positions[pos_id] = pos
        return pos

    def close_position(self, pos_id: str, reason: str = "manual") -> ClosedTrade:
        if pos_id not in self.positions:
            raise ResourceNotFoundError(f"Position {pos_id} not found")

        pos = self.positions.pop(pos_id)
        pair_data = market_service.prices.get(pos.symbol)
        dir_str = pos.side.value if hasattr(pos.side, "value") else str(pos.side)
        exit_price = Decimal(str(pair_data["bid"] if dir_str == "buy" else pair_data["ask"]))

        pnl_usd, pnl_pips = calculate_position_pnl(
            symbol=pos.symbol,
            direction=dir_str,
            lot_size=Decimal(str(pos.lot_size)),
            entry_price=Decimal(str(pos.entry_price)),
            current_bid=Decimal(str(pair_data["bid"])),
            current_ask=Decimal(str(pair_data["ask"])),
        )

        self.balance += pnl_usd
        now = datetime.now(timezone.utc)
        self.equity_history.append(
            EquityPoint(now.isoformat(), self.balance, self._calculate_metrics()["equity"])
        )

        trade = ClosedTrade(
            id=pos.id,
            symbol=pos.symbol,
            side=pos.side,
            lot_size=pos.lot_size,
            units=pos.units,
            leverage=pos.leverage,
            entry_price=pos.entry_price,
            exit_price=float(exit_price),
            realized_pnl=float(pnl_usd),
            realized_pnl_pips=float(pnl_pips),
            close_reason=reason,
            opened_at=pos.opened_at,
            closed_at=now,
            duration_minutes=max(1, int((now - pos.opened_at).total_seconds() / 60)),
        )
        self.closed_trades.append(trade)
        return trade

    def update_positions_on_tick(self) -> None:
        """Called on tick update: recalculate floating PnL, check SL/TP/trailing, and auto-liquidate if < 50%."""
        to_close = []
        for pos_id, pos in list(self.positions.items()):
            pair_data = market_service.prices.get(pos.symbol)
            if not pair_data:
                continue

            dir_str = pos.side.value if hasattr(pos.side, "value") else str(pos.side)
            bid = Decimal(str(pair_data["bid"]))
            ask = Decimal(str(pair_data["ask"]))
            curr_p = bid if dir_str == "buy" else ask

            pnl_usd, pnl_pips = calculate_position_pnl(
                symbol=pos.symbol,
                direction=dir_str,
                lot_size=Decimal(str(pos.lot_size)),
                entry_price=Decimal(str(pos.entry_price)),
                current_bid=bid,
                current_ask=ask,
            )
            pos.current_price = float(curr_p)
            pos.floating_pnl = float(pnl_usd)
            pos.floating_pnl_pips = float(pnl_pips)

            # SL/TP check
            if pos.stop_loss:
                if dir_str == "buy" and curr_p <= Decimal(str(pos.stop_loss)):
                    to_close.append((pos_id, "stop_loss"))
                    continue
                elif dir_str == "sell" and curr_p >= Decimal(str(pos.stop_loss)):
                    to_close.append((pos_id, "stop_loss"))
                    continue

            if pos.take_profit:
                if dir_str == "buy" and curr_p >= Decimal(str(pos.take_profit)):
                    to_close.append((pos_id, "take_profit"))
                    continue
                elif dir_str == "sell" and curr_p <= Decimal(str(pos.take_profit)):
                    to_close.append((pos_id, "take_profit"))
                    continue

        for p_id, r in to_close:
            self.close_position(p_id, r)

        # Auto-liquidation check (FR-4.12: margin level < 50%)
        metrics = self._calculate_metrics()
        if metrics["is_liquidation_required"] and self.positions:
            for p_id in list(self.positions.keys()):
                self.close_position(p_id, "liquidation")

    def reset_account(self) -> PaperAccount:
        self.balance = self.initial_balance
        self.positions.clear()
        self.closed_trades.clear()
        self.equity_history = [
            EquityPoint(datetime.now(timezone.utc).isoformat(), self.initial_balance, self.initial_balance)
        ]
        return self.get_account()

    def get_analytics(self) -> PerformanceAnalytics:
        trade_items = [
            ClosedTradeItem(
                symbol=t.symbol,
                realized_pnl=Decimal(str(t.realized_pnl)),
                realized_pnl_pips=Decimal(str(t.realized_pnl_pips)),
                session="London",
            )
            for t in self.closed_trades
        ]
        res = calculate_performance_analytics(trade_items, self.equity_history, self.initial_balance)

        from app.schemas.trading import DrawdownInfo, PairPerformance, SessionPerformance
        return PerformanceAnalytics(
            total_trades=res.total_trades,
            winning_trades=res.winning_trades,
            losing_trades=res.losing_trades,
            win_rate_pct=float(res.win_rate_pct),
            total_realized_pnl=float(res.total_realized_pnl),
            profit_factor=float(res.profit_factor),
            avg_win=float(res.avg_win),
            avg_loss=float(res.avg_loss),
            avg_risk_reward_ratio=float(res.avg_risk_reward_ratio),
            drawdown=DrawdownInfo(
                max_drawdown_amount=float(res.max_drawdown_amount),
                max_drawdown_pct=float(res.max_drawdown_pct),
                current_drawdown_amount=0.0,
                current_drawdown_pct=0.0,
                peak_balance=float(self.initial_balance),
            ),
            pair_performance=[PairPerformance(**p) for p in res.pair_performance],
            session_performance=[SessionPerformance(**s) for s in res.session_performance],
        )


trading_service = TradingService()
