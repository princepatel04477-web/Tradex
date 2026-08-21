"use client";

import React, { useEffect, useState, useRef } from "react";
import { Activity, Clock, ShieldCheck, Zap, LogOut, TrendingUp, ChevronDown } from "lucide-react";
import gsap from "gsap";
import { api } from "../../services/api";
import { MarketSessionOverview, AccountMetrics } from "../../types/market";
import { useAuth } from "../../context/AuthContext";

export default function Navbar() {
  const [sessionInfo, setSessionInfo] = useState<MarketSessionOverview | null>(null);
  const [metrics, setMetrics] = useState<AccountMetrics | null>(null);
  const { user, logout } = useAuth();
  const equityRef = useRef<HTMLSpanElement>(null);
  const navRef = useRef<HTMLElement>(null);

  useEffect(() => {
    // Navbar initial GSAP entrance
    if (navRef.current) {
      gsap.fromTo(
        navRef.current,
        { y: -20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }
      );
    }

    async function loadData() {
      try {
        const [sess, met] = await Promise.all([
          api.getMarketSessions(),
          api.getAccountMetrics()
        ]);
        setSessionInfo(sess);
        setMetrics(met);
      } catch (err) {
        // Fallback
      }
    }
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header
      ref={navRef}
      className="h-16 bg-[#080C14]/80 backdrop-blur-xl border-b border-tradly-border px-6 flex items-center justify-between sticky top-0 z-40 selection:bg-cyan-500 selection:text-black"
    >
      {/* Brand Logo & Tag */}
      <div className="flex items-center space-x-3.5">
        <div className="relative group cursor-pointer">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-400 via-blue-500 to-indigo-600 flex items-center justify-center shadow-neon-cyan transition-transform group-hover:scale-105">
            <Zap className="w-5 h-5 text-black stroke-[2.6]" />
          </div>
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-[#080C14]" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-black text-xl tracking-tight text-white font-mono">TRADLY</span>
            <span className="text-[10px] font-black tracking-widest px-2 py-0.5 rounded-md bg-cyan-400/10 text-cyan-400 border border-cyan-400/30">
              PRO
            </span>
          </div>
          <p className="text-[11px] text-tradly-muted font-medium tracking-wide">Forex Intelligence Platform</p>
        </div>
      </div>

      {/* FX Market Sessions Clock & Active Overlap Badge */}
      <div className="hidden md:flex items-center space-x-4">
        {sessionInfo?.active_overlap && (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold shadow-sm animate-pulse">
            <Activity className="w-3.5 h-3.5" />
            <span>{sessionInfo.active_overlap}</span>
          </div>
        )}

        <div className="flex items-center space-x-2.5 bg-[#0C101A] px-3.5 py-1.5 rounded-xl border border-tradly-border text-xs shadow-inner">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-tradly-secondary font-mono font-medium">{sessionInfo?.current_utc_time || "UTC"}</span>
          <div className="h-3.5 w-px bg-tradly-border mx-1" />
          <div className="flex items-center space-x-2">
            {sessionInfo?.sessions.map((s) => (
              <div
                key={s.name}
                className={`flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-medium transition-all ${
                  s.is_active
                    ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-neon-emerald"
                    : "text-tradly-muted opacity-50"
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    s.is_active ? "bg-emerald-400 animate-pulse" : "bg-tradly-muted"
                  }`}
                />
                <span>{s.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Account Equity & Operator Profile */}
      <div className="flex items-center space-x-4">
        {metrics && (
          <div className="text-right hidden sm:block bg-[#0C101A] px-3.5 py-1.5 rounded-xl border border-tradly-border">
            <div className="text-[9px] text-tradly-muted font-bold tracking-widest uppercase">Live Equity</div>
            <div className="text-xs font-black text-emerald-400 font-mono tracking-tight flex items-center justify-end space-x-1">
              <TrendingUp className="w-3 h-3 text-emerald-400 inline" />
              <span ref={equityRef}>${metrics.equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </div>
          </div>
        )}

        {user && (
          <div className="flex items-center space-x-2.5 bg-[#0C101A] p-1.5 pl-3 rounded-2xl border border-tradly-border text-xs font-mono shadow-sm">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-xl bg-gradient-to-tr from-cyan-400 to-blue-600 flex items-center justify-center text-black font-black text-[11px] shadow-neon-cyan">
                {user.name ? user.name.slice(0, 2).toUpperCase() : "PR"}
              </div>
              <div className="hidden md:flex flex-col text-left">
                <span className="text-white font-bold leading-tight">{user.name || user.email}</span>
                <span className="text-[9px] text-cyan-400 font-medium leading-none">VIP Admin</span>
              </div>
            </div>

            <button
              onClick={logout}
              title="Lock Terminal & Sign Out"
              className="p-2 rounded-xl hover:bg-red-500/10 text-tradly-muted hover:text-red-400 border border-transparent hover:border-red-500/20 transition-all cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
