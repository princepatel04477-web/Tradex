export type AgentName = "technical" | "macro" | "risk" | "synthesis";
export type AgentStatus = "ok" | "insufficient_context" | "failed";
export type EvidenceKind = "indicator" | "document" | "sentiment" | "account" | "calendar" | "volatility" | "timeframe";

export interface AgentEvidence {
  id: string;
  kind: EvidenceKind;
  label: string;
  value: string;
  url?: string | null;
}

export interface AgentClaim {
  text: string;
  stance: number;
  evidence_ids: string[];
}

export interface AgentReport {
  agent: AgentName;
  title: string;
  status: AgentStatus;
  stance: number;
  confidence: number;
  summary: string;
  claims: AgentClaim[];
  evidence: AgentEvidence[];
  model_used: string;
  duration_ms: number;
  error?: string | null;
}

export interface DiscardedClaim {
  agent: AgentName;
  text: string;
  reason: string;
}

export interface AgentVerdict {
  label: string;
  tilt: "bullish" | "bearish" | "neutral";
  score: number;
  confidence: number;
  risk_level: string;
  narrative: string;
  narrative_source: string;
  accepted_claims: number;
  discarded_claims: DiscardedClaim[];
}

export interface AgentRun {
  run_id: string;
  symbol: string;
  timeframe: string;
  verdict: AgentVerdict;
  agents: AgentReport[];
  disclaimer: string;
  total_duration_ms: number;
  created_at: string;
}
