"""Module 2 - Trading session clock.

Session windows are stated in IST in the notes and are stored that way in
``config.SESSIONS_IST``. Everything here converts through UTC so the same
clock can be rendered in any viewer's local timezone.

The primary window - pre-London open through London close, 11:30-20:30 IST -
is tracked separately and flagged in real time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from typing import List, Optional

from . import config

IST = timezone(timedelta(minutes=config.IST_UTC_OFFSET_MINUTES))


@dataclass
class SessionWindow:
    """One trading session, with its state at a given instant."""

    name: str
    open_ist: str
    close_ist: str
    open_utc: str
    close_utc: str
    is_active: bool
    #: True when the window runs past midnight IST (New York does).
    crosses_midnight: bool
    minutes_until_open: Optional[int] = None
    minutes_until_close: Optional[int] = None


@dataclass
class SessionClock:
    """Every session plus the primary-window flag, at one instant."""

    now_utc: datetime
    now_ist: datetime
    sessions: List[SessionWindow] = field(default_factory=list)
    active_sessions: List[str] = field(default_factory=list)
    overlap: Optional[str] = None
    in_primary_window: bool = False
    primary_window_ist: str = ""
    minutes_until_primary_open: Optional[int] = None
    minutes_until_primary_close: Optional[int] = None
    message: str = ""


def _parse(hhmm: str) -> time:
    hour, minute = hhmm.split(":")
    return time(int(hour), int(minute))


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _in_window(now_min: int, start_min: int, end_min: int) -> bool:
    """Handles windows that wrap past midnight (e.g. 19:00 -> 01:30)."""
    if start_min <= end_min:
        return start_min <= now_min < end_min
    return now_min >= start_min or now_min < end_min


def _until(now_min: int, target_min: int) -> int:
    """Minutes from now until ``target_min``, wrapping across the day."""
    delta = target_min - now_min
    return delta if delta >= 0 else delta + 24 * 60


def _to_utc_string(hhmm: str) -> str:
    """Render an IST wall-clock time as its UTC equivalent."""
    total = _minutes(_parse(hhmm)) - config.IST_UTC_OFFSET_MINUTES
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}"


def session_clock(now: Optional[datetime] = None) -> SessionClock:
    """Build the session clock for an instant.

    Args:
        now: any timezone-aware datetime. Defaults to the current UTC time.
            A naive datetime is assumed to be UTC.

    Returns:
        A :class:`SessionClock` describing which sessions are open, whether
        any overlap, and whether we are inside the primary trading window.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    now_utc = now.astimezone(timezone.utc)
    now_ist = now.astimezone(IST)
    now_min = now_ist.hour * 60 + now_ist.minute

    clock = SessionClock(
        now_utc=now_utc,
        now_ist=now_ist,
        primary_window_ist=(
            f"{config.PRIMARY_WINDOW_IST[0]} - {config.PRIMARY_WINDOW_IST[1]} IST"
        ),
    )

    for name, open_ist, close_ist in config.SESSIONS_IST:
        start = _minutes(_parse(open_ist))
        end = _minutes(_parse(close_ist))
        active = _in_window(now_min, start, end)

        clock.sessions.append(
            SessionWindow(
                name=name,
                open_ist=open_ist,
                close_ist=close_ist,
                open_utc=_to_utc_string(open_ist),
                close_utc=_to_utc_string(close_ist),
                is_active=active,
                crosses_midnight=start > end,
                minutes_until_open=None if active else _until(now_min, start),
                minutes_until_close=_until(now_min, end) if active else None,
            )
        )
        if active:
            clock.active_sessions.append(name)

    if len(clock.active_sessions) > 1:
        clock.overlap = " + ".join(clock.active_sessions) + " overlap"

    p_start = _minutes(_parse(config.PRIMARY_WINDOW_IST[0]))
    p_end = _minutes(_parse(config.PRIMARY_WINDOW_IST[1]))
    clock.in_primary_window = _in_window(now_min, p_start, p_end)

    if clock.in_primary_window:
        clock.minutes_until_primary_close = _until(now_min, p_end)
        mins = clock.minutes_until_primary_close
        clock.message = (
            f"Inside the primary window (pre-London through London close). "
            f"{mins // 60}h {mins % 60}m left."
        )
    else:
        clock.minutes_until_primary_open = _until(now_min, p_start)
        mins = clock.minutes_until_primary_open
        clock.message = (
            f"Outside the primary window. Opens in {mins // 60}h {mins % 60}m "
            f"({clock.primary_window_ist})."
        )

    return clock
