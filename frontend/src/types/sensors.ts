export type FanMode = 'automatic' | 'manual';

export interface SensorReading {
  temperature: number;
  humidity: number;
  vibration: number;
  timestamp: Date;
  fanActive: boolean;
  fanMode: FanMode;
}
