"""Responsible-AI output guard (SRS AI-4.2 / AI-4.3).

AI surfaces may describe evidence and probabilistic tilts, but must never emit a trade instruction:
no buy/sell imperative, no entry price and no position size. Every LLM output passes through
``contains_trade_instruction`` before it can reach a user; offending text is replaced by the
deterministic evidence summary.
"""

import re
from typing import List, Pattern

_ADVICE_PATTERNS: List[Pattern[str]] = [
    re.compile(r"\b(you should|we recommend|i recommend|recommendation is to)\b", re.IGNORECASE),
    re.compile(r"\b(buy|sell|go long|go short|short it|long it)\s+(now|here|at|the|this|eur|gbp|usd|jpy|aud|nzd|cad|chf)\b", re.IGNORECASE),
    re.compile(r"\b(enter|entry|open a (long|short|position))\b.{0,20}\b(at|near|around|price)\b", re.IGNORECASE),
    re.compile(r"\bentry (price|level|point|zone)\b", re.IGNORECASE),
    re.compile(r"\b(position size|lot size|lots?)\b.{0,15}\d", re.IGNORECASE),
    re.compile(r"\b\d+(\.\d+)?\s*(standard |mini |micro )?lots?\b", re.IGNORECASE),
    re.compile(r"\b(place|set) (a |your )?(stop|stop-loss|take[- ]profit)\b.{0,20}\d", re.IGNORECASE),
]


def contains_trade_instruction(text: str) -> bool:
    """Return True when ``text`` contains an entry price, position size or buy/sell instruction."""
    return any(p.search(text) for p in _ADVICE_PATTERNS)


def is_recommendation_request(query: str) -> bool:
    """Return True when a user prompt is asking the system for a trade instruction."""
    q = query.lower()
    triggers = (
        "should i buy",
        "should i sell",
        "should i go long",
        "should i go short",
        "what lot",
        "how many lots",
        "position size",
        "entry price",
        "where should i enter",
        "give me a trade",
        "trade signal",
    )
    return any(t in q for t in triggers)
