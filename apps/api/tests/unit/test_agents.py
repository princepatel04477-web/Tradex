"""Multi-agent analysis tests: evidence discipline, AI-4.2 output filter, failure isolation."""

import asyncio

import pytest

from app.domain.ai_safety import contains_trade_instruction, is_recommendation_request
from app.schemas.agents import AgentAnalyseRequest, AgentClaim, AgentReport, Evidence
from app.services.agent_service import AgentService, agent_service


def _run(symbol="EUR_USD", timeframe="H1"):
    return asyncio.run(agent_service.analyse(AgentAnalyseRequest(symbol=symbol, timeframe=timeframe, use_llm=False)))


def test_all_four_agents_report_with_provenance():
    run = _run()
    names = [a.agent for a in run.agents]
    assert names == ["technical", "macro", "risk", "synthesis"]
    assert all(a.model_used for a in run.agents)
    assert run.disclaimer
    assert 0 <= run.verdict.confidence <= 1
    assert run.verdict.tilt in ("bullish", "bearish", "neutral")


def test_every_accepted_claim_cites_evidence_the_agent_returned():
    run = _run("GBP_USD", "H4")
    for a in run.agents:
        known = {e.id for e in a.evidence}
        for c in a.claims:
            assert c.evidence_ids and set(c.evidence_ids) <= known


def test_uncited_and_fabricated_claims_are_discarded():
    report = AgentReport(
        agent="technical",
        title="Technical Analyst",
        status="ok",
        stance=0.5,
        confidence=0.6,
        summary="test",
        claims=[
            AgentClaim(text="Real claim", stance=0.5, evidence_ids=["IND:RSI14"]),
            AgentClaim(text="Claim with no evidence", stance=0.9, evidence_ids=[]),
            AgentClaim(text="Claim citing a ghost", stance=0.9, evidence_ids=["DOC:ghost"]),
            AgentClaim(text="You should buy EUR now", stance=1.0, evidence_ids=["IND:RSI14"]),
        ],
        evidence=[Evidence(id="IND:RSI14", kind="indicator", label="RSI", value="55")],
        model_used="test",
    )
    accepted, discarded = AgentService._validate_claims([report])
    assert [c.text for _, c in accepted] == ["Real claim"]
    assert {d.reason for d in discarded} == {
        "no evidence cited",
        "cites evidence the agent did not retrieve",
        "contains a trade instruction",
    }


def test_narrative_never_contains_trade_instruction():
    for sym in ("EUR_USD", "USD_JPY", "USD_MXN", "AUD_JPY"):
        run = _run(sym)
        assert not contains_trade_instruction(run.verdict.narrative)
        for a in run.agents:
            assert not contains_trade_instruction(a.summary)


@pytest.mark.parametrize(
    "text",
    [
        "You should buy EUR/USD here",
        "Entry price 1.0850 with stop at 1.0800",
        "Use 0.5 lots on this setup",
        "Position size of 2 lots is fine",
        "sell now before the NFP print",
    ],
)
def test_output_filter_blocks_advice(text):
    assert contains_trade_instruction(text)


def test_output_filter_allows_probabilistic_language():
    assert not contains_trade_instruction("Evidence leans bullish with 62% confidence; ATR is 14 pips.")


def test_recommendation_seeking_prompts_detected():
    assert is_recommendation_request("Should I buy EUR/USD right now?")
    assert is_recommendation_request("How many lots should I use?")
    assert not is_recommendation_request("What is the ECB policy outlook?")


def test_single_agent_failure_degrades_only_that_panel(monkeypatch):
    svc = AgentService()

    async def boom(symbol):
        raise RuntimeError("macro feed down")

    monkeypatch.setattr(svc, "macro_agent", boom)
    run = asyncio.run(svc.analyse(AgentAnalyseRequest(symbol="EUR_USD", use_llm=False)))
    status = {a.agent: a.status for a in run.agents}
    assert status["macro"] == "failed"
    assert status["technical"] == "ok"
    assert status["risk"] == "ok"
    assert status["synthesis"] == "ok"


def test_unknown_pair_rejected():
    from app.core.errors import ValidationError

    with pytest.raises(ValidationError):
        _run("ABC_XYZ")


def test_rag_refuses_recommendation_requests():
    from app.schemas.ai import RAGQueryRequest
    from app.services.ai_service import ai_service

    res = asyncio.run(ai_service.query_rag(RAGQueryRequest(query="Should I buy EUR/USD now? what lot size?", symbol="EUR_USD")))
    assert res.citations == []
    assert "does not give trade instructions" in res.answer
