"""Live macro/FX news and economic calendar (FXStreet RSS, Finnhub news, ForexFactory weekly calendar).

All fetches are synchronous, cached in-process and fail soft: a provider error returns the last good
result (or an empty list) instead of raising, so AI panels degrade rather than break.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
NEWS_TTL_SECONDS = 600
CALENDAR_TTL_SECONDS = 1800
CALENDAR_RETRY_SECONDS = 120
CALENDAR_SNAPSHOT = Path(__file__).resolve().parent.parent / "data" / "ff_calendar_thisweek.json"

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

GOOGLE_NEWS_QUERIES = [
    'forex OR "EUR/USD" OR "USD/JPY" OR "GBP/USD" OR "currency markets" when:2d',
    '"Federal Reserve" OR ECB OR "Bank of Japan" OR "Bank of England" interest rates when:2d',
    '"Australian dollar" OR "Canadian dollar" OR "New Zealand dollar" OR "Swiss franc" OR yen when:3d',
]

_TAG_RE = re.compile(r"<[^>]+>")
_ITEM_RE = re.compile(r"<item\b[^>]*>(.*?)</item>", re.DOTALL | re.IGNORECASE)
_CDATA_RE = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)


def _field(block: str, tag: str) -> str:
    m = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", block, re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    return _CDATA_RE.sub(lambda c: c.group(1), m.group(1))


def _clean(text: str) -> str:
    return html.unescape(_TAG_RE.sub("", html.unescape(text or ""))).strip()


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
        self._calendar_live = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ news
    def headlines(self) -> List[dict]:
        """Recent FX-relevant headlines, newest first (cached for ``NEWS_TTL_SECONDS``)."""
        if self._news and time.time() - self._news_at < NEWS_TTL_SECONDS:
            return self._news
        with self._lock:
            if self._news and time.time() - self._news_at < NEWS_TTL_SECONDS:
                return self._news
            items = self._fxstreet() + self._finnhub() + self._google_news()
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

    def _rss(self, url: str, source: Optional[str], params: Optional[dict] = None) -> List[dict]:
        """Tolerant RSS reader (regex, not a strict XML parser - some feeds serve slightly malformed XML).

        ``source=None`` takes the publisher from a trailing " - Publisher" in the title (Google News style).
        """
        try:
            res = self._client.get(url, params=params)
            text = res.text
        except Exception as exc:
            logger.warning(f"RSS fetch failed for {url}: {exc}")
            return []
        out = []
        for block in _ITEM_RE.findall(text):
            title = _clean(_field(block, "title"))
            if not title:
                continue
            publisher = source
            if publisher is None:
                head, sep, tail = title.rpartition(" - ")
                if sep:
                    title, publisher = head.strip(), tail.strip()
                else:
                    publisher = "Google News"
            summary = _clean(_field(block, "description"))
            if source is None:
                summary = ""  # Google News descriptions only repeat the title as links
            try:
                published = parsedate_to_datetime(_field(block, "pubDate")).astimezone(timezone.utc)
            except Exception:
                published = datetime.now(timezone.utc)
            out.append(self._row(title, summary, publisher, _clean(_field(block, "link")) or None, published))
        if not out:
            logger.warning(f"RSS feed {url} returned no items (HTTP {res.status_code})")
        return out

    def _fxstreet(self) -> List[dict]:
        return self._rss("https://www.fxstreet.com/rss/news", "FXStreet")

    def _google_news(self) -> List[dict]:
        out: List[dict] = []
        for query in GOOGLE_NEWS_QUERIES:
            rows = self._rss(
                "https://news.google.com/rss/search",
                None,
                {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
            )
            out.extend(r for r in rows if r["currencies"])
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
        if time.time() - self._calendar_at < (CALENDAR_TTL_SECONDS if self._calendar_live else CALENDAR_RETRY_SECONDS):
            return self._calendar
        with self._lock:
            if time.time() - self._calendar_at < (CALENDAR_TTL_SECONDS if self._calendar_live else CALENDAR_RETRY_SECONDS):
                return self._calendar
            self._calendar_at = time.time()  # also throttles retries after a 429
            try:
                res = self._client.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json")
                if res.status_code == 200:
                    rows = res.json()
                    if isinstance(rows, list) and rows:
                        self._calendar = rows
                        self._calendar_live = True
                        return self._calendar
                else:
                    logger.warning(f"ForexFactory calendar HTTP {res.status_code}")
            except Exception as exc:
                logger.warning(f"ForexFactory calendar failed: {exc}")
            if not self._calendar_live:
                self._calendar = self._calendar_snapshot()
        return self._calendar

    @staticmethod
    def _calendar_snapshot() -> List[dict]:
        """Last downloaded ForexFactory week (bundled), used only while the live feed is rate-limited.

        Returned only if the snapshot covers the current week, so it can never show a stale week.
        """
        try:
            rows = json.loads(CALENDAR_SNAPSHOT.read_text(encoding="utf-8"))
            dates = [datetime.fromisoformat(r["date"]) for r in rows]
            now = datetime.now(timezone.utc)
            if dates and min(dates) - timedelta(days=1) <= now <= max(dates) + timedelta(days=1):
                logger.info("Serving bundled ForexFactory calendar snapshot for the current week")
                return rows
        except Exception as exc:
            logger.warning(f"Calendar snapshot unavailable: {exc}")
        return []


live_news = LiveNews()
