"""Forex trading session clock and overlap computation (SRS Appendix B).

Session Windows (UTC):
- Sydney: 21:00 to 06:00 UTC (AUD/NZD pairs active)
- Tokyo: 00:00 to 09:00 UTC (JPY pairs active)
- London: 07:00 to 16:00 UTC (EUR/GBP pairs active, highest volume)
- New York: 12:00 to 21:00 UTC (USD pairs dominant, high volatility)
- London-NY Overlap: 12:00 to 16:00 UTC (Peak liquidity & volatility window)
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, NamedTuple


class SessionInfo(NamedTuple):
    name: str
    is_active: bool
    open_utc: str
    close_utc: str
    description: str


def get_market_sessions_overview(utc_dt: Optional[datetime] = None) -> dict:
    """Compute active market sessions and active overlap status for the given UTC time."""
    now = utc_dt or datetime.now(timezone.utc)
    cur_hour = now.hour + (now.minute / 60.0)

    # Sydney: 21:00 - 06:00 UTC (crosses midnight)
    sydney_active = (cur_hour >= 21.0) or (cur_hour < 6.0)
    # Tokyo: 00:00 - 09:00 UTC
    tokyo_active = 0.0 <= cur_hour < 9.0
    # London: 07:00 - 16:00 UTC
    london_active = 7.0 <= cur_hour < 16.0
    # New York: 12:00 - 21:00 UTC
    ny_active = 12.0 <= cur_hour < 21.0

    sessions = [
        SessionInfo("Sydney", sydney_active, "21:00", "06:00", "Lower volatility; AUD/NZD pairs most active"),
        SessionInfo("Tokyo", tokyo_active, "00:00", "09:00", "JPY pairs active; range-bound tendency"),
        SessionInfo("London", london_active, "07:00", "16:00", "Highest volume globally; EUR/GBP pairs active"),
        SessionInfo("New York", ny_active, "12:00", "21:00", "High volatility; USD pairs dominant"),
    ]

    overlap = None
    if 12.0 <= cur_hour < 16.0:
        overlap = "London–NY Overlap (Peak Liquidity & Volatility)"
    elif 0.0 <= cur_hour < 6.0:
        overlap = "Sydney–Tokyo Overlap"

    return {
        "sessions": [
            {
                "name": s.name,
                "is_active": s.is_active,
                "open_utc": s.open_utc,
                "close_utc": s.close_utc,
                "description": s.description,
            }
            for s in sessions
        ],
        "active_overlap": overlap,
        "current_utc_time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
