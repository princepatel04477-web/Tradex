"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Download, Sliders, CheckSquare, Square, Zap, Activity, Layers, AlertTriangle } from "lucide-react";
import { api } from "../../services/api";
import { Candle, IndicatorSnapshot, CompositeBias } from "../../types/market";
import CandlestickChart from "../../components/chart/CandlestickChart";
import TradingViewWidget from "../../components/chart/TradingViewWidget";

function ChartContent() {
  const searchParams = useSearchParams();
  const initialPair = searchParams.get("pair") || "EUR_USD";

  const [symbol, setSymbol] = useState<string>(initialPair);
  const [timeframe, setTimeframe] = useState<string>("H1");
  const [chartMode, setChartMode] = useState<"tradingview" | "quant">("tradingview");
  const [candles, setCandles] = useState<Candle[]>([]);
  const [indicators, setIndicators] = useState<IndicatorSnapshot | null>(null);
  const [bias, setBias] = useState<CompositeBias | null>(null);

  // Indicator overlay toggles (up to 5 overlays allowed simultaneously FR-1.6)
  const [showRSI, setShowRSI] = useState<boolean>(true);
  const [showMACD, setShowMACD] = useState<boolean>(true);
  const [showBB, setShowBB] = useState<boolean>(true);
  const [showEMA, setShowEMA] = useState<boolean>(true);
  const [showSMA200, setShowSMA200] = useState<boolean>(true);

  useEffect(() => {
    async function loadChartData() {
      try {
        const [cData, iData, bData] = await Promise.all([
          api.getCandles(symbol, timeframe, 80),
          api.getIndicators(symbol, timeframe),
          api.getCompositeBias(symbol, timeframe)
        ]);
        setCandles(cData);
        setIndicators(iData);
        setBias(bData);
      } catch (err) {
        console.error("Failed to load chart data", err);
      }
    }
    loadChartData();
  }, [symbol, timeframe]);

  // Export CSV (FR-1.9)
  const handleExportCSV = () => {
    if (!candles.length) return;
    const headers = "Symbol,Timeframe,OpenTime,Open,High,Low,Close,Volume\n";
    const rows = candles
      .map(
        (c) =>
          `${c.symbol},${c.timeframe},"${c.open_time}",${c.open},${c.high},${c.low},${c.close},${c.volume}`
      )
      .join("\n");

    const blob = new Blob([headers + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `${symbol}_${timeframe}_candles.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div>
            <label className="text-[10px] text-tradly-muted font-bold uppercase block mb-1">Currency Pair</label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="p-2 rounded-xl bg-tradly-bg border border-tradly-border text-white text-sm font-bold font-mono focus:outline-none focus:border-cyan-400 cursor-pointer"
            >
              {[
                "EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD",
                "NZD_USD", "USD_CAD", "EUR_GBP", "EUR_JPY", "GBP_JPY",
                "AUD_JPY", "EUR_AUD", "USD_INR", "USD_SGD", "USD_MXN"
              ].map((p) => (
                <option key={p} value={p}>{p.replace("_", "/")}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[10px] text-tradly-muted font-bold uppercase block mb-1">Timeframe</label>
            <div className="flex items-center space-x-1 bg-tradly-bg p-1 rounded-xl border border-tradly-border text-xs font-mono">
              {["M1", "M5", "M15", "M30", "H1", "H4", "D1"].map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={`px-2.5 py-1 rounded-lg font-bold transition-all ${
                    timeframe === tf
                      ? "bg-cyan-500 text-black shadow-sm"
                      : "text-tradly-muted hover:text-white"
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-[10px] text-tradly-muted font-bold uppercase block mb-1">Chart Engine</label>
            <div className="flex items-center space-x-1 bg-tradly-bg p-1 rounded-xl border border-tradly-border text-xs font-mono">
              <button
                onClick={() => setChartMode("tradingview")}
                className={`px-3 py-1 rounded-lg font-bold flex items-center space-x-1.5 transition-all ${
                  chartMode === "tradingview"
                    ? "bg-cyan-500 text-black shadow-sm"
                    : "text-tradly-muted hover:text-white"
                }`}
              >
                <Activity className="w-3.5 h-3.5" />
                <span>TradingView Pro</span>
              </button>
              <button
                onClick={() => setChartMode("quant")}
                className={`px-3 py-1 rounded-lg font-bold flex items-center space-x-1.5 transition-all ${
                  chartMode === "quant"
                    ? "bg-cyan-500 text-black shadow-sm"
                    : "text-tradly-muted hover:text-white"
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Quant Studio</span>
              </button>
            </div>
          </div>
        </div>

        {/* Export CSV & Bias Badge */}
        <div className="flex items-center space-x-3">
          {bias && (
            <div className="px-3 py-1.5 rounded-xl bg-tradly-bg border border-tradly-border text-xs flex items-center space-x-2">
              <span className="text-tradly-muted font-medium">Quant Bias:</span>
              <span className={`font-bold font-mono ${bias.score >= 0.2 ? "text-emerald-400" : bias.score <= -0.2 ? "text-red-400" : "text-amber-400"}`}>
                {bias.bias} ({bias.score > 0 ? `+${bias.score}` : bias.score})
              </span>
            </div>
          )}

          <button
            onClick={handleExportCSV}
            className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-bold transition-all cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Main Chart Area */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-9 p-5 rounded-2xl bg-tradly-card border border-tradly-border space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center space-x-2">
              <Zap className="w-4 h-4 text-cyan-400" />
              <span>
                {symbol.replace("_", "/")} {chartMode === "tradingview" ? "TradingView Advanced Terminal" : "Quant Price Canvas"} ({timeframe})
              </span>
            </h2>
            <span className="text-xs text-tradly-muted font-mono">
              {chartMode === "tradingview" ? "Institutional Real-Time Feed" : `${candles.length} Candles Loaded`}
            </span>
          </div>

          {chartMode === "tradingview" ? (
            <TradingViewWidget
              symbol={symbol}
              interval={timeframe}
              height={620}
            />
          ) : (
            <CandlestickChart
              candles={candles}
              indicators={indicators}
              showRSI={showRSI}
              showMACD={showMACD}
              showBB={showBB}
              showEMA={showEMA}
              showSMA200={showSMA200}
            />
          )}
        </div>

        {/* Right Sidebar: Indicator Controls & Snapshot */}
        <div className="lg:col-span-3 space-y-6">
          {/* Indicator Overlays Toggle Panel (FR-1.6) */}
          <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border space-y-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <span>Technical Indicators</span>
            </h3>

            <div className="space-y-2 text-xs">
              {[
                { label: "RSI (14) Momentum", state: showRSI, setter: setShowRSI },
                { label: "MACD (12,26,9) Trend", state: showMACD, setter: setShowMACD },
                { label: "Bollinger Bands (20,2)", state: showBB, setter: setShowBB },
                { label: "EMA 9 & 21 Ribbon", state: showEMA, setter: setShowEMA },
                { label: "SMA 200 Institutional", state: showSMA200, setter: setShowSMA200 },
              ].map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => item.setter(!item.state)}
                  className="w-full flex items-center justify-between p-2 rounded-xl bg-tradly-bg hover:bg-tradly-hover border border-tradly-border text-slate-300 transition-colors cursor-pointer"
                >
                  <span>{item.label}</span>
                  {item.state ? <CheckSquare className="w-4 h-4 text-cyan-400" /> : <Square className="w-4 h-4 text-tradly-muted" />}
                </button>
              ))}
            </div>
          </div>

          {/* Indicator Values Snapshot */}
          {indicators && (
            <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border space-y-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Quant Metrics Snapshot</h3>
              
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-tradly-muted">RSI (14):</span>
                  <span className={`font-bold ${indicators.rsi_14 > 70 ? "text-red-400" : indicators.rsi_14 < 30 ? "text-emerald-400" : "text-white"}`}>
                    {indicators.rsi_14}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-tradly-muted">MACD Hist:</span>
                  <span className={indicators.macd_histogram >= 0 ? "text-emerald-400" : "text-red-400"}>
                    {indicators.macd_histogram}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-tradly-muted">ATR (14):</span>
                  <span className="text-white">{indicators.atr_14}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-tradly-muted">EMA 9 / 21:</span>
                  <span className="text-cyan-400">{indicators.ema_9} / {indicators.ema_21}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-tradly-muted">BB Upper/Lower:</span>
                  <span className="text-slate-300">{indicators.bb_upper} / {indicators.bb_lower}</span>
                </div>
              </div>

              {/* Pattern Alerts */}
              {(indicators.macd_crossover || indicators.rsi_condition !== "neutral") && (
                <div className="mt-3 pt-3 border-t border-tradly-border space-y-1.5">
                  <div className="text-[10px] uppercase font-bold text-amber-400 flex items-center space-x-1">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Active Technical Flags</span>
                  </div>
                  {indicators.macd_crossover && (
                    <div className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
                      MACD Crossover: {indicators.macd_crossover.toUpperCase()}
                    </div>
                  )}
                  {indicators.rsi_condition !== "neutral" && (
                    <div className="text-xs text-amber-400 bg-amber-500/10 px-2 py-1 rounded border border-amber-500/20">
                      RSI Alert: {indicators.rsi_condition?.toUpperCase()}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function InteractiveChartPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-tradly-muted font-mono">Loading TradingView Terminal...</div>}>
      <ChartContent />
    </Suspense>
  );
}
