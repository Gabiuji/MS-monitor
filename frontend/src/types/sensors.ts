export interface SensorReading {
  device_id: string;
  uptime_ms: number;
  window_ms: number;
  temperature_c: number | null;
  humidity_pct: number | null;
  dht_ok: boolean;
  probe_temperature_c?: number | null;
  probe_ok?: boolean | null;
  vibration_do: 0 | 1;
  vibration_transitions: number;
  received_at: string;
}

export interface LatestReading {
  data: SensorReading | null;
  device_status: 'waiting' | 'online' | 'stale';
  age_seconds: number | null;
  diagnosis?: AIDiagnosis;
}

export type AIRiskLevel = 'low' | 'moderate' | 'high' | 'critical' | 'unavailable';

export interface AIDiagnosis {
  risk_level: AIRiskLevel;
  risk_score: number | null;
  confidence: number | null;
  message: string;
  reasons: string[];
  model_version: string | null;
  generated_at: string;
}
