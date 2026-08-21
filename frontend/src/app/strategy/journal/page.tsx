"use client";

import React, { useCallback, useEffect, useState } from "react";
import { BookOpen, Lock, Trash2 } from "lucide-react";
import { strategyApi } from "../../../services/strategyApi";
import {
  JournalEntry,
  JournalStats,
  JournalWeek,
  WeeklyPace,
} from "../../../types/strategy";
import { Card, TrendBadge } from "../../../components/strategy/panels";

export default function JournalPage() {
  const [weeks, setWeeks] = useState<JournalWeek[]>([]);
  const [stats, setStats] = useState<JournalStats | null>(null);
  const [pace, setPace] = useState<WeeklyPace | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [w, s, p] = await Promise.all([
        strategyApi.journalWeeks(),
        strategyApi.journalStats(),
        strategyApi.pace(),
      ]);
      setWeeks(w);
      setStats(s);
      setPace(p);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function close(entry: JournalEntry) {
    const raw = window.prompt(
      `Exit price for ${entry.symbol.replace("_", "/")}?`,
      String(entry.take_profit)
    );
    if (raw === null) return;
    const exit = Number(raw);
    if (!Number.isFinite(exit)) {
      setError("That exit price is not a number.");
      return;
    }
    try {
      await strategyApi.closeTrade(entry.id, exit);
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function editStop(entry: JournalEntry) {
    const raw = window.prompt(
      `New stop loss for ${entry.symbol.replace("_", "/")}?`,
      String(entry.stop_loss)
    );
    if (raw === null) return;
    const stop = Number(raw);
    if (!Number.isFinite(stop)) return;

    // First attempt is expected to be refused - Set & Forget is deliberate friction.
    const first = await strategyApi.editLevels(entry.id, { stop_loss: stop });
    if (!first.applied && first.notice) {
      const confirmed = window.confirm(`${first.notice}\n\nEdit anyway?`);
      if (!confirmed) {
        setNotice("Left alone. Set & forget.");
        return;
      }
      await strategyApi.editLevels(entry.id, {
        stop_loss: stop,
        acknowledge_set_and_forget: true,
      });
    }
    await load();
  }

  async function remove(entry: JournalEntry) {
    if (!window.confirm("Delete this journal entry?")) return;
    await strategyApi.deleteTrade(entry.id);
    await load();
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-bold text-white">Trade journal</h1>
        <p className="text-xs text-tradly-muted mt-1">
          Every trade with the decision trail that produced it — sync state, AOI,
          patterns, confluence score, levels and outcome.
        </p>
      </header>

      {error && (
        <div className="rounded-xl border border-red-500/25 bg-red-500/[0.07] p-4 text-xs text-red-300">
          {error}
        </div>
      )}
      {notice && (
        <div className="rounded-xl border border-cyan-500/25 bg-cyan-500/[0.07] p-4 text-xs text-cyan-300">
          {notice}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {pace && (
          <Card title="1 trade a week" subtitle="The pace rule from the notes." icon={Lock}>
            <div className="flex items-center gap-4">
              <div className="text-4xl font-bold font-mono text-white">
                {pace.trades_this_week}
                <span className="text-tradly-muted text-xl">/{pace.limit}</span>
              </div>
              <p
                className={`text-xs leading-relaxed ${
                  pace.at_limit ? "text-amber-400" : "text-tradly-muted"
                }`}
              >
                {pace.message}
              </p>
            </div>
          </Card>
        )}

        {stats && (
          <Card title="Performance" subtitle="Across closed trades." icon={BookOpen}>
            <div className="grid grid-cols-3 gap-3 font-mono text-xs">
              <Stat label="Closed" value={String(stats.closed_trades)} />
              <Stat
                label="Win rate"
                value={`${stats.win_rate}%`}
                tone={stats.win_rate >= 50 ? "text-emerald-400" : "text-red-400"}
              />
              <Stat
                label="Avg RR"
                value={`1:${stats.average_rr}`}
                tone={stats.average_rr >= 2 ? "text-emerald-400" : "text-tradly-text"}
              />
              <Stat label="Wins" value={String(stats.wins)} tone="text-emerald-400" />
              <Stat label="Losses" value={String(stats.losses)} tone="text-red-400" />
              <Stat label="Avg score" value={String(stats.average_confluence)} />
            </div>
          </Card>
        )}
      </div>

      {weeks.length === 0 ? (
        <Card title="No trades logged yet" icon={BookOpen}>
          <p className="text-sm text-tradly-muted">
            Run the toolkit, find a setup that passes the core 4, and log the plan —
            it will appear here with its whole decision trail.
          </p>
        </Card>
      ) : (
        weeks.map((week) => (
          <section key={week.week} className="space-y-3">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-bold text-white font-mono">{week.week}</h2>
              <span
                className={`text-[10px] px-2 py-0.5 rounded border font-bold ${
                  week.over_limit
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/25"
                    : "bg-tradly-hover text-tradly-muted border-tradly-border"
                }`}
              >
                {week.trade_count}/{week.limit} trades
                {week.over_limit && " — over the weekly cap"}
              </span>
            </div>

            <div className="space-y-3">
              {week.trades.map((trade) => (
                <TradeRow
                  key={trade.id}
                  trade={trade}
                  onClose={() => close(trade)}
                  onEditStop={() => editStop(trade)}
                  onDelete={() => remove(trade)}
                />
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  tone = "text-white",
}: {
  label: string;
  value: string;
  tone?: string;
}) {
  return (
    <div>
      <div className="text-[10px] text-tradly-muted uppercase tracking-wider">
        {label}
      </div>
      <div className={`font-bold text-base ${tone}`}>{value}</div>
    </div>
  );
}

function TradeRow({
  trade,
  onClose,
  onEditStop,
  onDelete,
}: {
  trade: JournalEntry;
  onClose: () => void;
  onEditStop: () => void;
  onDelete: () => void;
}) {
  const outcomeTone: Record<string, string> = {
    open: "bg-cyan-500/10 text-cyan-400 border-cyan-500/25",
    win: "bg-emerald-500/10 text-emerald-400 border-emerald-500/25",
    loss: "bg-red-500/10 text-red-400 border-red-500/25",
    breakeven: "bg-slate-500/10 text-tradly-muted border-slate-500/25",
    cancelled: "bg-slate-500/10 text-tradly-muted border-slate-500/25",
  };

  return (
    <article className="rounded-2xl bg-tradly-card border border-tradly-border p-4 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <span className="text-sm font-bold text-white">
            {trade.symbol.replace("_", "/")}
          </span>
          <TrendBadge trend={trade.direction === "buy" ? "bullish" : "bearish"} />
          <span
            className={`text-[10px] px-2 py-0.5 rounded border font-bold uppercase ${
              outcomeTone[trade.outcome]
            }`}
          >
            {trade.outcome}
          </span>
          {trade.low_risk_high_reward && (
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 font-bold">
              Low Risk / High Reward
            </span>
          )}
        </div>
        <span className="text-[10px] font-mono text-tradly-muted">
          {new Date(trade.placed_at).toLocaleString()}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 font-mono text-[11px]">
        <Stat label="Entry" value={String(trade.entry)} />
        <Stat label="Stop" value={String(trade.stop_loss)} tone="text-red-400" />
        <Stat label="Target" value={String(trade.take_profit)} tone="text-emerald-400" />
        <Stat label="Planned RR" value={`1:${trade.planned_rr}`} />
        <Stat
          label="Realised RR"
          value={trade.realised_rr === null ? "—" : `1:${trade.realised_rr}`}
          tone={
            trade.realised_rr === null
              ? "text-tradly-muted"
              : trade.realised_rr > 0
              ? "text-emerald-400"
              : "text-red-400"
          }
        />
      </div>

      <div className="rounded-lg bg-tradly-bg border border-tradly-border p-3 space-y-1.5 text-[11px]">
        <div className="text-[10px] font-bold uppercase tracking-wider text-tradly-muted">
          Decision trail
        </div>
        {trade.sync_state && (
          <p className="text-tradly-text">
            <span className="text-tradly-muted">Sync:</span> {trade.sync_state}
          </p>
        )}
        {trade.aoi_zone && (
          <p className="text-tradly-text">
            <span className="text-tradly-muted">AOI:</span> {trade.aoi_timeframe}{" "}
            {trade.aoi_zone} ({trade.aoi_touches} touches)
          </p>
        )}
        {trade.patterns.length > 0 && (
          <p className="text-tradly-text">
            <span className="text-tradly-muted">Patterns:</span>{" "}
            {trade.patterns.join(", ")}
          </p>
        )}
        <p className="text-tradly-text">
          <span className="text-tradly-muted">Confluence:</span>{" "}
          {trade.confluence_score}/{trade.confluence_max}
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {trade.outcome === "open" && (
          <>
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 text-[11px] font-bold hover:bg-cyan-500/25 transition-colors"
            >
              Close trade
            </button>
            <button
              onClick={onEditStop}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-tradly-border text-tradly-muted text-[11px] font-semibold hover:text-white hover:bg-tradly-hover transition-colors"
              title="Set & Forget — this is deliberately awkward"
            >
              <Lock className="w-3 h-3" />
              Edit stop
            </button>
          </>
        )}
        <button
          onClick={onDelete}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-tradly-border text-tradly-muted text-[11px] font-semibold hover:text-red-400 hover:bg-tradly-hover transition-colors ml-auto"
        >
          <Trash2 className="w-3 h-3" />
          Delete
        </button>
      </div>
    </article>
  );
}
