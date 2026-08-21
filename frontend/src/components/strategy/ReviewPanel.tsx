"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Bot, Loader2, RefreshCw } from "lucide-react";
import { strategyApi } from "../../services/strategyApi";
import { BridgeStatus, SetupReview } from "../../types/strategy";
import { Card } from "./panels";

/**
 * Optional LLM second opinion on a setup the engine has already ruled on.
 *
 * Two things this panel will not do. It never runs on its own - the review
 * costs a call, so it waits to be asked. And it never fills the gap with
 * generated prose when no model is configured: with no key it says so and
 * shows which environment variable to set. The engine's verdict is what
 * decides the trade either way.
 */
export default function ReviewPanel({
  scenarioKey,
  accountSize,
}: {
  scenarioKey: string;
  accountSize: number;
}) {
  const [status, setStatus] = useState<BridgeStatus | null>(null);
  const [review, setReview] = useState<SetupReview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStatus = useCallback(() => {
    strategyApi
      .reviewStatus()
      .then(setStatus)
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(loadStatus, [loadStatus]);

  // A review belongs to one scenario; drop it when the dataset changes.
  useEffect(() => {
    setReview(null);
  }, [scenarioKey]);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      setReview(await strategyApi.review(scenarioKey, accountSize));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const ready = status?.available ?? false;

  return (
    <Card
      title="AI second opinion"
      subtitle="Bull case, bear case and a verdict on the rule-checked setup."
      icon={Bot}
      accent={ready ? `${status?.provider}/${status?.model}` : "not configured"}
    >
      {error && (
        <div className="rounded-xl border border-red-500/25 bg-red-500/[0.07] p-3 text-[11px] text-red-300">
          {error}
        </div>
      )}

      {status && !ready && (
        <div className="rounded-xl border border-amber-500/25 bg-amber-500/[0.07] p-3 space-y-2">
          <p className="text-[11px] text-amber-300/90 leading-relaxed">
            {status.reason}
          </p>
          {/* Only walk through keys when a key is what is missing. With one
              already set the blocker is something else, and repeating the .env
              instructions just buries the reason that actually applies. */}
          {!status.api_key_present && (
            <>
              {/* With no provider pinned, the key you add is what decides the
                  provider — so suggest a key you are likely to have rather
                  than the env var of a default nobody chose. */}
              <pre className="text-[10px] font-mono text-amber-200/80 bg-black/25 rounded-lg p-2 overflow-x-auto">
                {status.provider_explicit
                  ? `# repo root .env\n${status.api_key_env}=your-key-here`
                  : "# repo root .env — one key is enough\nGROQ_API_KEY=your-key-here"}
              </pre>
              <p className="text-[10px] text-tradly-muted leading-relaxed">
                {status.provider_explicit ? (
                  <>
                    TRADINGAGENTS_LLM_PROVIDER pins this to{" "}
                    <strong>{status.provider}</strong>, so only{" "}
                    {status.api_key_env} will do. Unset it to let any supported
                    key choose the provider.
                  </>
                ) : (
                  <>
                    Groq, OpenAI, Anthropic, Google and the rest all work —
                    whichever key is present picks the provider. Set
                    TRADINGAGENTS_LLM_PROVIDER and TRADINGAGENTS_QUICK_THINK_LLM
                    to override the choice or the model.
                  </>
                )}{" "}
                Restart the API after editing .env.
              </p>
            </>
          )}
          <button
            onClick={loadStatus}
            className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-400 hover:underline"
          >
            <RefreshCw className="w-3 h-3" />
            Re-check
          </button>
        </div>
      )}

      {ready && (
        <>
          {status?.provider_autodetected && (
            <p className="text-[10px] font-mono text-tradly-muted">
              Provider auto-selected from {status.api_key_env}.
            </p>
          )}

          <button
            onClick={run}
            disabled={busy}
            className="w-full py-2.5 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 text-xs font-bold hover:bg-cyan-500/25 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {busy ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Bot className="w-3.5 h-3.5" />
            )}
            {review ? "Run again" : "Ask for a review"}
          </button>
        </>
      )}

      {review && !review.available && (
        <p className="text-[11px] text-amber-300/90 leading-relaxed">
          {review.reason}
        </p>
      )}

      {review?.available && (
        <div className="space-y-3">
          <div className="rounded-xl bg-tradly-bg border border-tradly-border p-3">
            <h3 className="text-[10px] font-bold uppercase tracking-wider text-tradly-muted mb-1">
              Engine verdict (authoritative)
            </h3>
            <p className="text-[11px] font-mono text-white leading-relaxed">
              {review.engine_verdict}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Argument
              title="Bull case"
              body={review.bull_case}
              className="border-emerald-500/25 bg-emerald-500/[0.06] text-emerald-300/90"
            />
            <Argument
              title="Bear case"
              body={review.bear_case}
              className="border-red-500/25 bg-red-500/[0.06] text-red-300/90"
            />
          </div>

          <Argument
            title="Verdict"
            body={review.verdict}
            className="border-cyan-500/25 bg-cyan-500/[0.06] text-cyan-300/90"
          />

          {review.key_risks.length > 0 && (
            <div>
              <h3 className="text-[10px] font-bold uppercase tracking-wider text-tradly-muted mb-1.5">
                Key risks
              </h3>
              <ul className="space-y-1">
                {review.key_risks.map((risk, i) => (
                  <li
                    key={i}
                    className="text-[11px] text-tradly-text leading-relaxed pl-3 border-l border-tradly-border"
                  >
                    {risk}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-[10px] text-tradly-muted leading-relaxed">
            {review.model_used} · {review.disclaimer}
          </p>
        </div>
      )}
    </Card>
  );
}

function Argument({
  title,
  body,
  className,
}: {
  title: string;
  body: string;
  className: string;
}) {
  if (!body) return null;
  return (
    <div className={`rounded-xl border p-3 ${className}`}>
      <h3 className="text-[10px] font-bold uppercase tracking-wider mb-1 opacity-70">
        {title}
      </h3>
      <p className="text-[11px] leading-relaxed">{body}</p>
    </div>
  );
}
