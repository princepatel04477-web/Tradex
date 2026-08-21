import {
  CurrencyPair, Candle, IndicatorSnapshot, CompositeBias,
  MarketSessionOverview, Position, AccountMetrics, ClosedTrade,
  PerformanceAnalytics, RAGQueryResponse, CurrencySentiment, EconomicEvent
} from "../types/market";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

interface ApiResponseEnvelope<T> {
  data: T | null;
  error: { code: string; message: string; details?: any } | null;
  meta: { request_id: string; timestamp: string; version: string };
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText}`);
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
};
