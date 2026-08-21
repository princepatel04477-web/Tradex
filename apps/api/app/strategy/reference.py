"""Modules 1, 13 & 14 - pair basics, resources and discipline guardrails.

Static reference content, kept in one place so the UI never hardcodes strings.
Module 1's directional logic is a real function, not a paragraph: the API can
answer "what does buying EUR/USD actually mean" for any pair.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from . import config
from .pips import pip_size, split_pair

#: The majors, in the order the notes list them.
MAJOR_PAIRS: tuple = (
    "EUR_USD",
    "GBP_USD",
    "USD_JPY",
    "USD_CHF",
    "USD_CAD",
    "AUD_USD",
    "NZD_USD",
)

CURRENCY_NAMES: Dict[str, str] = {
    "EUR": "Euro",
    "USD": "US Dollar",
    "GBP": "British Pound",
    "JPY": "Japanese Yen",
    "CHF": "Swiss Franc",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "NZD": "New Zealand Dollar",
    "INR": "Indian Rupee",
    "SGD": "Singapore Dollar",
    "MXN": "Mexican Peso",
}

CHART_TYPES: tuple = ("candlestick", "line")


@dataclass
class PairExplainer:
    """Plain-language breakdown of one currency pair."""

    symbol: str
    base: str
    quote: str
    base_name: str
    quote_name: str
    is_major: bool
    pip_size: float
    quote_example: str
    up_means: str
    down_means: str
    buy_when: str
    sell_when: str


def explain_pair(symbol: str, example_rate: Optional[float] = None) -> PairExplainer:
    """Explain base/quote and the directional logic for a pair.

    Args:
        symbol: e.g. ``EUR_USD``.
        example_rate: a rate to use in the worked example. Defaults to 1.10.

    Returns:
        A :class:`PairExplainer`.
    """
    base, quote = split_pair(symbol)
    rate = example_rate if example_rate is not None else 1.10

    return PairExplainer(
        symbol=f"{base}/{quote}",
        base=base,
        quote=quote,
        base_name=CURRENCY_NAMES.get(base, base),
        quote_name=CURRENCY_NAMES.get(quote, quote),
        is_major=f"{base}_{quote}" in MAJOR_PAIRS,
        pip_size=pip_size(symbol),
        quote_example=(
            f"If {base}/{quote} = {rate:g}, then 1 {base} = {rate:g} {quote}."
        ),
        up_means=f"Price up: {base} (the base) is getting stronger.",
        down_means=f"Price down: {quote} (the quote) is getting stronger.",
        buy_when=(
            f"Buy when you expect {base} to strengthen, or {quote} to weaken."
        ),
        sell_when=(
            f"Sell when you expect {quote} to strengthen, or {base} to weaken."
        ),
    )


# ---------------------------------------------------------------------------
# Module 13 - resources
# ---------------------------------------------------------------------------

TOOLS: List[Dict[str, str]] = [
    {
        "name": "TradingView",
        "purpose": "Charting and analysis",
        "url": "https://www.tradingview.com",
    },
    {
        "name": "Forex Factory",
        "purpose": "News and economic calendar",
        "url": "https://www.forexfactory.com",
    },
    {
        "name": "MetaTrader 5",
        "purpose": "Trade execution",
        "url": "https://www.metatrader5.com",
    },
]

BROKERS: List[Dict[str, str]] = [
    {"name": "LQH Markets", "note": "Execution via MT5"},
    {
        "name": "1xTrade",
        "note": (
            "Execution via MT5. Written '1xTrade' in the notes and 'IXTrade' in "
            "the build brief - confirm the spelling."
        ),
    },
    {"name": "Exness", "note": "Execution via MT5"},
]

GUIDING_PRINCIPLE: Dict[str, str] = {
    "title": "Price action over news",
    "body": (
        "Fundamentals are a mystery box - roughly a coin flip, 50% good and 50% "
        "bad. Watch the calendar so a release doesn't blindside a position, but "
        "the edge is price action and structure. No indicator tells you the "
        "trend; the market's own structure does."
    ),
}


# ---------------------------------------------------------------------------
# Module 14 - discipline guardrails
# ---------------------------------------------------------------------------

GOLDEN_RULES: List[str] = [
    "Trend is your friend.",
    "No indicator tells you the trend - market structure does.",
    "Buy = Support. Sell = Resistance.",
    "No AOI, no trade.",
    "AOI needs 3+ touches to be valid; more touches = better.",
    "AOI zone size: minimum 5 pips, maximum 60 pips.",
    "Only look for AOI on Weekly & Daily - never 4H.",
    "You can only enter a trade after a Break & Retest happens.",
    "Candlestick patterns only count when they occur at an AOI.",
    "The higher the time frame, the stronger any pattern/signal.",
    "Selling at the right shoulder of a Head & Shoulders is extremely risky - "
    "wait for the retest.",
    "2 consecutive time frames must sync before a pair is worth trading.",
    "Wait for the work - don't force a trade. If the market doesn't come to "
    "your area, switch pairs.",
    "1 trade a week. Minimum 1:2 RR, aim for 1:4 RR.",
    "Set & forget.",
]

COMMON_MISTAKES: List[Dict[str, str]] = [
    {
        "mistake": "Overtrading",
        "why_fatal": "Increases commission drag, creates emotional exhaustion, and lowers setup quality.",
        "antidote": "Strict 1-trade-a-week pace limit.",
    },
    {
        "mistake": "Trading without AOI",
        "why_fatal": "Entering mid-range creates poor risk-to-reward ratios and false breakouts.",
        "antidote": "Only enter inside Weekly/Daily Zones of Interest.",
    },
    {
        "mistake": "Chasing the breakout",
        "why_fatal": "Buying high into resistance or selling low into support guarantees wide stop losses.",
        "antidote": "Wait for the retest and price rejection confirmation.",
    },
    {
        "mistake": "Moving stop losses",
        "why_fatal": "Turns small controlled losses into catastrophic liquidations.",
        "antidote": "Set & Forget discipline rule.",
    },
]


def guardrail(reason_key: str) -> str:
    """Contextual discipline message for a given failure state."""
    return config.GUARDRAIL_MESSAGES.get(
        reason_key, config.GUARDRAIL_MESSAGES["no_setup"]
    )


def flagged_for_confirmation() -> List[Dict[str, str]]:
    """Every value the engine is running on that the trader has not confirmed."""
    return list(config.FLAGGED_FOR_CONFIRMATION)


@dataclass
class ReferenceTopic:
    id: str
    title: str
    category: str
    summary: str
    details: str
    rules: List[str]
    mistakes: List[Dict[str, str]]


def get_all_reference_topics() -> List[ReferenceTopic]:
    return [
        ReferenceTopic(
            id="market-structure",
            title="Market Structure & Directional Bias",
            category="Trend",
            summary="Market structure (HH/HL or LH/LL) is the only authoritative trend detector.",
            details="Higher Timeframe (1W/1D) structure defines bias. 4H provides the transition bridge, and 15M provides precision trigger timing.",
            rules=GOLDEN_RULES[:3],
            mistakes=COMMON_MISTAKES[1:],
        ),
        ReferenceTopic(
            id="aoi-zones",
            title="Areas of Interest (AOI)",
            category="AOI",
            summary="Key horizontal support and resistance zones identified exclusively on Weekly and Daily charts.",
            details="AOIs represent institutional supply/demand pools where previous major reversals occurred.",
            rules=[GOLDEN_RULES[2], GOLDEN_RULES[3]],
            mistakes=[COMMON_MISTAKES[1]],
        ),
        ReferenceTopic(
            id="risk-management",
            title="Risk Management & Trade Sizing",
            category="Risk",
            summary="Never risk more than your predefined allocation; minimum 1:2 RR, target 1:4.",
            details="Position size is mathematically derived from stop distance in pips and account currency value.",
            rules=[GOLDEN_RULES[6], GOLDEN_RULES[7], GOLDEN_RULES[8]],
            mistakes=[COMMON_MISTAKES[0], COMMON_MISTAKES[3]],
        ),
    ]
