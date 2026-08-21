"""Integration tests for Grounded RAG AI Service (SRS TC-5, AI-1.1, AI-1.3, AI-4.1)."""

import asyncio
import pytest
from app.schemas.ai import RAGQueryRequest
from app.services.ai_service import AIService


def test_grounded_rag_query_with_citations():
    ai = AIService()
    req = RAGQueryRequest(query="What is the Federal Reserve policy stance on interest rates?", symbol="EUR_USD")
    res = asyncio.run(ai.query_rag(req))

    assert res.relevance_score > 0.0
    assert len(res.citations) > 0
    assert "Federal Reserve" in res.answer or "FOMC" in res.answer or "monetary" in res.answer.lower()
    assert res.disclaimer is not None
    assert "TRADLY RESPONSIBLE AI DISCLAIMER" in res.disclaimer


def test_tc5_rag_refusal_on_ungrounded_query():
    """SRS TC-5: Queries outside the macroeconomic corpus must trigger explicit refusal."""
    ai = AIService()
    req = RAGQueryRequest(query="What is the recipe for chocolate cake and who won the 1994 world cup?")
    res = asyncio.run(ai.query_rag(req))

    assert res.relevance_score == 0.0
    assert len(res.citations) == 0
    assert "cannot provide an answer" in res.answer.lower()
    assert "relevance criteria" in res.answer.lower()
