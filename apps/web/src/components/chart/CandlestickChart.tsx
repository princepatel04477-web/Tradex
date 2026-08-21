"use client";

import React, { useState } from "react";
import { Candle, IndicatorSnapshot } from "../../types/market";

interface CandlestickChartProps {
  candles: Candle[];
  indicators: IndicatorSnapshot | null;
  showRSI: boolean;
  showMACD: boolean;
  showBB: boolean;
  showEMA: boolean;
  showSMA200: boolean;
}

export default function CandlestickChart({
  candles,
  indicators,
  showRSI,
  showMACD,
  showBB,
  showEMA,
  showSMA200
}: CandlestickChartProps) {
  const [hoveredCandle, setHoveredCandle] = useState<Candle | null>(null);

  if (!candles || candles.length === 0) {
    return (
      <div className="h-[420px] w-full flex items-center justify-center text-xs font-mono text-tradly-muted border border-dashed border-tradly-border rounded-xl">
        Loading Candlestick Data...
      </div>
    );
  }

  // Calculate High / Low price bounds
  const prices = candles.flatMap((c) => [c.high, c.low]);
  const maxPrice = Math.max(...prices);
  const minPrice = Math.min(...prices);
  const priceRange = maxPrice - minPrice || 0.001;

  const svgWidth = 850;
  const mainHeight = 260;
  const subHeight = 80;
  const padding = 35;

  const candleWidth = Math.max(3, (svgWidth - padding * 2) / candles.length - 2);

  // Price Y scale
  const getPriceY = (val: number) => {
    return mainHeight - padding - ((val - minPrice) / priceRange) * (mainHeight - padding * 2);
  };

  // Hover candle target
  const displayCandle = hoveredCandle || candles[candles.length - 1];

  return (
    <div className="space-y-4">
      {/* Interactive OHLC Bar Header */}
      {displayCandle && (
        <div className="p-3 rounded-xl bg-tradly-bg border border-tradly-border flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
          <div className="flex items-center space-x-3">
            <span className="text-white font-bold">{displayCandle.symbol.replace("_", "/")}</span>
            <span className="text-tradly-muted">
              O: <strong className="text-white">{displayCandle.open}</strong>
            </span>
            <span className="text-tradly-muted">
              H: <strong className="text-emerald-400">{displayCandle.high}</strong>
            </span>
            <span className="text-tradly-muted">
              L: <strong className="text-red-400">{displayCandle.low}</strong>
            </span>
            <span className="text-tradly-muted">
              C: <strong className="text-white">{displayCandle.close}</strong>
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-tradly-muted">Change:</span>
            <span
              className={`font-bold ${
                displayCandle.close >= displayCandle.open ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {(displayCandle.close - displayCandle.open > 0 ? "+" : "") +
                (displayCandle.close - displayCandle.open).toFixed(
                  displayCandle.symbol.includes("JPY") ? 2 : 4
                )}
            </span>
          </div>
        </div>
      )}

      {/* Main SVG Candlestick Canvas */}
      <div className="relative overflow-x-auto rounded-xl bg-tradly-bg border border-tradly-border p-2">
        <svg viewBox={`0 0 ${svgWidth} ${mainHeight + (showRSI ? subHeight : 0) + (showMACD ? subHeight : 0)}`} className="w-full h-auto">
          {/* Background Grid Lines */}
          {[0.2, 0.4, 0.6, 0.8].map((pct, idx) => {
            const y = padding + pct * (mainHeight - padding * 2);
            const gridPrice = (maxPrice - pct * priceRange).toFixed(
              candles[0].symbol.includes("JPY") ? 2 : 4
            );
            return (
              <g key={idx}>
                <line x1={padding} y1={y} x2={svgWidth - padding} y2={y} stroke="#1E2638" strokeDasharray="3 3" />
                <text x={svgWidth - padding + 5} y={y + 3} fill="#94A3B8" fontSize="9" fontFamily="monospace">
                  {gridPrice}
                </text>
              </g>
            );
          })}

          {/* Render Bollinger Bands overlay if enabled */}
          {showBB && indicators && (
            <g opacity="0.4">
              <line x1={padding} y1={getPriceY(indicators.bb_upper)} x2={svgWidth - padding} y2={getPriceY(indicators.bb_upper)} stroke="#00F0FF" strokeDasharray="2 2" strokeWidth="1" />
              <line x1={padding} y1={getPriceY(indicators.bb_lower)} x2={svgWidth - padding} y2={getPriceY(indicators.bb_lower)} stroke="#00F0FF" strokeDasharray="2 2" strokeWidth="1" />
            </g>
          )}

          {/* Render SMA-200 overlay line if enabled */}
          {showSMA200 && indicators && (
            <line x1={padding} y1={getPriceY(indicators.sma_200)} x2={svgWidth - padding} y2={getPriceY(indicators.sma_200)} stroke="#FF9100" strokeWidth="1.5" strokeDasharray="4 4" />
          )}

          {/* Candlesticks (Wicks + Bodies) */}
          {candles.map((c, idx) => {
            const x = padding + idx * ((svgWidth - padding * 2) / candles.length) + candleWidth / 2;
            const yHigh = getPriceY(c.high);
            const yLow = getPriceY(c.low);
            const yOpen = getPriceY(c.open);
            const yClose = getPriceY(c.close);

            const isBullish = c.close >= c.open;
            const color = isBullish ? "#00E676" : "#FF1744";

            const bodyY = Math.min(yOpen, yClose);
            const bodyHeight = Math.max(1.5, Math.abs(yOpen - yClose));

            return (
              <g
                key={idx}
                className="cursor-pointer hover:opacity-80 transition-opacity"
                onMouseEnter={() => setHoveredCandle(c)}
              >
                {/* High/Low Wick */}
                <line x1={x} y1={yHigh} x2={x} y2={yLow} stroke={color} strokeWidth="1" />

                {/* Open/Close Body */}
                <rect
                  x={x - candleWidth / 2}
                  y={bodyY}
                  width={candleWidth}
                  height={bodyHeight}
                  fill={isBullish ? color : color}
                  rx="1"
                />
              </g>
            );
          })}

          {/* RSI Subchart if enabled */}
          {showRSI && indicators && (
            <g transform={`translate(0, ${mainHeight})`}>
              <rect x={padding} y={0} width={svgWidth - padding * 2} height={subHeight} fill="#121722" opacity="0.5" />
              <text x={padding + 5} y={15} fill="#00F0FF" fontSize="10" fontWeight="bold">RSI (14): {indicators.rsi_14}</text>
              {/* Overbought 70 & Oversold 30 reference lines */}
              <line x1={padding} y1={subHeight * 0.3} x2={svgWidth - padding} y2={subHeight * 0.3} stroke="#FF1744" strokeDasharray="2 2" opacity="0.6" />
              <line x1={padding} y1={subHeight * 0.7} x2={svgWidth - padding} y2={subHeight * 0.7} stroke="#00E676" strokeDasharray="2 2" opacity="0.6" />
              {/* RSI level indicator bar */}
              <circle cx={padding + (svgWidth - padding * 2) * (indicators.rsi_14 / 100)} cy={subHeight * (1 - indicators.rsi_14 / 100)} r="4" fill="#00F0FF" />
            </g>
          )}

          {/* MACD Subchart if enabled */}
          {showMACD && indicators && (
            <g transform={`translate(0, ${mainHeight + (showRSI ? subHeight : 0)})`}>
              <rect x={padding} y={0} width={svgWidth - padding * 2} height={subHeight} fill="#0B0E14" opacity="0.8" />
              <text x={padding + 5} y={15} fill="#FF9100" fontSize="10" fontWeight="bold">
                MACD (12,26,9) Hist: {indicators.macd_histogram}
              </text>
              <line x1={padding} y1={subHeight / 2} x2={svgWidth - padding} y2={subHeight / 2} stroke="#1E2638" />
              {/* MACD Histogram indicator bar */}
              <rect
                x={svgWidth / 2 - 20}
                y={indicators.macd_histogram >= 0 ? subHeight / 2 - Math.min(25, indicators.macd_histogram * 500) : subHeight / 2}
                width="40"
                height={Math.max(2, Math.min(25, Math.abs(indicators.macd_histogram) * 500))}
                fill={indicators.macd_histogram >= 0 ? "#00E676" : "#FF1744"}
                rx="2"
              />
            </g>
          )}
        </svg>
      </div>
    </div>
  );
}
