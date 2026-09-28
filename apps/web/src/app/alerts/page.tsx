"use client";

import React, { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Bell, BellOff, BellRing, Plus, RefreshCw, Trash2 } from "lucide-react";
import { api } from "../../services/api";
import { CurrencyPair } from "../../types/market";
import { AlertNotification, AlertType, PriceAlert } from "../../types/alerts";

const ALERT_TYPES: { id: AlertType; label: string; glyph: string }[] = [
  { id: "price_above", label: "Price crosses above", glyph: "▲" },
  { id: "price_below", label: "Price crosses below", glyph: "▼" },
];

const MAX_ALERTS = 50;

function decimalsFor(symbol: string): number {
  return symbol.endsWith("JPY") ? 3 : 5;
}

function timeAgo(iso: string): string {
  const s = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return new Date(iso).toLocaleDateString();
}

export default function AlertsPage() {
  const [pairs, setPairs] = useState<CurrencyPair[]>([]);
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [notifications, setNotifications] = useState<AlertNotification[]>([]);
  const [symbol, setSymbol] = useState("EUR_USD");
  const [alertType, setAlertType] = useState<AlertType>("price_above");
  const [threshold, setThreshold] = useState<string>("");
  const [note, setNote] = useState("");
  const [email, setEmail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const current = pairs.find((p) => p.symbol === symbol);
  const mid = current ? (current.bid + current.ask) / 2 : null;
  const decimals = decimalsFor(symbol);

  const refresh = useCallback(async () => {
    try {
      const [p, a, n] = await Promise.all([api.getPairs(), api.getAlerts(), api.getNotifications()]);
      setPairs(p);
      setAlerts(a);
      setNotifications(n);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load alerts");
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 3000);
    return () => clearInterval(id);
  }, [refresh]);

  const presetFromMid = (pips: number) => {
    if (!current || mid === null) return;
    setThreshold((mid + pips * current.pip_size).toFixed(decimals));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const value = parseFloat(threshold);
    if (!Number.isFinite(value) || value <= 0) {
      setError("Enter a positive threshold price.");
      return;
    }
    setIsSaving(true);
    try {
      await api.createAlert({
        symbol,
        alert_type: alertType,
        threshold_value: value,
        timeframe: "H1",
        note: note.trim() || undefined,
        email_notification: email,
      });
      setThreshold("");
      setNote("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create alert");
    } finally {
      setIsSaving(false);
    }
  };

  const toggle = async (id: string) => {
    try {
      await api.toggleAlert(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update alert");
    }
  };

  const remove = async (id: string) => {
    try {
      await api.deleteAlert(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete alert");
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-2xl font-extrabold text-white flex items-center gap-2.5">
          <BellRing className="w-6 h-6 text-cyan-400" /> Alert Management
        </h1>
        <p className="text-xs text-tradly-muted mt-1 font-mono">
          Server-side evaluation every tick · fires once on crossing · in-app notifications · {alerts.length}/{MAX_ALERTS} used
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <form onSubmit={handleCreate} className="xl:col-span-4 p-5 rounded-3xl bg-tradly-card border border-tradly-border space-y-4 h-fit">
          <h2 className="text-xs font-black text-white uppercase tracking-wider font-mono flex items-center gap-2">
            <Plus className="w-4 h-4 text-cyan-400" /> New alert
          </h2>
          <label className="block">
            <span className="text-[10px] text-tradly-muted font-bold uppercase block mb-1 font-mono">Pair</span>
            <select
              value={symbol}
              onChange={(e) => { setSymbol(e.target.value); setThreshold(""); }}
              className="w-full p-2.5 rounded-xl bg-[#080C14] border border-tradly-border text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
            >
              {(pairs.length ? pairs.map((p) => p.symbol) : ["EUR_USD"]).map((s) => (
                <option key={s} value={s}>{s.replace("_", "/")}</option>
              ))}
            </select>
          </label>
          {mid !== null && (
            <div className="text-[11px] font-mono text-tradly-secondary">
              Live mid <span className="text-white font-bold tabular-nums">{mid.toFixed(decimals)}</span>
            </div>
          )}
          <label className="block">
            <span className="text-[10px] text-tradly-muted font-bold uppercase block mb-1 font-mono">Condition</span>
            <div className="grid grid-cols-2 gap-2">
              {ALERT_TYPES.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setAlertType(t.id)}
                  className={`p-2.5 rounded-xl border text-[11px] font-bold font-mono ${
                    alertType === t.id
                      ? t.id === "price_above"
                        ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-400"
                        : "bg-red-500/15 border-red-500/40 text-red-400"
                      : "bg-[#080C14] border-tradly-border text-tradly-muted"
                  }`}
                >
                  {t.glyph} {t.label}
                </button>
              ))}
            </div>
          </label>
          <label className="block">
            <span className="text-[10px] text-tradly-muted font-bold uppercase block mb-1 font-mono">Threshold price</span>
            <input
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              inputMode="decimal"
              placeholder={mid !== null ? mid.toFixed(decimals) : "1.08500"}
              className="w-full p-2.5 rounded-xl bg-[#080C14] border border-tradly-border text-white text-xs font-mono tabular-nums focus:outline-none focus:border-cyan-400"
            />
            <div className="flex gap-1.5 mt-2">
              {[-10, -3, 3, 10].map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => presetFromMid(p)}
                  className="flex-1 py-1 rounded-lg bg-[#080C14] border border-tradly-border text-[10px] font-mono text-tradly-secondary hover:text-white hover:border-cyan-500/40"
                >
                  {p > 0 ? "+" : ""}{p} pips
                </button>
              ))}
            </div>
          </label>
          <label className="block">
            <span className="text-[10px] text-tradly-muted font-bold uppercase block mb-1 font-mono">Note (optional)</span>
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={120}
              className="w-full p-2.5 rounded-xl bg-[#080C14] border border-tradly-border text-white text-xs focus:outline-none focus:border-cyan-400"
            />
          </label>
          <label className="flex items-center gap-2 text-xs text-tradly-secondary font-mono cursor-pointer">
            <input type="checkbox" checked={email} onChange={(e) => setEmail(e.target.checked)} className="accent-cyan-400" />
            Also queue an email notification
          </label>
          <button
            type="submit"
            disabled={isSaving || alerts.length >= MAX_ALERTS}
            className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-black text-xs shadow-neon-cyan disabled:opacity-50"
          >
            {isSaving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Bell className="w-4 h-4" />}
            {alerts.length >= MAX_ALERTS ? "Alert cap reached (50)" : "Create alert"}
          </button>
        </form>

        <div className="xl:col-span-5 p-5 rounded-3xl bg-tradly-card border border-tradly-border space-y-3">
          <h2 className="text-sm font-bold text-white">Your alerts</h2>
          {alerts.length === 0 ? (
            <p className="text-xs text-tradly-muted">
              No alerts yet. Use a ±3 pip preset to see one trigger within a few seconds on the live feed.
            </p>
          ) : (
            <div className="space-y-2">
              {alerts.map((a) => {
                const above = a.alert_type === "price_above";
                const state = a.is_triggered ? "Triggered" : a.is_active ? "Watching" : "Paused";
                return (
                  <div key={a.id} className="p-3 rounded-2xl bg-[#080C14] border border-tradly-border flex items-center gap-3">
                    <span className={`text-lg ${above ? "text-emerald-400" : "text-red-400"}`}>{above ? "▲" : "▼"}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-bold text-white font-mono">
                        {a.symbol.replace("_", "/")} {above ? "crosses above" : "crosses below"}{" "}
                        <span className="tabular-nums">{a.threshold_value.toFixed(decimalsFor(a.symbol))}</span>
                      </div>
                      <div className="text-[10px] text-tradly-muted font-mono truncate">
                        {state}
                        {a.last_triggered_at ? ` · ${timeAgo(a.last_triggered_at)}` : ""}
                        {a.note ? ` · ${a.note}` : ""}
                      </div>
                    </div>
                    <span
                      className={`text-[9px] font-black px-2 py-0.5 rounded-full border font-mono ${
                        a.is_triggered
                          ? "bg-cyan-500/15 text-cyan-300 border-cyan-500/40"
                          : a.is_active
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                          : "bg-slate-500/10 text-slate-400 border-slate-500/30"
                      }`}
                    >
                      {state.toUpperCase()}
                    </span>
                    <button type="button" onClick={() => toggle(a.id)} aria-label={a.is_active ? "Pause alert" : "Resume alert"}
                      className="p-1.5 rounded-lg text-tradly-muted hover:text-white hover:bg-tradly-hover">
                      {a.is_active ? <BellOff className="w-4 h-4" /> : <Bell className="w-4 h-4" />}
                    </button>
                    <button type="button" onClick={() => remove(a.id)} aria-label="Delete alert"
                      className="p-1.5 rounded-lg text-tradly-muted hover:text-red-400 hover:bg-red-500/10">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="xl:col-span-3 p-5 rounded-3xl bg-tradly-card border border-tradly-border space-y-3">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <BellRing className="w-4 h-4 text-cyan-400" /> Notifications
          </h2>
          {notifications.length === 0 ? (
            <p className="text-xs text-tradly-muted">Triggered alerts appear here.</p>
          ) : (
            <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
              {notifications.map((n) => (
                <div key={n.id} className="p-3 rounded-xl bg-[#080C14] border border-cyan-500/20">
                  <div className="text-[11px] font-bold text-cyan-300">{n.title}</div>
                  <div className="text-[11px] text-tradly-secondary mt-0.5">{n.message}</div>
                  <div className="text-[10px] text-tradly-muted mt-1 font-mono">{timeAgo(n.created_at)} · {n.channel}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
