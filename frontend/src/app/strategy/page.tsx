"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Download, Loader2, RefreshCw } from "lucide-react";
import { strategyApi } from "../../services/strategyApi";
import {
  ALL_TIMEFRAMES,
  Analysis,
  Candle,
  Scenario,
} from "../../types/strategy";
import ReviewPanel from "../../components/strategy/ReviewPanel";
import StructureChart from "../../components/strategy/StructureChart";
import {
  AOIPanel,
  ConfluencePanel,
  GuardrailBanner,
  NarrativePanel,
  PatternPanel,
  SessionPanel,
  TradePlanPanel,
  TrendDashboard,
  TriggerPanel,
} from "../../components/strategy/panels";

const CHART_TIMEFRAMES = ["1W", "1D", "4H", "1H"] as const;

export default function StrategyPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [scenarioKey, setScenarioKey] = useState<string>("");
  const [accountSize, setAccountSize] = useState(10000);
  const [chartTimeframe, setChartTimeframe] = useState<string>("1D");

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(true);
  const [logging, setLogging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // Load the scenario catalogue once.
  useEffect(() => {
    strategyApi
      .scenarios()
      .then((list) => {
        setScenarios(list);
        if (list.length) setScenarioKey(list[0].key);
      })
      .catch((e: Error) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  const load = useCallback(async () => {
    if (!scenarioKey) return;
    setLoading(true);
    setError(null);
    try {
      const [result, series] = await Promise.all([
        strategyApi.analysis(scenarioKey, accountSize),
        // Ask for the whole series so chart annotations line up with structure.
        strategyApi.candles(scenarioKey, chartTimeframe, 2000),
      ]);
      setAnalysis(result);
      setCandles(series.candles);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [scenarioKey, accountSize, chartTimeframe]);

  useEffect(() => {
    load();
  }, [load]);

  const scenario = useMemo(
    () => scenarios.find((s) => s.key === scenarioKey),
    [scenarios, scenarioKey]
  );

  const structure = analysis
    ? analysis.top_down.trend_layer[chartTimeframe] ??
      analysis.top_down.entry_layer[chartTimeframe] ??
      null
    : null;

  const chartZones = useMemo(() => {
    // AOI is only ever computed on Weekly and Daily ("never on 4H"), so a chart
    // filtered to its own timeframe would show no zones at all below Daily.
    // Draw the zones from this timeframe and every higher one: a Daily zone is
    // exactly what you drop to 4H to trade into.
    const rank = (tf: string) => {
      const i = ALL_TIMEFRAMES.indexOf(tf as never);
      return i === -1 ? ALL_TIMEFRAMES.length : i;
    };
    return (analysis?.valid_zones ?? []).filter(
      (z) => rank(z.timeframe) <= rank(chartTimeframe)
    );
  }, [analysis, chartTimeframe]);

  async function logTrade() {
    if (!analysis?.trade_plan) return;
    const plan = analysis.trade_plan;
    setLogging(true);
    setNotice(null);
    try {
      await strategyApi.logTrade({
        symbol: plan.symbol,
        direction: plan.direction,
        entry: plan.entry,
        stop_loss: plan.stop_loss,
        take_profit: plan.take_profit,
        position_size_lots: plan.position_size_lots,
        risk_amount: plan.risk_amount,
        planned_rr: plan.reward_risk,
        sync_state: analysis.top_down.sync?.explanation ?? "",
        sync_timeframes: analysis.top_down.sync?.agreeing_timeframes ?? [],
        aoi_zone: analysis.valid_zones[0]
          ? `${analysis.valid_zones[0].lower}-${analysis.valid_zones[0].upper}`
          : null,
        aoi_timeframe: analysis.valid_zones[0]?.timeframe ?? null,
        aoi_touches: analysis.valid_zones[0]?.touches ?? 0,
        // Only the formations that actually confirmed the setup: a bearish
        // engulfing sitting at an AOI did nothing for a long.
        patterns: Array.from(
          new Set(
            analysis.actionable_patterns
              .filter((p) => p.bias === analysis.bias)
              .map((p) => p.name)
          )
        ),
        confluence_score: analysis.confluence?.score ?? 0,
        confluence_max: analysis.confluence?.max_score ?? 0,
        low_risk_high_reward: analysis.confluence?.low_risk_high_reward ?? false,
      });
      setNotice("Trade logged. Set & forget — leave it alone now.");
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLogging(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header + controls */}
      <header className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">
              Forex Top-Down Confluence Toolkit
            </h1>
            <p className="text-xs text-tradly-muted mt-1">
              Trend → AOI → break &amp; retest → pattern → confluence → sized plan.
              Every stage computed on real OHLC.
            </p>
          </div>

          <div className="flex flex-wrap items-end gap-2">
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-tradly-muted">
                Dataset
              </span>
              <select
                value={scenarioKey}
                onChange={(e) => setScenarioKey(e.target.value)}
                className="bg-tradly-card border border-tradly-border rounded-lg px-3 py-2 text-xs text-white min-w-[240px]"
              >
                {scenarios.map((s) => (
                  <option key={s.key} value={s.key}>
                    {s.symbol.replace("_", "/")} — {s.title.split("—")[1]?.trim() ?? s.title}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-tradly-muted">
                Account
              </span>
              <input
                type="number"
                min={100}
                step={100}
                value={accountSize}
                onChange={(e) => setAccountSize(Number(e.target.value) || 100)}
                className="bg-tradly-card border border-tradly-border rounded-lg px-3 py-2 text-xs text-white w-32 font-mono"
              />
            </label>

            <button
              onClick={load}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 text-xs font-bold hover:bg-cyan-500/25 transition-colors disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" />
              )}
              Re-run
            </button>
          </div>
        </div>

        {scenario && (
          <div className="rounded-xl bg-tradly-card border border-tradly-border p-4">
            <p className="text-xs text-tradly-text leading-relaxed">
              {scenario.description}
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {scenario.demonstrates.map((item, i) => (
                <span
                  key={i}
                  className="text-[10px] px-2 py-1 rounded bg-tradly-bg border border-tradly-border text-tradly-muted"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}
      </header>

      {error && (
        <div className="rounded-xl border border-red-500/25 bg-red-500/[0.07] p-4 text-xs text-red-300">
          {error}
          <p className="mt-1 text-tradly-muted">
            Is the API running? Start it with{" "}
            <code className="font-mono">uvicorn main:app --reload</code> from{" "}
            <code className="font-mono">backend/</code>.
          </p>
        </div>
      )}

      {notice && (
        <div className="rounded-xl border border-cyan-500/25 bg-cyan-500/[0.07] p-4 text-xs text-cyan-300">
          {notice}
        </div>
      )}

      {analysis && (
        <>
          <GuardrailBanner messages={analysis.guardrails} />

          {/* Chart */}
          <section className="rounded-2xl bg-tradly-card border border-tradly-border p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-1 p-1 rounded-lg bg-tradly-bg border border-tradly-border">
                {CHART_TIMEFRAMES.map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setChartTimeframe(tf)}
                    className={`px-3 py-1 rounded text-[11px] font-bold transition-colors ${
                      chartTimeframe === tf
                        ? "bg-cyan-500/15 text-cyan-400"
                        : "text-tradly-muted hover:text-white"
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>

              <a
                href={strategyApi.candlesCsvUrl(scenarioKey, chartTimeframe)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-tradly-border text-[11px] font-semibold text-tradly-muted hover:text-white hover:bg-tradly-hover transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                Export CSV
              </a>
            </div>

            <StructureChart
              symbol={analysis.symbol}
              timeframe={chartTimeframe}
              candles={candles}
              structure={structure}
              zones={chartZones}
              ema={chartTimeframe === "1D" ? analysis.ema : null}
              headShoulders={analysis.head_shoulders[chartTimeframe] ?? []}
              trigger={analysis.trigger}
            />
          </section>

          <NarrativePanel analysis={analysis} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <TrendDashboard topDown={analysis.top_down} />
            <AOIPanel scans={analysis.aoi_scans} zones={analysis.valid_zones} />
            <TriggerPanel trigger={analysis.trigger} />
            <PatternPanel
              patterns={analysis.actionable_patterns}
              headShoulders={analysis.head_shoulders}
            />
            <ConfluencePanel confluence={analysis.confluence} />
            <TradePlanPanel
              plan={analysis.trade_plan}
              onLog={analysis.trade_plan ? logTrade : undefined}
              logging={logging}
            />
            <SessionPanel clock={analysis.session} />

            <ReviewPanel scenarioKey={scenarioKey} accountSize={accountSize} />

            {analysis.weekly_pace && (
              <section className="rounded-2xl bg-tradly-card border border-tradly-border p-5 space-y-3">
                <h2 className="text-sm font-bold text-white">1 trade a week</h2>
                <div className="flex items-center gap-3">
                  <div className="text-3xl font-bold font-mono text-white">
                    {analysis.weekly_pace.trades_this_week}
                    <span className="text-tradly-muted text-lg">
                      /{analysis.weekly_pace.limit}
                    </span>
                  </div>
                  <p
                    className={`text-xs leading-relaxed ${
                      analysis.weekly_pace.at_limit
                        ? "text-amber-400"
                        : "text-tradly-muted"
                    }`}
                  >
                    {analysis.weekly_pace.message}
                  </p>
                </div>
                <Link
                  href="/strategy/journal"
                  className="inline-block text-[11px] font-semibold text-cyan-400 hover:underline"
                >
                  Open the trade journal →
                </Link>
              </section>
            )}
          </div>
        </>
      )}

      {loading && !analysis && (
        <div className="flex items-center justify-center gap-2 py-20 text-xs text-tradly-muted">
          <Loader2 className="w-4 h-4 animate-spin" />
          Running the top-down pass…
        </div>
      )}
    </div>
  );
}
