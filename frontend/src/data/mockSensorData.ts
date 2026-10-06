import type { SensorReading } from '../types/sensors';

export const mockSensorData: SensorReading = {
  temperature: 29.2,
  humidity: 72.4,
  vibration: 0.08,
  timestamp: new Date(),
  fanActive: true,
  fanMode: 'automatic',
};
