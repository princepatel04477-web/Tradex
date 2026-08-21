"""API Router tests: verifying response envelope { data, error, meta }, status codes, and error formats."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_envelope():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert "data" in body
    assert "error" in body
    assert "meta" in body
    assert body["error"] is None
    assert body["data"]["status"] == "healthy"
    assert "request_id" in body["meta"]


def test_market_pairs_endpoint():
    res = client.get("/api/v1/market/pairs")
    assert res.status_code == 200
    body = res.json()
    assert body["error"] is None
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 15


def test_market_sessions_endpoint():
    res = client.get("/api/v1/market/sessions")
    assert res.status_code == 200
    body = res.json()
    assert body["error"] is None
    assert "sessions" in body["data"]
    assert len(body["data"]["sessions"]) == 4


def test_analysis_indicators_endpoint():
    res = client.get("/api/v1/analysis/indicators/EUR_USD?timeframe=H1")
    assert res.status_code == 200
    body = res.json()
    assert body["error"] is None
    assert body["data"]["symbol"] == "EUR_USD"
    assert "rsi_14" in body["data"]
    assert "bias_label" in body["data"]


def test_paper_trading_account_and_order():
    res = client.get("/api/v1/trading/account")
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["balance"] == 10000.0

    order_payload = {
        "symbol": "EUR_USD",
        "side": "buy",
        "lot_size": 0.1,
        "leverage": 100,
    }
    res_order = client.post("/api/v1/trading/orders", json=order_payload)
    assert res_order.status_code == 200
    order_body = res_order.json()
    assert order_body["data"]["symbol"] == "EUR_USD"


def test_ai_rag_query_endpoint():
    payload = {"query": "What is the Federal Reserve stance?", "symbol": "EUR_USD"}
    res = client.post("/api/v1/ai/rag/query", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["answer"] is not None
    assert "TRADLY RESPONSIBLE AI DISCLAIMER" in body["data"]["disclaimer"]


def test_validation_error_envelope_formatting():
    # Submit invalid order (negative lot size)
    payload = {"symbol": "EUR_USD", "side": "buy", "lot_size": -5.0, "leverage": 100}
    res = client.post("/api/v1/trading/orders", json=payload)
    assert res.status_code == 422
    body = res.json()
    assert body["data"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "meta" in body
