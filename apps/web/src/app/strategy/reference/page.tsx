"use client";

import React, { useEffect, useState } from "react";
import { AlertTriangle, BookMarked, Compass, HelpCircle, Wrench } from "lucide-react";
import { strategyApi } from "../../../services/strategyApi";
import { PairExplainer, Reference } from "../../../types/strategy";
import { Card } from "../../../components/strategy/panels";

export default function ReferencePage() {
  const [reference, setReference] = useState<Reference | null>(null);
  const [pair, setPair] = useState("EUR_USD");
  const [explainer, setExplainer] = useState<PairExplainer | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    strategyApi.reference().then(setReference).catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    strategyApi
      .explainPair(pair)
      .then(setExplainer)
      .catch((e: Error) => setError(e.message));
  }, [pair]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-bold text-white">Reference</h1>
        <p className="text-xs text-tradly-muted mt-1">
          Pair basics, tools, brokers, and every value the engine is running on that
          still needs confirming against the original notebook.
        </p>
      </header>

      {error && (
        <div className="rounded-xl border border-red-500/25 bg-red-500/[0.07] p-4 text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Flagged questions first - they change how the output should be read. */}
      {reference && reference.flagged_for_confirmation.length > 0 && (
        <Card
          title="Needs your confirmation"
          subtitle="Transcribed from handwriting. The engine runs on these today; correcting them is a one-file edit."
          icon={HelpCircle}
          accent={`${reference.flagged_for_confirmation.length} open`}
        >
          <div className="space-y-3">
            {reference.flagged_for_confirmation.map((item) => (
              <div
                key={item.id}
                className="rounded-xl border border-amber-500/25 bg-amber-500/[0.06] p-3 space-y-1.5"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs font-bold text-amber-400">{item.title}</span>
                  <span className="text-[10px] font-mono text-tradly-muted">
                    Module {item.module}
                  </span>
                </div>
                <div className="font-mono text-[11px] text-white break-all">
                  {item.current_value}
                </div>
                <p className="text-[11px] text-tradly-muted leading-relaxed">
                  {item.note}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card
          title="Pair basics"
          subtitle="Base, quote, and what buying it actually means."
          icon={Compass}
        >
          <select
            value={pair}
            onChange={(e) => setPair(e.target.value)}
            className="bg-tradly-bg border border-tradly-border rounded-lg px-3 py-2 text-xs text-white w-full"
          >
            {(reference?.majors ?? ["EUR/USD"]).map((p) => (
              <option key={p} value={p.replace("/", "_")}>
                {p}
              </option>
            ))}
          </select>

          {explainer && (
            <div className="space-y-2.5">
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-tradly-bg border border-tradly-border p-3">
                  <div className="text-[10px] uppercase tracking-wider text-tradly-muted">
                    Base
                  </div>
                  <div className="text-sm font-bold text-white">{explainer.base}</div>
                  <div className="text-[11px] text-tradly-muted">
                    {explainer.base_name}
                  </div>
                </div>
                <div className="rounded-lg bg-tradly-bg border border-tradly-border p-3">
                  <div className="text-[10px] uppercase tracking-wider text-tradly-muted">
                    Quote
                  </div>
                  <div className="text-sm font-bold text-white">{explainer.quote}</div>
                  <div className="text-[11px] text-tradly-muted">
                    {explainer.quote_name}
                  </div>
                </div>
              </div>

              <p className="text-xs text-tradly-text font-mono">
                {explainer.quote_example}
              </p>

              <ul className="space-y-1.5 text-xs">
                <li className="text-emerald-400">{explainer.up_means}</li>
                <li className="text-red-400">{explainer.down_means}</li>
                <li className="text-tradly-text">{explainer.buy_when}</li>
                <li className="text-tradly-text">{explainer.sell_when}</li>
              </ul>

              <div className="text-[10px] font-mono text-tradly-muted">
                1 pip = {explainer.pip_size}
                {explainer.is_major && " · major pair"}
              </div>
            </div>
          )}
        </Card>

        {reference && (
          <Card
            title="Tools & brokers"
            subtitle="Charting, news, and execution."
            icon={Wrench}
          >
            <div className="space-y-1.5">
              {reference.tools.map((tool) => (
                <a
                  key={tool.name}
                  href={tool.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between rounded-lg bg-tradly-bg border border-tradly-border px-3 py-2 hover:bg-tradly-hover transition-colors"
                >
                  <span className="text-xs font-semibold text-white">{tool.name}</span>
                  <span className="text-[10px] text-tradly-muted">{tool.purpose}</span>
                </a>
              ))}
            </div>

            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-tradly-muted mb-1.5">
                Brokers
              </div>
              <div className="space-y-1.5">
                {reference.brokers.map((broker) => (
                  <div
                    key={broker.name}
                    className="rounded-lg bg-tradly-bg border border-tradly-border px-3 py-2"
                  >
                    <div className="text-xs font-semibold text-white">
                      {broker.name}
                    </div>
                    <div className="text-[10px] text-tradly-muted">{broker.note}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-cyan-500/25 bg-cyan-500/[0.06] p-3">
              <div className="text-xs font-bold text-cyan-400 mb-1">
                {reference.guiding_principle.title}
              </div>
              <p className="text-[11px] text-tradly-text leading-relaxed">
                {reference.guiding_principle.body}
              </p>
            </div>
          </Card>
        )}
      </div>

      {reference && (
        <Card
          title="Golden rules"
          subtitle="The mantras the engine enforces in code."
          icon={BookMarked}
        >
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
            {reference.golden_rules.map((rule, i) => (
              <li key={i} className="flex gap-2.5 text-xs leading-relaxed">
                <span className="font-mono text-cyan-400 shrink-0">{i + 1}.</span>
                <span className="text-tradly-text">{rule}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <div className="rounded-2xl border border-tradly-border bg-tradly-card p-5">
        <div className="flex gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p className="text-[11px] text-tradly-muted leading-relaxed">
            This tool implements one personal trading strategy and computes its rules
            on the data you give it. It is analysis tooling, not financial advice, and
            nothing here executes an order. The risk percentages transcribed from the
            notebook are far above conventional position-sizing practice — read the
            warnings on the risk page before applying them to real money.
          </p>
        </div>
      </div>
    </div>
  );
}
