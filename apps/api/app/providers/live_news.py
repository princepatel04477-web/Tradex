"""Live macro/FX news and economic calendar (FXStreet RSS, Finnhub news, ForexFactory weekly calendar).

All fetches are synchronous, cached in-process and fail soft: a provider error returns the last good
result (or an empty list) instead of raising, so AI panels degrade rather than break.
"""

from __future__ import annotations

import hashlib
import html
import re
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
NEWS_TTL_SECONDS = 600
CALENDAR_TTL_SECONDS = 1800

# Keywords that tag a headline to a currency.
CURRENCY_KEYWORDS: Dict[str, List[str]] = {
    "USD": ["usd", "us dollar", "u.s. dollar", "greenback", "fed", "federal reserve", "fomc", "powell", "us treasury",
            "treasury yields", "us cpi", "nonfarm", "nfp", "dxy", "dollar index", "united states"],
    "EUR": ["eur", "euro", "ecb", "lagarde", "eurozone", "euro area", "germany", "german"],
    "JPY": ["jpy", "yen", "boj", "bank of japan", "japan", "japanese", "ueda"],
    "GBP": ["gbp", "pound", "sterling", "boe", "bank of england", "bailey", "uk", "britain", "british"],
    "AUD": ["aud", "aussie", "australian dollar", "rba", "reserve bank of australia", "australia", "australian"],
    "CAD": ["cad", "loonie", "canadian dollar", "boc", "bank of canada", "canada", "canadian"],
    "CHF": ["chf", "swiss franc", "snb", "swiss national bank", "switzerland", "swiss"],
    "NZD": ["nzd", "kiwi", "new zealand dollar", "rbnz", "new zealand"],
}
_CURRENCY_PATTERNS = {
    ccy: re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b") for ccy, words in CURRENCY_KEYWORDS.items()
}

_TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    return html.unescape(_TAG_RE.sub("", text or "")).strip()


def tag_currencies(text: str) -> List[str]:
    t = text.lower()
    return [ccy for ccy, pattern in _CURRENCY_PATTERNS.items() if pattern.search(t)]


class LiveNews:
    def __init__(self) -> None:
        self._client = httpx.Client(timeout=httpx.Timeout(8.0, connect=4.0), headers=HEADERS, follow_redirects=True)
        self._news: List[dict] = []
        self._news_at = 0.0
        self._calendar: List[dict] = []
        self._calendar_at = 0.0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ news
    def headlines(self) -> List[dict]:
        """Recent FX-relevant headlines, newest first (cached for ``NEWS_TTL_SECONDS``)."""
        if self._news and time.time() - self._news_at < NEWS_TTL_SECONDS:
            return self._news
        with self._lock:
            if self._news and time.time() - self._news_at < NEWS_TTL_SECONDS:
                return self._news
            items = self._fxstreet() + self._finnhub()
            if items:
                seen = set()
                unique = []
                for it in sorted(items, key=lambda x: x["published_at"], reverse=True):
                    key = it["title"].lower()[:80]
                    if key not in seen:
                        seen.add(key)
                        unique.append(it)
                self._news = unique[:120]
                self._news_at = time.time()
            elif self._news:
                logger.warning("News refresh failed; serving cached headlines")
        return self._news

    def _fxstreet(self) -> List[dict]:
        try:
            res = self._client.get("https://www.fxstreet.com/rss/news")
            root = ET.fromstring(res.content)
        except Exception as exc:
            logger.warning(f"FXStreet RSS failed: {exc}")
            return []
        out = []
        for item in root.iter("item"):
            title = _clean(item.findtext("title", ""))
            if not title:
                continue
            summary = _clean(item.findtext("description", ""))
            try:
                published = parsedate_to_datetime(item.findtext("pubDate", "")).astimezone(timezone.utc)
            except Exception:
                published = datetime.now(timezone.utc)
            link = item.findtext("link", "")
            out.append(self._row(title, summary, "FXStreet", link, published))
        return out

    def _finnhub(self) -> List[dict]:
        if not settings.FINNHUB_API_KEY:
            return []
        out = []
        for category in ("forex", "general"):
            try:
                res = self._client.get(
                    "https://finnhub.io/api/v1/news", params={"category": category, "token": settings.FINNHUB_API_KEY}
                )
                if res.status_code != 200:
                    continue
                for item in res.json():
                    title = _clean(item.get("headline", ""))
                    summary = _clean(item.get("summary", ""))
                    row = self._row(
                        title,
                        summary,
                        item.get("source") or "Finnhub",
                        item.get("url"),
                        datetime.fromtimestamp(item.get("datetime", 0), tz=timezone.utc),
                    )
                    # General news is broad market news; keep only items that touch a G8 currency/central bank.
                    if category == "forex" or row["currencies"]:
                        out.append(row)
            except Exception as exc:
                logger.warning(f"Finnhub {category} news failed: {exc}")
        return out

    @staticmethod
    def _row(title: str, summary: str, source: str, url: Optional[str], published: datetime) -> dict:
        return {
            "id": "news-" + hashlib.md5(title.encode("utf-8")).hexdigest()[:10],
            "title": title,
            "summary": summary[:600],
            "source": source,
            "url": url,
            "published_at": published.isoformat(),
            "currencies": tag_currencies(f"{title} {summary}"),
        }

    # -------------------------------------------------------------- calendar
    def calendar(self) -> List[dict]:
        """This week's economic calendar from ForexFactory (cached for ``CALENDAR_TTL_SECONDS``)."""
        if self._calendar and time.time() - self._calendar_at < CALENDAR_TTL_SECONDS:
            return self._calendar
        with self._lock:
            if self._calendar and time.time() - self._calendar_at < CALENDAR_TTL_SECONDS:
                return self._calendar
            try:
                res = self._client.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json")
                if res.status_code == 200:
                    rows = res.json()
                    if isinstance(rows, list) and rows:
                        self._calendar = rows
                        self._calendar_at = time.time()
                else:
                    logger.warning(f"ForexFactory calendar HTTP {res.status_code}")
            except Exception as exc:
                logger.warning(f"ForexFactory calendar failed: {exc}")
        return self._calendar


live_news = LiveNews()
