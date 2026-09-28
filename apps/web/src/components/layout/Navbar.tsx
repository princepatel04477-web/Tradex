"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Clock,
  ShieldCheck,
  Zap,
  LogOut,
  TrendingUp,
  Menu,
  X,
  Target,
  Calculator,
  BookOpen,
  Compass,
  Radio,
  FlaskConical,
  BellRing,
  BarChart3,
} from "lucide-react";
import gsap from "gsap";
import { api } from "../../services/api";
import { MarketSessionOverview, AccountMetrics } from "../../types/market";
import { useAuth } from "../../context/AuthContext";

const STRATEGY_ITEMS = [
  { name: "Confluence Engine", href: "/strategy", icon: Target },
  { name: "Risk & Position Sizer", href: "/strategy/risk", icon: Calculator },
  { name: "Trade Journal", href: "/strategy/journal", icon: BookOpen },
  { name: "Technical Playbook", href: "/strategy/reference", icon: Compass },
  { name: "Backtest Lab", href: "/backtest", icon: FlaskConical },
  { name: "Alerts", href: "/alerts", icon: BellRing },
  { name: "Performance & Journal", href: "/analytics", icon: BarChart3 },
];

export default function Navbar() {
  const [sessionInfo, setSessionInfo] = useState<MarketSessionOverview | null>(null);
  const [metrics, setMetrics] = useState<AccountMetrics | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);
  const { user, logout } = useAuth();
  const navRef = useRef<HTMLElement>(null);
  const pathname = usePathname();

  useEffect(() => {
    // Close mobile menu on route change
    setIsMobileMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
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
          api.getAccountMetrics(),
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
    <>
      <header
        ref={navRef}
        className="h-16 bg-[#080C14]/85 backdrop-blur-xl border-b border-tradly-border px-4 sm:px-6 flex items-center justify-between sticky top-0 z-40 selection:bg-cyan-500 selection:text-black"
      >
        {/* Brand Logo & Mobile Menu Toggle */}
        <div className="flex items-center space-x-3">
          {/* Mobile Menu Button (< lg) */}
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="lg:hidden p-2 rounded-xl bg-[#0C101A] border border-tradly-border text-tradly-secondary hover:text-white"
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? <X className="w-4 h-4 text-cyan-400" /> : <Menu className="w-4 h-4" />}
          </button>

          <Link href="/" className="flex items-center space-x-2.5 group">
            <div className="w-8 sm:w-9 h-8 sm:h-9 rounded-xl bg-gradient-to-tr from-cyan-400 via-blue-500 to-indigo-600 flex items-center justify-center shadow-neon-cyan transition-transform group-hover:scale-105">
              <Zap className="w-4 sm:w-5 h-4 sm:h-5 text-black stroke-[2.6]" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-black text-lg sm:text-xl tracking-tight text-white font-mono">TRADLY</span>
                <span className="text-[9px] sm:text-[10px] font-black tracking-widest px-1.5 py-0.5 rounded bg-cyan-400/10 text-cyan-400 border border-cyan-400/30">
                  PRO
                </span>
              </div>
            </div>
          </Link>
        </div>

        {/* FX Market Sessions Clock & Overlap Badge (Desktop Only) */}
        <div className="hidden lg:flex items-center space-x-4">
          {sessionInfo?.active_overlap && (
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold animate-pulse">
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
        <div className="flex items-center space-x-2.5 sm:space-x-4">
          {metrics && (
            <div className="text-right bg-[#0C101A] px-2.5 sm:px-3.5 py-1 sm:py-1.5 rounded-xl border border-tradly-border">
              <div className="text-[8px] sm:text-[9px] text-tradly-muted font-bold tracking-widest uppercase">Equity</div>
              <div className="text-[11px] sm:text-xs font-black text-emerald-400 font-mono tracking-tight flex items-center justify-end space-x-1">
                <TrendingUp className="w-2.5 sm:w-3 h-2.5 sm:h-3 text-emerald-400" />
                <span>${metrics.equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
            </div>
          )}

          {user && (
            <div className="flex items-center space-x-2 bg-[#0C101A] p-1 sm:p-1.5 pl-2 sm:pl-3 rounded-2xl border border-tradly-border text-xs font-mono">
              <div className="flex items-center space-x-1.5 sm:space-x-2">
                <div className="w-6 sm:w-7 h-6 sm:h-7 rounded-xl bg-gradient-to-tr from-cyan-400 to-blue-600 flex items-center justify-center text-black font-black text-[10px] sm:text-[11px] shadow-neon-cyan">
                  {user.name ? user.name.slice(0, 2).toUpperCase() : "PR"}
                </div>
                <span className="text-white font-bold hidden sm:inline text-xs">{user.name || user.email}</span>
              </div>

              <button
                type="button"
                onClick={logout}
                title="Lock Terminal & Sign Out"
                className="p-1.5 sm:p-2 rounded-xl hover:bg-red-500/10 text-tradly-muted hover:text-red-400 transition-all cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Mobile Drawer Menu (< lg) */}
      {isMobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 top-16 bg-black/80 backdrop-blur-2xl z-40 p-5 space-y-6 overflow-y-auto animate-in fade-in slide-in-from-top-4 duration-200">
          {/* Strategy Navigation */}
          <div className="space-y-2">
            <div className="text-[10px] font-black uppercase tracking-widest text-tradly-muted font-mono">
              Strategy Architecture
            </div>
            <div className="grid grid-cols-2 gap-2">
              {STRATEGY_ITEMS.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center space-x-2.5 p-3 rounded-xl border text-xs font-medium transition-all ${
                      isActive
                        ? "bg-cyan-500/15 border-cyan-400 text-cyan-300 font-bold"
                        : "bg-[#0C101A] border-tradly-border text-tradly-secondary hover:text-white"
                    }`}
                  >
                    <Icon className="w-4 h-4 text-cyan-400" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Market Sessions on Mobile */}
          {sessionInfo && (
            <div className="p-4 rounded-2xl bg-[#0C101A] border border-tradly-border space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between text-tradly-muted text-[11px]">
                <span className="flex items-center space-x-1.5">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  <span>UTC Clock: {sessionInfo.current_utc_time}</span>
                </span>
                {sessionInfo.active_overlap && (
                  <span className="text-amber-400 font-bold">{sessionInfo.active_overlap}</span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-2">
                {sessionInfo.sessions.map((s) => (
                  <div
                    key={s.name}
                    className={`p-2.5 rounded-xl border flex items-center justify-between ${
                      s.is_active
                        ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400 font-bold"
                        : "bg-[#080C14] border-tradly-border/70 text-tradly-muted"
                    }`}
                  >
                    <span>{s.name}</span>
                    <span
                      className={`w-2 h-2 rounded-full ${
                        s.is_active ? "bg-emerald-400 animate-pulse" : "bg-tradly-muted"
                      }`}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Sign Out button in drawer */}
          <div className="pt-2">
            <button
              type="button"
              onClick={logout}
              className="w-full py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 font-bold text-xs flex items-center justify-center space-x-2"
            >
              <LogOut className="w-4 h-4" />
              <span>Lock Terminal & Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
