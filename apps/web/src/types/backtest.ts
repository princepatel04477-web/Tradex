export type StrategyName = "ema_crossover" | "rsi_reversion" | "macd_momentum";
export type BacktestTimeframe = "M30" | "H1" | "H4" | "D1";

export interface BacktestRequest {
  symbol: string;
  timeframe: BacktestTimeframe;
  strategy: StrategyName;
  bars: number;
  initial_balance: number;
  risk_per_trade_pct: number;
  sl_atr_mult: number;
  tp_atr_mult: number;
  fast_period: number;
  slow_period: number;
  rsi_period: number;
  rsi_lower: number;
  rsi_upper: number;
  allow_short: boolean;
}

export interface StrategyInfo {
  id: StrategyName;
  name: string;
  description: string;
  parameters: string[];
}

export interface BacktestTrade {
  trade_no: number;
  direction: "long" | "short";
  entry_time: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  units: number;
  stop_loss: number;
  take_profit: number;
  pnl: number;
  pnl_pips: number;
  r_multiple: number;
  exit_reason: string;
  bars_held: number;
}

export interface BacktestEquityPoint {
  time: string;
  equity: number;
  drawdown_pct: number;
}

export interface BacktestMetrics {
  initial_balance: number;
  final_balance: number;
  net_profit: number;
  total_return_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  profit_factor: number;
  avg_win: number;
  avg_loss: number;
  expectancy: number;
  avg_r_multiple: number;
  max_drawdown_pct: number;
  max_drawdown_amount: number;
  sharpe_ratio: number;
  exposure_pct: number;
  bars_tested: number;
}

export interface BacktestRun {
  run_id: string;
  status: string;
  request: BacktestRequest;
  period_start: string;
  period_end: string;
  spread_pips: number;
  data_source: string;
  runtime_ms: number;
  metrics: BacktestMetrics;
  equity_curve: BacktestEquityPoint[];
  trades: BacktestTrade[];
  created_at: string;
}

export interface BacktestRunSummary {
  run_id: string;
  symbol: string;
  timeframe: string;
  strategy: StrategyName;
  total_trades: number;
  net_profit: number;
  total_return_pct: number;
  win_rate_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  created_at: string;
}
