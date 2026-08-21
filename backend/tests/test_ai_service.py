import pytest
from app.schemas.ai import RAGQueryRequest
from app.services.ai_service import ai_service

def test_rag_query_with_context():
    req = RAGQueryRequest(query="What is the Federal Reserve stance on interest rates?", currency_pair="EUR_USD")
    res = ai_service.process_rag_query(req)
    assert not res.is_insufficient_context
    assert len(res.citations) > 0
    assert "Federal Reserve" in res.answer or "FOMC" in res.answer
    assert "TRADLY RESPONSIBLE AI DISCLAIMER" in res.disclaimer

def test_rag_query_insufficient_context():
    # TC-5: RAG query with irrelevant text returns refusal message without hallucination
    req = RAGQueryRequest(query="xyz987 quantum teleportation protocol in central banking")
    res = ai_service.process_rag_query(req)
    assert res.is_insufficient_context
    assert len(res.citations) == 0
    assert "cannot find sufficient verifiable macro news" in res.answer
