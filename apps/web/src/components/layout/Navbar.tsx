"use client";

import React, { useEffect, useState } from "react";
import { Activity, Clock, ShieldCheck, Zap } from "lucide-react";
import { api } from "../../services/api";
import { MarketSessionOverview, AccountMetrics } from "../../types/market";

export default function Navbar() {
  const [sessionInfo, setSessionInfo] = useState<MarketSessionOverview | null>(null);
  const [metrics, setMetrics] = useState<AccountMetrics | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [sess, met] = await Promise.all([
          api.getMarketSessions(),
          api.getAccountMetrics()
        ]);
        setSessionInfo(sess);
        setMetrics(met);
      } catch (err) {
        // Fallback info if server offline
      }
    }
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-tradly-card border-b border-tradly-border px-6 flex items-center justify-between sticky top-0 z-50">
      {/* Brand Logo & Tag */}
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Zap className="w-5 h-5 text-black stroke-[2.5]" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-extrabold text-xl tracking-tight text-white">TRADLY</span>
            <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              AI/ML v1.0
            </span>
          </div>
          <p className="text-xs text-tradly-muted font-medium">Forex Intelligence Platform</p>
        </div>
      </div>

      {/* FX Market Sessions Clock & Overlap Badge */}
      <div className="hidden md:flex items-center space-x-4">
        {sessionInfo?.active_overlap && (
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold animate-pulse">
            <Activity className="w-3.5 h-3.5" />
            <span>{sessionInfo.active_overlap}</span>
          </div>
        )}

        <div className="flex items-center space-x-2 bg-tradly-bg px-3 py-1.5 rounded-xl border border-tradly-border text-xs">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-tradly-muted font-mono">{sessionInfo?.current_utc_time || "UTC"}</span>
          <div className="h-3 w-px bg-tradly-border mx-1" />
          <div className="flex items-center space-x-2">
            {sessionInfo?.sessions.map((s) => (
              <span
                key={s.name}
                className={`px-1.5 py-0.5 rounded font-medium text-[11px] ${
                  s.is_active
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : "text-tradly-muted opacity-60"
                }`}
              >
                {s.name}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Account Equity Summary & Status */}
      <div className="flex items-center space-x-4">
        {metrics && (
          <div className="text-right hidden sm:block">
            <div className="text-xs text-tradly-muted">Equity</div>
            <div className="text-sm font-bold text-white font-mono">${metrics.equity.toLocaleString()}</div>
          </div>
        )}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-medium">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Paper Engine Active</span>
        </div>
      </div>
    </header>
  );
}
