"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  AlertTriangle,
  FlaskConical,
  History,
  Play,
  RefreshCw,
  Scale,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { api } from "../../services/api";
import {
  BacktestRequest,
  BacktestRun,
  BacktestRunSummary,
  BacktestTimeframe,
  StrategyInfo,
  StrategyName,
} from "../../types/backtest";

const PAIRS = [
  "EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD", "NZD_USD", "USD_CAD", "EUR_GBP",
  "EUR_JPY", "GBP_JPY", "AUD_JPY", "EUR_AUD", "USD_INR", "USD_SGD", "USD_MXN",
];
const TIMEFRAMES: BacktestTimeframe[] = ["M30", "H1", "H4", "D1"];

const DEFAULT_REQUEST: BacktestRequest = {
  symbol: "EUR_USD",
  timeframe: "H4",
  strategy: "ema_crossover",
  bars: 1500,
  initial_balance: 10000,
  risk_per_trade_pct: 1,
  sl_atr_mult: 1.5,
  tp_atr_mult: 3,
  fast_period: 9,
  slow_period: 21,
  rsi_period: 14,
  rsi_lower: 30,
  rsi_upper: 70,
  allow_short: true,
};

const EXIT_LABELS: Record<string, string> = {
  take_profit: "Take profit",
  stop_loss: "Stop loss",
  signal_reversal: "Signal reversal",
  end_of_test: "End of test",
};

function priceDecimals(symbol: string): number {
  return symbol.endsWith("JPY") ? 3 : 5;
}

function money(v: number): string {
  const sign = v < 0 ? "-" : v > 0 ? "+" : "";
  return `${sign}$${Math.abs(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function shortDate(iso: string, withTime: boolean): string {
  const d = new Date(iso);
  const date = d.toLocaleDateString(undefined, { year: "2-digit", month: "short", day: "numeric" });
  return withTime ? `${date} ${d.toISOString().slice(11, 16)}Z` : date;
}

interface NumberFieldProps {
  label: string;
  value: number;
  step?: number;
  min?: number;
  max?: number;
  onChange: (v: number) => void;
}

function NumberField({ label, value, step = 1, min, max, onChange }: NumberFieldProps) {
  return (
    <label className="block">
      <span className="text-[10px] text-tradly-muted font-bold uppercase block mb-1 font-mono">{label}</span>
      <input
        type="number"
        value={Number.isFinite(value) ? value : ""}
        step={step}
        min={min}
        max={max}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full p-2.5 rounded-xl bg-[#080C14] border border-tradly-border text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
      />
    </label>
  );
}

interface MetricCardProps {
  label: string;
  value: string;
  sub?: string;
  tone?: "pos" | "neg" | "neutral";
}

function MetricCard({ label, value, sub, tone = "neutral" }: MetricCardProps) {
  const color = tone === "pos" ? "text-emerald-400" : tone === "neg" ? "text-red-400" : "text-cyan-400";
  return (
    <div className="p-4 rounded-2xl bg-tradly-card border border-tradly-border">
      <div className="text-[10px] font-bold text-tradly-muted uppercase font-mono">{label}</div>
      <div className={`text-xl font-extrabold font-mono mt-1 tabular-nums ${color}`}>{value}</div>
      {sub && <div className="text-[11px] text-tradly-muted mt-0.5 font-mono">{sub}</div>}
    </div>
  );
}

export default function BacktestPage() {
  const [req, setReq] = useState<BacktestRequest>(DEFAULT_REQUEST);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [run, setRun] = useState<BacktestRun | null>(null);
  const [history, setHistory] = useState<BacktestRunSummary[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAllTrades, setShowAllTrades] = useState(false);

  const update = <K extends keyof BacktestRequest>(key: K, value: BacktestRequest[K]) =>
    setReq((prev) => ({ ...prev, [key]: value }));

  const refreshHistory = useCallback(async () => {
    try {
      setHistory(await api.getBacktestRuns());
    } catch {
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    api.getBacktestStrategies().then(setStrategies).catch(() => setStrategies([]));
    refreshHistory();
  }, [refreshHistory]);

  const handleRun = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const result = await api.runBacktest(req);
      setRun(result);
      setShowAllTrades(false);
      refreshHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Backtest failed");
    } finally {
      setIsRunning(false);
    }
  };

  const loadRun = async (runId: string) => {
    setError(null);
    try {
      const result = await api.getBacktestRun(runId);
      setRun(result);
      setReq(result.request);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load run");
    }
  };

  const exitBreakdown = useMemo(() => {
    const counts: Record<string, { n: number; pnl: number }> = {};
    for (const t of run?.trades ?? []) {
      const row = counts[t.exit_reason] ?? { n: 0, pnl: 0 };
      row.n += 1;
      row.pnl += t.pnl;
      counts[t.exit_reason] = row;
    }
    return Object.entries(counts).sort((a, b) => b[1].n - a[1].n);
  }, [run]);

  const chartData = useMemo(
    () =>
      (run?.equity_curve ?? []).map((p) => ({
        time: p.time,
        equity: p.equity,
        drawdown: -p.drawdown_pct,
      })),
    [run]
  );

  const activeStrategy = strategies.find((s) => s.id === req.strategy);
  const m = run?.metrics;
  const withTime = run ? run.request.timeframe !== "D1" : true;
  const decimals = priceDecimals(run?.request.symbol ?? req.symbol);
  const trades = run ? (showAllTrades ? run.trades : run.trades.slice(-40).reverse()) : [];

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2.5">
            <FlaskConical className="w-6 h-6 text-cyan-400" />
            Strategy Backtest Lab
          </h1>
          <p className="text-xs text-tradly-muted mt-1 font-mono">
            Deterministic bar-by-bar engine · bid/ask fills · no look-ahead · ATR-based stops
          </p>
        </div>
        {run && (
          <span className="text-[11px] font-mono text-tradly-secondary px-3 py-1.5 rounded-xl bg-[#080C14] border border-tradly-border">
            Run {run.run_id} · {run.runtime_ms} ms
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Configuration panel */}
        <div className="xl:col-span-3 space-y-4">
          <div className="p-5 rounded-3xl bg-tradly-card border border-tradly-border shadow-card-depth space-y-4">
            <h2 className="text-xs font-black text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <Target className="w-4 h-4 text-cyan-400" /> Configuration
            </h2>

            <label className="block">
              <span className="text-[10px] text-tradly-muted font-bold uppercase block mb-1 font-mono">Strategy</span>
              <select
                value={req.strategy}
                onChange={(e) => update("strategy", e.target.value as StrategyName)}
                className="w-full p-2.5 rounded-xl bg-[#080C14] border border-tradly-border text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
              >
                {(strategies.length ? strategies : [
                  { id: "ema_crossover", name: "EMA Crossover" },
                  { id: "rsi_reversion", name: "RSI Mean Reversion" },
                  { id: "macd_momentum", name: "MACD Momentum" },
                ]).map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              {activeStrategy && (
                <span className="text-[10px] text-tradly-muted mt-1 block">{activeStrategy.description}</span>
              )}
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-[10px] text-tradly-muted font-bold uppercase block mb-1 font-mono">Pair</span>
                <select
                  value={req.symbol}
                  onChange={(e) => update("symbol", e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-[#080C14] border border-tradly-border text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
                >
                  {PAIRS.map((p) => (
                    <option key={p} value={p}>{p.replace("_", "/")}</option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-[10px] text-tradly-muted font-bold uppercase block mb-1 font-mono">Timeframe</span>
                <select
                  value={req.timeframe}
                  onChange={(e) => update("timeframe", e.target.value as BacktestTimeframe)}
                  className="w-full p-2.5 rounded-xl bg-[#080C14] border border-tradly-border text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
                >
                  {TIMEFRAMES.map((tf) => (
                    <option key={tf} value={tf}>{tf}</option>
                  ))}
                </select>
              </label>
              <NumberField label="Bars" value={req.bars} min={200} max={3000} step={100} onChange={(v) => update("bars", v)} />
              <NumberField label="Balance $" value={req.initial_balance} min={100} step={1000} onChange={(v) => update("initial_balance", v)} />
              <NumberField label="Risk / trade %" value={req.risk_per_trade_pct} min={0.1} max={5} step={0.25} onChange={(v) => update("risk_per_trade_pct", v)} />
              <NumberField label="Stop (×ATR)" value={req.sl_atr_mult} min={0.5} max={10} step={0.25} onChange={(v) => update("sl_atr_mult", v)} />
              <NumberField label="Target (×ATR)" value={req.tp_atr_mult} min={0.5} max={20} step={0.25} onChange={(v) => update("tp_atr_mult", v)} />
              {req.strategy === "ema_crossover" && (
                <>
                  <NumberField label="Fast EMA" value={req.fast_period} min={2} max={100} onChange={(v) => update("fast_period", v)} />
                  <NumberField label="Slow EMA" value={req.slow_period} min={3} max={300} onChange={(v) => update("slow_period", v)} />
                </>
              )}
              {req.strategy === "rsi_reversion" && (
                <>
                  <NumberField label="RSI period" value={req.rsi_period} min={2} max={50} onChange={(v) => update("rsi_period", v)} />
                  <NumberField label="Oversold" value={req.rsi_lower} min={5} max={50} onChange={(v) => update("rsi_lower", v)} />
                  <NumberField label="Overbought" value={req.rsi_upper} min={50} max={95} onChange={(v) => update("rsi_upper", v)} />
                </>
              )}
            </div>

            <label className="flex items-center gap-2 text-xs text-tradly-secondary font-mono cursor-pointer">
              <input
                type="checkbox"
                checked={req.allow_short}
                onChange={(e) => update("allow_short", e.target.checked)}
                className="accent-cyan-400"
              />
              Allow short trades
            </label>

            <button
              type="button"
              onClick={handleRun}
              disabled={isRunning}
              className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-300 hover:to-blue-400 text-black font-black text-xs shadow-neon-cyan transition-all disabled:opacity-50"
            >
              {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-black" />}
              {isRunning ? "Running backtest…" : "Run backtest"}
            </button>

            {error && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
              </div>
            )}
          </div>

          <div className="p-5 rounded-3xl bg-tradly-card border border-tradly-border space-y-3">
            <h2 className="text-xs font-black text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <History className="w-4 h-4 text-cyan-400" /> Recent runs
            </h2>
            {history.length === 0 ? (
              <p className="text-[11px] text-tradly-muted">No runs yet in this session.</p>
            ) : (
              <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
                {history.map((h) => (
                  <button
                    key={h.run_id}
                    type="button"
                    onClick={() => loadRun(h.run_id)}
                    className={`w-full text-left p-2.5 rounded-xl border text-[11px] font-mono transition-all ${
                      run?.run_id === h.run_id
                        ? "border-cyan-500/40 bg-cyan-500/10"
                        : "border-tradly-border bg-[#080C14] hover:border-cyan-500/30"
                    }`}
                  >
                    <div className="flex justify-between text-white font-bold">
                      <span>{h.symbol.replace("_", "/")} · {h.timeframe}</span>
                      <span className={h.net_profit >= 0 ? "text-emerald-400" : "text-red-400"}>
                        {h.total_return_pct >= 0 ? "▲" : "▼"} {h.total_return_pct.toFixed(2)}%
                      </span>
                    </div>
                    <div className="text-tradly-muted">
                      {h.strategy.replace("_", " ")} · {h.total_trades} trades · SR {h.sharpe_ratio}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Results */}
        <div className="xl:col-span-9 space-y-6">
          {!run || !m ? (
            <div className="h-[420px] rounded-3xl bg-tradly-card border border-dashed border-tradly-border flex flex-col items-center justify-center text-center p-8 gap-3">
              <FlaskConical className="w-10 h-10 text-tradly-muted" />
              <p className="text-sm text-white font-bold">Configure a strategy and run a backtest</p>
              <p className="text-xs text-tradly-muted max-w-md">
                Signals are evaluated on each bar&apos;s close and filled at the next bar&apos;s open — buys at the ask,
                sells at the bid — with ATR-sized stops and targets and risk-based position sizing.
              </p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard
                  label="Net profit"
                  value={money(m.net_profit)}
                  sub={`${m.total_return_pct >= 0 ? "▲" : "▼"} ${m.total_return_pct.toFixed(2)}% return`}
                  tone={m.net_profit >= 0 ? "pos" : "neg"}
                />
                <MetricCard
                  label="Win rate"
                  value={`${m.win_rate_pct.toFixed(1)}%`}
                  sub={`${m.winning_trades}W / ${m.losing_trades}L of ${m.total_trades}`}
                />
                <MetricCard
                  label="Profit factor"
                  value={m.profit_factor.toFixed(2)}
                  sub={`Expectancy ${money(m.expectancy)} / trade`}
                  tone={m.profit_factor >= 1 ? "pos" : "neg"}
                />
                <MetricCard
                  label="Sharpe ratio"
                  value={m.sharpe_ratio.toFixed(2)}
                  sub="Annualised, bar returns"
                  tone={m.sharpe_ratio >= 0 ? "pos" : "neg"}
                />
                <MetricCard
                  label="Max drawdown"
                  value={`▼ ${m.max_drawdown_pct.toFixed(2)}%`}
                  sub={`-$${m.max_drawdown_amount.toFixed(2)}`}
                  tone="neg"
                />
                <MetricCard label="Avg win / loss" value={`${money(m.avg_win)}`} sub={`${money(m.avg_loss)} avg loss`} />
                <MetricCard label="Avg R multiple" value={`${m.avg_r_multiple >= 0 ? "+" : ""}${m.avg_r_multiple.toFixed(2)}R`} tone={m.avg_r_multiple >= 0 ? "pos" : "neg"} />
                <MetricCard label="Market exposure" value={`${m.exposure_pct.toFixed(1)}%`} sub={`${m.bars_tested} bars tested`} />
              </div>

              <div className="p-5 rounded-3xl bg-tradly-card border border-tradly-border space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-sm font-bold text-white flex items-center gap-2">
                    <Activity className="w-4 h-4 text-cyan-400" /> Equity curve & drawdown
                  </h2>
                  <span className="text-[11px] text-tradly-muted font-mono">
                    {run.request.symbol.replace("_", "/")} {run.request.timeframe} · {shortDate(run.period_start, false)} →{" "}
                    {shortDate(run.period_end, false)} · spread {run.spread_pips} pips
                  </span>
                </div>
                <div className="h-[320px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="eqFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#00F0FF" stopOpacity={0.25} />
                          <stop offset="100%" stopColor="#00F0FF" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1E2638" vertical={false} />
                      <XAxis
                        dataKey="time"
                        stroke="#5A6B85"
                        fontSize={10}
                        tickLine={false}
                        minTickGap={60}
                        tickFormatter={(v: string) => shortDate(v, false)}
                      />
                      <YAxis yAxisId="eq" stroke="#5A6B85" fontSize={10} tickLine={false} domain={["auto", "auto"]} width={70}
                        tickFormatter={(v: number) => `$${Math.round(v).toLocaleString()}`} />
                      <YAxis yAxisId="dd" orientation="right" stroke="#FF1744" fontSize={10} tickLine={false} width={45}
                        tickFormatter={(v: number) => `${v.toFixed(0)}%`} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#121722", borderColor: "#1E2638", borderRadius: "12px", fontSize: "12px" }}
                        labelFormatter={(v: string) => shortDate(v, withTime)}
                        formatter={(value: number, name: string) =>
                          name === "Drawdown" ? [`${value.toFixed(2)}%`, name] : [`$${value.toFixed(2)}`, name]
                        }
                      />
                      <Area yAxisId="dd" type="monotone" dataKey="drawdown" name="Drawdown" stroke="#FF1744" strokeOpacity={0.5}
                        fill="#FF1744" fillOpacity={0.12} isAnimationActive={false} />
                      <Area yAxisId="eq" type="monotone" dataKey="equity" name="Equity" stroke="none" fill="url(#eqFill)" isAnimationActive={false} />
                      <Line yAxisId="eq" type="monotone" dataKey="equity" name="Equity" stroke="#00F0FF" strokeWidth={2} dot={false} isAnimationActive={false} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="p-5 rounded-3xl bg-tradly-card border border-tradly-border space-y-3">
                  <h2 className="text-sm font-bold text-white flex items-center gap-2">
                    <Scale className="w-4 h-4 text-cyan-400" /> Exit breakdown
                  </h2>
                  {exitBreakdown.length === 0 ? (
                    <p className="text-xs text-tradly-muted">No trades were triggered with these parameters.</p>
                  ) : (
                    exitBreakdown.map(([reason, row]) => (
                      <div key={reason} className="flex items-center justify-between text-xs font-mono p-2.5 rounded-xl bg-[#080C14] border border-tradly-border">
                        <span className="text-tradly-secondary">{EXIT_LABELS[reason] ?? reason}</span>
                        <span className="text-white">{row.n}</span>
                        <span className={row.pnl >= 0 ? "text-emerald-400" : "text-red-400"}>{money(row.pnl)}</span>
                      </div>
                    ))
                  )}
                  <p className="text-[10px] text-tradly-muted leading-relaxed pt-1">
                    Data: {run.data_source}. Past or simulated performance does not predict future results.
                  </p>
                </div>

                <div className="lg:col-span-2 p-5 rounded-3xl bg-tradly-card border border-tradly-border space-y-3">
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm font-bold text-white">Trade ledger</h2>
                    {run.trades.length > 40 && (
                      <button
                        type="button"
                        onClick={() => setShowAllTrades((v) => !v)}
                        className="text-[11px] text-cyan-400 font-mono hover:underline"
                      >
                        {showAllTrades ? "Show latest 40" : `Show all ${run.trades.length}`}
                      </button>
                    )}
                  </div>
                  <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
                    <table className="w-full text-[11px] font-mono tabular-nums">
                      <thead className="sticky top-0 bg-tradly-card">
                        <tr className="text-tradly-muted text-left border-b border-tradly-border">
                          <th className="py-2 pr-3">#</th>
                          <th className="py-2 pr-3">Side</th>
                          <th className="py-2 pr-3">Entry</th>
                          <th className="py-2 pr-3">Exit</th>
                          <th className="py-2 pr-3 text-right">Pips</th>
                          <th className="py-2 pr-3 text-right">P&L</th>
                          <th className="py-2 pr-3 text-right">R</th>
                          <th className="py-2">Reason</th>
                        </tr>
                      </thead>
                      <tbody>
                        {trades.map((t) => (
                          <tr key={t.trade_no} className="border-b border-tradly-border/50 text-tradly-secondary">
                            <td className="py-1.5 pr-3 text-tradly-muted">{t.trade_no}</td>
                            <td className={`py-1.5 pr-3 font-bold ${t.direction === "long" ? "text-emerald-400" : "text-red-400"}`}>
                              {t.direction === "long" ? (
                                <span className="inline-flex items-center gap-1"><TrendingUp className="w-3 h-3" />LONG</span>
                              ) : (
                                <span className="inline-flex items-center gap-1"><TrendingDown className="w-3 h-3" />SHORT</span>
                              )}
                            </td>
                            <td className="py-1.5 pr-3">
                              <div className="text-white">{t.entry_price.toFixed(decimals)}</div>
                              <div className="text-tradly-muted text-[10px]">{shortDate(t.entry_time, withTime)}</div>
                            </td>
                            <td className="py-1.5 pr-3">
                              <div className="text-white">{t.exit_price.toFixed(decimals)}</div>
                              <div className="text-tradly-muted text-[10px]">{shortDate(t.exit_time, withTime)}</div>
                            </td>
                            <td className={`py-1.5 pr-3 text-right ${t.pnl_pips >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                              {t.pnl_pips >= 0 ? "+" : ""}{t.pnl_pips.toFixed(1)}
                            </td>
                            <td className={`py-1.5 pr-3 text-right font-bold ${t.pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                              {money(t.pnl)}
                            </td>
                            <td className="py-1.5 pr-3 text-right">{t.r_multiple.toFixed(2)}</td>
                            <td className="py-1.5 text-tradly-muted">{EXIT_LABELS[t.exit_reason] ?? t.exit_reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
