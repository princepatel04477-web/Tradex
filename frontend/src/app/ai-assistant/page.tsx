"use client";

import React, { useEffect, useState } from "react";
import {
  Bot, Send, BookOpen, AlertTriangle, Calendar, ShieldAlert,
  Flame, CheckCircle2, RefreshCw, FileText
} from "lucide-react";
import { api } from "../../services/api";
import { RAGQueryResponse, CurrencySentiment, EconomicEvent } from "../../types/market";

export default function AIAssistantPage() {
  const [query, setQuery] = useState<string>("");
  const [selectedPair, setSelectedPair] = useState<string>("EUR_USD");
  const [loading, setLoading] = useState<boolean>(false);
  const [ragResult, setRagResult] = useState<RAGQueryResponse | null>(null);
  const [sentiments, setSentiments] = useState<CurrencySentiment[]>([]);
  const [calendar, setCalendar] = useState<EconomicEvent[]>([]);
  const [expandedBriefing, setExpandedBriefing] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [sData, cData] = await Promise.all([
          api.getSentiments(),
          api.getCalendar()
        ]);
        setSentiments(sData);
        setCalendar(cData);
      } catch (err) {
        console.error("AI Assistant load error", err);
      }
    }
    loadData();
  }, []);

  const handleAskRAG = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await api.queryRAG(query, selectedPair);
      setRagResult(res);
    } catch (err) {
      console.error("RAG Query Error", err);
    } finally {
      setLoading(false);
    }
  };

  const sampleQuestions = [
    "What is the Federal Reserve stance on interest rates?",
    "Why is the Euro weakening against the US Dollar?",
    "How does the BoJ yield curve control impact USD/JPY?",
    "What is the market consensus for upcoming NFP?"
  ];

  return (
    <div className="space-y-6">
      {/* Persistent Responsible AI Disclaimer Banner (FR-3.10 & NFR-L1) */}
      <div className="p-4 rounded-2xl bg-cyan-950/20 border border-cyan-500/30 flex items-start space-x-3 text-xs text-cyan-300">
        <ShieldAlert className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-white uppercase tracking-wider font-bold mr-1">Tradly Responsible AI Disclaimer:</strong>
          All RAG answers, FinBERT sentiment scores, and economic briefings are generated for informational and academic purposes only.
          Outputs do NOT constitute financial, investment, or trading advice.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Natural Language RAG Chat Assistant */}
        <div className="lg:col-span-7 space-y-6">
          <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <Bot className="w-5 h-5 text-cyan-400" />
                <span>RAG Market Intelligence Assistant</span>
              </h2>
              <span className="text-xs text-tradly-muted font-mono">Groq LLaMA 3 + FinBERT</span>
            </div>

            {/* Input Form */}
            <form onSubmit={handleAskRAG} className="space-y-3">
              <div className="relative">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask any macroeconomic or Forex question (e.g. 'What is the ECB outlook on inflation?')"
                  rows={3}
                  className="w-full p-3.5 pr-12 rounded-xl bg-tradly-bg border border-tradly-border text-white text-sm focus:outline-none focus:border-cyan-400 placeholder:text-tradly-muted resize-none"
                />
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="absolute right-3 bottom-3 p-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-black transition-all"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>

              {/* Quick Sample Question Chips */}
              <div className="flex flex-wrap gap-2 pt-1">
                {sampleQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setQuery(q);
                    }}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-tradly-bg hover:bg-tradly-hover border border-tradly-border text-tradly-muted hover:text-white transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </form>

            {/* RAG Answer Display */}
            {loading && (
              <div className="p-8 text-center space-y-2">
                <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin mx-auto" />
                <p className="text-xs text-tradly-muted font-mono">Retrieving grounded corpus & generating answer...</p>
              </div>
            )}

            {ragResult && !loading && (
              <div className="space-y-4 pt-4 border-t border-tradly-border">
                {/* Insufficient Context Warning (FR-3.4 / AI-1.3) */}
                {ragResult.is_insufficient_context ? (
                  <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start space-x-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{ragResult.answer}</span>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-tradly-bg border border-tradly-border space-y-3">
                    <div className="flex items-center justify-between text-xs text-tradly-muted border-b border-tradly-border/50 pb-2">
                      <span className="font-semibold text-white">Synthesized Grounded Response</span>
                      <span className="font-mono text-cyan-400">{ragResult.model_used}</span>
                    </div>
                    <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-line font-normal">
                      {ragResult.answer}
                    </div>
                  </div>
                )}

                {/* Source Citation Cards (FR-3.3 & AI-1.2) */}
                {ragResult.citations.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs font-bold text-tradly-muted uppercase tracking-wider flex items-center space-x-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Grounded Source Citations ({ragResult.citations.length})</span>
                    </div>

                    <div className="grid grid-cols-1 gap-2">
                      {ragResult.citations.map((c) => (
                        <div
                          key={c.id}
                          className="p-3 rounded-xl bg-tradly-bg border border-tradly-border space-y-1 hover:border-cyan-500/30 transition-colors text-xs"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-white text-xs">{c.title}</span>
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                              Rel: {(c.relevance_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <p className="text-tradly-muted text-[11px] leading-snug">{c.snippet}</p>
                          <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                            <span>Source: {c.source}</span>
                            <span className="font-mono">{new Date(c.published_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: FinBERT Currency Sentiment Heatmap & Economic Calendar */}
        <div className="lg:col-span-5 space-y-6">
          {/* FinBERT Currency Sentiment Heatmap */}
          <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Flame className="w-4 h-4 text-amber-400" />
                <span>FinBERT Currency Sentiment Score</span>
              </h3>
              <span className="text-[10px] text-tradly-muted">Updated Hourly</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {sentiments.map((s) => (
                <div
                  key={s.currency}
                  className="p-3 rounded-xl bg-tradly-bg border border-tradly-border flex items-center justify-between"
                >
                  <div>
                    <div className="font-extrabold text-sm text-white">{s.currency}</div>
                    <div className="text-[10px] text-tradly-muted">{s.article_count} news feeds</div>
                  </div>
                  <div className="text-right">
                    <div
                      className={`font-bold font-mono text-xs px-2 py-0.5 rounded ${
                        s.score > 0.2
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : s.score < -0.2
                          ? "bg-red-500/20 text-red-400 border border-red-500/30"
                          : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {s.score > 0 ? `+${s.score}` : s.score}
                    </div>
                    <div className="text-[10px] text-tradly-muted mt-0.5">{s.label}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Economic Calendar & AI Event Briefings */}
          <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border space-y-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-cyan-400" />
                <span>High-Impact Economic Calendar</span>
              </h3>
            </div>

            <div className="space-y-2.5">
              {calendar.map((evt) => {
                const isExpanded = expandedBriefing === evt.id;
                return (
                  <div
                    key={evt.id}
                    className="p-3 rounded-xl bg-tradly-bg border border-tradly-border space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{evt.title}</span>
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30">
                        {evt.impact} Impact
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-tradly-muted font-mono text-[11px]">
                      <span>Curr: <strong className="text-white">{evt.currency}</strong></span>
                      <span>Consensus: <strong className="text-cyan-400">{evt.consensus}</strong></span>
                      <span>Previous: {evt.previous}</span>
                    </div>

                    {evt.ai_briefing && (
                      <div className="pt-1">
                        <button
                          onClick={() => setExpandedBriefing(isExpanded ? null : evt.id)}
                          className="text-[11px] text-cyan-400 hover:underline font-semibold flex items-center space-x-1"
                        >
                          <FileText className="w-3 h-3" />
                          <span>{isExpanded ? "Hide AI Volatility Briefing" : "Expand AI Volatility Briefing"}</span>
                        </button>

                        {isExpanded && (
                          <div className="mt-2 p-2.5 rounded-lg bg-tradly-card border border-tradly-border text-[11px] text-slate-300 space-y-1">
                            <p>{evt.ai_briefing}</p>
                            {evt.historical_pip_volatility && (
                              <div className="text-[10px] font-mono text-amber-400 pt-1 border-t border-tradly-border/50">
                                Historical Volatility: {evt.historical_pip_volatility}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
