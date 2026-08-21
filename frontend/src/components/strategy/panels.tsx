"use client";

import React from "react";
import {
  AlertTriangle,
  Check,
  Clock,
  Crosshair,
  Info,
  Layers,
  Minus,
  ShieldAlert,
  Target,
  TrendingDown,
  TrendingUp,
  X,
} from "lucide-react";
import {
  Analysis,
  AOIScan,
  AOIZone,
  CHECKLIST_LABELS,
  Confluence,
  CORE_LABELS,
  HeadShoulders,
  PatternMatch,
  SessionClock,
  Structure,
  TopDown,
  TradePlan,
  Trend,
  Trigger,
} from "../../types/strategy";

/* ------------------------------------------------------------------ */
/* Shared building blocks                                              */
/* ------------------------------------------------------------------ */

export function Card({
  title,
  subtitle,
  icon: Icon,
  children,
  accent,
}: {
  title: string;
  subtitle?: string;
  icon?: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  accent?: string;
}) {
  return (
    <section className="rounded-2xl bg-tradly-card border border-tradly-border p-5 space-y-4">
      <header className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          {Icon && <Icon className="w-4 h-4 mt-0.5 text-cyan-400 shrink-0" />}
          <div>
            <h2 className="text-sm font-bold text-white">{title}</h2>
            {subtitle && (
              <p className="text-[11px] text-tradly-muted mt-0.5">{subtitle}</p>
            )}
          </div>
        </div>
        {accent && (
          <span className="text-[10px] font-mono px-2 py-1 rounded bg-tradly-hover text-tradly-muted shrink-0">
            {accent}
          </span>
        )}
      </header>
      {children}
    </section>
  );
}

export function TrendBadge({ trend, size = "sm" }: { trend: Trend; size?: "sm" | "lg" }) {
  const map = {
    bullish: {
      Icon: TrendingUp,
      cls: "bg-emerald-500/10 text-emerald-400 border-emerald-500/25",
    },
    bearish: {
      Icon: TrendingDown,
      cls: "bg-red-500/10 text-red-400 border-red-500/25",
    },
    undetermined: {
      Icon: Minus,
      cls: "bg-slate-500/10 text-tradly-muted border-slate-500/25",
    },
  } as const;

  const { Icon, cls } = map[trend];
  const pad = size === "lg" ? "px-3 py-1.5 text-xs" : "px-2 py-0.5 text-[10px]";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-bold uppercase tracking-wide ${cls} ${pad}`}
    >
      <Icon className={size === "lg" ? "w-3.5 h-3.5" : "w-3 h-3"} />
      {trend}
    </span>
  );
}

export function Tick({ on }: { on: boolean }) {
  return on ? (
    <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
  ) : (
    <X className="w-3.5 h-3.5 text-tradly-muted shrink-0" />
  );
}

/* ------------------------------------------------------------------ */
/* Module 14 - discipline guardrails                                   */
/* ------------------------------------------------------------------ */

export function GuardrailBanner({ messages }: { messages: string[] }) {
  if (!messages.length) return null;

  return (
    <div className="rounded-2xl border border-amber-500/25 bg-amber-500/[0.07] p-4 space-y-2">
      <div className="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wide">
        <ShieldAlert className="w-4 h-4" />
        Discipline check
      </div>
      {messages.map((message, i) => (
        <p key={i} className="text-sm text-amber-200/90 leading-relaxed">
          {message}
        </p>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Module 4 - top-down trend dashboard                                 */
/* ------------------------------------------------------------------ */

export function TrendDashboard({ topDown }: { topDown: TopDown }) {
  const sync = topDown.sync;

  return (
    <Card
      title="Top-down trend"
      subtitle="Weekly / Daily / 4H set the bias. Lower timeframes only time the entry."
      icon={Layers}
      accent={sync?.rule}
    >
      {topDown.trend_is_your_friend && (
        <div className="rounded-xl border border-emerald-500/25 bg-emerald-500/[0.07] px-3 py-2 text-xs font-semibold text-emerald-400">
          Trend is your friend — Weekly, Daily and 4H all agree.
        </div>
      )}

      <div>
        <div className="text-[10px] font-bold uppercase tracking-wider text-tradly-muted mb-2">
          Trend + AOI timeframes
        </div>
        <div className="grid grid-cols-3 gap-2">
          {Object.entries(topDown.trend_layer).map(([tf, s]) => (
            <StructureTile key={tf} timeframe={tf} structure={s} />
          ))}
        </div>
      </div>

      {Object.keys(topDown.entry_layer).length > 0 && (
        <div>
          <div className="text-[10px] font-bold uppercase tracking-wider text-tradly-muted mb-2">
            Entry-signal timeframes
          </div>
          <div className="grid grid-cols-4 gap-2">
            {Object.entries(topDown.entry_layer).map(([tf, s]) => (
              <div
                key={tf}
                className="rounded-lg bg-tradly-bg border border-tradly-border p-2 text-center"
              >
                <div className="text-[11px] font-bold text-white">{tf}</div>
                <div className="mt-1 flex justify-center">
                  <TrendBadge trend={s.trend} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {sync && (
        <div
          className={`rounded-xl border p-3 space-y-2 ${
            sync.in_sync
              ? "border-emerald-500/25 bg-emerald-500/[0.06]"
              : "border-red-500/25 bg-red-500/[0.06]"
          }`}
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-[11px] font-bold uppercase tracking-wide text-white">
              Sync gate
            </span>
            <span
              className={`text-[10px] font-bold ${
                sync.in_sync ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {sync.in_sync ? "IN SYNC" : "NOT IN SYNC"}
            </span>
          </div>
          <p className="text-xs text-tradly-text leading-relaxed">{sync.explanation}</p>
          {sync.rule_is_unconfirmed && (
            <details className="text-[11px] text-amber-400/90">
              <summary className="cursor-pointer font-semibold">
                This rule is unconfirmed — read why
              </summary>
              <p className="mt-1.5 text-tradly-muted leading-relaxed">{sync.rule_note}</p>
            </details>
          )}
        </div>
      )}
    </Card>
  );
}

function StructureTile({
  timeframe,
  structure,
}: {
  timeframe: string;
  structure: Structure;
}) {
  return (
    <div className="rounded-xl bg-tradly-bg border border-tradly-border p-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-white">{timeframe}</span>
        <TrendBadge trend={structure.trend} />
      </div>
      <dl className="space-y-1 text-[10px] font-mono text-tradly-muted">
        {structure.last_hh && (
          <Row label="HH" value={structure.last_hh.price} tone="emerald" />
        )}
        {structure.last_valid_hl && (
          <Row label="HL" value={structure.last_valid_hl.price} tone="emerald" />
        )}
        {structure.last_valid_lh && (
          <Row label="LH" value={structure.last_valid_lh.price} tone="red" />
        )}
        {structure.last_ll && (
          <Row label="LL" value={structure.last_ll.price} tone="red" />
        )}
        {structure.snake_trace_price !== null && (
          <Row label="Snake" value={structure.snake_trace_price} tone="cyan" />
        )}
      </dl>
      {structure.choch_events.length > 0 && (
        <div className="text-[10px] text-amber-400 font-mono">
          {structure.choch_events.length} CHoCH
        </div>
      )}
    </div>
  );
}

function Row({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "emerald" | "red" | "cyan";
}) {
  const cls = {
    emerald: "text-emerald-400",
    red: "text-red-400",
    cyan: "text-cyan-400",
  }[tone];

  return (
    <div className="flex items-center justify-between gap-2">
      <dt>{label}</dt>
      <dd className={`font-bold ${cls}`}>{value.toFixed(5)}</dd>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Module 5 - AOI                                                      */
/* ------------------------------------------------------------------ */

export function AOIPanel({
  scans,
  zones,
}: {
  scans: Record<string, AOIScan>;
  zones: AOIZone[];
}) {
  return (
    <Card
      title="Area of Interest"
      subtitle="Weekly & Daily only · 3+ touches · 5–60 pips · inside the structural range"
      icon={Target}
      accent={`${zones.length} valid`}
    >
      {zones.length === 0 ? (
        <p className="text-sm text-amber-300/90 leading-relaxed">
          No valid AOI on this pair right now — wait or switch pairs.
        </p>
      ) : (
        <div className="space-y-2">
          {zones.map((zone, i) => (
            <ZoneRow key={i} zone={zone} />
          ))}
        </div>
      )}

      {Object.values(scans).some((s) => s.rejected.length > 0) && (
        <details className="text-[11px]">
          <summary className="cursor-pointer font-semibold text-tradly-muted hover:text-white">
            Rejected zones and why
          </summary>
          <div className="mt-2 space-y-2">
            {Object.values(scans).flatMap((scan) =>
              scan.rejected.map((zone, i) => (
                <div
                  key={`${scan.timeframe}-${i}`}
                  className="rounded-lg bg-tradly-bg border border-tradly-border p-2.5"
                >
                  <div className="font-mono text-[10px] text-tradly-muted">
                    {zone.timeframe} · {zone.lower.toFixed(5)}–{zone.upper.toFixed(5)} ·{" "}
                    {zone.width_pips}p · {zone.touches} touches
                  </div>
                  {zone.rejection_reasons.map((reason, j) => (
                    <p key={j} className="mt-1 text-[11px] text-red-400/90">
                      {reason}
                    </p>
                  ))}
                </div>
              ))
            )}
          </div>
        </details>
      )}
    </Card>
  );
}

function ZoneRow({ zone }: { zone: AOIZone }) {
  const isBuy = zone.zone_type === "support";
  return (
    <div
      className={`rounded-xl border p-3 space-y-2 ${
        isBuy
          ? "border-emerald-500/25 bg-emerald-500/[0.06]"
          : "border-red-500/25 bg-red-500/[0.06]"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className={`text-[10px] font-bold uppercase tracking-wide ${
            isBuy ? "text-emerald-400" : "text-red-400"
          }`}
        >
          {zone.timeframe} · {zone.golden_rule_tag}
        </span>
        <span className="text-[10px] font-mono text-tradly-muted">
          {zone.width_pips} pips
        </span>
      </div>

      <div className="font-mono text-sm font-bold text-white">
        {zone.lower.toFixed(5)} — {zone.upper.toFixed(5)}
      </div>

      <div className="flex items-center gap-2">
        <span className="text-[10px] text-tradly-muted font-mono">
          {zone.touches} touches
        </span>
        <div className="flex-1 h-1.5 rounded-full bg-tradly-border overflow-hidden">
          <div
            className={isBuy ? "h-full bg-emerald-400" : "h-full bg-red-400"}
            style={{ width: `${Math.round(zone.confidence * 100)}%` }}
          />
        </div>
        <span className="text-[10px] font-bold font-mono text-white">
          {Math.round(zone.confidence * 100)}%
        </span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Module 6 - break & retest trigger                                   */
/* ------------------------------------------------------------------ */

export function TriggerPanel({ trigger }: { trigger: Trigger | null }) {
  const tone = trigger?.is_armed
    ? "border-cyan-500/25 bg-cyan-500/[0.06]"
    : "border-tradly-border bg-tradly-bg";

  return (
    <Card
      title="Break & retest"
      subtitle="The only valid entry trigger. Never mid-zone, never on the break candle."
      icon={Crosshair}
      accent={trigger?.status ?? "none"}
    >
      <div className={`rounded-xl border p-3 space-y-2 ${tone}`}>
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-white">
            {trigger?.level_label || "No level being tracked"}
          </span>
          <span
            className={`text-[10px] font-bold uppercase ${
              trigger?.is_armed ? "text-cyan-400" : "text-tradly-muted"
            }`}
          >
            {trigger?.status ?? "none"}
          </span>
        </div>

        {trigger?.level != null && (
          <div className="font-mono text-sm text-white">
            Level {trigger.level.toFixed(5)}
            {trigger.direction && (
              <span className="ml-2 text-tradly-muted">→ {trigger.direction}</span>
            )}
          </div>
        )}

        {trigger?.notes.map((note, i) => (
          <p key={i} className="text-[11px] text-tradly-muted leading-relaxed">
            {note}
          </p>
        ))}
      </div>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* Modules 7 & 8 - patterns                                            */
/* ------------------------------------------------------------------ */

export function PatternPanel({
  patterns,
  headShoulders,
}: {
  patterns: PatternMatch[];
  headShoulders: Record<string, HeadShoulders[]>;
}) {
  const allHS = Object.values(headShoulders).flat();

  return (
    <Card
      title="Patterns at the AOI"
      subtitle="A formation only counts when it prints at a validated AOI. Higher timeframe = stronger."
      icon={Info}
      accent={`${patterns.length} actionable`}
    >
      {patterns.length === 0 ? (
        <p className="text-sm text-tradly-muted">
          Nothing actionable — no formation is sitting at a validated AOI.
        </p>
      ) : (
        <div className="space-y-2">
          {patterns
            .slice()
            .sort((a, b) => b.weighted_strength - a.weighted_strength)
            .slice(0, 6)
            .map((pattern, i) => (
              <div
                key={i}
                className="rounded-lg bg-tradly-bg border border-tradly-border p-2.5 space-y-1"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-bold text-white">{pattern.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-tradly-hover text-tradly-muted">
                      {pattern.timeframe}
                    </span>
                    <TrendBadge trend={pattern.bias} />
                  </div>
                </div>
                <p className="text-[11px] text-tradly-muted leading-relaxed">
                  {pattern.detail}
                </p>
                <div className="text-[10px] font-mono text-cyan-400">
                  weighted strength {pattern.weighted_strength.toFixed(2)}
                </div>
              </div>
            ))}
        </div>
      )}

      {allHS.length > 0 && (
        <div className="space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-wider text-tradly-muted">
            Head &amp; Shoulders
          </div>
          {allHS.map((hs, i) => (
            <div
              key={i}
              className={`rounded-lg border p-2.5 space-y-1 ${
                hs.early_entry_risk
                  ? "border-amber-500/25 bg-amber-500/[0.06]"
                  : "border-tradly-border bg-tradly-bg"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-bold text-white">
                  {hs.kind === "head_and_shoulders"
                    ? "Head & Shoulders"
                    : "Inverse Head & Shoulders"}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-tradly-hover text-tradly-muted">
                  {hs.timeframe}
                </span>
              </div>

              <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] font-mono">
                <span className="flex items-center gap-1">
                  <Tick on={hs.neckline_broken} /> neckline broken
                </span>
                <span className="flex items-center gap-1">
                  <Tick on={hs.neckline_retested} /> retested
                </span>
                {hs.target_price !== null && (
                  <span className="text-cyan-400">
                    target {hs.target_price.toFixed(5)}
                  </span>
                )}
              </div>

              {hs.early_entry_risk && (
                <p className="text-[11px] text-amber-400 leading-relaxed flex gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-px" />
                  High risk / early entry — the neckline has not broken. Wait for the
                  break, then the retest.
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* Module 10 - confluence                                              */
/* ------------------------------------------------------------------ */

export function ConfluencePanel({ confluence }: { confluence: Confluence | null }) {
  if (!confluence) return null;

  const pct = confluence.max_score
    ? (confluence.score / confluence.max_score) * 100
    : 0;

  return (
    <Card
      title="Confluence score"
      subtitle="All four core pillars are mandatory before the expanded checklist is scored at all."
      icon={Layers}
      accent={confluence.core_complete ? `${confluence.score}/${confluence.max_score}` : "blocked"}
    >
      {/* Core 4 */}
      <div className="space-y-1.5">
        <div className="text-[10px] font-bold uppercase tracking-wider text-tradly-muted">
          Core 4 pillars — all mandatory
        </div>
        {Object.entries(confluence.core_pillars).map(([key, ok]) => (
          <div key={key} className="flex items-center gap-2 text-xs">
            <Tick on={ok} />
            <span className={ok ? "text-white" : "text-tradly-muted"}>
              {CORE_LABELS[key] ?? key}
            </span>
          </div>
        ))}
      </div>

      {!confluence.core_complete ? (
        <div className="rounded-xl border border-red-500/25 bg-red-500/[0.06] p-3">
          <p className="text-xs text-red-300 leading-relaxed">
            No score is computed and no trade is suggested while a core pillar is
            missing: {confluence.missing_core.map((k) => CORE_LABELS[k] ?? k).join(", ")}.
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-tradly-muted">
                Expanded checklist
              </span>
              <span className="font-mono text-sm font-bold text-white">
                {confluence.score}/{confluence.max_score}
              </span>
            </div>
            <div className="h-2 rounded-full bg-tradly-border overflow-hidden">
              <div
                className={
                  confluence.low_risk_high_reward
                    ? "h-full bg-emerald-400"
                    : "h-full bg-cyan-400"
                }
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5">
            {Object.entries(confluence.expanded).map(([key, ok]) => (
              <div key={key} className="flex items-center gap-2 text-[11px]">
                <Tick on={ok} />
                <span className={ok ? "text-white" : "text-tradly-muted"}>
                  {CHECKLIST_LABELS[key] ?? key}
                </span>
              </div>
            ))}
          </div>

          {confluence.low_risk_high_reward && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-center">
              <span className="text-xs font-bold uppercase tracking-wide text-emerald-400">
                Low Risk / High Reward
              </span>
            </div>
          )}
        </>
      )}
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* Module 11 - trade plan                                              */
/* ------------------------------------------------------------------ */

export function TradePlanPanel({
  plan,
  onLog,
  logging,
}: {
  plan: TradePlan | null;
  onLog?: () => void;
  logging?: boolean;
}) {
  if (!plan) {
    return (
      <Card
        title="Trade plan"
        subtitle="Produced only when the core 4 pass and the plan clears 1:2 RR."
        icon={Target}
      >
        <p className="text-sm text-tradly-muted">
          No plan — the setup did not qualify. Wait for the work; don&apos;t make
          something work.
        </p>
      </Card>
    );
  }

  const isBuy = plan.direction === "buy";

  return (
    <Card
      title="Trade plan"
      subtitle="Sized from the risk table and the real stop distance."
      icon={Target}
      accent={`1:${plan.reward_risk}`}
    >
      <div
        className={`rounded-xl border p-4 space-y-3 ${
          isBuy
            ? "border-emerald-500/25 bg-emerald-500/[0.06]"
            : "border-red-500/25 bg-red-500/[0.06]"
        }`}
      >
        <div className="flex items-center justify-between">
          <span
            className={`text-lg font-bold uppercase ${
              isBuy ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {plan.direction} {plan.symbol.replace("_", "/")}
          </span>
          <span className="font-mono text-sm text-white">
            {plan.position_size_lots} lots
          </span>
        </div>

        <div className="grid grid-cols-3 gap-3 font-mono text-xs">
          <Metric label="Entry" value={plan.entry} tone="text-white" />
          <Metric
            label={`Stop (${plan.stop_distance_pips}p)`}
            value={plan.stop_loss}
            tone="text-red-400"
          />
          <Metric
            label={`Target (${plan.target_distance_pips}p)`}
            value={plan.take_profit}
            tone="text-emerald-400"
          />
        </div>

        <div className="grid grid-cols-3 gap-3 pt-2 border-t border-tradly-border font-mono text-[11px]">
          <div>
            <div className="text-tradly-muted">Reward:risk</div>
            <div
              className={`font-bold ${
                plan.meets_target_rr
                  ? "text-emerald-400"
                  : plan.meets_min_rr
                  ? "text-cyan-400"
                  : "text-red-400"
              }`}
            >
              1:{plan.reward_risk}
            </div>
          </div>
          <div>
            <div className="text-tradly-muted">Risk</div>
            <div className="font-bold text-white">
              ${plan.risk_amount.toLocaleString()} ({plan.risk_pct}%)
            </div>
          </div>
          <div>
            <div className="text-tradly-muted">Pip value / lot</div>
            <div className="font-bold text-white">${plan.pip_value_per_lot}</div>
          </div>
        </div>
      </div>

      {plan.warnings.length > 0 && (
        <div className="space-y-1.5">
          {plan.warnings.map((warning, i) => (
            <p
              key={i}
              className="flex gap-2 text-[11px] text-amber-400/90 leading-relaxed"
            >
              <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-px" />
              {warning}
            </p>
          ))}
        </div>
      )}

      {onLog && (
        <button
          onClick={onLog}
          disabled={logging}
          className="w-full py-2.5 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 text-xs font-bold hover:bg-cyan-500/25 transition-colors disabled:opacity-50"
        >
          {logging ? "Logging…" : "Log this trade to the journal"}
        </button>
      )}
    </Card>
  );
}

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div>
      <div className="text-tradly-muted text-[10px]">{label}</div>
      <div className={`font-bold ${tone}`}>{value}</div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Module 2 - session clock                                            */
/* ------------------------------------------------------------------ */

export function SessionPanel({ clock }: { clock: SessionClock | null }) {
  if (!clock) return null;

  const localTime = new Date(clock.now_utc).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Card
      title="Trading sessions"
      subtitle={`Primary window ${clock.primary_window_ist} — pre-London through London close`}
      icon={Clock}
      accent={localTime}
    >
      <div
        className={`rounded-xl border px-3 py-2.5 ${
          clock.in_primary_window
            ? "border-emerald-500/25 bg-emerald-500/[0.07]"
            : "border-tradly-border bg-tradly-bg"
        }`}
      >
        <div
          className={`text-xs font-bold ${
            clock.in_primary_window ? "text-emerald-400" : "text-tradly-muted"
          }`}
        >
          {clock.in_primary_window
            ? "Inside the primary trading window"
            : "Outside the primary trading window"}
        </div>
        <p className="text-[11px] text-tradly-muted mt-1">{clock.message}</p>
      </div>

      <div className="space-y-1.5">
        {clock.sessions.map((session) => (
          <div
            key={session.name}
            className="flex items-center justify-between gap-2 rounded-lg bg-tradly-bg border border-tradly-border px-3 py-2"
          >
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  session.is_active ? "bg-emerald-400" : "bg-tradly-border"
                }`}
              />
              <span className="text-xs font-semibold text-white">{session.name}</span>
            </div>
            <div className="text-right font-mono text-[10px] text-tradly-muted">
              <div>
                {session.open_ist}–{session.close_ist} IST
              </div>
              <div className="opacity-60">
                {session.open_utc}–{session.close_utc} UTC
              </div>
            </div>
          </div>
        ))}
      </div>

      {clock.overlap && (
        <div className="text-[11px] font-semibold text-cyan-400">{clock.overlap}</div>
      )}
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* Narrative                                                           */
/* ------------------------------------------------------------------ */

export function NarrativePanel({ analysis }: { analysis: Analysis }) {
  return (
    <Card
      title="What the engine did"
      subtitle="Each stage of the top-down pass, in order."
      icon={Info}
    >
      <ol className="space-y-2">
        {analysis.narrative.map((line, i) => (
          <li key={i} className="flex gap-3 text-xs leading-relaxed">
            <span className="font-mono text-cyan-400 shrink-0">{i + 1}.</span>
            <span className="text-tradly-text">{line}</span>
          </li>
        ))}
      </ol>
    </Card>
  );
}
