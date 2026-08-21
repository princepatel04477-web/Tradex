"""Module 12 - Trade journal.

Every logged trade carries the whole decision trail: which timeframes were in
sync, which AOI was used, which patterns confirmed, the confluence score, the
levels, the resulting RR and the outcome. The weekly view feeds the
"1 trade a week" pacer directly.

Storage is in-memory, matching the rest of the backend's services. Swapping in
Postgres later means replacing ``JournalStore`` only - nothing else imports the
list.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from . import config
from .risk import WeeklyPace, set_and_forget_notice, week_bounds, weekly_pace


@dataclass
class JournalEntry:
    """One trade, from decision to outcome."""

    id: str
    symbol: str
    direction: str
    placed_at: datetime

    # --- the decision trail ---
    sync_state: str = ""
    sync_timeframes: List[str] = field(default_factory=list)
    aoi_zone: Optional[str] = None
    aoi_timeframe: Optional[str] = None
    aoi_touches: int = 0
    patterns: List[str] = field(default_factory=list)
    confluence_score: int = 0
    confluence_max: int = 0
    low_risk_high_reward: bool = False

    # --- the levels ---
    entry: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    planned_rr: float = 0.0
    position_size_lots: float = 0.0
    risk_amount: float = 0.0

    # --- the result ---
    outcome: str = "open"  # open | win | loss | breakeven | cancelled
    exit_price: Optional[float] = None
    closed_at: Optional[datetime] = None
    realised_rr: Optional[float] = None
    pnl: Optional[float] = None
    notes: str = ""
    tags: List[str] = field(default_factory=list)

    #: Set & Forget - true once placed, which makes level edits friction-gated.
    is_placed: bool = True

    @property
    def week_key(self) -> str:
        """ISO year-week the trade belongs to, e.g. ``2026-W34``."""
        year, week, _ = self.placed_at.isocalendar()
        return f"{year}-W{week:02d}"


class JournalStore:
    """In-memory trade journal."""

    def __init__(self) -> None:
        self._entries: Dict[str, JournalEntry] = {}

    # -- writes ------------------------------------------------------------

    def log(self, **fields) -> JournalEntry:
        """Log a trade.

        Args:
            **fields: any :class:`JournalEntry` field. ``symbol`` and
                ``direction`` are required; ``id`` and ``placed_at`` default.

        Returns:
            The stored entry.
        """
        entry_id = fields.pop("id", None) or uuid.uuid4().hex[:12]
        placed_at = fields.pop("placed_at", None) or datetime.now(timezone.utc)
        if placed_at.tzinfo is None:
            placed_at = placed_at.replace(tzinfo=timezone.utc)

        entry = JournalEntry(
            id=entry_id,
            symbol=fields.pop("symbol"),
            direction=fields.pop("direction"),
            placed_at=placed_at,
            **fields,
        )
        self._entries[entry.id] = entry
        return entry

    def close(
        self,
        entry_id: str,
        exit_price: float,
        outcome: Optional[str] = None,
        closed_at: Optional[datetime] = None,
        pnl: Optional[float] = None,
    ) -> JournalEntry:
        """Close a trade and compute its realised RR.

        Args:
            entry_id: id of the trade.
            exit_price: price the trade closed at.
            outcome: win/loss/breakeven. Derived from the exit price if omitted.
            closed_at: close time; defaults to now.
            pnl: realised profit or loss in account currency, if known.

        Returns:
            The updated entry.

        Raises:
            KeyError: if the trade does not exist.
        """
        entry = self.get(entry_id)
        entry.exit_price = exit_price
        entry.closed_at = closed_at or datetime.now(timezone.utc)
        entry.pnl = pnl

        risk = abs(entry.entry - entry.stop_loss)
        if risk > 0:
            move = (
                exit_price - entry.entry
                if entry.direction == "buy"
                else entry.entry - exit_price
            )
            entry.realised_rr = round(move / risk, 2)

        if outcome:
            entry.outcome = outcome
        elif entry.realised_rr is None:
            entry.outcome = "breakeven"
        elif entry.realised_rr > 0.05:
            entry.outcome = "win"
        elif entry.realised_rr < -0.05:
            entry.outcome = "loss"
        else:
            entry.outcome = "breakeven"

        return entry

    def annotate(
        self,
        entry_id: str,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> JournalEntry:
        """Attach free-text notes or tags. Always allowed - never level edits."""
        entry = self.get(entry_id)
        if notes is not None:
            entry.notes = notes
        if tags is not None:
            entry.tags = tags
        return entry

    def edit_levels(
        self,
        entry_id: str,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        acknowledge_set_and_forget: bool = False,
    ) -> tuple:
        """Edit a placed trade's levels - deliberately gated by friction.

        Args:
            entry_id: id of the trade.
            entry_price / stop_loss / take_profit: new levels.
            acknowledge_set_and_forget: the caller must explicitly acknowledge
                the Set & Forget rule for the edit to apply.

        Returns:
            ``(entry, notice)``. When ``notice`` is non-empty and the caller has
            not acknowledged it, nothing was changed.
        """
        entry = self.get(entry_id)
        notice = set_and_forget_notice(entry.is_placed)

        if notice and not acknowledge_set_and_forget:
            return entry, notice

        if entry_price is not None:
            entry.entry = entry_price
        if stop_loss is not None:
            entry.stop_loss = stop_loss
        if take_profit is not None:
            entry.take_profit = take_profit

        risk = abs(entry.entry - entry.stop_loss)
        if risk > 0:
            entry.planned_rr = round(abs(entry.take_profit - entry.entry) / risk, 2)

        return entry, ""

    def delete(self, entry_id: str) -> bool:
        return self._entries.pop(entry_id, None) is not None

    def reset(self) -> None:
        self._entries.clear()

    # -- reads -------------------------------------------------------------

    def get(self, entry_id: str) -> JournalEntry:
        if entry_id not in self._entries:
            raise KeyError(f"No journal entry {entry_id!r}")
        return self._entries[entry_id]

    def all(self) -> List[JournalEntry]:
        return sorted(self._entries.values(), key=lambda e: e.placed_at, reverse=True)

    def for_week(self, now: Optional[datetime] = None) -> List[JournalEntry]:
        start, end = week_bounds(now)
        return [e for e in self.all() if start <= e.placed_at < end]

    def pace(self, now: Optional[datetime] = None) -> WeeklyPace:
        """The "1 trade a week" state, derived from logged trades."""
        return weekly_pace([e.placed_at for e in self._entries.values()], now)

    def stats(self) -> Dict[str, float]:
        """Aggregate performance across closed trades."""
        closed = [e for e in self._entries.values() if e.outcome in ("win", "loss", "breakeven")]
        if not closed:
            return {
                "closed_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "average_rr": 0.0,
                "average_confluence": 0.0,
                "total_pnl": 0.0,
            }

        wins = [e for e in closed if e.outcome == "win"]
        losses = [e for e in closed if e.outcome == "loss"]
        rrs = [e.realised_rr for e in closed if e.realised_rr is not None]
        pnls = [e.pnl for e in closed if e.pnl is not None]

        return {
            "closed_trades": len(closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / len(closed) * 100, 1),
            "average_rr": round(sum(rrs) / len(rrs), 2) if rrs else 0.0,
            "average_confluence": round(
                sum(e.confluence_score for e in closed) / len(closed), 1
            ),
            "total_pnl": round(sum(pnls), 2) if pnls else 0.0,
        }

    def weekly_view(self) -> List[Dict]:
        """Trades grouped by ISO week, newest first, with the weekly cap shown."""
        buckets: Dict[str, List[JournalEntry]] = {}
        for entry in self.all():
            buckets.setdefault(entry.week_key, []).append(entry)

        return [
            {
                "week": week,
                "trade_count": len(entries),
                "limit": config.MAX_TRADES_PER_WEEK,
                "over_limit": len(entries) > config.MAX_TRADES_PER_WEEK,
                "trades": entries,
            }
            for week, entries in sorted(buckets.items(), reverse=True)
        ]


#: Process-wide journal, mirroring the other services' singleton pattern.
journal_store = JournalStore()
