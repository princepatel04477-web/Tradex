"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CandlestickChart,
  Bot,
  DollarSign,
  BarChart3,
  Target,
  Calculator,
  BookOpen,
  Compass,
  Radio,
  Sparkles,
} from "lucide-react";
import { api } from "../../services/api";
import { CurrencyPair } from "../../types/market";

const NAV_ITEMS = [
  { name: "Command Center", href: "/", icon: LayoutDashboard },
  { name: "Analysis Workspace", href: "/trading-analysis", icon: Sparkles, badge: "AI + TV" },
  { name: "Interactive Chart", href: "/chart", icon: CandlestickChart },
  { name: "AI Macro Assistant", href: "/ai-assistant", icon: Bot },
  { name: "Paper Trading", href: "/paper-trading", icon: DollarSign },
  { name: "Performance & Journal", href: "/analytics", icon: BarChart3 },
];

const STRATEGY_ITEMS = [
  { name: "Confluence Engine", href: "/strategy", icon: Target },
  { name: "Risk & Sizing Sizer", href: "/strategy/risk", icon: Calculator },
  { name: "Trade Journal", href: "/strategy/journal", icon: BookOpen },
  { name: "Technical Playbook", href: "/strategy/reference", icon: Compass },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [pairs, setPairs] = useState<CurrencyPair[]>([]);

  useEffect(() => {
    async function loadPairs() {
      try {
        const data = await api.getPairs();
        setPairs(data.slice(0, 6));
      } catch (e) {
        // Fallback
      }
    }
    loadPairs();
    const interval = setInterval(loadPairs, 6000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="w-64 bg-[#080C14] border-r border-tradly-border flex flex-col justify-between p-4 shrink-0 min-h-[calc(100vh-4rem)] select-none">
      <div className="space-y-6">
        {/* Navigation Core */}
        <div>
          <div className="px-3 mb-2 text-[10px] font-black uppercase tracking-widest text-tradly-muted font-mono">
            Platform Engine
          </div>
          <nav className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`group relative flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-xs transition-all duration-200 ${
                    isActive
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-neon-cyan font-bold"
                      : "text-tradly-secondary hover:text-white hover:bg-[#0E1422] border border-transparent"
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Icon
                      className={`w-4 h-4 transition-transform group-hover:scale-110 ${
                        isActive ? "text-cyan-400" : "text-tradly-muted group-hover:text-cyan-400"
                      }`}
                    />
                    <span>{item.name}</span>
                  </div>

                  {item.badge && (
                    <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/30">
                      {item.badge}
                    </span>
                  )}

                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-cyan-400 rounded-r-full shadow-neon-cyan" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Forex Top-Down Confluence Toolkit */}
        <div>
          <div className="px-3 mb-2 text-[10px] font-black uppercase tracking-widest text-tradly-muted font-mono">
            Strategy Architecture
          </div>
          <nav className="space-y-1">
            {STRATEGY_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`group relative flex items-center space-x-3 px-3.5 py-2.5 rounded-xl font-medium text-xs transition-all duration-200 ${
                    isActive
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-neon-cyan font-bold"
                      : "text-tradly-secondary hover:text-white hover:bg-[#0E1422] border border-transparent"
                  }`}
                >
                  <Icon
                    className={`w-4 h-4 transition-transform group-hover:scale-110 ${
                      isActive ? "text-cyan-400" : "text-tradly-muted group-hover:text-cyan-400"
                    }`}
                  />
                  <span>{item.name}</span>

                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-cyan-400 rounded-r-full shadow-neon-cyan" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Currency Pair Quick Watchlist */}
        <div>
          <div className="px-3 mb-2 flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-tradly-muted font-mono">
            <span>Live FX Radar</span>
            <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
          </div>
          <div className="space-y-1.5 font-mono text-[11px]">
            {pairs.length > 0
              ? pairs.map((pair) => (
                  <Link
                    key={pair.symbol}
                    href={`/chart?pair=${pair.symbol.replace("/", "_")}`}
                    className="group flex items-center justify-between px-3 py-2 rounded-xl bg-[#0B0F19] hover:bg-[#121826] border border-tradly-border/70 hover:border-cyan-500/40 text-tradly-secondary hover:text-white transition-all shadow-sm"
                  >
                    <span className="font-bold">{pair.symbol}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-white text-xs">{pair.bid.toFixed(4)}</span>
                      <span
                        className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${
                          pair.change_24h_pct >= 0
                            ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                            : "bg-red-500/15 text-red-400 border border-red-500/30"
                        }`}
                      >
                        {pair.change_24h_pct >= 0 ? "+" : ""}
                        {pair.change_24h_pct.toFixed(2)}%
                      </span>
                    </div>
                  </Link>
                ))
              : ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "USD/CHF"].map((s) => (
                  <div
                    key={s}
                    className="flex items-center justify-between px-3 py-2 rounded-xl bg-[#0B0F19] border border-tradly-border/70 text-tradly-muted"
                  >
                    <span className="font-bold">{s}</span>
                    <span className="text-[10px] text-emerald-400 animate-pulse">STREAMING</span>
                  </div>
                ))}
          </div>
        </div>
      </div>

      {/* Quant Terminal Health Meter */}
      <div className="p-3.5 rounded-2xl bg-[#0B0F19] border border-tradly-border text-xs font-mono space-y-2">
        <div className="flex items-center justify-between text-white font-bold text-[11px]">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-neon-emerald" />
            <span>QUANT FEED ACTIVE</span>
          </div>
          <span className="text-[10px] text-cyan-400">12ms</span>
        </div>
        <div className="text-[10px] text-tradly-muted leading-tight flex items-center justify-between">
          <span>Neon Cluster: Synced</span>
          <span className="text-emerald-400">100%</span>
        </div>
      </div>
    </aside>
  );
}
