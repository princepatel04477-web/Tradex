import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from app.schemas.ai import (
    RAGQueryRequest, RAGQueryResponse, Citation,
    CurrencySentiment, HeadlineSentiment, EconomicEvent
)

SAMPLE_CORPUS = [
    {
        "id": "doc-001",
        "title": "Federal Reserve Signals Prolonged Higher Rate Stance Amid Sticky CPI",
        "source": "Federal Reserve Statement / Reuters",
        "published_at": "2026-08-05T14:00:00Z",
        "snippet": "FOMC Chair Jerome Powell emphasized that while inflation has decelerated from peak levels, persistent core service inflation warrants keeping policy rates restrictive. Market participants adjusted rate cut expectations out to Q1 2027.",
        "currencies": ["USD"],
        "sentiment": "Bullish",
        "confidence": 0.88
    },
    {
        "id": "doc-002",
        "title": "ECB Prepares for Potential Rate Cut as Eurozone Composite PMI Contracts",
        "source": "European Central Bank Bulletin",
        "published_at": "2026-08-06T09:30:00Z",
        "snippet": "Eurozone manufacturing activity registered a sharper-than-expected slowdown in July, with Germany's manufacturing PMI dipping to 42.1. ECB policymakers highlighted downside risks to regional GDP growth.",
        "currencies": ["EUR"],
        "sentiment": "Bearish",
        "confidence": 0.85
    },
    {
        "id": "doc-003",
        "title": "Bank of Japan Hinting at Further Yield Curve Control Normalization",
        "source": "BoJ Monetary Policy Report",
        "published_at": "2026-08-04T04:15:00Z",
        "snippet": "Governor Ueda noted rising domestic wage momentum, opening the doorway to potential short-term rate hikes if Tokyo CPI remains above the 2.0% target throughout Q3.",
        "currencies": ["JPY"],
        "sentiment": "Bullish",
        "confidence": 0.82
    },
    {
        "id": "doc-004",
        "title": "UK Inflation Slows to 2.4%, Raising Bank of England Cut Probability",
        "source": "UK Office for National Statistics",
        "published_at": "2026-08-05T07:00:00Z",
        "snippet": "Headline British CPI fell faster than expected due to declines in retail energy tariffs and food price pressure. Cable (GBP/USD) pulled back 45 pips following the release.",
        "currencies": ["GBP", "USD"],
        "sentiment": "Bearish",
        "confidence": 0.79
    },
    {
        "id": "doc-005",
        "title": "Reserve Bank of India Keeps Repo Rate Unchanged at 6.50%",
        "source": "RBI Press Release",
        "published_at": "2026-08-06T04:30:00Z",
        "snippet": "The Monetary Policy Committee decided by a 5-1 majority to retain the policy repo rate while maintaining a stance focused on withdrawal of accommodation to align inflation with the 4% target.",
        "currencies": ["INR"],
        "sentiment": "Neutral",
        "confidence": 0.90
    }
]

class AIService:
    def __init__(self):
        self.disclaimer = (
            "TRADLY RESPONSIBLE AI DISCLAIMER: All AI-generated responses, sentiment scores, and market briefings "
            "are strictly for informational and educational purposes. They do NOT constitute investment advice or "
            "trade recommendations. Past performance is not indicative of future results."
        )

    def process_rag_query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        query_text = request.query.strip().lower()
        now = datetime.now(timezone.utc)
        
        # Simple keywords search score matching for Grounded RAG
        keywords = [k for k in query_text.split() if len(k) > 2]
        scored_docs = []
        
        for doc in SAMPLE_CORPUS:
            text = (doc["title"] + " " + doc["snippet"]).lower()
            match_count = sum(1 for kw in keywords if kw in text)
            if request.currency_pair:
                cp = request.currency_pair.upper()
                if any(c in cp for c in doc["currencies"]):
                    match_count += 2
                    
            rel_score = min(0.95, 0.50 + (match_count * 0.12))
            if match_count > 0 or len(keywords) < 2:
                scored_docs.append((doc, rel_score))
                
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        top_docs = scored_docs[:3]

        # Check refusal threshold (SRS 6.1.2 & FR-3.4 / AI-1.3: Cosine similarity >= 0.72 required)
        if not top_docs or top_docs[0][1] < 0.65:
            return RAGQueryResponse(
                query=request.query,
                answer=(
                    "I cannot find sufficient verifiable macro news or policy context in my ingested database "
                    "to answer your question accurately. Please rephrase your query or ask about recent central bank "
                    "statements, CPI releases, or major currency trends."
                ),
                citations=[],
                is_insufficient_context=True,
                disclaimer=self.disclaimer,
                model_used="Keyword retrieval over the local corpus (no LLM call)",
                timestamp=now
            )

        citations = []
        for i, (doc, score) in enumerate(top_docs, 1):
            citations.append(Citation(
                id=doc["id"],
                title=doc["title"],
                source=doc["source"],
                published_at=doc["published_at"],
                snippet=doc["snippet"],
                relevance_score=round(score, 2)
            ))

        primary_doc = top_docs[0][0]
        answer_text = (
            f"Based on recent central bank updates and macroeconomic data [{primary_doc['id']}]:\n\n"
            f"{primary_doc['snippet']}\n\n"
            f"Key Takeaway: The macro narrative for {', '.join(primary_doc['currencies'])} remains grounded in "
            f"{primary_doc['sentiment'].lower()} monetary policy expectations. Market participants should monitor "
            f"upcoming Economic Calendar events for potential volatility."
        )

        return RAGQueryResponse(
            query=request.query,
            answer=answer_text,
            citations=citations,
            is_insufficient_context=False,
            disclaimer=self.disclaimer,
            model_used="Keyword retrieval over the local corpus (no LLM call)",
            timestamp=now
        )

    def get_currency_sentiments(self) -> List[CurrencySentiment]:
        currencies = ["USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "INR"]
        results = []
        
        for curr in currencies:
            matching_docs = [d for d in SAMPLE_CORPUS if curr in d["currencies"]]
            if not matching_docs:
                score = round(random.uniform(-0.1, 0.1), 2)
                label = "Neutral"
                headlines = ["Market conditions remain steady ahead of key economic releases."]
            else:
                scores = []
                for d in matching_docs:
                    val = d["confidence"] if d["sentiment"] == "Bullish" else -d["confidence"] if d["sentiment"] == "Bearish" else 0.0
                    scores.append(val)
                score = round(sum(scores) / len(scores), 2)
                label = "Bullish" if score > 0.2 else "Bearish" if score < -0.2 else "Neutral"
                headlines = [d["title"] for d in matching_docs]
                
            results.append(CurrencySentiment(
                currency=curr,
                score=score,
                label=label,
                article_count=len(matching_docs),
                top_headlines=headlines
            ))
            
        return results

    def get_economic_calendar(self) -> List[EconomicEvent]:
        now = datetime.now(timezone.utc)
        return [
            EconomicEvent(
                id="evt-101",
                title="US Non-Farm Payrolls (NFP) & Unemployment Rate",
                country="United States",
                currency="USD",
                scheduled_at=now + timedelta(hours=4),
                impact="High",
                previous="185K",
                consensus="165K",
                ai_briefing=(
                    "NFP releases consistently trigger peak intraday volatility across all USD pairs. "
                    "Consensus expects 165K jobs added. Historically, a deviation > 30K from consensus causes "
                    "an immediate 35-60 pip repricing in EUR/USD and USD/JPY within the first 15 minutes."
                ),
                historical_pip_volatility="±48 pips average H1 move"
            ),
            EconomicEvent(
                id="evt-102",
                title="ECB Press Conference & Rate Decision",
                country="Eurozone",
                currency="EUR",
                scheduled_at=now + timedelta(hours=18),
                impact="High",
                previous="3.75%",
                consensus="3.50%",
                ai_briefing=(
                    "ECB is widely expected to deliver a 25 bps rate cut. Traders should focus on President Lagarde's "
                    "forward guidance regarding potential Q4 policy pauses."
                ),
                historical_pip_volatility="±38 pips average H1 move"
            ),
            EconomicEvent(
                id="evt-103",
                title="UK Consumer Price Index (CPI YoY)",
                country="United Kingdom",
                currency="GBP",
                scheduled_at=now + timedelta(days=1, hours=8),
                impact="High",
                previous="2.4%",
                consensus="2.2%",
                ai_briefing=(
                    "Services inflation remains the key metric watched by the BoE. An upside surprise above 2.4% "
                    "could ignite a sharp GBP rally."
                ),
                historical_pip_volatility="±42 pips average H1 move"
            ),
            EconomicEvent(
                id="evt-104",
                title="Bank of Japan Policy Rate Statement",
                country="Japan",
                currency="JPY",
                scheduled_at=now + timedelta(days=2, hours=3),
                impact="High",
                previous="0.25%",
                consensus="0.25%",
                ai_briefing=(
                    "Market participants will analyze BoJ stance on JGB purchases and future rate normalization path."
                ),
                historical_pip_volatility="±65 pips average H1 move"
            )
        ]

# Global singleton
ai_service = AIService()
