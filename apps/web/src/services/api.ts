import {
  CurrencyPair, Candle, IndicatorSnapshot, CompositeBias,
  MarketSessionOverview, Position, AccountMetrics, ClosedTrade,
  PerformanceAnalytics, RAGQueryResponse, CurrencySentiment, EconomicEvent
} from "../types/market";
import { BacktestRequest, BacktestRun, BacktestRunSummary, StrategyInfo } from "../types/backtest";
import { AgentRun } from "../types/agents";
import { AlertCreate, AlertNotification, PriceAlert } from "../types/alerts";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 
  (typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8000/api/v1"
    : "https://tradex-api-q7re.onrender.com/api/v1");

interface ApiResponseEnvelope<T> {
  data: T | null;
  error: { code: string; message: string; details?: unknown } | null;
  meta: { request_id: string; timestamp: string; version: string };
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const token =
      typeof window !== "undefined"
        ? sessionStorage.getItem("tradly_session_token") || localStorage.getItem("tradly_token")
        : null;
    const headers: Record<string, string> = {
      ...(options?.headers as Record<string, string> || {}),
    };
    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(url, {
      ...options,
      headers,
    });
    if (!res.ok) {
      if (res.status === 429) {
        throw new Error("Rate limit exceeded. Please slow down and wait a few seconds.");
      }
      let message = `API error ${res.status}: ${res.statusText}`;
      try {
        const errBody: unknown = await res.json();
        if (errBody && typeof errBody === "object" && "error" in errBody) {
          const envErr = (errBody as { error: { message?: string } | null }).error;
          if (envErr?.message) message = envErr.message;
        }
      } catch {
        // Response body was not JSON; keep the status-based message.
      }
      throw new Error(message);
    }
    const json = await res.json();
    // Unwrap { data, error, meta } envelope if present
    if (json && typeof json === "object" && "data" in json && json.data !== undefined) {
      if (json.error) {
        throw new Error(json.error.message || json.error.code || "API Error");
      }
      return json.data as T;
    }
    return json as T;
  } catch (err) {
    console.warn(`Fetch error for ${url}:`, err);
    throw err;
  }
}

export const api = {
  getPairs: () => fetchJSON<CurrencyPair[]>(`${API_BASE}/market/pairs`),
  getPair: (symbol: string) => fetchJSON<CurrencyPair>(`${API_BASE}/market/pairs/${symbol}`),
  getCandles: (symbol: string, timeframe = "H1", limit = 100) =>
    fetchJSON<Candle[]>(`${API_BASE}/market/candles/${symbol}?timeframe=${timeframe}&limit=${limit}`),
  getMarketSessions: () => fetchJSON<MarketSessionOverview>(`${API_BASE}/market/sessions`),
  getIndicators: (symbol: string, timeframe = "H1") =>
    fetchJSON<IndicatorSnapshot>(`${API_BASE}/analysis/indicators/${symbol}?timeframe=${timeframe}`),
  getCompositeBias: (symbol: string, timeframe = "H1") =>
    fetchJSON<CompositeBias>(`${API_BASE}/analysis/bias/${symbol}?timeframe=${timeframe}`),
  
  // Trading
  getAccountMetrics: () => fetchJSON<AccountMetrics>(`${API_BASE}/trading/metrics`),
  getPositions: () => fetchJSON<Position[]>(`${API_BASE}/trading/positions`),
  placeOrder: (data: {
    symbol: string;
    side?: "buy" | "sell";
    direction?: string;
    lot_size: number;
    leverage: number;
    stop_loss?: number;
    take_profit?: number;
    trailing_stop_pips?: number;
  }) => {
    const side = data.side || (data.direction === "buy" ? "buy" : "sell");
    return fetchJSON<Position>(`${API_BASE}/trading/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...data, side })
    });
  },
  closePosition: (positionId: string) =>
    fetchJSON<ClosedTrade>(`${API_BASE}/trading/positions/${positionId}/close`, { method: "POST" }),
  resetAccount: (balance?: number) =>
    fetchJSON<AccountMetrics>(`${API_BASE}/trading/account/reset`, { method: "POST" }),
  getAnalytics: () => fetchJSON<PerformanceAnalytics>(`${API_BASE}/trading/analytics`),
  getClosedTrades: () => fetchJSON<ClosedTrade[]>(`${API_BASE}/trading/trades`),

  // AI & RAG
  queryRAG: (query: string, symbol?: string) =>
    fetchJSON<RAGQueryResponse>(`${API_BASE}/ai/rag/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, symbol })
    }),
  getSentiments: () => fetchJSON<{ currencies: CurrencySentiment[] }>(`${API_BASE}/ai/sentiment`).then(r => r.currencies || r),
  getCalendar: () => fetchJSON<EconomicEvent[]>(`${API_BASE}/ai/calendar`),

  // Backtesting (Month 3)
  getBacktestStrategies: () => fetchJSON<StrategyInfo[]>(`${API_BASE}/backtest/strategies`),
  runBacktest: (req: BacktestRequest) =>
    fetchJSON<BacktestRun>(`${API_BASE}/backtest/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    }),
  getBacktestRuns: () => fetchJSON<BacktestRunSummary[]>(`${API_BASE}/backtest/runs`),
  getBacktestRun: (runId: string) => fetchJSON<BacktestRun>(`${API_BASE}/backtest/runs/${runId}`),

  // Multi-agent analysis (Month 4)
  runAgentAnalysis: (symbol: string, timeframe: string, useLlm = true) =>
    fetchJSON<AgentRun>(`${API_BASE}/agents/analyse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol, timeframe, use_llm: useLlm }),
    }),

  // Alerts (FG-6)
  getAlerts: () => fetchJSON<PriceAlert[]>(`${API_BASE}/alerts`),
  createAlert: (req: AlertCreate) =>
    fetchJSON<PriceAlert>(`${API_BASE}/alerts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    }),
  toggleAlert: (alertId: string) =>
    fetchJSON<PriceAlert>(`${API_BASE}/alerts/${alertId}/toggle`, { method: "POST" }),
  deleteAlert: (alertId: string) =>
    fetchJSON<boolean>(`${API_BASE}/alerts/${alertId}`, { method: "DELETE" }),
  getNotifications: () => fetchJSON<AlertNotification[]>(`${API_BASE}/alerts/notifications`),
};
