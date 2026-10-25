import type { SensorReading } from '../types/sensors';

export function readingKey(reading: SensorReading) {
  return `${reading.device_id}:${reading.received_at}:${reading.uptime_ms}`;
}

export function mergeReadings(current: SensorReading[], incoming: SensorReading[], limit: number) {
  const unique = new Map<string, SensorReading>();
  for (const reading of [...current, ...incoming]) {
    if (Number.isFinite(Date.parse(reading.received_at))) unique.set(readingKey(reading), reading);
  }
  return [...unique.values()]
    .sort((left, right) => Date.parse(left.received_at) - Date.parse(right.received_at))
    .slice(-limit);
}

export function mergeHistorySnapshot(current: SensorReading[], snapshot: SensorReading[], limit: number) {
  const ordered = mergeReadings([], snapshot, limit);
  if (!ordered.length) return mergeReadings([], current, limit);
  const last = Date.parse(ordered[ordered.length - 1].received_at);
  // A slow historical response must not replace live readings received meanwhile.
  const newer = current.filter(reading => Date.parse(reading.received_at) >= last);
  return mergeReadings(ordered, newer, limit);
}

export function isNewSession(previous: SensorReading, current: SensorReading) {
  return Date.parse(current.received_at) - Date.parse(previous.received_at) >= 10000
    || previous.device_id !== current.device_id || current.uptime_ms < previous.uptime_ms;
}

export function currentSession(readings: SensorReading[]) {
  for (let index = readings.length - 1; index > 0; index--) {
    if (isNewSession(readings[index - 1], readings[index])) return readings.slice(index);
  }
  return readings;
}
