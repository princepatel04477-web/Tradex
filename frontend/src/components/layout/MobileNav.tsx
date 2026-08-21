"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CandlestickChart,
  Bot,
  DollarSign,
  Sparkles,
} from "lucide-react";

const MOBILE_TABS = [
  { name: "Command", href: "/", icon: LayoutDashboard },
  { name: "Analysis", href: "/trading-analysis", icon: Sparkles },
  { name: "Chart", href: "/chart", icon: CandlestickChart },
  { name: "Execute", href: "/paper-trading", icon: DollarSign },
  { name: "AI Macro", href: "/ai-assistant", icon: Bot },
];

export default function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-[#080C14]/95 backdrop-blur-2xl border-t border-tradly-border z-50 px-2 flex items-center justify-around select-none">
      {MOBILE_TABS.map((tab) => {
        const Icon = tab.icon;
        const isActive = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`flex flex-col items-center justify-center w-16 py-1 rounded-xl transition-all ${
              isActive
                ? "text-cyan-400 font-bold"
                : "text-tradly-muted hover:text-white"
            }`}
          >
            <div className="relative">
              <Icon className={`w-5 h-5 ${isActive ? "text-cyan-400" : "text-tradly-muted"}`} />
              {isActive && (
                <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-cyan-400 shadow-neon-cyan" />
              )}
            </div>
            <span className="text-[10px] tracking-tight mt-1 font-mono">{tab.name}</span>
          </Link>
        );
      })}
    </nav>
  );
}
