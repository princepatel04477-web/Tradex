export interface CurrencyPair {
  symbol: string;
  name: string;
  base_currency: string;
  quote_currency: string;
  pip_decimal_places: number;
  category: string;
  pip_size: number;
  bid: number;
  ask: number;
  spread_pips: number;
  change_24h_pct: number;
  high_24h: number;
  low_24h: number;
  timestamp: string;
}

export interface Candle {
  symbol: string;
  timeframe: string;
  open_time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorSnapshot {
  symbol: string;
  timeframe: string;
  rsi_14: number;
  macd_line: number;
  macd_signal: number;
  macd_histogram: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
  atr_14: number;
  ema_9: number;
  ema_21: number;
  ema_50: number;
  sma_200: number;
  fib_levels: Record<string, number>;
  macd_crossover?: string | null;
  rsi_condition?: string | null;
  bb_squeeze: boolean;
  timestamp: string;
}

export interface CompositeBias {
  symbol: string;
  timeframe: string;
  bias: string;
  score: number;
  indicator_contributions: Record<string, number>;
  reasons: string[];
  timestamp: string;
}

export interface MarketSession {
  name: string;
  is_active: boolean;
  open_utc: string;
  close_utc: string;
  description: string;
}

export interface MarketSessionOverview {
  sessions: MarketSession[];
  active_overlap?: string | null;
  current_utc_time: string;
}

export interface Position {
  id: string;
  symbol: string;
  direction: string;
  lot_size: number;
  units: number;
  leverage: number;
  entry_price: number;
  current_price: number;
  stop_loss?: number | null;
  take_profit?: number | null;
  trailing_stop_pips?: number | null;
  unrealized_pnl: number;
  unrealized_pnl_pips: number;
  required_margin: number;
  opened_at: string;
  status: string;
}

export interface AccountMetrics {
  balance: number;
  equity: number;
  used_margin: number;
  free_margin: number;
  margin_level_pct: number;
  floating_pnl: number;
  open_positions_count: number;
}

export interface ClosedTrade {
  id: string;
  symbol: string;
  direction: string;
  lot_size: number;
  units: number;
  entry_price: number;
  exit_price: number;
  realized_pnl: number;
  realized_pnl_pips: number;
  opened_at: string;
  closed_at: string;
  close_reason: string;
  notes?: string;
  tags: string[];
}

export interface PerformanceAnalytics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  total_realized_pnl: number;
  profit_factor: number;
  avg_win: number;
  avg_loss: number;
  avg_risk_reward_ratio: number;
  max_drawdown_amount: number;
  max_drawdown_pct: number;
  equity_curve: Array<{ timestamp: string; balance: number; equity: number }>;
  pair_performance: Array<{ symbol: string; trades: number; pnl: number; wins: number }>;
  session_performance: Array<{ session: string; trades: number; pnl: number }>;
}

export interface Citation {
  id: string;
  title: string;
  source: string;
  url?: string;
  published_at: string;
  snippet: string;
  relevance_score: number;
}

export interface RAGQueryResponse {
  query: string;
  answer: string;
  citations: Citation[];
  is_insufficient_context: boolean;
  disclaimer: string;
  model_used: string;
  timestamp: string;
}

export interface CurrencySentiment {
  currency: string;
  score: number;
  label: string;
  article_count: number;
  top_headlines: string[];
}

export interface EconomicEvent {
  id: string;
  title: string;
  country: string;
  currency: string;
  scheduled_at: string;
  impact: string;
  previous: string;
  consensus: string;
  actual?: string;
  ai_briefing?: string;
  historical_pip_volatility?: string;
}
