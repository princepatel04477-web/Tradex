"use client";

import React, { useEffect, useRef, memo } from "react";

interface TradingViewWidgetProps {
  symbol: string;
  interval?: string;
  height?: number | string;
  autosize?: boolean;
}

const SYMBOL_MAP: Record<string, string> = {
  EUR_USD: "FX:EURUSD",
  GBP_USD: "FX:GBPUSD",
  USD_JPY: "FX:USDJPY",
  USD_CHF: "FX:USDCHF",
  AUD_USD: "FX:AUDUSD",
  NZD_USD: "FX:NZDUSD",
  USD_CAD: "FX:USDCAD",
  EUR_GBP: "FX:EURGBP",
  EUR_JPY: "FX:EURJPY",
  GBP_JPY: "FX:GBPJPY",
  AUD_JPY: "FX:AUDJPY",
  EUR_AUD: "FX:EURAUD",
  USD_INR: "FX_IDC:USDINR",
  USD_SGD: "FX_IDC:USDSGD",
  USD_MXN: "FX:USDMXN",
};

const INTERVAL_MAP: Record<string, string> = {
  M1: "1",
  M5: "5",
  M15: "15",
  M30: "30",
  H1: "60",
  H4: "240",
  D1: "D",
  W1: "W",
};

function TradingViewWidget({
  symbol,
  interval = "H1",
  height = 680,
  autosize = true,
}: TradingViewWidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const tvSymbol = SYMBOL_MAP[symbol] || `FX:${symbol.replace("_", "")}`;
  const tvInterval = INTERVAL_MAP[interval] || "60";

  useEffect(() => {
    const currentContainer = containerRef.current;
    if (!currentContainer) return;

    currentContainer.innerHTML = "";

    const widgetDiv = document.createElement("div");
    widgetDiv.className = "tradingview-widget-container__widget";
    widgetDiv.style.height = "100%";
    widgetDiv.style.width = "100%";
    currentContainer.appendChild(widgetDiv);

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      autosize: autosize,
      symbol: tvSymbol,
      interval: tvInterval,
      timezone: "Etc/UTC",
      theme: "dark",
      style: "1",
      locale: "en",
      enable_publishing: false,
      allow_symbol_change: true,
      calendar: false,
      support_host: "https://www.tradingview.com",
      backgroundColor: "rgba(6, 8, 13, 1)",
      gridColor: "rgba(24, 34, 56, 0.4)",
      hide_side_toolbar: false,
      hide_top_toolbar: false,
      withdateranges: true,
      save_image: true,
      studies: ["STD;RSI", "STD;MACD", "STD;SMA"],
      show_popup_button: true,
      popup_width: "1000",
      popup_height: "650",
    });

    currentContainer.appendChild(script);

    return () => {
      if (currentContainer) {
        currentContainer.innerHTML = "";
      }
    };
  }, [tvSymbol, tvInterval, autosize]);

  return (
    <div
      className="tradingview-widget-container rounded-2xl overflow-hidden border border-tradly-border bg-[#06080D] shadow-2xl w-full h-[420px] sm:h-[520px] lg:h-[660px]"
      ref={containerRef}
    >
      <div className="tradingview-widget-container__widget w-full h-full" />
    </div>
  );
}

export default memo(TradingViewWidget);
