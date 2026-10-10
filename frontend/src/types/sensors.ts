export interface SensorReading {
  device_id: string;
  uptime_ms: number;
  window_ms: number;
  temperature_c: number | null;
  humidity_pct: number | null;
  dht_ok: boolean;
  vibration_do: 0 | 1;
  vibration_transitions: number;
  received_at: string;
}

export interface LatestReading {
  data: SensorReading | null;
  device_status: 'waiting' | 'online' | 'stale';
  age_seconds: number | null;
}
