"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  ShieldCheck,
  RefreshCw,
  Zap,
  CheckCircle2,
  ChevronRight,
  Sparkles,
  Layers,
  Activity,
  DollarSign,
  Radio,
} from "lucide-react";
import gsap from "gsap";
import { api } from "../services/api";
import { CurrencyPair, CompositeBias, AccountMetrics } from "../types/market";
import { useGsapStagger } from "../hooks/useGsap";

// Dynamic import for 3D FX Globe
const FXGlobe = dynamic(() => import("../components/3d/FXGlobe"), { ssr: false });

export default function CommandCenter() {
  const [pairs, setPairs] = useState<CurrencyPair[]>([]);
  const [selectedPair, setSelectedPair] = useState<string>("EUR_USD");
  const [bias, setBias] = useState<CompositeBias | null>(null);
  const [metrics, setMetrics] = useState<AccountMetrics | null>(null);
  const [orderSide, setOrderSide] = useState<"buy" | "sell">("buy");
  const [lotSize, setLotSize] = useState<number>(0.1);
  const [leverage, setLeverage] = useState<number>(30);
  const [orderMsg, setOrderMsg] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // GSAP stagger container ref
  const containerRef = useGsapStagger<HTMLDivElement>(".gsap-reveal", [pairs.length > 0]);

  useEffect(() => {
    async function loadInitial() {
      try {
        const [pData, mData] = await Promise.all([
          api.getPairs().catch(() => []),
          api.getAccountMetrics().catch(() => null),
        ]);
        if (pData && pData.length > 0) {
          setPairs(pData);
          const b = await api.getCompositeBias(pData[0].symbol).catch(() => null);
          if (b) setBias(b);
        }
        if (mData) {
          setMetrics(mData);
        }
      } catch (err) {
        console.warn("Dashboard using offline initial state:", err);
      }
    }
    loadInitial();

    // Dynamic WebSocket stream
    let ws: WebSocket | null = null;
    try {
      const wsUrl =
        process.env.NEXT_PUBLIC_WS_URL ||
        (typeof window !== "undefined" && window.location.hostname === "localhost"
          ? "ws://localhost:8000/api/v1/ws/stream"
          : "wss://tradex-api-q7re.onrender.com/api/v1/ws/stream");
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "ticks_update" || data.type === "market_tick") {
            if (data.pairs) setPairs(data.pairs);
            if (data.ticks) {
              setPairs((prev) =>
                prev.map((p) => {
                  const t = data.ticks[p.symbol];
                  return t ? { ...p, bid: t.bid, ask: t.ask, spread_pips: t.spread_pips } : p;
                })
              );
            }
            if (data.metrics) setMetrics(data.metrics);
            if (data.account) setMetrics(data.account);
          }
        } catch (e) {}
      };
    } catch (e) {}

    return () => {
      if (ws) ws.close();
    };
  }, []);

  const handlePairSelect = async (symbol: string) => {
    setSelectedPair(symbol);
    try {
      const b = await api.getCompositeBias(symbol);
      setBias(b);
    } catch (e) {}
  };

  const handlePlaceOrder = async () => {
    try {
      setIsSubmitting(true);
      setOrderMsg("");
      await api.placeOrder({
        symbol: selectedPair,
        direction: orderSide,
        lot_size: lotSize,
        leverage: leverage,
      });
      const newMet = await api.getAccountMetrics();
      setMetrics(newMet);
      setOrderMsg(`Executed ${lotSize} Lot ${orderSide.toUpperCase()} on ${selectedPair.replace("_", "/")}`);
    } catch (err: any) {
      setOrderMsg(`Execution error: ${err.message || "Failed to place order"}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const activePairObj = pairs.find((p) => p.symbol === selectedPair) || pairs[0];

  return (
    <div ref={containerRef} className="space-y-6 pb-12 selection:bg-cyan-500 selection:text-black">
      {/* Hero Telemetry Banner */}
      <div className="gsap-reveal relative rounded-3xl bg-gradient-to-r from-[#0C101A] via-[#101726] to-[#0A1220] border border-tradly-border p-7 shadow-card-depth overflow-hidden">
        <div className="absolute -right-24 -top-24 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -left-24 -bottom-24 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center space-x-3">
              <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-cyan-400/10 text-cyan-400 border border-cyan-400/30 text-[11px] font-bold font-mono">
                <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
                <span>15 FX PAIRS STREAMING</span>
              </span>
              <span className="text-[11px] font-mono text-tradly-muted">Twelve Data Engine</span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight font-sans">
              Institutional Market Command
            </h1>
            <p className="text-sm text-tradly-secondary leading-relaxed">
              Multi-timeframe price action confluence, rule-ensemble AI signals, and pip-accurate institutional execution.
            </p>
          </div>

          {/* Quick HUD Metrics */}
          {metrics && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 bg-[#06080D]/80 backdrop-blur-xl p-4 rounded-2xl border border-tradly-border shadow-inner font-mono">
              <div className="p-2.5">
                <div className="text-[10px] uppercase font-bold text-tradly-muted tracking-wider">Account Equity</div>
                <div className="text-lg font-black text-white tracking-tight">
                  ${metrics.equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>

              <div className="p-2.5 border-l border-tradly-border/70">
                <div className="text-[10px] uppercase font-bold text-tradly-muted tracking-wider">Free Margin</div>
                <div className="text-lg font-black text-emerald-400 tracking-tight">
                  ${metrics.free_margin.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>

              <div className="p-2.5 border-l border-tradly-border/70 col-span-2 sm:col-span-1">
                <div className="text-[10px] uppercase font-bold text-tradly-muted tracking-wider">Margin Level</div>
                <div
                  className={`text-lg font-black tracking-tight ${
                    metrics.margin_level_pct < 100 ? "text-red-400" : "text-cyan-400"
                  }`}
                >
                  {metrics.margin_level_pct.toFixed(0)}%
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bento Grid Architecture */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left 8-Column Block: 3D Visualization + AI Bias + Pairs Grid */}
        <div className="lg:col-span-8 space-y-6">
          {/* Top Row: 3D Interactive FX Sphere & AI Directional Engine */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 3D Global Liquidity Globe */}
            <div className="gsap-reveal h-[280px] rounded-3xl bg-[#080C14] border border-tradly-border overflow-hidden shadow-card-depth relative">
              <div className="absolute top-3 left-4 z-10 flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="text-[10px] font-bold font-mono tracking-widest text-tradly-muted uppercase">
                  Global Liquidity Map
                </span>
              </div>
              <FXGlobe />
            </div>

            {/* AI Ensemble Confluence Bias Card */}
            <div className="gsap-reveal p-6 rounded-3xl bg-tradly-card border border-tradly-border shadow-card-depth flex flex-col justify-between relative overflow-hidden">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-bold font-mono text-tradly-muted uppercase tracking-wider">
                      Composite Bias Engine
                    </span>
                  </div>
                  <span className="text-xs font-black font-mono text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-lg border border-cyan-500/20">
                    {selectedPair.replace("_", "/")} (H1)
                  </span>
                </div>

                {bias ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between bg-[#080C14] p-4 rounded-2xl border border-tradly-border">
                      <div className="flex items-center space-x-3.5">
                        {bias.score >= 0.2 ? (
                          <div className="w-11 h-11 rounded-xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center justify-center shadow-neon-emerald">
                            <TrendingUp className="w-6 h-6 stroke-[2.5]" />
                          </div>
                        ) : bias.score <= -0.2 ? (
                          <div className="w-11 h-11 rounded-xl bg-red-500/15 text-red-400 border border-red-500/30 flex items-center justify-center shadow-neon-red">
                            <TrendingDown className="w-6 h-6 stroke-[2.5]" />
                          </div>
                        ) : (
                          <div className="w-11 h-11 rounded-xl bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center justify-center">
                            <RefreshCw className="w-6 h-6 stroke-[2.5]" />
                          </div>
                        )}
                        <div>
                          <div className="text-lg font-black text-white font-mono">{bias.bias}</div>
                          <div className="text-xs text-tradly-muted font-mono">
                            Conviction: <strong className="text-cyan-400">{bias.score > 0 ? `+${bias.score}` : bias.score}</strong>
                          </div>
                        </div>
                      </div>

                      <Link
                        href={`/trading-analysis?pair=${selectedPair.replace("_", "/")}`}
                        className="px-3 py-2 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-bold flex items-center space-x-1.5 transition-all"
                      >
                        <span>Workspace</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>

                    <div className="space-y-2">
                      <div className="text-[11px] font-bold uppercase tracking-wider text-tradly-muted font-mono">
                        Confluence Drivers
                      </div>
                      <div className="space-y-1.5">
                        {bias.reasons.slice(0, 3).map((reason, idx) => (
                          <div key={idx} className="flex items-start space-x-2 text-xs text-tradly-secondary font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                            <span>{reason}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-tradly-muted py-10 text-center font-mono animate-pulse">
                    Aggregating multi-timeframe indicators...
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-tradly-border flex items-center justify-between text-[10px] font-mono text-tradly-muted">
                <span>Rule-Ensemble Logic</span>
                <span className="text-emerald-400 font-bold">100% Deterministic</span>
              </div>
            </div>
          </div>

          {/* Live Currency Ticker Matrix (Gapless Grid) */}
          <div className="gsap-reveal p-6 rounded-3xl bg-tradly-card border border-tradly-border shadow-card-depth space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-cyan-400" />
                </div>
                <h2 className="text-base font-bold text-white font-mono">Real-Time Currency Ticker Matrix</h2>
              </div>
              <span className="text-xs text-tradly-muted font-mono">Select pair to populate ticket</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {pairs.map((p) => {
                const isSelected = p.symbol === selectedPair;
                const isPos = (p.change_24h_pct || 0) >= 0;
                return (
                  <button
                    key={p.symbol}
                    onClick={() => handlePairSelect(p.symbol)}
                    className={`p-4 rounded-2xl border text-left transition-all duration-200 cursor-pointer font-mono ${
                      isSelected
                        ? "bg-cyan-500/10 border-cyan-400/60 shadow-neon-cyan"
                        : "bg-[#080C14] border-tradly-border hover:border-cyan-500/40 hover:bg-[#0D121E]"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-sm text-white">{p.symbol.replace("_", "/")}</span>
                      <span
                        className={`text-xs font-bold flex items-center px-1.5 py-0.5 rounded-md ${
                          isPos
                            ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                            : "bg-red-500/15 text-red-400 border border-red-500/30"
                        }`}
                      >
                        {isPos ? <ArrowUpRight className="w-3 h-3 mr-0.5" /> : <ArrowDownRight className="w-3 h-3 mr-0.5" />}
                        {p.change_24h_pct >= 0 ? `+${(p.change_24h_pct || 0).toFixed(2)}%` : `${(p.change_24h_pct || 0).toFixed(2)}%`}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs pt-1 border-t border-tradly-border/50">
                      <div>
                        <span className="text-[10px] text-tradly-muted mr-1">BID</span>
                        <span className="text-white font-bold">{p.bid.toFixed(4)}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-tradly-muted mr-1">ASK</span>
                        <span className="text-white font-bold">{p.ask.toFixed(4)}</span>
                      </div>
                    </div>

                    <div className="mt-2 flex items-center justify-between text-[10px] text-tradly-muted">
                      <span>Spread: <strong className="text-cyan-400">{p.spread_pips} pips</strong></span>
                      <span className="uppercase text-[9px] px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-300">
                        {p.category || "Major"}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right 4-Column Block: Institutional Order Execution Ticket */}
        <div className="lg:col-span-4 space-y-6">
          <div className="gsap-reveal p-6 rounded-3xl bg-tradly-card border border-tradly-border shadow-card-depth space-y-5 font-mono">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <DollarSign className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-black text-white uppercase tracking-wider">Order Execution Ticket</h2>
              </div>
              <span className="text-xs font-bold text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-lg border border-cyan-500/20">
                {activePairObj ? activePairObj.symbol.replace("_", "/") : "EUR/USD"}
              </span>
            </div>

            {/* Long / Short Selection Buttons */}
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setOrderSide("buy")}
                className={`py-3.5 rounded-2xl font-black text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer ${
                  orderSide === "buy"
                    ? "bg-gradient-to-r from-emerald-500 to-teal-400 text-black shadow-neon-emerald font-black"
                    : "bg-[#080C14] text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/10"
                }`}
              >
                <TrendingUp className="w-4 h-4 stroke-[2.5]" />
                <span>BUY (LONG)</span>
              </button>

              <button
                type="button"
                onClick={() => setOrderSide("sell")}
                className={`py-3.5 rounded-2xl font-black text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer ${
                  orderSide === "sell"
                    ? "bg-gradient-to-r from-red-500 to-rose-400 text-white shadow-neon-red font-black"
                    : "bg-[#080C14] text-red-400 border border-red-500/30 hover:bg-red-500/10"
                }`}
              >
                <TrendingDown className="w-4 h-4 stroke-[2.5]" />
                <span>SELL (SHORT)</span>
              </button>
            </div>

            {/* Real-Time Price Fill Preview */}
            {activePairObj && (
              <div className="p-4 rounded-2xl bg-[#080C14] border border-tradly-border flex items-center justify-between text-xs">
                <div>
                  <span className="text-[10px] text-tradly-muted uppercase block mb-0.5">Execution Fill Price</span>
                  <span className="text-white font-black text-base">
                    {orderSide === "buy" ? activePairObj.ask.toFixed(4) : activePairObj.bid.toFixed(4)}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-tradly-muted uppercase block mb-0.5">Calculated Spread</span>
                  <span className="text-cyan-400 font-bold text-sm">{activePairObj.spread_pips} pips</span>
                </div>
              </div>
            )}

            {/* Position Size (Lots) */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-tradly-muted font-bold text-[10px] uppercase tracking-wider">Position Size (Lots)</span>
                <span className="text-cyan-400 font-bold">
                  {lotSize === 1.0 ? "1.0 Standard (100k units)" : lotSize === 0.1 ? "0.1 Mini (10k units)" : `${lotSize} Lots`}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {[0.01, 0.1, 1.0].map((size) => (
                  <button
                    key={size}
                    type="button"
                    onClick={() => setLotSize(size)}
                    className={`py-2.5 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
                      lotSize === size
                        ? "bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-neon-cyan"
                        : "bg-[#080C14] border-tradly-border text-tradly-secondary hover:bg-[#0E1422]"
                    }`}
                  >
                    {size === 1.0 ? "1.0 Std" : size === 0.1 ? "0.1 Mini" : "0.01 Micro"}
                  </button>
                ))}
              </div>
            </div>

            {/* Account Leverage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-tradly-muted font-bold text-[10px] uppercase tracking-wider">Account Leverage</span>
                <span className="text-cyan-400 font-bold">1:{leverage}</span>
              </div>
              <select
                value={leverage}
                onChange={(e) => setLeverage(Number(e.target.value))}
                className="w-full p-3 rounded-xl bg-[#080C14] border border-tradly-border text-white text-xs focus:outline-none focus:border-cyan-400 transition-colors"
              >
                <option value={1}>1:1 (No Leverage)</option>
                <option value={10}>1:10 (Conservative)</option>
                <option value={30}>1:30 (Institutional Standard)</option>
                <option value={50}>1:50 (Aggressive)</option>
                <option value={100}>1:100 (Max Capacity)</option>
              </select>
            </div>

            {/* Submit Order Button */}
            <button
              type="button"
              disabled={isSubmitting}
              onClick={handlePlaceOrder}
              className={`w-full py-4 rounded-2xl font-black text-xs uppercase tracking-widest transition-all cursor-pointer transform active:scale-[0.98] disabled:opacity-50 ${
                orderSide === "buy"
                  ? "bg-gradient-to-r from-emerald-400 to-teal-400 text-black shadow-neon-emerald"
                  : "bg-gradient-to-r from-red-500 to-rose-500 text-white shadow-neon-red"
              }`}
            >
              <span>{isSubmitting ? "Routing to Engine..." : "Submit Market Order"}</span>
            </button>

            {orderMsg && (
              <div
                className={`p-3.5 rounded-2xl text-xs font-semibold ${
                  orderMsg.startsWith("Execution error")
                    ? "bg-red-500/10 border border-red-500/30 text-red-400"
                    : "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                }`}
              >
                {orderMsg}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
