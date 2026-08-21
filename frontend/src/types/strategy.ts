/**
 * Types for the Forex Top-Down Confluence Toolkit API.
 * Mirrors backend/app/schemas/strategy.py - keep the two in step.
 */

export type Trend = "bullish" | "bearish" | "undetermined";
export type StructureLabel = "HH" | "HL" | "LH" | "LL";
export type ZoneType = "support" | "resistance";
export type Direction = "buy" | "sell";
export type TriggerStatus = "none" | "broken" | "armed" | "invalidated";

export const TREND_TIMEFRAMES = ["1W", "1D", "4H"] as const;
export const ENTRY_TIMEFRAMES = ["2H", "1H", "30M", "15M"] as const;
/** Every timeframe the engine understands, highest first. Mirrors config.TIMEFRAMES. */
export const ALL_TIMEFRAMES = [
  "1W",
  "1D",
  "4H",
  "2H",
  "1H",
  "30M",
  "15M",
] as const;

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface CandleSeries {
  symbol: string;
  timeframe: string;
  candles: Candle[];
  count: number;
}

export interface SwingPoint {
  index: number;
  time: string;
  price: number;
  kind: "high" | "low";
  label: StructureLabel | null;
  /** True once price closed through the level, or a later CHoCH relabelled it. */
  broken: boolean;
  broken_time: string | null;
  broken_reason: string;
}

export interface ChochEvent {
  index: number;
  time: string;
  close: number;
  broken_level: number;
  broken_label: StructureLabel;
  from_trend: Trend;
  to_trend: Trend;
  description: string;
}

export interface Structure {
  timeframe: string;
  trend: Trend;
  swings: SwingPoint[];
  live_swing_count: number;
  choch_events: ChochEvent[];
  last_valid_hl: SwingPoint | null;
  last_valid_lh: SwingPoint | null;
  last_hh: SwingPoint | null;
  last_ll: SwingPoint | null;
  structural_range: number[] | null;
  candles_analysed: number;
  summary: string;
  snake_trace_price: number | null;
}

export interface SyncVerdict {
  in_sync: boolean;
  rule: string;
  direction: Trend;
  agreeing_timeframes: string[];
  explanation: string;
  rule_is_unconfirmed: boolean;
  rule_note: string;
}

export interface TopDown {
  symbol: string;
  trend_layer: Record<string, Structure>;
  entry_layer: Record<string, Structure>;
  sync: SyncVerdict | null;
  trend_is_your_friend: boolean;
  bias: Trend;
  messages: string[];
}

export interface AOIZone {
  timeframe: string;
  lower: number;
  upper: number;
  mid: number;
  zone_type: ZoneType;
  golden_rule_tag: string;
  touches: number;
  touch_times: string[];
  width_pips: number;
  valid: boolean;
  confidence: number;
  rejection_reasons: string[];
}

export interface AOIScan {
  timeframe: string;
  allowed: boolean;
  zones: AOIZone[];
  rejected: AOIZone[];
  message: string;
  has_valid_aoi: boolean;
}

export interface Trigger {
  status: TriggerStatus;
  direction: Direction | null;
  level: number | null;
  level_label: string;
  break_time: string | null;
  break_close: number | null;
  retest_time: string | null;
  retest_price: number | null;
  candles_to_retest: number | null;
  is_armed: boolean;
  notes: string[];
}

export interface PatternMatch {
  name: string;
  index: number;
  time: string;
  timeframe: string;
  bias: Trend;
  strength: number;
  weighted_strength: number;
  at_aoi: boolean;
  detail: string;
}

export interface HeadShoulders {
  kind: "head_and_shoulders" | "inverse_head_and_shoulders";
  timeframe: string;
  bias: Trend;
  left_shoulder: SwingPoint;
  head: SwingPoint;
  right_shoulder: SwingPoint;
  neckline_start: SwingPoint;
  neckline_end: SwingPoint;
  neckline_broken: boolean;
  neckline_retested: boolean;
  target_price: number | null;
  is_valid_signal: boolean;
  early_entry_risk: boolean;
  notes: string[];
}

export interface EMAState {
  period: number;
  value: number | null;
  price: number;
  alignment: Trend;
  slope: number;
  series: (number | null)[];
}

export interface Confluence {
  core_pillars: Record<string, boolean>;
  core_complete: boolean;
  missing_core: string[];
  expanded: Record<string, boolean>;
  score: number;
  max_score: number;
  low_risk_high_reward: boolean;
  reasons: string[];
}

export interface TradePlan {
  symbol: string;
  direction: Direction;
  entry: number;
  stop_loss: number;
  take_profit: number;
  stop_distance_pips: number;
  target_distance_pips: number;
  reward_risk: number;
  account_size: number;
  risk_pct: number;
  risk_amount: number;
  pip_value_per_lot: number;
  position_size_lots: number;
  position_size_units: number;
  meets_min_rr: boolean;
  meets_target_rr: boolean;
  risk_tier_unconfirmed: boolean;
  warnings: string[];
}

export interface SessionWindow {
  name: string;
  open_ist: string;
  close_ist: string;
  open_utc: string;
  close_utc: string;
  is_active: boolean;
  crosses_midnight: boolean;
  minutes_until_open: number | null;
  minutes_until_close: number | null;
}

export interface SessionClock {
  now_utc: string;
  now_ist: string;
  sessions: SessionWindow[];
  active_sessions: string[];
  overlap: string | null;
  in_primary_window: boolean;
  primary_window_ist: string;
  minutes_until_primary_open: number | null;
  minutes_until_primary_close: number | null;
  message: string;
}

export interface WeeklyPace {
  week_start: string;
  week_end: string;
  trades_this_week: number;
  limit: number;
  remaining: number;
  at_limit: boolean;
  message: string;
}

export interface Analysis {
  symbol: string;
  generated_at: string;
  entry_timeframe: string;
  current_price: number;
  bias: Trend;
  tradeable: boolean;
  top_down: TopDown;
  aoi_scans: Record<string, AOIScan>;
  valid_zones: AOIZone[];
  active_zone: AOIZone | null;
  trigger: Trigger | null;
  patterns: Record<string, PatternMatch[]>;
  actionable_patterns: PatternMatch[];
  head_shoulders: Record<string, HeadShoulders[]>;
  ema: EMAState | null;
  confluence: Confluence | null;
  trade_plan: TradePlan | null;
  session: SessionClock | null;
  weekly_pace: WeeklyPace | null;
  guardrails: string[];
  narrative: string[];
}

export interface Scenario {
  key: string;
  symbol: string;
  title: string;
  description: string;
  demonstrates: string[];
}

export interface BridgeStatus {
  available: boolean;
  package_importable: boolean;
  provider: string;
  model: string;
  api_key_env: string | null;
  api_key_present: boolean;
  reason: string;
  provider_autodetected: boolean;
  provider_explicit: boolean;
}

export interface SetupReview {
  available: boolean;
  symbol: string;
  engine_verdict: string;
  bull_case: string;
  bear_case: string;
  verdict: string;
  key_risks: string[];
  model_used: string;
  reason: string;
  disclaimer: string;
}

export interface RiskTier {
  account_size: number;
  risk_pct_min: number;
  risk_pct_max: number;
  risk_pct_used: number;
  unconfirmed: boolean;
  note: string;
}

export interface RiskTable {
  tiers: RiskTier[];
  min_reward_risk: number;
  target_reward_risk: number;
  max_trades_per_week: number;
  note: string;
}

export interface PairExplainer {
  symbol: string;
  base: string;
  quote: string;
  base_name: string;
  quote_name: string;
  is_major: boolean;
  pip_size: number;
  quote_example: string;
  up_means: string;
  down_means: string;
  buy_when: string;
  sell_when: string;
}

export interface FlaggedItem {
  id: string;
  title: string;
  module: string;
  current_value: string;
  note: string;
}

export interface Reference {
  majors: string[];
  chart_types: string[];
  tools: Record<string, string>[];
  brokers: Record<string, string>[];
  guiding_principle: Record<string, string>;
  golden_rules: string[];
  flagged_for_confirmation: FlaggedItem[];
}

export interface JournalEntry {
  id: string;
  symbol: string;
  direction: Direction;
  placed_at: string;
  week_key: string;
  sync_state: string;
  sync_timeframes: string[];
  aoi_zone: string | null;
  aoi_timeframe: string | null;
  aoi_touches: number;
  patterns: string[];
  confluence_score: number;
  confluence_max: number;
  low_risk_high_reward: boolean;
  entry: number;
  stop_loss: number;
  take_profit: number;
  planned_rr: number;
  position_size_lots: number;
  risk_amount: number;
  outcome: "open" | "win" | "loss" | "breakeven" | "cancelled";
  exit_price: number | null;
  closed_at: string | null;
  realised_rr: number | null;
  pnl: number | null;
  notes: string;
  tags: string[];
  is_placed: boolean;
}

export interface JournalWeek {
  week: string;
  trade_count: number;
  limit: number;
  over_limit: boolean;
  trades: JournalEntry[];
}

export interface JournalStats {
  closed_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  average_rr: number;
  average_confluence: number;
  total_pnl: number;
}

export interface JournalEditResponse {
  entry: JournalEntry;
  notice: string;
  applied: boolean;
}

/** Human labels for the expanded confluence checklist keys. */
export const CHECKLIST_LABELS: Record<string, string> = {
  directional_bias: "Directional bias",
  at_valid_aoi: "At a valid AOI",
  star_pattern: "Morning / Evening Star",
  head_and_shoulders: "Head & Shoulders",
  ema_alignment: "EMA alignment",
  break_and_retest: "Break & retest",
  daily_trend_confirmation: "Daily trend confirmation",
  engulfing: "Engulfing candle",
  h4_head_and_shoulders: "4H Head & Shoulders",
  hs_neckline_break_retest: "H&S neckline break & retest",
};

/** Human labels for the mandatory core pillars. */
export const CORE_LABELS: Record<string, string> = {
  trend_confirmed: "Trend confirmed",
  aoi_valid: "AOI valid",
  entry_trigger_confirmed: "Entry trigger (break & retest)",
  pattern_confirmed: "Pattern confirmed",
};
