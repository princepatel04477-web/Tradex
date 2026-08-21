"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight,
  ShieldCheck, RefreshCw, Zap, Sliders, CheckCircle2, ChevronRight
} from "lucide-react";
import { api } from "../services/api";
import { CurrencyPair, CompositeBias, AccountMetrics } from "../types/market";

// Dynamic import for 3D component
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

  useEffect(() => {
    async function loadInitial() {
      try {
        const [pData, mData] = await Promise.all([
          api.getPairs().catch(() => []),
          api.getAccountMetrics().catch(() => null)
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
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 
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
              setPairs(prev => prev.map(p => {
                const t = data.ticks[p.symbol];
                return t ? { ...p, bid: t.bid, ask: t.ask, spread_pips: t.spread_pips } : p;
              }));
            }
            if (data.metrics) setMetrics(data.metrics);
            if (data.account) setMetrics(data.account);
          }
        } catch (e) {}
      };
    } catch (e) {
      // WS fallback
    }

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
      setOrderMsg("");
      await api.placeOrder({
        symbol: selectedPair,
        direction: orderSide,
        lot_size: lotSize,
        leverage: leverage
      });
      const newMet = await api.getAccountMetrics();
      setMetrics(newMet);
      setOrderMsg(`Successfully opened ${lotSize} lot ${orderSide.toUpperCase()} on ${selectedPair.replace("_", "/")}`);
    } catch (err: any) {
      setOrderMsg(`Error: ${err.message || "Failed to place order"}`);
    }
  };

  const activePairObj = pairs.find((p) => p.symbol === selectedPair) || pairs[0];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-tradly-card via-tradly-card to-cyan-950/30 border border-tradly-border relative overflow-hidden">
        <div className="space-y-1 z-10">
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Market Command Center</h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              15 Pairs Streaming
            </span>
          </div>
          <p className="text-sm text-tradly-muted">
            Institutional multi-timeframe Forex intelligence, AI bias signals, and paper execution engine.
          </p>
        </div>

        {metrics && (
          <div className="flex items-center space-x-4 z-10 bg-tradly-bg/80 backdrop-blur p-3 rounded-xl border border-tradly-border">
            <div>
              <div className="text-[10px] uppercase font-semibold text-tradly-muted">Account Balance</div>
              <div className="text-lg font-bold text-white font-mono">${metrics.balance.toLocaleString()}</div>
            </div>
            <div className="h-8 w-px bg-tradly-border" />
            <div>
              <div className="text-[10px] uppercase font-semibold text-tradly-muted">Margin Level</div>
              <div className={`text-lg font-bold font-mono ${metrics.margin_level_pct < 100 ? "text-red-400" : "text-emerald-400"}`}>
                {metrics.margin_level_pct.toFixed(0)}%
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Grid: 3D Visual + Composite AI Bias + Quick Execution */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: 3D FX Globe + Active Composite Signal */}
        <div className="lg:col-span-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 3D Visual Sphere */}
            <div className="h-[260px]">
              <FXGlobe />
            </div>

            {/* AI Composite Directional Bias Card */}
            <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-tradly-muted uppercase tracking-wider">
                    AI Composite Bias
                  </span>
                  <span className="text-xs font-mono text-cyan-400">{selectedPair.replace("_", "/")} (H1)</span>
                </div>

                {bias ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {bias.score >= 0.2 ? (
                          <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <TrendingUp className="w-6 h-6" />
                          </div>
                        ) : bias.score <= -0.2 ? (
                          <div className="p-2 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20">
                            <TrendingDown className="w-6 h-6" />
                          </div>
                        ) : (
                          <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            <RefreshCw className="w-6 h-6" />
                          </div>
                        )}
                        <div>
                          <div className="text-lg font-bold text-white">{bias.bias}</div>
                          <div className="text-xs text-tradly-muted font-mono">Score: {bias.score > 0 ? `+${bias.score}` : bias.score}</div>
                        </div>
                      </div>
                      <Link
                        href={`/chart?pair=${selectedPair}`}
                        className="p-2 rounded-xl bg-tradly-hover hover:bg-cyan-500/20 text-cyan-400 transition-colors"
                      >
                        <ChevronRight className="w-5 h-5" />
                      </Link>
                    </div>

                    <div className="space-y-1.5 pt-2 border-t border-tradly-border">
                      <div className="text-[11px] font-semibold text-tradly-muted">Signal Contributing Factors:</div>
                      {bias.reasons.slice(0, 3).map((r, idx) => (
                        <div key={idx} className="flex items-start space-x-1.5 text-xs text-slate-300">
                          <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                          <span>{r}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-tradly-muted py-8 text-center">Loading AI signal analysis...</div>
                )}
              </div>

              <div className="mt-3 pt-2 text-[10px] text-tradly-muted border-t border-tradly-border flex items-center justify-between">
                <span>Rule-Ensemble Signal</span>
                <span className="text-cyan-400">SRS FG-2 Compliant</span>
              </div>
            </div>
          </div>

          {/* Real-Time Currency Pairs Grid */}
          <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <Zap className="w-4 h-4 text-cyan-400" />
                <span>Live Streaming Forex Pairs</span>
              </h2>
              <span className="text-xs text-tradly-muted">Click pair to select</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {pairs.map((p) => {
                const isSelected = p.symbol === selectedPair;
                const isPos = p.change_24h_pct >= 0;
                return (
                  <button
                    key={p.symbol}
                    onClick={() => handlePairSelect(p.symbol)}
                    className={`p-3.5 rounded-xl border text-left transition-all ${
                      isSelected
                        ? "bg-cyan-500/10 border-cyan-500/40 shadow-lg shadow-cyan-500/5"
                        : "bg-tradly-bg border-tradly-border hover:bg-tradly-hover"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-white">{p.name}</span>
                      <span className={`text-xs font-mono font-semibold flex items-center ${isPos ? "text-emerald-400" : "text-red-400"}`}>
                        {isPos ? <ArrowUpRight className="w-3 h-3 mr-0.5" /> : <ArrowDownRight className="w-3 h-3 mr-0.5" />}
                        {p.change_24h_pct > 0 ? `+${p.change_24h_pct}%` : `${p.change_24h_pct}%`}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs font-mono">
                      <div className="text-slate-300">
                        <span className="text-[10px] text-tradly-muted mr-1">BID</span>
                        {p.bid}
                      </div>
                      <div className="text-slate-300">
                        <span className="text-[10px] text-tradly-muted mr-1">ASK</span>
                        {p.ask}
                      </div>
                    </div>

                    <div className="mt-2 pt-1.5 border-t border-tradly-border/50 flex items-center justify-between text-[10px] text-tradly-muted">
                      <span>Spread: <strong className="text-cyan-400 font-mono">{p.spread_pips} pips</strong></span>
                      <span className="uppercase text-[9px] px-1 py-0.2 rounded bg-slate-800 text-slate-400">{p.category}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Quick Paper Execution Ticket */}
        <div className="lg:col-span-4 space-y-6">
          <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white">Quick Paper Execution</h2>
              <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                {activePairObj ? activePairObj.name : "EUR/USD"}
              </span>
            </div>

            {/* Buy / Sell Toggle Buttons */}
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setOrderSide("buy")}
                className={`py-3 rounded-xl font-bold text-sm flex items-center justify-center space-x-2 transition-all ${
                  orderSide === "buy"
                    ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/20"
                    : "bg-tradly-bg text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/10"
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                <span>BUY (LONG)</span>
              </button>

              <button
                onClick={() => setOrderSide("sell")}
                className={`py-3 rounded-xl font-bold text-sm flex items-center justify-center space-x-2 transition-all ${
                  orderSide === "sell"
                    ? "bg-red-500 text-white shadow-lg shadow-red-500/20"
                    : "bg-tradly-bg text-red-400 border border-red-500/30 hover:bg-red-500/10"
                }`}
              >
                <TrendingDown className="w-4 h-4" />
                <span>SELL (SHORT)</span>
              </button>
            </div>

            {/* Price Preview */}
            {activePairObj && (
              <div className="p-3 rounded-xl bg-tradly-bg border border-tradly-border flex items-center justify-between text-xs font-mono">
                <div>
                  <span className="text-tradly-muted">Order Fill Price:</span>
                  <div className="text-white font-bold text-sm">
                    {orderSide === "buy" ? activePairObj.ask : activePairObj.bid}
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-tradly-muted">Spread:</span>
                  <div className="text-cyan-400 font-bold">{activePairObj.spread_pips} pips</div>
                </div>
              </div>
            )}

            {/* Lot Size Selector */}
            <div className="space-y-1.5">
              <label className="text-xs text-tradly-muted font-medium flex justify-between">
                <span>Position Size (Lots)</span>
                <span className="text-cyan-400 font-mono">
                  {lotSize === 1.0 ? "1.0 Standard (100k)" : lotSize === 0.1 ? "0.1 Mini (10k)" : `${lotSize} Lots`}
                </span>
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[0.01, 0.1, 1.0].map((size) => (
                  <button
                    key={size}
                    onClick={() => setLotSize(size)}
                    className={`py-2 rounded-lg text-xs font-bold font-mono border ${
                      lotSize === size
                        ? "bg-cyan-500/20 border-cyan-400 text-cyan-400"
                        : "bg-tradly-bg border-tradly-border text-slate-300 hover:bg-tradly-hover"
                    }`}
                  >
                    {size === 1.0 ? "1.0 Std" : size === 0.1 ? "0.1 Mini" : "0.01 Micro"}
                  </button>
                ))}
              </div>
            </div>

            {/* Leverage Selector */}
            <div className="space-y-1.5">
              <label className="text-xs text-tradly-muted font-medium flex justify-between">
                <span>Account Leverage</span>
                <span className="text-cyan-400 font-mono">1:{leverage}</span>
              </label>
              <select
                value={leverage}
                onChange={(e) => setLeverage(Number(e.target.value))}
                className="w-full p-2.5 rounded-xl bg-tradly-bg border border-tradly-border text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
              >
                <option value={1}>1:1 (No Leverage)</option>
                <option value={10}>1:10</option>
                <option value={30}>1:30 (Default ESMA/Retail)</option>
                <option value={50}>1:50</option>
                <option value={100}>1:100 (Max Leverage)</option>
              </select>
            </div>

            {/* Execute Button */}
            <button
              onClick={handlePlaceOrder}
              className={`w-full py-3.5 rounded-xl font-extrabold text-sm uppercase tracking-wider text-black transition-all shadow-lg ${
                orderSide === "buy"
                  ? "bg-emerald-400 hover:bg-emerald-300 shadow-emerald-500/20"
                  : "bg-red-400 hover:bg-red-300 text-white shadow-red-500/20"
              }`}
            >
              Submit Paper Order
            </button>

            {orderMsg && (
              <div className={`p-3 rounded-xl text-xs font-medium ${
                orderMsg.startsWith("Error")
                  ? "bg-red-500/10 border border-red-500/20 text-red-400"
                  : "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
              }`}>
                {orderMsg}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
