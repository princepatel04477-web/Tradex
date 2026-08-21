"""Data input - CSV / manual OHLC paste, plus an optional live source.

CSV and paste are the baseline and always work offline. A free-tier live
provider sits behind ``TRADLY_LIVE_DATA`` and never blocks anything: if the
flag is off or the request fails, callers fall back to sample or uploaded data.
"""

from __future__ import annotations

import csv
import io
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence

from .types import Candle

#: Accepted header spellings, mapped to the canonical field.
_ALIASES: Dict[str, str] = {
    "time": "time",
    "date": "time",
    "datetime": "time",
    "timestamp": "time",
    "open_time": "time",
    "open": "open",
    "o": "open",
    "high": "high",
    "h": "high",
    "low": "low",
    "l": "low",
    "close": "close",
    "c": "close",
    "adj close": "close",
    "volume": "volume",
    "vol": "volume",
    "v": "volume",
}

_TIME_FORMATS: Sequence[str] = (
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
    "%m/%d/%Y",
)


def parse_time(value: str) -> datetime:
    """Parse a timestamp from any of the common chart-export formats.

    Args:
        value: the raw cell value. Epoch seconds/milliseconds are accepted too.

    Returns:
        A timezone-aware UTC datetime.

    Raises:
        ValueError: if nothing parses.
    """
    raw = value.strip()
    if not raw:
        raise ValueError("Empty timestamp")

    if raw.isdigit():
        number = int(raw)
        if number > 10_000_000_000:  # milliseconds
            number //= 1000
        return datetime.fromtimestamp(number, tz=timezone.utc)

    normalised = raw.replace("Z", "+0000")
    for fmt in _TIME_FORMATS:
        try:
            parsed = datetime.strptime(normalised, fmt)
        except ValueError:
            continue
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    try:
        parsed = datetime.fromisoformat(raw)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"Unrecognised timestamp: {value!r}") from exc


def parse_ohlc_csv(text: str) -> List[Candle]:
    """Parse pasted or uploaded OHLC data.

    Accepts comma, semicolon or tab delimiters, any column order, and the
    header spellings in :data:`_ALIASES`. Rows that fail to parse are skipped
    rather than failing the whole import.

    Args:
        text: the raw CSV body, including its header row.

    Returns:
        Candles sorted chronologically.

    Raises:
        ValueError: if the header is missing a required column, or no row parsed.
    """
    stripped = text.strip()
    if not stripped:
        raise ValueError("No data supplied")

    sample = stripped.splitlines()[0]
    delimiter = "\t" if "\t" in sample else (";" if ";" in sample else ",")

    reader = csv.reader(io.StringIO(stripped), delimiter=delimiter)
    rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    if len(rows) < 2:
        raise ValueError("Need a header row and at least one data row")

    header = [_ALIASES.get(cell.strip().lower(), "") for cell in rows[0]]
    missing = {"time", "open", "high", "low", "close"} - set(header)
    if missing:
        raise ValueError(
            f"Missing required column(s): {', '.join(sorted(missing))}. "
            f"Expected headers like: time,open,high,low,close[,volume]"
        )

    index = {name: i for i, name in enumerate(header) if name}
    candles: List[Candle] = []

    for row in rows[1:]:
        try:
            candle = Candle(
                time=parse_time(row[index["time"]]),
                open=float(row[index["open"]]),
                high=float(row[index["high"]]),
                low=float(row[index["low"]]),
                close=float(row[index["close"]]),
                volume=(
                    float(row[index["volume"]])
                    if "volume" in index and index["volume"] < len(row)
                    and row[index["volume"]].strip()
                    else 0.0
                ),
            )
        except (ValueError, IndexError, KeyError):
            continue

        if candle.high < candle.low:
            continue
        candles.append(candle)

    if not candles:
        raise ValueError("No rows parsed - check the delimiter and column headers")

    candles.sort(key=lambda c: c.time)
    return candles


# ---------------------------------------------------------------------------
# Optional live source
# ---------------------------------------------------------------------------


def live_data_enabled() -> bool:
    """Whether the optional live OHLC source is switched on."""
    return os.getenv("TRADLY_LIVE_DATA", "").strip().lower() in ("1", "true", "yes", "on")


def fetch_live_candles(
    symbol: str, timeframe: str, limit: int = 300
) -> Optional[List[Candle]]:
    """Fetch candles from the configured provider, or ``None``.

    Deliberately best-effort: any failure returns ``None`` so the caller falls
    back to sample or uploaded data. Configure with::

        TRADLY_LIVE_DATA=1
        TRADLY_LIVE_PROVIDER=twelvedata
        TRADLY_LIVE_API_KEY=...

    Args:
        symbol: pair, e.g. ``EUR_USD``.
        timeframe: engine timeframe label.
        limit: how many candles to request.

    Returns:
        Candles, or ``None`` when live data is off or unavailable.
    """
    if not live_data_enabled():
        return None

    api_key = os.getenv("TRADLY_LIVE_API_KEY", "").strip()
    if not api_key:
        return None

    interval = {
        "1W": "1week",
        "1D": "1day",
        "4H": "4h",
        "2H": "2h",
        "1H": "1h",
        "30M": "30min",
        "15M": "15min",
    }.get(timeframe)
    if interval is None:
        return None

    try:
        import requests  # imported lazily so the engine has no hard dependency

        response = requests.get(
            "https://api.twelvedata.com/time_series",
            params={
                "symbol": symbol.replace("_", "/"),
                "interval": interval,
                "outputsize": limit,
                "apikey": api_key,
                "format": "JSON",
            },
            timeout=10,
        )
        payload = response.json()
        values = payload.get("values")
        if not values:
            return None

        candles = [
            Candle(
                time=parse_time(row["datetime"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume") or 0.0),
            )
            for row in values
        ]
        candles.sort(key=lambda c: c.time)
        return candles
    except Exception:
        # Live data must never break the rest of the build.
        return None
