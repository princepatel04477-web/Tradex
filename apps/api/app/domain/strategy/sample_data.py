"""Deterministic sample OHLC datasets.

Every scenario here is built from an explicit price path, so opening the tool
shows real computed output rather than empty states: structure that labels,
an AOI that validates (or is correctly refused), a break & retest that arms,
candlestick and H&S patterns that fire, and a confluence score.

The same waypoint path is rendered at every timeframe with different candle
granularity, so the levels agree across 1W / 1D / 4H / 1H as they would on a
real chart.

Nothing here is random at runtime - each scenario is seeded, so tests and the
demo see identical bars on every run.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Sequence

from .pips import from_pips, pip_size
from .types import Candle

#: Hours per candle, used to space timestamps.
TIMEFRAME_HOURS: Dict[str, float] = {
    "1W": 168.0,
    "1D": 24.0,
    "4H": 4.0,
    "2H": 2.0,
    "1H": 1.0,
    "30M": 0.5,
    "15M": 0.25,
}

#: Candles rendered per waypoint leg, per timeframe.
CANDLES_PER_LEG: Dict[str, int] = {
    "1W": 4,
    "1D": 9,
    "4H": 16,
    "2H": 20,
    "1H": 24,
    "30M": 28,
    "15M": 32,
}


@dataclass
class Scenario:
    """A named price path plus what it is meant to demonstrate."""

    key: str
    symbol: str
    title: str
    description: str
    waypoints: List[float]
    demonstrates: List[str] = field(default_factory=list)
    inject_pattern: str = ""  # "" | "bullish_engulfing" | "morning_star" | "evening_star"
    seed: int = 7


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

SCENARIOS: Dict[str, Scenario] = {
    "eurusd_bullish_aoi": Scenario(
        key="eurusd_bullish_aoi",
        symbol="EUR_USD",
        title="EUR/USD - bullish structure into a validated support AOI",
        description=(
            "Rising highs and near-equal lows build a 12-pip support zone that "
            "gets tested four times. Price then breaks the zone's upper edge, "
            "retests it and holds, with a bullish reversal formation printed at "
            "the zone."
        ),
        # Lows creep up (1.0800 -> 1.0812) forming HLs inside one tight zone;
        # highs step up (1.1000 -> 1.1200) forming HHs.
        waypoints=[
            1.09500,
            1.08000,
            1.10000,
            1.08040,
            1.10500,
            1.08080,
            1.11000,
            1.08120,
            1.12000,
            1.08300,
            1.09200,
        ],
        demonstrates=[
            "Bullish HH/HL structure on 1W, 1D and 4H",
            "Valid Daily AOI: 4 touches, ~12 pips wide, Buy zone",
            "Break & retest of the AOI upper edge",
            "Bullish reversal candle at the AOI",
            "Full confluence score and a sized trade plan",
        ],
        inject_pattern="bullish_engulfing",
        seed=11,
    ),
    "gbpusd_head_shoulders": Scenario(
        key="gbpusd_head_shoulders",
        symbol="GBP_USD",
        title="GBP/USD - Head & Shoulders with a broken, retested neckline",
        description=(
            "Left shoulder, higher head, matching right shoulder, then a body "
            "close through the neckline followed by a retest that holds. The "
            "neckline retest is the AOI retest - the same event."
        ),
        waypoints=[
            1.24000,
            1.27000,  # left shoulder
            1.25500,  # neckline anchor A
            1.29000,  # head
            1.25600,  # neckline anchor B
            1.27200,  # right shoulder
            1.24500,  # neckline break
            1.25680,  # retest pokes back into the broken neckline
            1.22800,  # measured move down
        ],
        demonstrates=[
            "Head & Shoulders identified from swing structure",
            "Neckline computed and drawn between the two troughs",
            "Pattern invalid until the neckline breaks",
            "Break-and-retest of the neckline as the trigger",
        ],
        inject_pattern="evening_star",
        seed=23,
    ),
    "usdjpy_no_setup": Scenario(
        key="usdjpy_no_setup",
        symbol="USD_JPY",
        title="USD/JPY - deliberately no valid setup",
        description=(
            "Wide, directionless swings with no level tested three times inside "
            "60 pips. The engine must refuse to find an AOI here and say so "
            "rather than relaxing a rule."
        ),
        # A clean staircase: every pivot is hundreds of pips from every other,
        # so no cluster can gather three reactions inside the 60-pip limit.
        # Levels are crossed in passing but never respected twice.
        waypoints=[
            150.00,
            154.00,
            152.50,
            157.00,
            155.00,
            160.00,
            158.00,
            163.00,
        ],
        demonstrates=[
            "Correct refusal: no AOI, and the discipline message that follows",
            "JPY pip handling (0.01, not 0.0001)",
        ],
        seed=5,
    ),
}


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def _leg_candles(
    rng: random.Random,
    symbol: str,
    start_price: float,
    target_price: float,
    count: int,
    start_time: datetime,
    step_hours: float,
    noise_pips: float,
) -> List[Candle]:
    """Render one waypoint leg as ``count`` candles ending exactly at ``target``.

    The final candle of the leg puts its wick precisely on the target and
    closes back off it, so the turning point is a clean pivot at a known price
    - which is what makes the AOI touch count reproducible.
    """
    candles: List[Candle] = []
    price = start_price
    total = target_price - start_price
    step = total / count
    rising = total > 0
    noise = from_pips(noise_pips, symbol)
    wick = from_pips(max(noise_pips * 0.8, 0.5), symbol)

    for k in range(count):
        is_last = k == count - 1
        open_price = price

        if is_last:
            close_price = target_price - (step * 0.35)
            high = max(open_price, close_price) + wick * 0.4
            low = min(open_price, close_price) - wick * 0.4
            # Put the exact waypoint on the wick, but never at the cost of a
            # valid bar: noise can leave the open beyond the target, and a
            # high below the open is not a candle.
            if rising:
                high = max(high, target_price)
            else:
                low = min(low, target_price)
        else:
            drift = step * (1.0 + rng.uniform(-0.25, 0.25))
            close_price = open_price + drift + rng.uniform(-noise, noise)
            high = max(open_price, close_price) + abs(rng.gauss(0, wick))
            low = min(open_price, close_price) - abs(rng.gauss(0, wick))

        candles.append(
            Candle(
                time=start_time + timedelta(hours=step_hours * k),
                open=round(open_price, 6),
                high=round(high, 6),
                low=round(low, 6),
                close=round(close_price, 6),
                volume=round(rng.uniform(800, 2400)),
            )
        )
        price = close_price

    return candles


def _inject_pattern(
    candles: List[Candle], kind: str, symbol: str, at_index: int
) -> None:
    """Overwrite a few candles so a named formation prints at a known place.

    Sample data has to *demonstrate* the pattern recognizer, so the reversal
    candles at the final AOI touch are shaped deliberately instead of being
    left to the noise generator.
    """
    if not kind or at_index < 2 or at_index >= len(candles):
        return

    unit = pip_size(symbol)
    anchor = candles[at_index].low if kind != "evening_star" else candles[at_index].high

    if kind == "bullish_engulfing":
        prev = Candle(
            time=candles[at_index - 1].time,
            open=anchor + 14 * unit,
            high=anchor + 16 * unit,
            low=anchor + 2 * unit,
            close=anchor + 5 * unit,
            volume=candles[at_index - 1].volume,
        )
        cur = Candle(
            time=candles[at_index].time,
            open=anchor + 3 * unit,
            high=anchor + 26 * unit,
            low=anchor,
            close=anchor + 24 * unit,
            volume=candles[at_index].volume,
        )
        candles[at_index - 1] = prev
        candles[at_index] = cur

    elif kind == "morning_star":
        candles[at_index - 2] = Candle(
            time=candles[at_index - 2].time,
            open=anchor + 30 * unit,
            high=anchor + 32 * unit,
            low=anchor + 6 * unit,
            close=anchor + 8 * unit,
            volume=candles[at_index - 2].volume,
        )
        candles[at_index - 1] = Candle(
            time=candles[at_index - 1].time,
            open=anchor + 6 * unit,
            high=anchor + 9 * unit,
            low=anchor,
            close=anchor + 5 * unit,
            volume=candles[at_index - 1].volume,
        )
        candles[at_index] = Candle(
            time=candles[at_index].time,
            open=anchor + 6 * unit,
            high=anchor + 28 * unit,
            low=anchor + 4 * unit,
            close=anchor + 26 * unit,
            volume=candles[at_index].volume,
        )

    elif kind == "evening_star":
        candles[at_index - 2] = Candle(
            time=candles[at_index - 2].time,
            open=anchor - 30 * unit,
            high=anchor - 6 * unit,
            low=anchor - 32 * unit,
            close=anchor - 8 * unit,
            volume=candles[at_index - 2].volume,
        )
        candles[at_index - 1] = Candle(
            time=candles[at_index - 1].time,
            open=anchor - 6 * unit,
            high=anchor,
            low=anchor - 9 * unit,
            close=anchor - 5 * unit,
            volume=candles[at_index - 1].volume,
        )
        candles[at_index] = Candle(
            time=candles[at_index].time,
            open=anchor - 6 * unit,
            high=anchor - 4 * unit,
            low=anchor - 28 * unit,
            close=anchor - 26 * unit,
            volume=candles[at_index].volume,
        )


def generate_series(
    scenario: Scenario,
    timeframe: str,
    end_time: datetime | None = None,
) -> List[Candle]:
    """Render one scenario at one timeframe.

    Args:
        scenario: the price path to render.
        timeframe: one of ``TIMEFRAME_HOURS``.
        end_time: timestamp of the final candle; defaults to now (UTC).

    Returns:
        Chronological candles ending at ``end_time``.
    """
    if timeframe not in TIMEFRAME_HOURS:
        raise ValueError(f"Unknown timeframe {timeframe!r}")

    # Seed from the characters of the label, never from hash(): Python
    # randomises string hashing per process, which would make "deterministic"
    # sample data differ between runs.
    tf_seed = sum(ord(ch) * (i + 1) for i, ch in enumerate(timeframe))
    rng = random.Random(scenario.seed * 1_000 + tf_seed)
    per_leg = CANDLES_PER_LEG[timeframe]
    step_hours = TIMEFRAME_HOURS[timeframe]

    # Lower timeframes ride the same path with proportionally smaller noise.
    noise_pips = {"1W": 6.0, "1D": 4.0, "4H": 2.5, "2H": 2.0}.get(timeframe, 1.5)
    if scenario.symbol.endswith("JPY"):
        noise_pips *= 1.2

    total = per_leg * (len(scenario.waypoints) - 1)
    if end_time is None:
        end_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=step_hours * (total - 1))

    candles: List[Candle] = []
    cursor = start_time
    for i in range(len(scenario.waypoints) - 1):
        leg = _leg_candles(
            rng,
            scenario.symbol,
            scenario.waypoints[i],
            scenario.waypoints[i + 1],
            per_leg,
            cursor,
            step_hours,
            noise_pips,
        )
        candles.extend(leg)
        cursor = cursor + timedelta(hours=step_hours * per_leg)

    # Print the named formation at the last major turning point, which is where
    # the AOI reaction happens.
    if scenario.inject_pattern:
        turn_index = per_leg * (len(scenario.waypoints) - 3) - 1
        _inject_pattern(candles, scenario.inject_pattern, scenario.symbol, turn_index)

    return candles


def generate_all_timeframes(
    scenario_key: str,
    timeframes: Sequence[str] | None = None,
    end_time: datetime | None = None,
) -> Dict[str, List[Candle]]:
    """Render a scenario across every timeframe the engine uses.

    Args:
        scenario_key: key into :data:`SCENARIOS`.
        timeframes: defaults to all seven.
        end_time: timestamp of the final candle.

    Returns:
        Candle series keyed by timeframe.
    """
    scenario = get_scenario(scenario_key)
    tfs = timeframes or tuple(TIMEFRAME_HOURS.keys())
    return {tf: generate_series(scenario, tf, end_time) for tf in tfs}


def get_scenario(key: str) -> Scenario:
    if key not in SCENARIOS:
        raise KeyError(
            f"Unknown scenario {key!r}. Available: {', '.join(SCENARIOS)}"
        )
    return SCENARIOS[key]


def list_scenarios() -> List[Dict]:
    """Scenario catalogue for the UI's dataset picker."""
    return [
        {
            "key": s.key,
            "symbol": s.symbol,
            "title": s.title,
            "description": s.description,
            "demonstrates": s.demonstrates,
        }
        for s in SCENARIOS.values()
    ]


def candles_to_csv(candles: List[Candle]) -> str:
    """Serialise candles as CSV - the same shape the importer accepts."""
    lines = ["time,open,high,low,close,volume"]
    for c in candles:
        lines.append(
            f"{c.time.isoformat()},{c.open},{c.high},{c.low},{c.close},{c.volume:g}"
        )
    return "\n".join(lines)
