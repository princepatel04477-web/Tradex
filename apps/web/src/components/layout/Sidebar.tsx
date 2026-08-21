"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, CandlestickChart, Bot, DollarSign, BarChart3,
  Target, Calculator, BookOpen, Compass
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Command Center", href: "/", icon: LayoutDashboard },
  { name: "Analysis Workspace", href: "/trading-analysis", icon: CandlestickChart },
  { name: "Interactive Chart", href: "/chart", icon: CandlestickChart },
  { name: "AI Assistant (RAG)", href: "/ai-assistant", icon: Bot },
  { name: "Paper Trading", href: "/paper-trading", icon: DollarSign },
  { name: "Analytics & Journal", href: "/analytics", icon: BarChart3 }
];

// The price-action toolkit - top-down confluence strategy engine.
const STRATEGY_ITEMS = [
  { name: "Confluence Toolkit", href: "/strategy", icon: Target },
  { name: "Risk & Sizing", href: "/strategy/risk", icon: Calculator },
  { name: "Trade Journal", href: "/strategy/journal", icon: BookOpen },
  { name: "Reference", href: "/strategy/reference", icon: Compass }
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-tradly-card border-r border-tradly-border flex flex-col justify-between p-4 shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        <div>
          <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-tradly-muted">
            Main Navigation
          </div>
          <nav className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                    isActive
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-md shadow-cyan-500/5 font-semibold"
                      : "text-tradly-muted hover:text-white hover:bg-tradly-hover"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-cyan-400" : "text-tradly-muted"}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Forex Top-Down Confluence Toolkit */}
        <div>
          <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-tradly-muted">
            Strategy Toolkit
          </div>
          <nav className="space-y-1">
            {STRATEGY_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                    isActive
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-md shadow-cyan-500/5 font-semibold"
                      : "text-tradly-muted hover:text-white hover:bg-tradly-hover"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-cyan-400" : "text-tradly-muted"}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Currency Pair Quick Watchlist */}
        <div>
          <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-tradly-muted">
            Major FX Watchlist
          </div>
          <div className="space-y-1 text-xs">
            {["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "USD/INR"].map((pair) => (
              <Link
                key={pair}
                href={`/chart?pair=${pair.replace("/", "_")}`}
                className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-tradly-hover text-tradly-muted hover:text-white transition-colors"
              >
                <span className="font-semibold">{pair}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  LIVE
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-3 rounded-xl bg-tradly-bg border border-tradly-border text-xs text-tradly-muted space-y-1">
        <div className="flex items-center justify-between text-white font-semibold">
          <span>OANDA v20 Stream</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        </div>
        <p className="text-[11px] leading-tight">
          Real-time tick engine active with pip precision.
        </p>
      </div>
    </aside>
  );
}
