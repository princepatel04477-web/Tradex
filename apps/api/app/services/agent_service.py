"""Multi-Agent Analysis Service (Month 4 roadmap, SRS AI-4).

Four collaborating agents run as a small directed graph:

    Technical ─┐
    Macro ─────┼──► Synthesis
    Risk ──────┘

* Technical agent reads the Analysis Service (indicators + composite bias across H1/H4/D1).
* Macro agent reads the grounded RAG pipeline and the currency sentiment engine; below the
  relevance floor it reports ``insufficient_context`` instead of guessing.
* Risk agent reads volatility (ATR vs spread), the paper-trading account and the economic calendar.
* Synthesis keeps only claims that cite evidence the producing agent actually returned, weights
  the surviving stances, and phrases a probabilistic verdict. It never outputs an entry price,
  position size or buy/sell instruction; any LLM phrasing is filtered and falls back to the
  deterministic narrative when it violates that rule.

The three evidence agents run concurrently and fail independently: one failing agent degrades
only its own panel (NFR-R3).
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections import OrderedDict
from typing import Awaitable, Callable, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.errors import ValidationError
from app.core.logging import logger
from app.domain.ai_safety import contains_trade_instruction
from app.domain.pips import get_pip_size, normalize_symbol, split_symbol
from app.schemas.agents import (
    AgentAnalyseRequest,
    AgentClaim,
    AgentReport,
    AgentRunOut,
    AgentVerdict,
    DiscardedClaim,
    Evidence,
)
from app.schemas.ai import RAGQueryRequest
from app.services.ai_service import ai_service
from app.services.analysis_service import analysis_service
from app.services.market_service import PAIRS_METADATA, market_service
from app.services.trading_service import trading_service

RULE_ENGINE = "Tradly rule-engine v1 (deterministic)"
MAX_STORED_RUNS = 30

HAWKISH_TERMS = ("maintained", "increase", "hike", "restrictive", "elevated", "firm", "strong", "tighten", "taper")
DOVISH_TERMS = ("lower", "reduce", "cut", "easing", "subdued", "headwinds", "moderat", "loosen", "accommodative")


def _clip(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _policy_tone(text: str) -> float:
    """Crude hawkish (+) / dovish (−) tone score in [-1, 1] from a central-bank passage."""
    t = text.lower()
    hawk = sum(t.count(w) for w in HAWKISH_TERMS)
    dove = sum(t.count(w) for w in DOVISH_TERMS)
    total = hawk + dove
    return 0.0 if total == 0 else round((hawk - dove) / total, 2)


class AgentService:
    def __init__(self) -> None:
        self._runs: "OrderedDict[str, AgentRunOut]" = OrderedDict()

    # ------------------------------------------------------------------ agents

    async def technical_agent(self, symbol: str, timeframe: str) -> AgentReport:
        snap = analysis_service.get_indicators(symbol, timeframe)
        decimals = next((c["pip_decimals"] for c in PAIRS_METADATA if c["symbol"] == symbol), 4) + 1
        fmt = f"{{:.{decimals}f}}"
        evidence = [
            Evidence(id="IND:RSI14", kind="indicator", label=f"RSI-14 ({timeframe})", value=f"{snap.rsi_14:.2f} · {snap.rsi_condition}"),
            Evidence(id="IND:MACD", kind="indicator", label=f"MACD hist ({timeframe})", value=f"{snap.macd_hist:+.6f}"),
            Evidence(id="IND:EMA", kind="indicator", label="EMA 9 / 21", value=f"{fmt.format(snap.ema_9)} / {fmt.format(snap.ema_21)}"),
            Evidence(id="IND:SMA200", kind="indicator", label="SMA-200", value=fmt.format(snap.sma_200)),
            Evidence(id="IND:BB", kind="indicator", label="Bollinger 20/2", value=f"{fmt.format(snap.bb_lower)} – {fmt.format(snap.bb_upper)}"
                     + (" · squeeze" if snap.bb_squeeze else "")),
            Evidence(id="IND:BIAS", kind="indicator", label=f"Composite bias ({timeframe})", value=f"{snap.bias_label} ({snap.bias_score:+.2f})"),
        ]
        name_to_evidence = {
            "EMA 9/21 Alignment": "IND:EMA",
            "Price vs SMA-200": "IND:SMA200",
            "MACD Momentum": "IND:MACD",
            "RSI Oscillator": "IND:RSI14",
            "Bollinger Band Position": "IND:BB",
        }
        claims: List[AgentClaim] = []
        for item in snap.bias_breakdown:
            ev = name_to_evidence.get(item.name)
            if ev is None or item.contribution == 0:
                continue
            claims.append(
                AgentClaim(
                    text=f"{item.name} contributes {item.contribution:+.2f} ({item.direction}).",
                    stance=_clip(item.contribution * 4),
                    evidence_ids=[ev],
                )
            )

        # Top-down alignment across higher timeframes.
        mtf_scores: Dict[str, float] = {}
        for tf in ("H1", "H4", "D1"):
            b = analysis_service.get_bias(symbol, tf)
            mtf_scores[tf] = b.score
            evidence.append(Evidence(id=f"TF:{tf}", kind="timeframe", label=f"Bias {tf}", value=f"{b.bias} ({b.score:+.2f})"))
        signs = {tf: (1 if s > 0.1 else -1 if s < -0.1 else 0) for tf, s in mtf_scores.items()}
        aligned = len(set(signs.values())) == 1 and 0 not in signs.values()
        claims.append(
            AgentClaim(
                text=(
                    "H1, H4 and D1 biases point the same way — top-down alignment."
                    if aligned
                    else "H1, H4 and D1 biases disagree — no top-down alignment."
                ),
                stance=_clip(sum(mtf_scores.values()) / 3),
                evidence_ids=["TF:H1", "TF:H4", "TF:D1"],
            )
        )

        contributions = [i.contribution for i in snap.bias_breakdown if i.contribution != 0]
        direction = 1 if snap.bias_score > 0 else -1 if snap.bias_score < 0 else 0
        agreement = (
            sum(1 for c in contributions if (c > 0) == (direction > 0)) / len(contributions)
            if contributions and direction != 0
            else 0.5
        )
        confidence = _clip(0.3 + 0.45 * agreement * min(1.0, abs(snap.bias_score) / 0.6) + (0.15 if aligned else 0.0), 0.0, 0.95)
        summary = (
            f"{snap.bias_label} composite bias ({snap.bias_score:+.2f}) on {timeframe}; RSI {snap.rsi_14:.1f}, "
            f"MACD histogram {'positive' if snap.macd_hist > 0 else 'negative'}, "
            f"{'top-down aligned' if aligned else 'mixed across H1/H4/D1'}."
        )
        return AgentReport(
            agent="technical",
            title="Technical Analyst",
            status="ok",
            stance=round(_clip(snap.bias_score), 2),
            confidence=round(confidence, 2),
            summary=summary,
            claims=claims,
            evidence=evidence,
            model_used=RULE_ENGINE,
        )

    async def macro_agent(self, symbol: str) -> AgentReport:
        base, quote = split_symbol(symbol)
        rag = await ai_service.query_rag(
            RAGQueryRequest(
                query=f"{base} {quote} central bank monetary policy interest rate inflation outlook",
                symbol=symbol,
            )
        )
        corpus = {d["id"]: d for d in ai_service.corpus}
        sentiments = {s.currency: s for s in ai_service.get_sentiment_overview().currencies}

        evidence: List[Evidence] = []
        claims: List[AgentClaim] = []
        tones: Dict[str, float] = {}
        relevant = [
            c for c in rag.citations
            if c.id in corpus and (base in corpus[c.id]["currencies"] or quote in corpus[c.id]["currencies"])
        ]
        for cit in relevant:
            doc = corpus[cit.id]
            evidence.append(Evidence(id=f"DOC:{cit.id}", kind="document", label=cit.title, value=cit.source, url=cit.url))
            tone = _policy_tone(doc["content"])
            for ccy in doc["currencies"]:
                if ccy in (base, quote):
                    tones[ccy] = tone
                    sign = 1 if ccy == base else -1
                    claims.append(
                        AgentClaim(
                            text=f"{doc['source']} policy tone reads {'hawkish' if tone > 0 else 'dovish' if tone < 0 else 'balanced'} "
                            f"({tone:+.2f}) for {ccy}.",
                            stance=_clip(sign * tone),
                            evidence_ids=[f"DOC:{cit.id}"],
                        )
                    )

        sent_parts: List[float] = []
        for ccy, sign in ((base, 1), (quote, -1)):
            s = sentiments.get(ccy)
            if s is None:
                continue
            evidence.append(Evidence(id=f"SENT:{ccy}", kind="sentiment", label=f"{ccy} news sentiment", value=f"{s.score:+.2f} ({s.label}, {s.article_count} articles)"))
            sent_parts.append(sign * s.score)
            claims.append(
                AgentClaim(
                    text=f"{ccy} headline sentiment is {s.label.lower()} ({s.score:+.2f}).",
                    stance=_clip(sign * s.score),
                    evidence_ids=[f"SENT:{ccy}"],
                )
            )

        if not relevant and not sent_parts:
            return AgentReport(
                agent="macro",
                title="Macro Researcher",
                status="insufficient_context",
                summary=(
                    f"No verified central-bank documents or sentiment series cover {base}/{quote} above the relevance floor; "
                    "the macro agent declines to speculate."
                ),
                model_used=rag.model_used,
            )

        tone_diff = (tones.get(base, 0.0) - tones.get(quote, 0.0)) / 2
        sent_diff = sum(sent_parts) / 2 if sent_parts else 0.0
        stance = _clip(0.55 * sent_diff + 0.45 * tone_diff)
        coverage = (int(base in tones or f"SENT:{base}" in {e.id for e in evidence}) + int(quote in tones or f"SENT:{quote}" in {e.id for e in evidence})) / 2
        confidence = _clip(0.25 + 0.35 * coverage + 0.3 * min(1.0, abs(stance) / 0.5), 0.0, 0.9)
        summary = (
            f"Sentiment differential {sent_diff:+.2f} and policy-tone differential {tone_diff:+.2f} for {base} vs {quote} "
            f"from {len(relevant)} cited central-bank document(s)."
        )
        return AgentReport(
            agent="macro",
            title="Macro Researcher",
            status="ok",
            stance=round(stance, 2),
            confidence=round(confidence, 2),
            summary=summary,
            claims=claims,
            evidence=evidence,
            model_used=rag.model_used,
        )

    async def risk_agent(self, symbol: str, timeframe: str) -> AgentReport:
        base, quote = split_symbol(symbol)
        snap = analysis_service.get_indicators(symbol, timeframe)
        pip = float(get_pip_size(symbol))
        atr_pips = snap.atr_14 / pip if pip else 0.0
        spread_pips = float(next((c["spread_pips"] for c in PAIRS_METADATA if c["symbol"] == symbol), 2))
        spread_ratio = spread_pips / atr_pips if atr_pips > 0 else 1.0
        account = trading_service.get_account()
        same_pair = [p for p in trading_service.positions.values() if p.symbol == symbol]
        events = [e for e in ai_service.get_economic_calendar() if e.currency in (base, quote) and e.impact == "High"]

        evidence = [
            Evidence(id="VOL:ATR", kind="volatility", label=f"ATR-14 ({timeframe})", value=f"{atr_pips:.1f} pips"),
            Evidence(id="VOL:SPREAD", kind="volatility", label="Spread / ATR", value=f"{spread_pips:.1f} pips · {spread_ratio * 100:.1f}% of ATR"),
            Evidence(id="ACC:MARGIN", kind="account", label="Paper account", value=(
                f"margin level {account.margin_level_pct:.0f}% · {account.open_positions_count} open"
                if account.open_positions_count
                else f"no open positions · equity ${account.equity:,.2f}"
            )),
        ]
        for e in events:
            evidence.append(Evidence(id=f"CAL:{e.id}", kind="calendar", label=e.title, value=f"{e.currency} · {e.impact} impact"))

        points = 0
        claims: List[AgentClaim] = []
        if spread_ratio > 0.15:
            points += 1
            claims.append(AgentClaim(text="Spread is a large share of typical bar range — trading costs are material.", stance=0, evidence_ids=["VOL:SPREAD"]))
        else:
            claims.append(AgentClaim(text="Spread is small relative to typical bar range.", stance=0, evidence_ids=["VOL:SPREAD", "VOL:ATR"]))
        if events:
            points += 1
            claims.append(AgentClaim(
                text=f"{len(events)} high-impact event(s) scheduled for {base}/{quote} — expect gap and slippage risk.",
                stance=0,
                evidence_ids=[f"CAL:{e.id}" for e in events],
            ))
        if account.open_positions_count and account.margin_level_pct < 300:
            points += 1
            claims.append(AgentClaim(text="Account margin level is below 300% — limited headroom for additional exposure.", stance=0, evidence_ids=["ACC:MARGIN"]))
        if same_pair:
            points += 1
            claims.append(AgentClaim(text=f"Existing exposure on {base}/{quote} ({len(same_pair)} open position(s)) concentrates risk.", stance=0, evidence_ids=["ACC:MARGIN"]))

        level = "Low" if points == 0 else "Moderate" if points == 1 else "Elevated"
        summary = (
            f"{level} risk: 1×ATR ≈ {atr_pips:.1f} pips on {timeframe}, spread {spread_pips:.1f} pips, "
            f"{len(events)} high-impact event(s) in the calendar window."
        )
        return AgentReport(
            agent="risk",
            title="Risk Manager",
            status="ok",
            stance=0.0,
            confidence=round({"Low": 0.85, "Moderate": 0.7, "Elevated": 0.55}[level], 2),
            summary=summary,
            claims=claims,
            evidence=evidence,
            model_used=RULE_ENGINE,
        )

    # --------------------------------------------------------------- synthesis

    @staticmethod
    def _validate_claims(reports: List[AgentReport]) -> Tuple[List[Tuple[AgentReport, AgentClaim]], List[DiscardedClaim]]:
        accepted: List[Tuple[AgentReport, AgentClaim]] = []
        discarded: List[DiscardedClaim] = []
        for r in reports:
            if r.status != "ok":
                continue
            known = {e.id for e in r.evidence}
            kept: List[AgentClaim] = []
            for c in r.claims:
                if not c.evidence_ids:
                    discarded.append(DiscardedClaim(agent=r.agent, text=c.text, reason="no evidence cited"))
                elif not set(c.evidence_ids).issubset(known):
                    discarded.append(DiscardedClaim(agent=r.agent, text=c.text, reason="cites evidence the agent did not retrieve"))
                elif contains_trade_instruction(c.text):
                    discarded.append(DiscardedClaim(agent=r.agent, text=c.text, reason="contains a trade instruction"))
                else:
                    kept.append(c)
                    accepted.append((r, c))
            r.claims = kept
        return accepted, discarded

    async def _llm_narrative(self, symbol: str, deterministic: str, reports: List[AgentReport]) -> Optional[str]:
        if not settings.GROQ_API_KEY:
            return None
        from app.providers.groq import GroqProvider

        evidence_lines = []
        for r in reports:
            if r.status == "ok":
                evidence_lines.append(f"[{r.title}] {r.summary}")
        system = (
            "You are the synthesis agent of a Forex research tool. Rewrite the supplied findings as 3 short sentences "
            "of plain English. Use ONLY the findings given. Speak in probabilities and evidence. NEVER give a buy or sell "
            "instruction, entry price, stop level, target, or position size. No advice."
        )
        user = f"Pair: {symbol.replace('_', '/')}\nVerdict: {deterministic}\nFindings:\n" + "\n".join(evidence_lines)
        try:
            text = await asyncio.wait_for(GroqProvider().generate(system, user, temperature=0.2, max_tokens=220), timeout=9.0)
        except Exception as exc:  # provider down, timeout or quota — degrade to deterministic narrative
            logger.warning(f"Synthesis LLM unavailable ({exc}); using deterministic narrative")
            return None
        text = (text or "").strip()
        if not text or contains_trade_instruction(text):
            logger.warning("Synthesis LLM output rejected by AI-4.2 output filter")
            return None
        return text

    async def synthesise(self, symbol: str, reports: List[AgentReport], use_llm: bool) -> Tuple[AgentReport, AgentVerdict]:
        started = time.perf_counter()
        accepted, discarded = self._validate_claims(reports)
        by_name = {r.agent: r for r in reports}
        tech = by_name.get("technical")
        macro = by_name.get("macro")
        risk = by_name.get("risk")

        weights: List[Tuple[float, float, float]] = []  # (weight, stance, confidence)
        if tech and tech.status == "ok":
            weights.append((0.6, tech.stance, tech.confidence))
        if macro and macro.status == "ok":
            weights.append((0.4, macro.stance, macro.confidence))
        total_w = sum(w for w, _, _ in weights)
        score = sum(w * s for w, s, _ in weights) / total_w if total_w else 0.0
        conf = sum(w * c for w, _, c in weights) / total_w if total_w else 0.0
        if tech and macro and tech.status == "ok" and macro.status == "ok" and tech.stance * macro.stance < 0:
            conf *= 0.75  # technical and macro disagree
        risk_level = "Unknown"
        if risk and risk.status == "ok":
            risk_level = risk.summary.split(" ", 1)[0]
            conf *= {"Low": 1.0, "Moderate": 0.9, "Elevated": 0.8}.get(risk_level, 0.9)
        score = round(_clip(score), 2)
        conf = round(_clip(conf, 0.0, 0.95), 2)

        if score >= 0.35:
            label, tilt = "Bullish tilt", "bullish"
        elif score >= 0.12:
            label, tilt = "Mild bullish tilt", "bullish"
        elif score <= -0.35:
            label, tilt = "Bearish tilt", "bearish"
        elif score <= -0.12:
            label, tilt = "Mild bearish tilt", "bearish"
        else:
            label, tilt = "No clear directional edge", "neutral"

        pair = symbol.replace("_", "/")
        parts = [f"The evidence on {pair} leans {tilt} (score {score:+.2f}) with {conf:.0%} confidence."]
        if tech and tech.status == "ok":
            parts.append(f"Technicals: {tech.summary}")
        if macro and macro.status == "ok":
            parts.append(f"Macro: {macro.summary}")
        elif macro:
            parts.append("Macro context is insufficient for this pair, so the verdict rests on technicals only.")
        if risk and risk.status == "ok":
            parts.append(f"Risk: {risk.summary}")
        deterministic = " ".join(parts)

        narrative, source = deterministic, RULE_ENGINE
        if use_llm:
            llm_text = await self._llm_narrative(symbol, f"{label} ({score:+.2f}, confidence {conf:.0%})", reports)
            if llm_text:
                narrative, source = llm_text, f"Groq · {settings.GROQ_MODEL} (filtered)"

        synth_report = AgentReport(
            agent="synthesis",
            title="Synthesis Lead",
            status="ok",
            stance=score,
            confidence=conf,
            summary=f"{label}: {len(accepted)} evidence-backed claims accepted, {len(discarded)} discarded.",
            claims=[],
            evidence=[],
            model_used=source,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        verdict = AgentVerdict(
            label=label,
            tilt=tilt,
            score=score,
            confidence=conf,
            risk_level=risk_level,
            narrative=narrative,
            narrative_source=source,
            accepted_claims=len(accepted),
            discarded_claims=discarded,
        )
        return synth_report, verdict

    # ------------------------------------------------------------ orchestrator

    @staticmethod
    async def _timed(name: str, title: str, fn: Callable[[], Awaitable[AgentReport]]) -> AgentReport:
        started = time.perf_counter()
        try:
            report = await fn()
        except Exception as exc:  # one agent failing must not take down the others (NFR-R3)
            logger.warning(f"Agent '{name}' failed: {exc}")
            report = AgentReport(
                agent=name,  # type: ignore[arg-type]
                title=title,
                status="failed",
                summary=f"{title} could not complete; its panel is degraded while other agents continue.",
                model_used=RULE_ENGINE,
                error=str(exc),
            )
        report.duration_ms = round((time.perf_counter() - started) * 1000, 1)
        return report

    async def analyse(self, req: AgentAnalyseRequest) -> AgentRunOut:
        symbol = normalize_symbol(req.symbol)
        if market_service.get_pair(symbol) is None:
            raise ValidationError(f"Pair {symbol} is not in the Tradly pair registry")
        started = time.perf_counter()

        reports = list(
            await asyncio.gather(
                self._timed("technical", "Technical Analyst", lambda: self.technical_agent(symbol, req.timeframe)),
                self._timed("macro", "Macro Researcher", lambda: self.macro_agent(symbol)),
                self._timed("risk", "Risk Manager", lambda: self.risk_agent(symbol, req.timeframe)),
            )
        )
        synth_report, verdict = await self.synthesise(symbol, reports, req.use_llm)
        run = AgentRunOut(
            run_id=str(uuid.uuid4())[:12],
            symbol=symbol,
            timeframe=req.timeframe,
            verdict=verdict,
            agents=reports + [synth_report],
            disclaimer=settings.AI_DISCLAIMER,
            total_duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        self._runs[run.run_id] = run
        while len(self._runs) > MAX_STORED_RUNS:
            self._runs.popitem(last=False)
        return run

    def list_runs(self) -> List[AgentRunOut]:
        return list(reversed(self._runs.values()))


agent_service = AgentService()
