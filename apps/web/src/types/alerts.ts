export type AlertType =
  | "price_above"
  | "price_below"
  | "rsi_overbought"
  | "rsi_oversold"
  | "macd_crossover"
  | "bb_squeeze";

export interface AlertCreate {
  symbol: string;
  alert_type: AlertType;
  threshold_value: number;
  timeframe: string;
  note?: string;
  email_notification: boolean;
}

export interface PriceAlert {
  id: string;
  user_id: string;
  symbol: string;
  alert_type: AlertType;
  threshold_value: number;
  timeframe?: string | null;
  note?: string | null;
  is_active: boolean;
  is_triggered: boolean;
  created_at: string;
  last_triggered_at?: string | null;
}

export interface AlertNotification {
  id: string;
  user_id: string;
  alert_id?: string | null;
  title: string;
  message: string;
  channel: "in_app" | "email";
  is_read: boolean;
  created_at: string;
}
