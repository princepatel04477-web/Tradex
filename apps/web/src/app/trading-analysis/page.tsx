"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Bot,
  Shield,
  Zap,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Layers,
  CheckCircle2,
  Play,
  Sparkles,
} from "lucide-react";
import TradingViewWidget from "../../components/chart/TradingViewWidget";
import AgentSquadPanel from "../../components/agents/AgentSquadPanel";
import { AgentRun } from "../../types/agents";
import { api } from "../../services/api";
import { CurrencyPair, CurrencySentiment } from "../../types/market";
import { useGsapStagger } from "../../hooks/useGsap";

function AnalysisWorkspaceContent() {
  const searchParams = useSearchParams();
  const initialPair = searchParams.get("pair") || "EUR_USD";

  const [symbol, setSymbol] = useState<string>(initialPair);
  const [timeframe, setTimeframe] = useState<string>("H1");
  const [pairs, setPairs] = useState<CurrencyPair[]>([]);
  const [sentiments, setSentiments] = useState<CurrencySentiment[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [agentRun, setAgentRun] = useState<AgentRun | null>(null);
  const [agentError, setAgentError] = useState<string | null>(null);

  const containerRef = useGsapStagger<HTMLDivElement>(".gsap-item", [symbol]);

  useEffect(() => {
    async function loadInitial() {
      try {
        const [pData, sData] = await Promise.all([
          api.getPairs(),
          api.getSentiments().catch(() => []),
        ]);
        setPairs(pData);
        if (Array.isArray(sData)) setSentiments(sData);
      } catch {
        setPairs([]);
      }
    }
    loadInitial();
  }, []);

  const handleRunAgentAnalysis = async () => {
    setIsAnalyzing(true);
    setAgentError(null);
    try {
      const run = await api.runAgentAnalysis(symbol, timeframe);
      setAgentRun(run);
    } catch (err) {
      setAgentRun(null);
      setAgentError(err instanceof Error ? err.message : "Agent analysis failed");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const selectedPairData = pairs.find((p) => p.symbol === symbol) || pairs[0];

  return (
    <div ref={containerRef} className="space-y-6 pb-12 selection:bg-cyan-500 selection:text-black">
      {/* Top Workspace Control Bar */}
      <div className="gsap-item p-4 rounded-3xl bg-[#080C14] border border-tradly-border flex flex-wrap items-center justify-between gap-4 shadow-card-depth">
        <div className="flex items-center space-x-4">
          <div>
            <label className="text-[10px] text-tradly-muted font-bold uppercase block mb-1 font-mono">
              Active Instrument
            </label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="p-2.5 rounded-xl bg-[#0C101A] border border-tradly-border text-white text-xs font-bold font-mono focus:outline-none focus:border-cyan-400 cursor-pointer shadow-inner"
            >
              {[
                "EUR_USD",
                "GBP_USD",
                "USD_JPY",
                "USD_CHF",
                "AUD_USD",
                "NZD_USD",
                "USD_CAD",
                "EUR_GBP",
                "EUR_JPY",
                "GBP_JPY",
                "AUD_JPY",
                "EUR_AUD",
                "USD_INR",
                "USD_SGD",
                "USD_MXN",
              ].map((p) => (
                <option key={p} value={p}>
                  {p.replace("_", "/")}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[10px] text-tradly-muted font-bold uppercase block mb-1 font-mono">
              Chart Interval
            </label>
            <div className="flex items-center space-x-1 bg-[#0C101A] p-1 rounded-xl border border-tradly-border text-xs font-mono">
              {["M1", "M5", "M15", "M30", "H1", "H4", "D1"].map((tf) => (
                <button
                  key={tf}
                  type="button"
                  onClick={() => setTimeframe(tf)}
                  className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                    timeframe === tf
                      ? "bg-cyan-400 text-black shadow-neon-cyan"
                      : "text-tradly-muted hover:text-white hover:bg-tradly-hover"
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Live Ticks & Run Agent Analysis CTA */}
        <div className="flex items-center space-x-4">
          {selectedPairData && (
            <div className="hidden sm:flex items-center space-x-3.5 bg-[#0C101A] px-4 py-2 rounded-xl border border-tradly-border text-xs font-mono shadow-inner">
              <div>
                <span className="text-[10px] text-tradly-muted mr-1.5">BID</span>
                <span className="text-white font-bold">{selectedPairData.bid.toFixed(4)}</span>
              </div>
              <div className="h-3.5 w-px bg-tradly-border" />
              <div>
                <span className="text-[10px] text-tradly-muted mr-1.5">ASK</span>
                <span className="text-white font-bold">{selectedPairData.ask.toFixed(4)}</span>
              </div>
              <div className="h-3.5 w-px bg-tradly-border" />
              <div>
                <span className="text-[10px] text-tradly-muted mr-1.5">SPREAD</span>
                <span className="text-cyan-400 font-bold">{selectedPairData.spread_pips} pips</span>
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={handleRunAgentAnalysis}
            disabled={isAnalyzing}
            className="flex items-center space-x-2 px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-300 hover:to-blue-400 text-black font-black text-xs shadow-neon-cyan transition-all transform active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-black" />
                <span>Squad Running...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-black fill-black" />
                <span>Deploy AI Analysis Squad</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Grid: TradingView Chart + AI Agent Intelligence Squad */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* TradingView Advanced Real-Time Chart (Left 8 Cols) */}
        <div className="xl:col-span-8 space-y-4">
          <div className="gsap-item p-5 rounded-3xl bg-tradly-card border border-tradly-border shadow-card-depth">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2.5">
                <Activity className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-bold text-white font-mono">
                  {symbol.replace("_", "/")} Official TradingView Advanced Terminal
                </h2>
              </div>
              <span className="text-xs text-emerald-400 font-mono flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-neon-emerald" />
                <span>Live Feed</span>
              </span>
            </div>

            {/* Embed Official TradingView Widget */}
            <TradingViewWidget symbol={symbol} interval={timeframe} height={660} />
          </div>
        </div>

        {/* AI Multi-Agent Squad & Confluence Panel (Right 4 Cols) */}
        <div className="xl:col-span-4 space-y-5">
          <div className="gsap-item">
            <AgentSquadPanel run={agentRun} isRunning={isAnalyzing} error={agentError} />
          </div>

          {/* Currency Sentiment Matrix */}
          <div className="gsap-item p-6 rounded-3xl bg-tradly-card border border-tradly-border shadow-card-depth space-y-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2 font-mono">
              <Layers className="w-4 h-4 text-cyan-400" />
              <span>Currency Sentiment Matrix</span>
            </h3>

            <div className="grid grid-cols-3 gap-2.5 text-xs font-mono">
              {sentiments.map((s) => (
                <div
                  key={s.currency}
                  className="p-2.5 rounded-xl bg-[#080C14] border border-tradly-border flex items-center justify-between"
                >
                  <span className="font-bold text-white">{s.currency}</span>
                  <span
                    className={`text-[11px] font-bold ${
                      s.score > 0.2 ? "text-emerald-400" : s.score < -0.2 ? "text-red-400" : "text-amber-300"
                    }`}
                  >
                    {s.score > 0.2 ? "▲" : s.score < -0.2 ? "▼" : "◆"} {s.score >= 0 ? "+" : ""}
                    {s.score.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AnalysisWorkspacePage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-xs text-tradly-muted font-mono animate-pulse">
          Initializing TradingView Engine & AI Squad...
        </div>
      }
    >
      <AnalysisWorkspaceContent />
    </Suspense>
  );
}
