"use client";

import React, { useEffect, useState } from "react";
import { AlertTriangle, Calculator, Loader2 } from "lucide-react";
import { strategyApi } from "../../../services/strategyApi";
import { RiskTable, TradePlan } from "../../../types/strategy";
import { Card, TradePlanPanel } from "../../../components/strategy/panels";

const PAIRS = [
  "EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF",
  "USD_CAD", "AUD_USD", "NZD_USD",
];

export default function RiskPage() {
  const [table, setTable] = useState<RiskTable | null>(null);
  const [plan, setPlan] = useState<TradePlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [form, setForm] = useState({
    symbol: "EUR_USD",
    direction: "buy" as "buy" | "sell",
    entry: 1.1,
    stop_loss: 1.095,
    take_profit: "" as string | number,
    account_size: 10000,
  });

  useEffect(() => {
    strategyApi.riskTable().then(setTable).catch((e: Error) => setError(e.message));
  }, []);

  async function calculate(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await strategyApi.tradePlan({
        symbol: form.symbol,
        direction: form.direction,
        entry: Number(form.entry),
        stop_loss: Number(form.stop_loss),
        account_size: Number(form.account_size),
        take_profit: form.take_profit === "" ? null : Number(form.take_profit),
      });
      setPlan(result);
    } catch (err) {
      setPlan(null);
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const field =
    "bg-tradly-bg border border-tradly-border rounded-lg px-3 py-2 text-xs text-white font-mono w-full";
  const label =
    "text-[10px] font-bold uppercase tracking-wider text-tradly-muted mb-1 block";

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-bold text-white">Risk management</h1>
        <p className="text-xs text-tradly-muted mt-1">
          Position size from the account-size risk table and the real stop distance.
          Minimum 1:2 RR, target 1:4, one trade a week.
        </p>
      </header>

      {error && (
        <div className="rounded-xl border border-red-500/25 bg-red-500/[0.07] p-4 text-xs text-red-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card
          title="Position size calculator"
          subtitle="Pip value is computed per pair — JPY pairs use a 0.01 pip."
          icon={Calculator}
        >
          <form onSubmit={calculate} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={label}>Pair</label>
                <select
                  value={form.symbol}
                  onChange={(e) => setForm({ ...form, symbol: e.target.value })}
                  className={field}
                >
                  {PAIRS.map((p) => (
                    <option key={p} value={p}>
                      {p.replace("_", "/")}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className={label}>Direction</label>
                <select
                  value={form.direction}
                  onChange={(e) =>
                    setForm({ ...form, direction: e.target.value as "buy" | "sell" })
                  }
                  className={field}
                >
                  <option value="buy">Buy (at support)</option>
                  <option value="sell">Sell (at resistance)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className={label}>Entry</label>
                <input
                  type="number"
                  step="any"
                  value={form.entry}
                  onChange={(e) => setForm({ ...form, entry: Number(e.target.value) })}
                  className={field}
                  required
                />
              </div>
              <div>
                <label className={label}>Stop loss</label>
                <input
                  type="number"
                  step="any"
                  value={form.stop_loss}
                  onChange={(e) =>
                    setForm({ ...form, stop_loss: Number(e.target.value) })
                  }
                  className={field}
                  required
                />
              </div>
              <div>
                <label className={label}>Target (blank = 1:4)</label>
                <input
                  type="number"
                  step="any"
                  value={form.take_profit}
                  onChange={(e) => setForm({ ...form, take_profit: e.target.value })}
                  className={field}
                  placeholder="auto"
                />
              </div>
            </div>

            <div>
              <label className={label}>Account size ($)</label>
              <input
                type="number"
                min={1}
                value={form.account_size}
                onChange={(e) =>
                  setForm({ ...form, account_size: Number(e.target.value) })
                }
                className={field}
                required
              />
            </div>

            <button
              type="submit"
              disabled={busy}
              className="w-full py-2.5 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 text-xs font-bold hover:bg-cyan-500/25 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Calculate position size
            </button>
          </form>
        </Card>

        <TradePlanPanel plan={plan} />
      </div>

      {table && (
        <Card
          title="Account size → risk %"
          subtitle="Edit backend/app/strategy/config.py — RISK_TIERS — to change this table."
          icon={AlertTriangle}
          accent={`min 1:${table.min_reward_risk} · target 1:${table.target_reward_risk}`}
        >
          {/* What the table actually means. The numbers are unusual enough
              that the columns need spelling out before anyone sizes off them. */}
          <div className="rounded-xl border border-tradly-border bg-tradly-bg p-4 space-y-3">
            <h3 className="text-[11px] font-bold uppercase tracking-wider text-white">
              How to read this table
            </h3>
            <dl className="space-y-2 text-[11px] leading-relaxed">
              <div>
                <dt className="font-bold text-cyan-400">Account size</dt>
                <dd className="text-tradly-text">
                  A threshold, not an exact match. Your balance uses the highest
                  row it has reached — a $10,000 account sits on the $8,000 row
                  until it crosses $15,000.
                </dd>
              </div>
              <div>
                <dt className="font-bold text-cyan-400">Risk %</dt>
                <dd className="text-tradly-text">
                  The share of the balance you are willing to <em>lose</em> if
                  that one trade hits its stop. It is not the position size and
                  not the margin — a 40% risk on $10,000 means $4,000 gone when
                  the stop is hit, whatever lot size that works out to.
                </dd>
              </div>
              <div>
                <dt className="font-bold text-cyan-400">Used</dt>
                <dd className="text-tradly-text">
                  The single number the calculator applies: the midpoint of the
                  row&apos;s range. A 35–40% row is sized at 37.5%.
                </dd>
              </div>
              <div>
                <dt className="font-bold text-cyan-400">Status</dt>
                <dd className="text-tradly-text">
                  &quot;as transcribed&quot; means the handwritten page gave that
                  row its own value. &quot;unconfirmed&quot; means it did not —
                  the row was inferred from a bracket spanning several sizes, or
                  sits out of order on the page.
                </dd>
              </div>
            </dl>
          </div>

          {/* The dollar consequence of the row that currently applies. */}
          <WorkedExample table={table} accountSize={Number(form.account_size)} />

          <div className="rounded-xl border border-amber-500/25 bg-amber-500/[0.07] p-3">
            <p className="text-[11px] text-amber-300/90 leading-relaxed">{table.note}</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-[10px] uppercase tracking-wider text-tradly-muted border-b border-tradly-border">
                  <th className="py-2 pr-4">Account size</th>
                  <th className="py-2 pr-4">Risk %</th>
                  <th className="py-2 pr-4">Used</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {table.tiers.map((tier) => (
                  <tr
                    key={tier.account_size}
                    className="border-b border-tradly-border/50"
                  >
                    <td className="py-2 pr-4 text-white font-bold">
                      ${tier.account_size.toLocaleString()}
                    </td>
                    <td className="py-2 pr-4 text-tradly-text">
                      {tier.risk_pct_min === tier.risk_pct_max
                        ? `${tier.risk_pct_min}%`
                        : `${tier.risk_pct_min}–${tier.risk_pct_max}%`}
                    </td>
                    <td className="py-2 pr-4 text-cyan-400">{tier.risk_pct_used}%</td>
                    <td className="py-2">
                      {tier.unconfirmed ? (
                        <span
                          className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/25"
                          title={tier.note}
                        >
                          unconfirmed
                        </span>
                      ) : (
                        <span className="text-[10px] text-tradly-muted">
                          as transcribed
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

/**
 * The row that applies to the account size in the form, turned into money.
 *
 * The table is transcribed from handwriting and its percentages are far above
 * any conventional standard, so the one thing that makes it understandable is
 * seeing what it does to a real balance — including what a losing run costs,
 * which is the part a percentage column hides.
 */
function WorkedExample({
  table,
  accountSize,
}: {
  table: RiskTable;
  accountSize: number;
}) {
  if (!Number.isFinite(accountSize) || accountSize <= 0) return null;

  // Highest tier the balance has reached; below the smallest, the smallest.
  const sorted = [...table.tiers].sort((a, b) => a.account_size - b.account_size);
  const tier =
    sorted.filter((t) => accountSize >= t.account_size).pop() ?? sorted[0];
  if (!tier) return null;

  const riskAmount = accountSize * (tier.risk_pct_used / 100);
  const money = (v: number) =>
    `$${v.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;

  // Compound the losses rather than subtracting a fixed amount: risk is a
  // percentage of the balance *at the time*, so each loss is smaller than the
  // last — and the account still never recovers to where it started.
  const losses: number[] = [];
  let balance = accountSize;
  for (let i = 0; i < 3; i++) {
    balance -= balance * (tier.risk_pct_used / 100);
    losses.push(balance);
  }

  // At the target 1:4, one win returns four times what one loss costs.
  const afterWin = accountSize + riskAmount * table.target_reward_risk;

  return (
    <div className="rounded-xl border border-cyan-500/25 bg-cyan-500/[0.06] p-4 space-y-3">
      <h3 className="text-[11px] font-bold uppercase tracking-wider text-cyan-400">
        Your account, on this table
      </h3>
      <p className="text-[11px] text-tradly-text leading-relaxed">
        {money(accountSize)} sits on the{" "}
        <strong className="text-white font-mono">
          ${tier.account_size.toLocaleString()}
        </strong>{" "}
        row, so the calculator risks{" "}
        <strong className="text-white font-mono">{tier.risk_pct_used}%</strong> —{" "}
        <strong className="text-white font-mono">{money(riskAmount)}</strong> on a
        single trade. At the 1:{table.target_reward_risk} target that one trade
        wins {money(riskAmount * table.target_reward_risk)}.
      </p>

      <div className="grid grid-cols-2 gap-3 font-mono text-[11px]">
        <div className="rounded-lg bg-tradly-bg border border-tradly-border p-3">
          <p className="text-[10px] uppercase tracking-wider text-tradly-muted mb-1">
            One win at 1:{table.target_reward_risk}
          </p>
          <p className="text-emerald-400 font-bold text-sm">{money(afterWin)}</p>
        </div>
        <div className="rounded-lg bg-tradly-bg border border-tradly-border p-3">
          <p className="text-[10px] uppercase tracking-wider text-tradly-muted mb-1">
            Three losses in a row
          </p>
          <p className="text-red-400 font-bold text-sm">{money(losses[2])}</p>
          <p className="text-[10px] text-tradly-muted mt-1">
            {money(accountSize)} → {losses.map((b) => money(b)).join(" → ")}
          </p>
        </div>
      </div>

      <p className="text-[11px] text-tradly-muted leading-relaxed">
        That losing run is the whole reason this table is flagged. At one trade a
        week, three losses is under a month, and it leaves{" "}
        {((losses[2] / accountSize) * 100).toFixed(1)}% of the account. A
        conventional 1–2% rule would leave{" "}
        {(100 * Math.pow(0.98, 3)).toFixed(1)}% after the same three losses. Both
        numbers come from the same three trades — only the risk % differs.
      </p>
    </div>
  );
}
