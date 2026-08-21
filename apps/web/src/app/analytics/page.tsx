"use client";

import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid
} from "recharts";
import {
  BarChart3, TrendingUp, Award, AlertTriangle, ShieldCheck, Tag, Save, Check
} from "lucide-react";
import { api } from "../../services/api";
import { PerformanceAnalytics, ClosedTrade } from "../../types/market";

export default function AnalyticsJournalPage() {
  const [analytics, setAnalytics] = useState<PerformanceAnalytics | null>(null);
  const [closedTrades, setClosedTrades] = useState<ClosedTrade[]>([]);
  const [editingNotes, setEditingNotes] = useState<Record<string, string>>({});
  const [saveSuccess, setSaveSuccess] = useState<string>("");

  useEffect(() => {
    async function loadData() {
      try {
        const [aData, tData] = await Promise.all([
          api.getAnalytics(),
          api.getClosedTrades()
        ]);
        setAnalytics(aData);
        setClosedTrades(tData);
      } catch (err) {
        console.error("Analytics load error", err);
      }
    }
    loadData();
  }, []);

  const handleSaveNote = (id: string) => {
    const text = editingNotes[id];
    setClosedTrades((prev) =>
      prev.map((t) => (t.id === id ? { ...t, notes: text } : t))
    );
    setSaveSuccess(id);
    setTimeout(() => setSaveSuccess(""), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border flex items-center justify-between">
        <div>
          <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <span>Performance Analytics & Trade Journal</span>
          </h1>
          <p className="text-xs text-tradly-muted">
            Institutional performance metrics, equity curve visualization, and trade journal tagging.
          </p>
        </div>
      </div>

      {/* Key Performance Indicators Grid */}
      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-tradly-card border border-tradly-border">
            <div className="text-[10px] font-bold text-tradly-muted uppercase">Win Rate</div>
            <div className="text-2xl font-extrabold text-emerald-400 font-mono mt-1">
              {analytics.win_rate_pct}%
            </div>
            <div className="text-[11px] text-tradly-muted mt-0.5">
              {analytics.winning_trades} Wins / {analytics.losing_trades} Losses
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-tradly-card border border-tradly-border">
            <div className="text-[10px] font-bold text-tradly-muted uppercase">Total Realized P&L</div>
            <div
              className={`text-2xl font-extrabold font-mono mt-1 ${
                analytics.total_realized_pnl >= 0 ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {analytics.total_realized_pnl >= 0
                ? `+$${analytics.total_realized_pnl.toFixed(2)}`
                : `-$${Math.abs(analytics.total_realized_pnl).toFixed(2)}`}
            </div>
            <div className="text-[11px] text-tradly-muted mt-0.5">{analytics.total_trades} Closed Trades</div>
          </div>

          <div className="p-4 rounded-2xl bg-tradly-card border border-tradly-border">
            <div className="text-[10px] font-bold text-tradly-muted uppercase">Profit Factor</div>
            <div className="text-2xl font-extrabold text-cyan-400 font-mono mt-1">
              {analytics.profit_factor}
            </div>
            <div className="text-[11px] text-tradly-muted mt-0.5">Avg R:R {analytics.avg_risk_reward_ratio}:1</div>
          </div>

          <div className="p-4 rounded-2xl bg-tradly-card border border-tradly-border">
            <div className="text-[10px] font-bold text-tradly-muted uppercase">Max Drawdown</div>
            <div className="text-2xl font-extrabold text-red-400 font-mono mt-1">
              -{analytics.max_drawdown_pct}%
            </div>
            <div className="text-[11px] text-tradly-muted mt-0.5">-${analytics.max_drawdown_amount.toFixed(2)}</div>
          </div>
        </div>
      )}

      {/* Interactive Equity Curve Chart */}
      <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <span>Account Equity Curve Progress</span>
          </h2>
          <span className="text-xs text-tradly-muted font-mono">Realized P&L Growth</span>
        </div>

        <div className="h-[280px] w-full">
          {analytics && analytics.equity_curve.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics.equity_curve} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E2638" vertical={false} />
                <XAxis dataKey="timestamp" stroke="#94A3B8" fontSize={10} tickLine={false} />
                <YAxis stroke="#94A3B8" fontSize={10} domain={["auto", "auto"]} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#121722", borderColor: "#1E2638", borderRadius: "12px", fontSize: "12px" }}
                />
                <Line type="monotone" dataKey="equity" stroke="#00E676" strokeWidth={2.5} dot={false} name="Account Equity ($)" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-tradly-muted">
              Place and close paper trades to plot your equity curve.
            </div>
          )}
        </div>
      </div>

      {/* Trade Journaling Log */}
      <div className="p-5 rounded-2xl bg-tradly-card border border-tradly-border space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <Tag className="w-4 h-4 text-cyan-400" />
            <span>Trade Journal & Notes Log</span>
          </h2>
          <span className="text-xs text-tradly-muted">FR-5.8 Compliant</span>
        </div>

        {closedTrades.length === 0 ? (
          <div className="p-8 text-center text-tradly-muted text-xs border border-dashed border-tradly-border rounded-xl">
            No closed trades in journal history.
          </div>
        ) : (
          <div className="space-y-3">
            {closedTrades.map((t) => (
              <div
                key={t.id}
                className="p-4 rounded-xl bg-tradly-bg border border-tradly-border space-y-3 text-xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="font-bold text-white text-sm">{t.symbol.replace("_", "/")}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        t.direction === "long" || t.direction === "buy"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : "bg-red-500/20 text-red-400 border border-red-500/30"
                      }`}
                    >
                      {t.direction}
                    </span>
                    <span className="text-tradly-muted font-mono">{t.lot_size} Lots</span>
                  </div>

                  <div
                    className={`font-extrabold font-mono text-sm ${
                      t.realized_pnl >= 0 ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {t.realized_pnl >= 0 ? `+$${t.realized_pnl.toFixed(2)}` : `-$${Math.abs(t.realized_pnl).toFixed(2)}`}
                    <span className="text-xs ml-1 font-normal opacity-70">
                      ({t.realized_pnl_pips > 0 ? `+${t.realized_pnl_pips}` : t.realized_pnl_pips} pips)
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-4 text-tradly-muted text-[11px] font-mono">
                  <span>Entry: <strong className="text-white">{t.entry_price}</strong></span>
                  <span>Exit: <strong className="text-white">{t.exit_price}</strong></span>
                  <span>Reason: <span className="uppercase text-cyan-400">{t.close_reason}</span></span>
                  <span>Closed: {new Date(t.closed_at).toLocaleTimeString()}</span>
                </div>

                {/* Free-text Trade Notes Input */}
                <div className="flex items-center space-x-2 pt-2 border-t border-tradly-border/50">
                  <input
                    type="text"
                    placeholder="Attach trading journal notes or setup observations..."
                    value={editingNotes[t.id] ?? t.notes ?? ""}
                    onChange={(e) =>
                      setEditingNotes({ ...editingNotes, [t.id]: e.target.value })
                    }
                    className="flex-1 p-2 rounded-lg bg-tradly-card border border-tradly-border text-white text-xs focus:outline-none focus:border-cyan-400 placeholder:text-tradly-muted"
                  />
                  <button
                    onClick={() => handleSaveNote(t.id)}
                    className="flex items-center space-x-1 px-3 py-2 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-bold transition-all"
                  >
                    {saveSuccess === t.id ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Saved</span>
                      </>
                    ) : (
                      <>
                        <Save className="w-3.5 h-3.5" />
                        <span>Save Note</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
