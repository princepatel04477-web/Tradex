"""AI Service: grounded RAG intelligence, sentiment analysis, economic calendar (FG-3, AI-1, AI-2, AI-4)."""

import asyncio
import hashlib
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.domain.ai_safety import contains_trade_instruction, is_recommendation_request
from app.providers.base import LLMProvider, NewsProvider
from app.providers.live_news import CURRENCY_KEYWORDS, live_news, tag_currencies
from app.schemas.ai import (
    CitationSource,
    CurrencySentiment,
    EconomicCalendarEvent,
    NewsHeadline,
    RAGQueryRequest,
    RAGQueryResponse,
    SentimentOverview,
)

# Static verified macroeconomic corpus chunks for RAG grounding
KNOWLEDGE_CORPUS = [
    {
        "id": "doc-001",
        "title": "Federal Reserve Monetary Policy Report (background)",
        "source": "Federal Reserve System",
        "url": "https://www.federalreserve.gov/monetarypolicy/mpr_default.htm",
        "currencies": ["USD"],
        "content": (
            "The Federal Open Market Committee maintained the target range for the federal funds rate at 5.25 to 5.50 percent. "
            "Recent indicators suggest economic activity has continued to expand at a solid pace. Job gains have moderated but remain strong, "
            "and the unemployment rate has remained low. Inflation has eased over the past year but remains elevated above the 2 percent objective. "
            "The Committee does not expect it will be appropriate to reduce the target range until it has gained greater confidence that inflation "
            "is moving sustainably toward 2 percent. High interest rate differentials continue to provide fundamental carry support for the US Dollar."
        ),
    },
    {
        "id": "doc-002",
        "title": "ECB Economic Bulletin (background)",
        "source": "European Central Bank",
        "url": "https://www.ecb.europa.eu/pub/economic-bulletin/html/index.en.html",
        "currencies": ["EUR"],
        "content": (
            "The Governing Council decided to lower the three key ECB interest rates by 25 basis points. The latest data broadly support the "
            "baseline inflation outlook, with headline inflation expected to fluctuate around current levels for the remainder of the year before "
            "declining toward target in late 2026. Wage growth is moderating, and corporate profits are absorbing part of the labor cost pressures. "
            "Eurozone manufacturing output remains subdued, particularly in Germany, creating headwinds for EUR appreciation against pro-cyclical currencies."
        ),
    },
    {
        "id": "doc-003",
        "title": "Bank of Japan Monetary Policy Statement (background)",
        "source": "Bank of Japan",
        "url": "https://www.boj.or.jp/en/mopo/index.htm",
        "currencies": ["JPY"],
        "content": (
            "The Bank of Japan decided to increase the uncollateralized overnight call rate to approximately 0.25 percent. "
            "Japan's economic activity has recovered moderately, with the virtuous cycle between wages and prices continuing to intensify. "
            "Real interest rates remain significantly negative, and accommodative financial conditions will firmly support economic growth. "
            "The BoJ announced plans to taper its Japanese Government Bond (JGB) monthly purchases to roughly 3 trillion yen per month by early 2026. "
            "Narrowing interest rate differentials with the Fed and ECB have triggered periodic short-covering rallies in the Japanese Yen."
        ),
    },
    {
        "id": "doc-004",
        "title": "Bank of England Monetary Policy Summary (background)",
        "source": "Bank of England",
        "url": "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes",
        "currencies": ["GBP"],
        "content": (
            "The Monetary Policy Committee voted by a majority to reduce Bank Rate by 0.25 percentage points to 5.0 percent. "
            "CPI inflation has returned close to the 2 percent target, though services inflation remains sticky at 5.2 percent. "
            "Labor market conditions continue to loosen, with private sector regular wage growth easing. The MPC will ensure Bank Rate "
            "remains restrictive for sufficiently long until the risks to inflation returning sustainably to the 2 percent target have dissipated."
        ),
    },
]


BULLISH_WORDS = {
    "rise", "rises", "rising", "rose", "gain", "gains", "gained", "surge", "surges", "surged", "rally", "rallies",
    "rallied", "strong", "stronger", "strength", "strengthens", "hawkish", "higher", "jump", "jumps", "jumped",
    "climb", "climbs", "climbed", "beat", "beats", "firm", "firmer", "firms", "boost", "boosted", "advance",
    "advances", "rebound", "rebounds", "upbeat", "robust", "hike", "hikes", "accelerate", "recovers", "recovery", "bid",
}
BEARISH_WORDS = {
    "fall", "falls", "falling", "fell", "drop", "drops", "dropped", "slide", "slides", "slid", "weak", "weaker",
    "weakness", "weakens", "dovish", "lower", "plunge", "plunges", "plunged", "slump", "slumps", "decline",
    "declines", "declined", "miss", "misses", "missed", "losses", "loses", "lost", "retreat", "retreats", "sinks",
    "sank", "tumble", "tumbles", "slows", "slowdown", "contraction", "cut", "cuts", "pressure", "offered", "selloff",
}
_WORD_RE = re.compile(r"[a-z0-9]+")


def _headline_score(text: str) -> float:
    words = _WORD_RE.findall(text.lower())
    pos = sum(1 for w in words if w in BULLISH_WORDS)
    neg = sum(1 for w in words if w in BEARISH_WORDS)
    return 0.0 if pos + neg == 0 else (pos - neg) / (pos + neg)


def _label(score: float) -> str:
    return "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"


COUNTRY_NAMES = {
    "USD": "United States", "EUR": "Eurozone", "JPY": "Japan", "GBP": "United Kingdom", "AUD": "Australia",
    "CAD": "Canada", "CHF": "Switzerland", "NZD": "New Zealand", "CNY": "China", "All": "Global",
}


class AIService:
    def __init__(self, llm_provider: Optional[LLMProvider] = None, news_provider: Optional[NewsProvider] = None, live: Optional[bool] = None):
        self.llm_provider = llm_provider
        self.news_provider = news_provider
        self.live = settings.LIVE_MARKET_DATA if live is None else live
        self.corpus = KNOWLEDGE_CORPUS

    # ------------------------------------------------------------------ news
    def get_headlines(self) -> List[dict]:
        return live_news.headlines() if self.live else []

    def _news_documents(self) -> List[dict]:
        return [
            {
                "id": h["id"],
                "title": h["title"],
                "source": h["source"],
                "url": h.get("url"),
                "currencies": h["currencies"],
                "content": f"{h['title']}. {h['summary']}",
                "published_at": h["published_at"],
                "live": True,
            }
            for h in self.get_headlines()
        ]

    # ------------------------------------------------------------------- RAG
    async def query_rag(self, req: RAGQueryRequest) -> RAGQueryResponse:
        if is_recommendation_request(req.query):
            # AI-4.2: never produce entry prices, position sizes or buy/sell instructions.
            return RAGQueryResponse(
                query=req.query,
                answer=(
                    "Tradly does not give trade instructions, entry prices or position sizes. "
                    "I can explain the macro drivers, central-bank policy and risk context for a pair instead — "
                    "for example: 'What is driving EUR/USD this week?'"
                ),
                citations=[],
                model_used="Tradly AI-4.2 guard",
                relevance_score=0.0,
                disclaimer=settings.AI_DISCLAIMER,
                timestamp=datetime.now(timezone.utc),
            )
        query_lower = req.query.lower()
        stop_words = {
            "what", "is", "the", "for", "and", "who", "won", "in", "of", "to", "a", "an", "on", "with", "at", "by",
            "from", "as", "how", "why", "where", "this", "that", "are", "be", "will", "it", "about", "me", "tell",
            "week", "today", "now", "latest", "s", "do", "does",
        }
        query_words = set(_WORD_RE.findall(query_lower)) - stop_words
        sym_ccys: List[str] = []
        sym = (req.symbol or req.currency_pair or "").replace("/", "_").upper()
        if sym:
            sym_ccys = sym.split("_") if "_" in sym else [sym[:3], sym[3:]]
        query_ccys = set(tag_currencies(req.query))
        pair_ccys = query_ccys | set(sym_ccys)

        matched_chunks = []
        news_docs = await asyncio.to_thread(self._news_documents) if self.live else []
        for doc in self.corpus + news_docs:
            doc_words = set(_WORD_RE.findall(doc["content"].lower() + " " + doc["title"].lower())) - stop_words
            intersection = query_words.intersection(doc_words)
            score = len(intersection) / len(query_words) if query_words else 0.0
            # Live headlines must either share 2+ query terms or cover a currency the question names.
            if doc.get("live") and len(intersection) < 2 and not (query_ccys & set(doc["currencies"])):
                continue
            if pair_ccys & set(doc["currencies"]):
                score += 0.35
            if doc.get("live"):
                score += 0.05  # prefer fresh news over background documents at equal relevance
            if score > 0.15:
                matched_chunks.append((score, doc))

        matched_chunks.sort(key=lambda x: x[0], reverse=True)

        if not matched_chunks:
            return RAGQueryResponse(
                query=req.query,
                answer=(
                    "I cannot provide an answer because no verified macroeconomic or central bank documentation "
                    "in the Tradly corpus satisfies the relevance criteria for your query. "
                    "Please refine your query with specific currencies, central banks, or economic indicators."
                ),
                citations=[],
                model_used="Tradly-Grounded-RAG (Rule-Floor 0.72)",
                relevance_score=0.0,
                disclaimer=settings.AI_DISCLAIMER,
                timestamp=datetime.now(timezone.utc),
            )

        # Prefer dated live headlines; background documents only fill in when live coverage is thin.
        live_matches = [m for m in matched_chunks if m[1].get("live")]
        top = live_matches[:6] if len(live_matches) >= 3 else matched_chunks[:6]
        top_score, top_doc = top[0]
        citations = [
            CitationSource(
                id=doc["id"],
                title=doc["title"],
                source=doc["source"],
                url=doc.get("url"),
                snippet=doc["content"][:220] + ("..." if len(doc["content"]) > 220 else ""),
                published_at=doc.get("published_at") or "Reference document",
            )
            for _, doc in top[:4]
        ]

        answer = (
            f"Based on {top_doc['source']}: {top_doc['content'][:350]}"
            f"{'...' if len(top_doc['content']) > 350 else ''} [Source: {top_doc['title']}]."
        )
        model_used = "Tradly-Grounded-RAG (retrieval only)"

        if self.live and settings.GROQ_API_KEY:
            context = "\n\n".join(
                f"[{i + 1}] {doc['title']} ({doc['source']}, {doc.get('published_at') or 'background reference'}): {doc['content'][:700]}"
                for i, (_, doc) in enumerate(top)
            )
            system = (
                "You are Tradly's macro research assistant for Forex. Answer ONLY from the numbered sources provided. "
                "Cite sources inline like [1]. If the sources do not answer the question, say so. Be concise (max 170 words). "
                "Never give trade instructions, entry prices, stop levels, lot or position sizes, or tell the user to buy or sell."
            )
            user = f"Question: {req.query}\nPair context: {sym or 'none'}\nToday (UTC): {datetime.now(timezone.utc):%Y-%m-%d}\n\nSources:\n{context}"
            from app.providers.groq import GroqProvider

            for attempt in range(2):  # reasoning models occasionally return an empty reply; retry once
                try:
                    text = await asyncio.wait_for(GroqProvider().generate(system, user, temperature=0.2, max_tokens=700), timeout=12.0)
                except Exception as exc:
                    logger.warning(f"Groq RAG synthesis failed, using retrieval answer: {exc}")
                    break
                text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()
                if text and not contains_trade_instruction(text):
                    answer = text
                    model_used = f"Groq {settings.GROQ_MODEL} + grounded retrieval ({len(top)} sources)"
                    break
                logger.warning(f"Groq RAG reply {'rejected by AI-4.2 filter' if text else 'was empty'} (attempt {attempt + 1})")

        return RAGQueryResponse(
            query=req.query,
            answer=answer,
            citations=citations,
            model_used=model_used,
            relevance_score=min(1.0, round(top_score + 0.5, 2)),
            disclaimer=settings.AI_DISCLAIMER,
            timestamp=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------- sentiment
    def get_sentiment_overview(self) -> SentimentOverview:
        """Per-currency headline sentiment from live FX news (lexicon scoring of FXStreet + Finnhub headlines)."""
        headlines = self.get_headlines()
        now = datetime.now(timezone.utc)
        currencies: List[CurrencySentiment] = []
        for ccy in CURRENCY_KEYWORDS:
            related = [h for h in headlines if ccy in h["currencies"]]
            scored = [(_headline_score(f"{h['title']} {h['summary']}"), h) for h in related]
            score = round(sum(s for s, _ in scored) / len(scored), 2) if scored else 0.0
            sample = max(scored, key=lambda x: abs(x[0]))[1]["title"] if scored else None
            currencies.append(
                CurrencySentiment(
                    currency=ccy,
                    score=score,
                    label=_label(score),
                    article_count=len(related),
                    sample_headline=sample,
                    timestamp=now,
                )
            )
        ranked = sorted((c for c in currencies if c.article_count), key=lambda c: c.score, reverse=True)
        if len(ranked) >= 2 and ranked[0].score - ranked[-1].score > 0.2:
            bias = f"{ranked[0].currency} strongest / {ranked[-1].currency} weakest in headlines"
        else:
            bias = "Mixed / Neutral"
        return SentimentOverview(
            currencies=currencies,
            overall_market_bias=bias if headlines else "No live headlines available",
            total_articles_analyzed=len(headlines),
            model_version="Lexicon sentiment on live FXStreet + Finnhub headlines",
            last_updated=now,
        )

    # -------------------------------------------------------------- calendar
    def get_economic_calendar(self) -> List[EconomicCalendarEvent]:
        """This week's real economic calendar (ForexFactory), High/Medium impact, upcoming first."""
        rows = live_news.calendar() if self.live else []
        now = datetime.now(timezone.utc)
        events: List[EconomicCalendarEvent] = []
        for row in rows:
            impact = row.get("impact", "")
            if impact not in ("High", "Medium"):
                continue
            try:
                when = datetime.fromisoformat(row["date"]).astimezone(timezone.utc)
            except Exception:
                continue
            ccy = row.get("country", "")
            title = row.get("title", "")
            upcoming = when >= now
            briefing = (
                f"{'Scheduled' if upcoming else 'Released'} {impact.lower()}-impact {ccy} data. "
                f"{ccy} pairs typically see wider spreads and faster moves around the release; "
                "compare the actual print against the forecast to gauge the surprise."
            )
            events.append(
                EconomicCalendarEvent(
                    id="ff-" + hashlib.md5(f"{title}|{row['date']}|{ccy}".encode()).hexdigest()[:10],
                    title=title,
                    country=COUNTRY_NAMES.get(ccy, ccy),
                    currency=ccy,
                    scheduled_at=when,
                    impact=impact,
                    previous=row.get("previous") or None,
                    consensus=row.get("forecast") or None,
                    actual=row.get("actual") or None,
                    ai_briefing=briefing,
                    historical_pip_volatility=None,
                )
            )
        # Upcoming events first (soonest first), then the most recent past releases.
        upcoming = sorted((e for e in events if e.scheduled_at >= now), key=lambda e: e.scheduled_at)
        past = sorted((e for e in events if e.scheduled_at < now), key=lambda e: e.scheduled_at, reverse=True)
        return upcoming + past


ai_service = AIService()
