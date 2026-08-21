"""Forex Top-Down Confluence Toolkit - the strategy calculation engine.

Pure, independently testable functions over OHLC data. Nothing here imports
FastAPI or touches a database; the API layer and the UI are consumers.

Module map (numbers match the build brief):

===  ===========================  ===================================
 1   :mod:`.reference`            Pair & market basics, resources, rules
 2   :mod:`.sessions`             Trading session clock (IST + local)
 3   :mod:`.structure`            HH/HL/LH/LL, CHoCH, snake-trick trace
 4   :mod:`.topdown`              Trend dashboard + timeframe sync gate
 5   :mod:`.aoi`                  Area of Interest detector & validator
 6   :mod:`.break_retest`         Break & retest / structure-shift trigger
 7   :mod:`.patterns`             Candlestick pattern recognizer
 8   :mod:`.head_shoulders`       Head & Shoulders (+ inverse) & neckline
 9   :mod:`.indicators`           50 EMA overlay (supplementary only)
10   :mod:`.confluence`           Core 4 pillars + expanded checklist score
11   :mod:`.risk`                 Risk table, sizing, RR floor, weekly pace
12   :mod:`.journal`              Trade journal + weekly view
13   :mod:`.reference`            Tools, brokers, guiding principle
14   :mod:`.reference`            Discipline guardrail messaging
===  ===========================  ===================================

Every uncertain number lives in :mod:`.config`.
"""

from . import (  # noqa: F401
    aoi,
    break_retest,
    config,
    confluence,
    data_input,
    engine,
    head_shoulders,
    indicators,
    journal,
    patterns,
    pips,
    reference,
    risk,
    sample_data,
    sessions,
    structure,
    topdown,
    types,
)
from .engine import StrategyAnalysis, analyse  # noqa: F401
from .types import (  # noqa: F401
    AOIZone,
    BreakRetestSignal,
    Candle,
    ConfluenceResult,
    Direction,
    HeadShouldersPattern,
    PatternMatch,
    StructureLabel,
    StructureResult,
    SwingPoint,
    TradePlan,
    Trend,
    ZoneType,
)

__all__ = [
    "analyse",
    "StrategyAnalysis",
    "Candle",
    "Trend",
    "Direction",
    "AOIZone",
    "BreakRetestSignal",
    "PatternMatch",
    "HeadShouldersPattern",
    "ConfluenceResult",
    "TradePlan",
    "StructureResult",
    "StructureLabel",
    "SwingPoint",
    "ZoneType",
    "config",
]
