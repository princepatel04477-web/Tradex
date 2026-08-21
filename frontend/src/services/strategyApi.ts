/** API client for the Forex Top-Down Confluence Toolkit. */

import {
  Analysis,
  AOIScan,
  BridgeStatus,
  CandleSeries,
  EMAState,
  JournalEditResponse,
  JournalEntry,
  JournalStats,
  JournalWeek,
  PairExplainer,
  Reference,
  RiskTable,
  Scenario,
  SessionClock,
  SetupReview,
  Structure,
  TradePlan,
  WeeklyPace,
} from "../types/strategy";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    // FastAPI puts the reason in `detail` - surface it instead of a bare status.
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {
      /* response had no JSON body */
    }
    throw new Error(detail);
  }

  return res.json();
}

export interface TradePlanInput {
  symbol: string;
  direction: "buy" | "sell";
  entry: number;
  stop_loss: number;
  account_size: number;
  take_profit?: number | null;
  risk_pct_override?: number | null;
  quote_to_account_rate?: number | null;
}

export const strategyApi = {
  // -- data -----------------------------------------------------------
  scenarios: () => request<Scenario[]>("/strategy/scenarios"),

  candles: (scenario: string, timeframe: string, limit = 300) =>
    request<CandleSeries>(
      `/strategy/candles/${scenario}/${timeframe}?limit=${limit}`
    ),

  candlesCsvUrl: (scenario: string, timeframe: string) =>
    `${API_BASE}/strategy/candles/${scenario}/${timeframe}/csv`,

  // -- the full top-down pass ------------------------------------------
  analysis: (scenario: string, accountSize = 10000, entryTimeframe = "1H") =>
    request<Analysis>(
      `/strategy/analysis/${scenario}?account_size=${accountSize}` +
        `&entry_timeframe=${entryTimeframe}`
    ),

  analyseUploaded: (payload: {
    symbol: string;
    csv_by_timeframe: Record<string, string>;
    account_size?: number;
    entry_timeframe?: string;
  }) =>
    request<Analysis>("/strategy/analyse", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // -- individual modules ----------------------------------------------
  structure: (scenario: string, timeframe: string) =>
    request<Structure>(`/strategy/structure/${scenario}/${timeframe}`),

  aoi: (scenario: string, timeframe: string) =>
    request<AOIScan>(`/strategy/aoi/${scenario}/${timeframe}`),

  ema: (scenario: string, timeframe: string, period = 50) =>
    request<EMAState>(`/strategy/ema/${scenario}/${timeframe}?period=${period}`),

  sessions: () => request<SessionClock>("/strategy/sessions"),

  // -- risk -------------------------------------------------------------
  riskTable: () => request<RiskTable>("/strategy/risk/table"),

  tradePlan: (input: TradePlanInput) =>
    request<TradePlan>("/strategy/risk/plan", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  // -- reference --------------------------------------------------------
  reference: () => request<Reference>("/strategy/reference"),

  explainPair: (symbol: string, rate?: number) =>
    request<PairExplainer>(
      `/strategy/reference/pairs/${symbol}${rate ? `?rate=${rate}` : ""}`
    ),

  // -- journal ----------------------------------------------------------
  journal: () => request<JournalEntry[]>("/strategy/journal"),

  logTrade: (payload: Record<string, unknown>) =>
    request<JournalEntry>("/strategy/journal", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  closeTrade: (id: string, exitPrice: number, pnl?: number) =>
    request<JournalEntry>(`/strategy/journal/${id}/close`, {
      method: "POST",
      body: JSON.stringify({ exit_price: exitPrice, pnl: pnl ?? null }),
    }),

  editLevels: (
    id: string,
    payload: {
      entry?: number;
      stop_loss?: number;
      take_profit?: number;
      acknowledge_set_and_forget?: boolean;
    }
  ) =>
    request<JournalEditResponse>(`/strategy/journal/${id}/levels`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteTrade: (id: string) =>
    request<{ message: string }>(`/strategy/journal/${id}`, { method: "DELETE" }),

  journalWeeks: () => request<JournalWeek[]>("/strategy/journal/weeks"),

  journalStats: () => request<JournalStats>("/strategy/journal/stats"),

  pace: () => request<WeeklyPace>("/strategy/pace"),

  // -- optional LLM second opinion ---------------------------------------
  reviewStatus: () => request<BridgeStatus>("/strategy/review/status"),

  review: (scenario: string, accountSize = 10000, entryTimeframe = "1H") =>
    request<SetupReview>(
      `/strategy/review/${scenario}?account_size=${accountSize}` +
        `&entry_timeframe=${entryTimeframe}`
    ),
};
