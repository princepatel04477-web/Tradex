"use client";

import React, { useEffect, useState } from "react";
import { Activity, Clock, ShieldCheck, Zap, User, LogOut, LogIn } from "lucide-react";
import { api } from "../../services/api";
import { MarketSessionOverview, AccountMetrics } from "../../types/market";
import { useAuth } from "../../context/AuthContext";
import AuthModal from "../auth/AuthModal";

export default function Navbar() {
  const [sessionInfo, setSessionInfo] = useState<MarketSessionOverview | null>(null);
  const [metrics, setMetrics] = useState<AccountMetrics | null>(null);
  const { user, logout, openAuthModal } = useAuth();

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
    <>
      <header className="h-16 bg-tradly-card border-b border-tradly-border px-6 flex items-center justify-between sticky top-0 z-40">
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

        {/* Auth Profile / Sign In Button & Equity */}
        <div className="flex items-center space-x-4">
          {metrics && (
            <div className="text-right hidden sm:block">
              <div className="text-[10px] text-tradly-muted font-bold uppercase">Equity</div>
              <div className="text-xs font-bold text-white font-mono">${metrics.equity.toLocaleString()}</div>
            </div>
          )}

          {user ? (
            <div className="flex items-center space-x-2.5 bg-tradly-bg p-1.5 pl-3 rounded-2xl border border-tradly-border text-xs font-mono">
              <div className="flex items-center space-x-2">
                <div className="w-6 h-6 rounded-full bg-cyan-500/20 border border-cyan-400 flex items-center justify-center text-cyan-400 font-bold text-[10px]">
                  {user.name.slice(0, 2).toUpperCase()}
                </div>
                <span className="text-white font-bold hidden md:inline">{user.name}</span>
              </div>
              <button
                onClick={logout}
                title="Sign Out"
                className="p-1.5 rounded-xl hover:bg-tradly-hover text-tradly-muted hover:text-red-400 transition-colors cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={openAuthModal}
              className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 font-bold text-xs transition-all cursor-pointer"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Sign In / Register</span>
            </button>
          )}

          <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-medium">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Paper Engine</span>
          </div>
        </div>
      </header>
      <AuthModal />
    </>
  );
}
