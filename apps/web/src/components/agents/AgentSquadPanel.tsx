"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  BarChart2,
  Bot,
  CheckCircle2,
  ExternalLink,
  Globe2,
  Info,
  Shield,
  Sparkles,
  XCircle,
} from "lucide-react";
import { AgentEvidence, AgentName, AgentReport, AgentRun } from "../../types/agents";

const AGENT_META: Record<AgentName, { icon: React.ComponentType<{ className?: string }>; short: string }> = {
  technical: { icon: BarChart2, short: "Technical" },
  macro: { icon: Globe2, short: "Macro" },
  risk: { icon: Shield, short: "Risk" },
  synthesis: { icon: Sparkles, short: "Synthesis" },
};

function tiltStyle(tilt: string): { cls: string; glyph: string } {
  if (tilt === "bullish") return { cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/40", glyph: "▲" };
  if (tilt === "bearish") return { cls: "bg-red-500/15 text-red-400 border-red-500/40", glyph: "▼" };
  return { cls: "bg-amber-500/15 text-amber-400 border-amber-500/40", glyph: "◆" };
}

function stanceText(stance: number): string {
  if (stance > 0.05) return `▲ +${stance.toFixed(2)}`;
  if (stance < -0.05) return `▼ ${stance.toFixed(2)}`;
  return `◆ ${stance.toFixed(2)}`;
}

function stanceColor(stance: number): string {
  if (stance > 0.05) return "text-emerald-400";
  if (stance < -0.05) return "text-red-400";
  return "text-amber-300";
}

function StatusBadge({ status }: { status: AgentReport["status"] }) {
  if (status === "ok") {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-400">
        <CheckCircle2 className="w-3 h-3" /> OK
      </span>
    );
  }
  if (status === "insufficient_context") {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-400">
        <Info className="w-3 h-3" /> INSUFFICIENT CONTEXT
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-red-400">
      <XCircle className="w-3 h-3" /> DEGRADED
    </span>
  );
}

function EvidenceChip({ ev }: { ev: AgentEvidence }) {
  const body = (
    <>
      <span className="text-cyan-300 font-bold">{ev.id}</span>
      <span className="text-tradly-muted">·</span>
      <span className="text-tradly-secondary">{ev.label}:</span>
      <span className="text-white">{ev.value}</span>
      {ev.url && <ExternalLink className="w-3 h-3 text-tradly-muted" />}
    </>
  );
  const cls =
    "inline-flex flex-wrap items-center gap-1 px-2 py-1 rounded-lg bg-[#080C14] border border-tradly-border text-[10px] font-mono";
  return ev.url ? (
    <a href={ev.url} target="_blank" rel="noopener noreferrer" className={`${cls} hover:border-cyan-500/40`}>
      {body}
    </a>
  ) : (
    <span className={cls}>{body}</span>
  );
}

interface AgentSquadPanelProps {
  run: AgentRun | null;
  isRunning: boolean;
  error: string | null;
}

export default function AgentSquadPanel({ run, isRunning, error }: AgentSquadPanelProps) {
  const [active, setActive] = useState<AgentName>("technical");
  const activeReport = run?.agents.find((a) => a.agent === active) ?? null;
  const tilt = run ? tiltStyle(run.verdict.tilt) : null;

  return (
    <div className="p-6 rounded-3xl bg-tradly-card border border-tradly-border shadow-card-depth space-y-4">
      <div className="flex items-center justify-between border-b border-tradly-border pb-3">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-black text-white uppercase tracking-wider font-mono">AI Multi-Agent Squad</h3>
        </div>
        {run && (
          <span className="text-[10px] text-tradly-muted font-mono">
            {run.total_duration_ms} ms · run {run.run_id}
          </span>
        )}
      </div>

      {isRunning && (
        <div className="space-y-2">
          {(["technical", "macro", "risk", "synthesis"] as AgentName[]).map((a) => {
            const Icon = AGENT_META[a].icon;
            return (
              <div key={a} className="flex items-center gap-2 p-3 rounded-xl bg-[#080C14] border border-tradly-border text-xs font-mono text-tradly-secondary">
                <Icon className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                <span>{AGENT_META[a].short} agent working…</span>
                <span className="ml-auto h-1.5 w-16 rounded-full bg-cyan-500/20 overflow-hidden">
                  <span className="block h-full w-1/2 bg-cyan-400 animate-pulse" />
                </span>
              </div>
            );
          })}
        </div>
      )}

      {!isRunning && error && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {!isRunning && !run && !error && (
        <p className="text-xs text-tradly-secondary leading-relaxed font-mono">
          Click <span className="text-cyan-400 font-bold">Deploy AI Analysis Squad</span>. Technical, Macro and Risk agents run in
          parallel, each returning evidence; the Synthesis agent keeps only claims backed by that evidence.
        </p>
      )}

      {!isRunning && run && tilt && (
        <>
          {/* Verdict card first */}
          <div className={`p-4 rounded-2xl border ${tilt.cls} space-y-2`}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-black font-mono">
                {tilt.glyph} {run.verdict.label}
              </span>
              <span className="text-[11px] font-mono font-bold">score {run.verdict.score >= 0 ? "+" : ""}{run.verdict.score.toFixed(2)}</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-black/40 overflow-hidden" aria-label="confidence">
              <div className="h-full bg-current" style={{ width: `${Math.round(run.verdict.confidence * 100)}%` }} />
            </div>
            <div className="flex justify-between text-[10px] font-mono text-tradly-secondary">
              <span>Confidence {Math.round(run.verdict.confidence * 100)}%</span>
              <span>Risk: {run.verdict.risk_level}</span>
              <span>{run.verdict.accepted_claims} claims · {run.verdict.discarded_claims.length} discarded</span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed pt-1">{run.verdict.narrative}</p>
            <p className="text-[10px] text-tradly-muted font-mono">Narrative: {run.verdict.narrative_source}</p>
          </div>

          {/* Agent tabs */}
          <div className="grid grid-cols-4 gap-1 bg-[#080C14] p-1 rounded-xl border border-tradly-border">
            {run.agents.map((a) => {
              const Icon = AGENT_META[a.agent].icon;
              return (
                <button
                  key={a.agent}
                  type="button"
                  onClick={() => setActive(a.agent)}
                  className={`flex flex-col items-center gap-0.5 py-1.5 rounded-lg text-[10px] font-bold font-mono transition-all ${
                    active === a.agent ? "bg-cyan-400 text-black" : "text-tradly-muted hover:text-white"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {AGENT_META[a.agent].short}
                  {a.status !== "ok" && <span className="text-[8px]">{a.status === "failed" ? "✕" : "…"}</span>}
                </button>
              );
            })}
          </div>

          {activeReport && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white font-mono">{activeReport.title}</span>
                <StatusBadge status={activeReport.status} />
              </div>
              <div className="flex gap-3 text-[11px] font-mono">
                <span className={stanceColor(activeReport.stance)}>Stance {stanceText(activeReport.stance)}</span>
                <span className="text-tradly-secondary">Confidence {Math.round(activeReport.confidence * 100)}%</span>
                <span className="text-tradly-muted">{activeReport.duration_ms} ms</span>
              </div>
              <p className="text-xs text-tradly-secondary leading-relaxed">{activeReport.summary}</p>

              {activeReport.claims.length > 0 && (
                <ul className="space-y-1.5">
                  {activeReport.claims.map((c, i) => (
                    <li key={`${activeReport.agent}-${i}`} className="p-2.5 rounded-xl bg-[#080C14] border border-tradly-border text-[11px]">
                      <div className="flex gap-2">
                        <span className={`font-mono shrink-0 ${stanceColor(c.stance)}`}>{stanceText(c.stance).split(" ")[0]}</span>
                        <span className="text-slate-200">{c.text}</span>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {c.evidence_ids.map((id) => (
                          <span key={id} className="px-1.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-[9px] font-mono">
                            [{id}]
                          </span>
                        ))}
                      </div>
                    </li>
                  ))}
                </ul>
              )}

              {activeReport.agent === "synthesis" && run.verdict.discarded_claims.length > 0 && (
                <div className="space-y-1.5">
                  <div className="text-[10px] font-bold text-tradly-muted uppercase font-mono">Discarded claims</div>
                  {run.verdict.discarded_claims.map((d, i) => (
                    <div key={i} className="p-2 rounded-lg bg-red-500/5 border border-red-500/20 text-[11px] text-tradly-secondary">
                      <span className="text-red-300 font-mono">{d.agent}</span> · {d.text} <span className="text-tradly-muted">({d.reason})</span>
                    </div>
                  ))}
                </div>
              )}

              {activeReport.evidence.length > 0 && (
                <div className="space-y-1.5">
                  <div className="text-[10px] font-bold text-tradly-muted uppercase font-mono">Evidence retrieved</div>
                  <div className="flex flex-wrap gap-1.5">
                    {activeReport.evidence.map((ev) => (
                      <EvidenceChip key={ev.id} ev={ev} />
                    ))}
                  </div>
                </div>
              )}

              {activeReport.error && (
                <p className="text-[11px] text-red-300 font-mono">Error: {activeReport.error}</p>
              )}
              <p className="text-[10px] text-tradly-muted font-mono">Model: {activeReport.model_used}</p>
            </div>
          )}

          <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 text-[10px] text-amber-200/80 leading-relaxed flex gap-2">
            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>Informational only · not financial advice. {run.disclaimer}</span>
          </div>
        </>
      )}
    </div>
  );
}
