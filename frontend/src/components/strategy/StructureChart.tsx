"use client";

import React, { useMemo, useState } from "react";
import {
  CandlestickChart as CandleIcon,
  History as HistoryIcon,
  LineChart as LineIcon,
} from "lucide-react";
import {
  AOIZone,
  Candle,
  EMAState,
  HeadShoulders,
  Structure,
  Trigger,
} from "../../types/strategy";

interface Props {
  symbol: string;
  timeframe: string;
  candles: Candle[];
  structure?: Structure | null;
  zones?: AOIZone[];
  ema?: EMAState | null;
  headShoulders?: HeadShoulders[];
  trigger?: Trigger | null;
  height?: number;
}

const WIDTH = 960;
const PAD_L = 8;
const PAD_R = 76;
const PAD_Y = 24;

/**
 * Price chart with the strategy's own annotations drawn on top: HH/HL/LH/LL
 * swing labels joined into the structure zigzag, validated AOI zones from this
 * timeframe and every higher one, the level that must hold for the trend to
 * survive, the 50 EMA, any Head & Shoulders neckline, and the armed
 * break-and-retest level.
 *
 * Broken structure is hidden. A swing whose level price has closed through, or
 * that a later CHoCH relabelled, is no longer where structure sits, so leaving
 * it on the chart only invites reading a trend that has already ended. The
 * history toggle brings those points back, ghosted, when you want the audit
 * trail rather than the current read.
 *
 * Swing points are matched to candles by timestamp, not array index: the engine
 * trims each series to its own lookback window, so indices are not guaranteed to
 * line up with whatever slice the chart happens to be showing.
 */
export default function StructureChart({
  symbol,
  timeframe,
  candles,
  structure,
  zones = [],
  ema,
  headShoulders = [],
  trigger,
  height = 420,
}: Props) {
  const [mode, setMode] = useState<"candlestick" | "line">("candlestick");
  const [showBroken, setShowBroken] = useState(false);
  const [hovered, setHovered] = useState<number | null>(null);

  const chart = useMemo(() => {
    if (!candles.length) return null;

    const validZones = zones.filter((z) => z.valid);
    const lows = candles.map((c) => c.low);
    const highs = candles.map((c) => c.high);

    // Include the zones so a zone at the edge of the range stays on screen.
    let min = Math.min(...lows, ...validZones.map((z) => z.lower));
    let max = Math.max(...highs, ...validZones.map((z) => z.upper));
    const span = max - min || 0.001;
    min -= span * 0.06;
    max += span * 0.06;

    const plotW = WIDTH - PAD_L - PAD_R;
    const plotH = height - PAD_Y * 2;
    const step = plotW / candles.length;

    const x = (i: number) => PAD_L + i * step + step / 2;
    const y = (price: number) =>
      PAD_Y + plotH - ((price - min) / (max - min)) * plotH;

    const byTime = new Map<string, number>();
    candles.forEach((c, i) => byTime.set(c.time, i));

    return { min, max, plotW, plotH, step, x, y, byTime, validZones };
  }, [candles, zones, height]);

  if (!chart) {
    return (
      <div
        className="w-full flex items-center justify-center text-xs font-mono text-tradly-muted border border-dashed border-tradly-border rounded-xl"
        style={{ height }}
      >
        No candles loaded.
      </div>
    );
  }

  const { min, max, step, x, y, byTime, validZones } = chart;
  const decimals = symbol.endsWith("JPY") ? 3 : 5;
  const fmt = (v: number) => v.toFixed(decimals);
  const candleW = Math.max(1.5, step * 0.62);

  const active = hovered !== null ? candles[hovered] : candles[candles.length - 1];

  /** Index for a swing, resolved by timestamp with an index fallback. */
  const indexFor = (time: string, fallback: number) => {
    const found = byTime.get(time);
    if (found !== undefined) return found;
    return fallback >= 0 && fallback < candles.length ? fallback : -1;
  };

  // Structure is split into what still stands and what has been taken out.
  // Only the first is drawn unless the history toggle is on.
  const allSwings = structure?.swings ?? [];
  const liveSwings = allSwings.filter((s) => !s.broken && s.label);
  const brokenSwings = allSwings.filter((s) => s.broken && s.label);

  const trendColour =
    structure?.trend === "bullish"
      ? "#00E676"
      : structure?.trend === "bearish"
      ? "#FF1744"
      : "#94A3B8";

  // The zigzag traces every pivot, broken ones included: it is the path price
  // actually walked. Only the *labels* are dropped when a point is retired -
  // skipping the vertices too would draw a swing path that never happened.
  const zigzag = allSwings
    .map((swing) => ({ idx: indexFor(swing.time, swing.index), price: swing.price }))
    .filter((pt) => pt.idx >= 0)
    .sort((a, b) => a.idx - b.idx);

  // The engine's current reference points get a larger dot: these are the ones
  // the rules actually key off, not just any surviving swing.
  const referenceTimes = new Set(
    [
      structure?.last_valid_hl,
      structure?.last_valid_lh,
      structure?.last_hh,
      structure?.last_ll,
    ]
      .filter(Boolean)
      .map((p) => (p as NonNullable<typeof p>).time)
  );

  // In an uptrend the last valid HL is the level whose break flips the trend;
  // in a downtrend it is the last valid LH. Nothing to draw either way when the
  // structure engine has not settled on a direction.
  const mustHold =
    structure?.trend === "bullish" && structure.last_valid_hl
      ? { ...structure.last_valid_hl, label: "HL", colour: "#00E676" }
      : structure?.trend === "bearish" && structure.last_valid_lh
      ? { ...structure.last_valid_lh, label: "LH", colour: "#FF1744" }
      : null;

  // Captions are placed top-down, each pushed clear of the one above it. Levels
  // that agree - a 1W and a 1D support at the same price, the armed trigger
  // sitting on the zone edge, the HL that must hold just under it - are the
  // whole point of the strategy, so they cluster by design and their captions
  // would otherwise overprint exactly where the chart matters most. Each side
  // of the chart keeps its own occupancy list.
  const leftRows: number[] = [];
  const rightRows: number[] = [];
  const place = (rows: number[], preferred: number) => {
    let row = Math.max(PAD_Y + 9, Math.min(preferred, height - PAD_Y - 2));
    while (rows.some((used) => Math.abs(used - row) < 10)) {
      row += 11;
    }
    rows.push(row);
    return row;
  };

  const zoneCaptionY = validZones.map((zone) =>
    place(leftRows, Math.min(y(zone.upper), y(zone.lower)) - 3)
  );
  const mustHoldRow = mustHold ? place(rightRows, y(mustHold.price) - 4) : 0;
  const triggerRow =
    trigger?.level != null && trigger.status !== "none"
      ? place(rightRows, y(trigger.level) - 5)
      : 0;

  const gridLines = Array.from({ length: 5 }, (_, i) => min + ((max - min) / 4) * i);

  return (
    <div className="space-y-3">
      {/* Header: OHLC readout + chart type toggle */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
          <span className="text-white font-bold text-sm">
            {symbol.replace("_", "/")}
          </span>
          <span className="px-2 py-0.5 rounded bg-tradly-hover text-tradly-muted">
            {timeframe}
          </span>
          {active && (
            <>
              <span className="text-tradly-muted">
                O <strong className="text-white">{fmt(active.open)}</strong>
              </span>
              <span className="text-tradly-muted">
                H <strong className="text-emerald-400">{fmt(active.high)}</strong>
              </span>
              <span className="text-tradly-muted">
                L <strong className="text-red-400">{fmt(active.low)}</strong>
              </span>
              <span className="text-tradly-muted">
                C <strong className="text-white">{fmt(active.close)}</strong>
              </span>
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          {brokenSwings.length > 0 && (
            <button
              onClick={() => setShowBroken((v) => !v)}
              aria-pressed={showBroken}
              title={
                `${brokenSwings.length} swing point(s) are no longer live: price ` +
                `closed through the level, or a CHoCH relabelled them.`
              }
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[11px] font-semibold transition-colors ${
                showBroken
                  ? "bg-tradly-hover border-tradly-border text-white"
                  : "bg-tradly-bg border-tradly-border text-tradly-muted hover:text-white"
              }`}
            >
              <HistoryIcon className="w-3.5 h-3.5" />
              {showBroken ? "Hide" : "Show"} {brokenSwings.length} broken
            </button>
          )}

          <div className="flex items-center gap-1 p-1 rounded-lg bg-tradly-bg border border-tradly-border">
            {(
              [
                ["candlestick", CandleIcon],
                ["line", LineIcon],
              ] as const
            ).map(([value, Icon]) => (
              <button
                key={value}
                onClick={() => setMode(value)}
                aria-pressed={mode === value}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-semibold capitalize transition-colors ${
                  mode === value
                    ? "bg-cyan-500/15 text-cyan-400"
                    : "text-tradly-muted hover:text-white"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {value}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-tradly-border bg-tradly-bg overflow-hidden">
        <svg
          viewBox={`0 0 ${WIDTH} ${height}`}
          className="w-full"
          style={{ height }}
          preserveAspectRatio="none"
          role="img"
          aria-label={`${symbol} ${timeframe} price chart with market structure annotations`}
        >
          {/* Price grid */}
          {gridLines.map((price) => (
            <g key={price}>
              <line
                x1={PAD_L}
                x2={WIDTH - PAD_R}
                y1={y(price)}
                y2={y(price)}
                stroke="#1E2638"
                strokeWidth={1}
              />
              <text
                x={WIDTH - PAD_R + 6}
                y={y(price) + 3}
                fill="#94A3B8"
                fontSize={9}
                fontFamily="monospace"
              >
                {fmt(price)}
              </text>
            </g>
          ))}

          {/* Validated AOI zones */}
          {validZones.map((zone, i) => {
            const top = y(zone.upper);
            const bottom = y(zone.lower);
            const isBuy = zone.zone_type === "support";
            const colour = isBuy ? "#00E676" : "#FF1744";
            return (
              <g key={`zone-${i}`}>
                <rect
                  x={PAD_L}
                  y={Math.min(top, bottom)}
                  width={WIDTH - PAD_R - PAD_L}
                  height={Math.max(2, Math.abs(bottom - top))}
                  fill={colour}
                  opacity={0.09}
                />
                <line
                  x1={PAD_L}
                  x2={WIDTH - PAD_R}
                  y1={top}
                  y2={top}
                  stroke={colour}
                  strokeWidth={1}
                  strokeDasharray="4 3"
                  opacity={0.55}
                />
                <line
                  x1={PAD_L}
                  x2={WIDTH - PAD_R}
                  y1={bottom}
                  y2={bottom}
                  stroke={colour}
                  strokeWidth={1}
                  strokeDasharray="4 3"
                  opacity={0.55}
                />
                <text
                  x={PAD_L + 6}
                  y={zoneCaptionY[i]}
                  fill={colour}
                  fontSize={9}
                  fontWeight="bold"
                  fontFamily="monospace"
                >
                  {zone.timeframe} AOI · {zone.golden_rule_tag} · {zone.touches} touches
                  {" · "}
                  {zone.width_pips}p
                </text>
              </g>
            );
          })}

          {/* Price series */}
          {mode === "candlestick"
            ? candles.map((c, i) => {
                const up = c.close >= c.open;
                const colour = up ? "#00E676" : "#FF1744";
                const bodyTop = y(Math.max(c.open, c.close));
                const bodyBottom = y(Math.min(c.open, c.close));
                return (
                  <g
                    key={i}
                    onMouseEnter={() => setHovered(i)}
                    onMouseLeave={() => setHovered(null)}
                  >
                    <line
                      x1={x(i)}
                      x2={x(i)}
                      y1={y(c.high)}
                      y2={y(c.low)}
                      stroke={colour}
                      strokeWidth={1}
                    />
                    <rect
                      x={x(i) - candleW / 2}
                      y={bodyTop}
                      width={candleW}
                      height={Math.max(1, bodyBottom - bodyTop)}
                      fill={colour}
                    />
                  </g>
                );
              })
            : (
              <polyline
                points={candles.map((c, i) => `${x(i)},${y(c.close)}`).join(" ")}
                fill="none"
                stroke="#00F0FF"
                strokeWidth={1.5}
              />
            )}

          {/* 50 EMA - supplementary confluence only */}
          {ema && ema.series.length > 0 && (
            <polyline
              points={ema.series
                .map((v, i) => {
                  // The EMA series is aligned to the tail of the candle array.
                  const offset = candles.length - ema.series.length;
                  const idx = i + offset;
                  if (v === null || idx < 0 || idx >= candles.length) return "";
                  return `${x(idx)},${y(v)}`;
                })
                .filter(Boolean)
                .join(" ")}
              fill="none"
              stroke="#FF9100"
              strokeWidth={1.4}
              opacity={0.85}
            />
          )}

          {/* Head & Shoulders necklines */}
          {headShoulders.map((hs, i) => {
            const a = indexFor(hs.neckline_start.time, hs.neckline_start.index);
            const b = indexFor(hs.neckline_end.time, hs.neckline_end.index);
            if (a < 0 || b < 0) return null;
            return (
              <g key={`hs-${i}`}>
                <line
                  x1={x(a)}
                  x2={WIDTH - PAD_R}
                  y1={y(hs.neckline_start.price)}
                  y2={y(hs.neckline_end.price)}
                  stroke={hs.neckline_broken ? "#00F0FF" : "#94A3B8"}
                  strokeWidth={1.4}
                  strokeDasharray={hs.neckline_broken ? undefined : "5 4"}
                />
                <text
                  x={x(b) + 6}
                  y={y(hs.neckline_end.price) - 5}
                  fill={hs.neckline_broken ? "#00F0FF" : "#94A3B8"}
                  fontSize={9}
                  fontWeight="bold"
                  fontFamily="monospace"
                >
                  Neckline{hs.neckline_broken ? " (broken)" : " (unbroken - not valid yet)"}
                </text>
                {[
                  [hs.left_shoulder, "S"],
                  [hs.head, "H"],
                  [hs.right_shoulder, "S"],
                ].map(([point, label], j) => {
                  const p = point as typeof hs.left_shoulder;
                  const idx = indexFor(p.time, p.index);
                  if (idx < 0) return null;
                  return (
                    <text
                      key={j}
                      x={x(idx)}
                      y={y(p.price) + (p.kind === "high" ? -14 : 18)}
                      fill="#00F0FF"
                      fontSize={11}
                      fontWeight="bold"
                      textAnchor="middle"
                      fontFamily="monospace"
                    >
                      {label as string}
                    </text>
                  );
                })}
              </g>
            );
          })}

          {/* Broken structure - only on request, ghosted so it never competes
              with the live read. */}
          {showBroken &&
            brokenSwings.map((swing, i) => {
              const idx = indexFor(swing.time, swing.index);
              if (idx < 0 || !swing.label) return null;
              const isHigh = swing.kind === "high";
              return (
                <g key={`broken-${i}`} opacity={0.3}>
                  <title>
                    {swing.label} {fmt(swing.price)} — broken:{" "}
                    {swing.broken_reason || "no longer live structure"}
                  </title>
                  <line
                    x1={x(idx) - 3}
                    x2={x(idx) + 3}
                    y1={y(swing.price) - 3}
                    y2={y(swing.price) + 3}
                    stroke="#94A3B8"
                    strokeWidth={1}
                  />
                  <line
                    x1={x(idx) - 3}
                    x2={x(idx) + 3}
                    y1={y(swing.price) + 3}
                    y2={y(swing.price) - 3}
                    stroke="#94A3B8"
                    strokeWidth={1}
                  />
                  <text
                    x={x(idx)}
                    y={y(swing.price) + (isHigh ? -7 : 13)}
                    fill="#94A3B8"
                    fontSize={8}
                    textAnchor="middle"
                    fontFamily="monospace"
                    textDecoration="line-through"
                  >
                    {swing.label}
                  </text>
                </g>
              );
            })}

          {/* The structure zigzag - the live points, in order, joined up. */}
          {zigzag.length > 1 && (
            <polyline
              points={zigzag.map((pt) => `${x(pt.idx)},${y(pt.price)}`).join(" ")}
              fill="none"
              stroke={trendColour}
              strokeWidth={1.2}
              strokeDasharray="6 4"
              opacity={0.5}
            />
          )}

          {/* Live swing points with HH / HL / LH / LL labels */}
          {liveSwings.map((swing, i) => {
            const idx = indexFor(swing.time, swing.index);
            if (idx < 0 || !swing.label) return null;
            const bullish = swing.label === "HH" || swing.label === "HL";
            const colour = bullish ? "#00E676" : "#FF1744";
            const isHigh = swing.kind === "high";
            const isReference =
              referenceTimes.has(swing.time) && swing.label !== null;
            return (
              <g key={`swing-${i}`}>
                <title>
                  {swing.label} {fmt(swing.price)}
                  {isReference ? " — current reference point" : ""}
                </title>
                <circle
                  cx={x(idx)}
                  cy={y(swing.price)}
                  r={isReference ? 4 : 2.5}
                  fill={colour}
                  stroke={isReference ? "#0B0F1A" : undefined}
                  strokeWidth={isReference ? 1 : undefined}
                />
                <text
                  x={x(idx)}
                  y={y(swing.price) + (isHigh ? -7 : 13)}
                  fill={colour}
                  fontSize={isReference ? 10 : 9}
                  fontWeight="bold"
                  textAnchor="middle"
                  fontFamily="monospace"
                >
                  {swing.label}
                </text>
              </g>
            );
          })}

          {/* The level whose break ends the trend - the one line to watch. */}
          {mustHold && (
            <g>
              <line
                x1={PAD_L}
                x2={WIDTH - PAD_R}
                y1={y(mustHold.price)}
                y2={y(mustHold.price)}
                stroke={mustHold.colour}
                strokeWidth={1.2}
                strokeDasharray="2 3"
                opacity={0.8}
              />
              <text
                // Right edge: the left is where the AOI captions live.
                x={WIDTH - PAD_R - 6}
                y={mustHoldRow}
                fill={mustHold.colour}
                fontSize={9}
                fontWeight="bold"
                textAnchor="end"
                fontFamily="monospace"
              >
                {mustHold.label} {fmt(mustHold.price)} must hold
              </text>
            </g>
          )}

          {/* CHoCH markers - where a body close flipped the trend */}
          {structure?.choch_events.map((event, i) => {
            const idx = indexFor(event.time, event.index);
            if (idx < 0) return null;
            return (
              <g key={`choch-${i}`}>
                <line
                  x1={x(idx)}
                  x2={x(idx)}
                  y1={PAD_Y}
                  y2={height - PAD_Y}
                  stroke="#FF9100"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  opacity={0.7}
                />
                <text
                  x={x(idx) + 3}
                  y={PAD_Y + 10}
                  fill="#FF9100"
                  fontSize={9}
                  fontWeight="bold"
                  fontFamily="monospace"
                >
                  CHoCH
                </text>
              </g>
            );
          })}

          {/* Armed break-and-retest level */}
          {trigger?.level != null && trigger.status !== "none" && (
            <g>
              <line
                x1={PAD_L}
                x2={WIDTH - PAD_R}
                y1={y(trigger.level)}
                y2={y(trigger.level)}
                stroke={trigger.is_armed ? "#00F0FF" : "#94A3B8"}
                strokeWidth={1.4}
                strokeDasharray="6 4"
              />
              <text
                x={WIDTH - PAD_R - 6}
                y={triggerRow}
                fill={trigger.is_armed ? "#00F0FF" : "#94A3B8"}
                fontSize={9}
                fontWeight="bold"
                textAnchor="end"
                fontFamily="monospace"
              >
                {trigger.is_armed ? "ARMED" : trigger.status.toUpperCase()} ·{" "}
                {trigger.level_label}
              </text>
            </g>
          )}

          {/* Crosshair */}
          {hovered !== null && (
            <line
              x1={x(hovered)}
              x2={x(hovered)}
              y1={PAD_Y}
              y2={height - PAD_Y}
              stroke="#E2E8F0"
              strokeWidth={0.7}
              opacity={0.35}
            />
          )}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] font-mono text-tradly-muted">
        <Legend colour="#00E676" label="Bullish structure (HH/HL) · Buy zone" />
        <Legend colour="#FF1744" label="Bearish structure (LH/LL) · Sell zone" />
        <Legend colour="#FF9100" label={`${ema?.period ?? 50} EMA · CHoCH`} />
        <Legend colour="#00F0FF" label="Neckline · armed trigger" />
        <Legend colour="#94A3B8" label="Broken structure (hidden by default)" />
      </div>

      {/* What is actually on the chart right now. */}
      <p className="text-[10px] font-mono text-tradly-muted leading-relaxed">
        {liveSwings.length} live structure point
        {liveSwings.length === 1 ? "" : "s"} drawn
        {brokenSwings.length > 0 && (
          <>
            {" · "}
            {brokenSwings.length} removed after price closed through the level or a
            CHoCH relabelled them
          </>
        )}
        {validZones.length > 0 && (
          <>
            {" · "}
            {validZones.length} validated AOI zone
            {validZones.length === 1 ? "" : "s"} (
            {Array.from(new Set(validZones.map((z) => z.timeframe))).join(", ")})
          </>
        )}
        {validZones.length === 0 && (
          <>
            {" · "}no validated AOI — Weekly/Daily only, and only after 3+ tests
          </>
        )}
      </p>
    </div>
  );
}

function Legend({ colour, label }: { colour: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span
        className="w-2.5 h-2.5 rounded-sm inline-block"
        style={{ backgroundColor: colour }}
      />
      {label}
    </span>
  );
}
