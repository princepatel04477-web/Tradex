"use client";

import React, { useEffect, useState } from "react";
import {
  DollarSign, TrendingUp, TrendingDown, RefreshCw, XCircle,
  AlertCircle, ShieldCheck, PieChart, Layers
} from "lucide-react";
import { api } from "../../services/api";
import { Position, AccountMetrics, CurrencyPair } from "../../types/market";

export default function PaperTradingPage() {
  const [metrics, setMetrics] = useState<AccountMetrics | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [pairs, setPairs] = useState<CurrencyPair[]>([]);
  
  // Order ticket state
  const [selectedPair, setSelectedPair] = useState<string>("EUR_USD");
  const [direction, setDirection] = useState<"buy" | "sell">("buy");
  const [lotSize, setLotSize] = useState<number>(0.1);
  const [leverage, setLeverage] = useState<number>(30);
  const [stopLossPips, setStopLossPips] = useState<string>("");
  const [takeProfitPips, setTakeProfitPips] = useState<string>("");
  const [trailingStopPips, setTrailingStopPips] = useState<string>("");
  const [orderError, setOrderError] = useState<string>("");
  const [orderSuccess, setOrderSuccess] = useState<string>("");

  useEffect(() => {
    async function loadData() {
      try {
        const [m, pos, pList] = await Promise.all([
          api.getAccountMetrics(),
          api.getPositions(),
          api.getPairs()
        ]);
        setMetrics(m);
        setPositions(pos);
        setPairs(pList);
      } catch (err) {
        console.error("Paper Trading load error", err);
      }
    }
    loadData();
    const interval = setInterval(loadData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setOrderError("");
    setOrderSuccess("");

    const activePair = pairs.find((p) => p.symbol === selectedPair);
    if (!activePair) return;

    const pipSize = activePair.pip_size;
    const currentPrice = direction === "buy" ? activePair.ask : activePair.bid;

    let slPrice: number | undefined = undefined;
    let tpPrice: number | undefined = undefined;

    if (stopLossPips) {
      const pips = parseFloat(stopLossPips);
      slPrice = direction === "buy" ? currentPrice - (pips * pipSize) : currentPrice + (pips * pipSize);
    }
    if (takeProfitPips) {
      const pips = parseFloat(takeProfitPips);
      tpPrice = direction === "buy" ? currentPrice + (pips * pipSize) : currentPrice - (pips * pipSize);
    }

    try {
      await api.placeOrder({
        symbol: selectedPair,
        direction: direction,
        lot_size: lotSize,
        leverage: leverage,
        stop_loss: slPrice ? roundPrice(slPrice, activePair.pip_decimal_places) : undefined,
        take_profit: tpPrice ? roundPrice(tpPrice, activePair.pip_decimal_places) : undefined,
        trailing_stop_pips: trailingStopPips ? parseFloat(trailingStopPips) : undefined,
      });

      setOrderSuccess(`Order Filled: ${direction.toUpperCase()} ${lotSize} lots of ${selectedPair.replace("_", "/")} @ ${currentPrice}`);
      const [newM, newPos] = await Promise.all([api.getAccountMetrics(), api.getPositions()]);
      setMetrics(newM);
      setPositions(newPos);
    } catch (err: any) {
      setOrderError(err.message || "Failed to place paper order");
    }
  };

  const handleClosePosition = async (id: string) => {
    try {
      await api.closePosition(id);
      const [newM, newPos] = await Promise.all([api.getAccountMetrics(), api.getPositions()]);
      setMetrics(newM);
      setPositions(newPos);
    } catch (err: any) {
      alert("Error closing position: " + err.message);
    }
  };

  const handleResetAccount = async () => {
    if (confirm("Are you sure you want to reset your paper account balance to $10,000? All active positions will be closed.")) {
      const newM = await api.resetAccount(10000);
      setMetrics(newM);
      setPositions([]);
    }
  };

  function roundPrice(val: number, decimals: number) {
    return Number(val.toFixed(decimals + 1));
  }

  const activePairObj = pairs.find((p) => p.symbol === selectedPair) || pairs[0];

  return (
    <div className="space-y-6">
      {/* Account Metrics Top Summary Bar */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="p-4 rounded-2xl bg-tradly-card border border-tradly-border">
            <div className="text-[10px] font-bold text-tradly-muted uppercase">Balance</div>
            <div className="text-xl font-extrabold text-white font-mono mt-1">${metrics.balance.toLocaleString()}</div>
          </div>
          <div className="p-4 rounded-2xl bg-tradly-card border border-tradly-border">
            <div className="text-[10px] font-bold text-tradly-muted uppercase">Equity</div>
            <div className="text-xl font-extrabold text-white font-mono mt-1">${metrics.equity.toLocaleString()}</div>
          </div>
          <div className="p-4 rounded-2xl bg-tradly-card border border-tradly-border">
            <div className="text-[10px] font-bold text-tradly-muted uppercase">Used Margin</div>
            <div className="text-xl font-extrabold text-white font-mono mt-1">${metrics.used_margin.toLocaleString()}</div>
          </div>
          <div className="p-4 rounded-2xl bg-tradly-card border border-tradly-border">
            <div className="text-[10px] font-bold text-tradly-muted uppercase">Free Margin</div>
            <div className="text-xl font-extrabold text-white font-mono mt-1">${metrics.free_margin.toLocaleString()}</div>
          </div>
          <div className="p-4 rounded-2xl bg-tradly-card border border-tradly-border col-span-2 md:col-span-1 flex items-center justify-between">
            <div>
              <div className="text-[10px] font-bold text-tradly-muted uppercase">Margin Level %</div>
              <div className={`text-xl font-extrabold font-mono mt-1 ${metrics.margin_level_pct < 100 ? "text-red-400" : "text-emerald-400"}`}>
                {metrics.margin_level_pct.toFixed(0)}%
              </div>
            </div>
            <button
              onClick={handleResetAccount}
              className="p-2 rounded-xl bg-tradly-bg hover:bg-tradly-hover border border-tradly-border text-xs text-tradly-muted hover:text-white transition-colors"
              title="Reset Account to $10,000"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Main Container: Ticket + Positions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Order Execution Ticket Form */}
        <div className="lg:col-span-5 p-5 rounded-2xl bg-tradly-card border border-tradly-border space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <DollarSign className="w-5 h-5 text-cyan-400" />
              <span>Paper Trading Ticket</span>
            </h2>
            <span className="text-xs text-tradly-muted">Instant Execution</span>
          </div>

          <form onSubmit={handlePlaceOrder} className="space-y-4">
            {/* Pair Selector */}
            <div className="space-y-1">
              <label className="text-xs text-tradly-muted font-medium">Currency Pair</label>
              <select
                value={selectedPair}
                onChange={(e) => setSelectedPair(e.target.value)}
                className="w-full p-3 rounded-xl bg-tradly-bg border border-tradly-border text-white text-sm font-bold font-mono focus:outline-none focus:border-cyan-400"
              >
                {pairs.map((p) => (
                  <option key={p.symbol} value={p.symbol}>
                    {p.name} ({p.spread_pips} pips spread)
                  </option>
                ))}
              </select>
            </div>

            {/* Direction Toggle */}
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setDirection("buy")}
                className={`py-3 rounded-xl font-extrabold text-sm flex items-center justify-center space-x-2 transition-all ${
                  direction === "buy"
                    ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/20"
                    : "bg-tradly-bg text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/10"
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                <span>BUY (LONG)</span>
              </button>

              <button
                type="button"
                onClick={() => setDirection("sell")}
                className={`py-3 rounded-xl font-extrabold text-sm flex items-center justify-center space-x-2 transition-all ${
                  direction === "sell"
                    ? "bg-red-500 text-white shadow-lg shadow-red-500/20"
                    : "bg-tradly-bg text-red-400 border border-red-500/30 hover:bg-red-500/10"
                }`}
              >
                <TrendingDown className="w-4 h-4" />
                <span>SELL (SHORT)</span>
              </button>
            </div>

            {/* Lot Size & Leverage Grid */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-tradly-muted font-medium">Lot Size</label>
                <select
                  value={lotSize}
                  onChange={(e) => setLotSize(Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl bg-tradly-bg border border-tradly-border text-white text-xs font-mono"
                >
                  <option value={0.01}>0.01 Micro (1k)</option>
                  <option value={0.1}>0.10 Mini (10k)</option>
                  <option value={0.5}>0.50 Lots (50k)</option>
                  <option value={1.0}>1.00 Standard (100k)</option>
                  <option value={5.0}>5.00 Standard (500k)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs text-tradly-muted font-medium">Leverage</label>
                <select
                  value={leverage}
                  onChange={(e) => setLeverage(Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl bg-tradly-bg border border-tradly-border text-white text-xs font-mono"
                >
                  <option value={1}>1:1</option>
                  <option value={10}>1:10</option>
                  <option value={30}>1:30</option>
                  <option value={50}>1:50</option>
                  <option value={100}>1:100</option>
                </select>
              </div>
            </div>

            {/* Stop Loss & Take Profit (Pips) */}
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-tradly-muted font-medium">Stop Loss (Pips)</label>
                <input
                  type="number"
                  placeholder="e.g. 20"
                  value={stopLossPips}
                  onChange={(e) => setStopLossPips(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-tradly-bg border border-tradly-border text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-tradly-muted font-medium">Take Profit (Pips)</label>
                <input
                  type="number"
                  placeholder="e.g. 50"
                  value={takeProfitPips}
                  onChange={(e) => setTakeProfitPips(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-tradly-bg border border-tradly-border text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-tradly-muted font-medium">Trailing Stop</label>
                <input
                  type="number"
                  placeholder="e.g. 15"
                  value={trailingStopPips}
                  onChange={(e) => setTrailingStopPips(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-tradly-bg border border-tradly-border text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
                />
              </div>
            </div>

            {/* Price Fill Preview */}
            {activePairObj && (
              <div className="p-3 rounded-xl bg-tradly-bg border border-tradly-border flex items-center justify-between text-xs font-mono text-tradly-muted">
                <span>Expected Fill: <strong className="text-white">{direction === "buy" ? activePairObj.ask : activePairObj.bid}</strong></span>
                <span>Margin: <strong className="text-cyan-400">${(((lotSize * 100000) * activePairObj.ask) / leverage).toFixed(2)}</strong></span>
              </div>
            )}

            <button
              type="submit"
              className={`w-full py-3.5 rounded-xl font-extrabold text-sm uppercase tracking-wider text-black transition-all shadow-lg ${
                direction === "buy"
                  ? "bg-emerald-400 hover:bg-emerald-300 shadow-emerald-500/20"
                  : "bg-red-400 hover:bg-red-300 text-white shadow-red-500/20"
              }`}
            >
              Execute Paper Order
            </button>

            {orderError && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium">
                {orderError}
              </div>
            )}
            {orderSuccess && (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
                {orderSuccess}
              </div>
            )}
          </form>
        </div>

        {/* Live Positions Table */}
        <div className="lg:col-span-7 p-5 rounded-2xl bg-tradly-card border border-tradly-border space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <Layers className="w-5 h-5 text-cyan-400" />
              <span>Open Positions ({positions.length})</span>
            </h2>
            <span className="text-xs text-tradly-muted font-mono">Real-time Tick P&L</span>
          </div>

          {positions.length === 0 ? (
            <div className="p-12 text-center text-tradly-muted text-xs space-y-2 border border-dashed border-tradly-border rounded-xl">
              <p>No active open positions in your paper account.</p>
              <p className="text-[11px] text-slate-500">Use the execution ticket to open long or short trades.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="text-tradly-muted border-b border-tradly-border uppercase text-[10px]">
                    <th className="py-2.5 px-2">Pair</th>
                    <th className="py-2.5 px-2">Type</th>
                    <th className="py-2.5 px-2">Lots</th>
                    <th className="py-2.5 px-2">Entry</th>
                    <th className="py-2.5 px-2">Current</th>
                    <th className="py-2.5 px-2">Floating P&L</th>
                    <th className="py-2.5 px-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-tradly-border/50">
                  {positions.map((pos) => {
                    const isPos = pos.unrealized_pnl >= 0;
                    return (
                      <tr key={pos.id} className="hover:bg-tradly-hover/50">
                        <td className="py-3 px-2 font-bold text-white">{pos.symbol.replace("_", "/")}</td>
                        <td className="py-3 px-2">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                              pos.direction === "long" || pos.direction === "buy"
                                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                : "bg-red-500/20 text-red-400 border border-red-500/30"
                            }`}
                          >
                            {pos.direction}
                          </span>
                        </td>
                        <td className="py-3 px-2 text-slate-300">{pos.lot_size}</td>
                        <td className="py-3 px-2 text-slate-300">{pos.entry_price}</td>
                        <td className="py-3 px-2 text-slate-300">{pos.current_price}</td>
                        <td className={`py-3 px-2 font-bold ${isPos ? "text-emerald-400" : "text-red-400"}`}>
                          {isPos ? `+$${pos.unrealized_pnl.toFixed(2)}` : `-$${Math.abs(pos.unrealized_pnl).toFixed(2)}`}
                          <span className="text-[10px] ml-1 opacity-70">
                            ({pos.unrealized_pnl_pips > 0 ? `+${pos.unrealized_pnl_pips}` : pos.unrealized_pnl_pips} pips)
                          </span>
                        </td>
                        <td className="py-3 px-2 text-right">
                          <button
                            onClick={() => handleClosePosition(pos.id)}
                            className="px-2.5 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-[11px] font-bold transition-colors"
                          >
                            Close Position
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
