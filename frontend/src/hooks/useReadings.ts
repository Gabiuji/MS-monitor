import { useEffect, useRef, useState } from 'react';
import type { LatestReading, SensorReading } from '../types/sensors';
import { fetchJson } from '../services/api';
import { mergeHistorySnapshot, mergeReadings } from '../utils/history';

export function useReadings(historyLimit = 300) {
  const [latest, setLatest] = useState<LatestReading>({ data: null, device_status: 'waiting', age_seconds: null });
  const [apiStatus, setApiStatus] = useState<'loading' | 'online' | 'unreachable'>('loading');
  const [history, setHistory] = useState<SensorReading[]>([]);
  const [historyStatus, setHistoryStatus] = useState<'loading' | 'online' | 'unreachable'>('loading');
  const limitRef = useRef(historyLimit);
  limitRef.current = historyLimit;

  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    let controller: AbortController;
    let timeout: ReturnType<typeof setTimeout>;
    async function poll() {
      const started = performance.now();
      controller = new AbortController();
      timeout = setTimeout(() => controller.abort(), 4000);
      try {
        const result = await fetchJson<LatestReading>('/api/readings/latest', controller.signal);
        if (!stopped) {
          setLatest(result);
          setApiStatus('online');
          const reading = result.data;
          if (reading) {
            setHistory(current => mergeReadings(current, [reading], limitRef.current));
          }
        }
      } catch {
        if (!stopped) setApiStatus('unreachable');
      } finally {
        clearTimeout(timeout);
        if (!stopped) timer = setTimeout(poll, Math.max(0, 1000 - (performance.now() - started)));
      }
    }
    void poll();
    return () => { stopped = true; clearTimeout(timer); clearTimeout(timeout); controller?.abort(); };
  }, []);

  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    let timeout: ReturnType<typeof setTimeout>;
    let controller: AbortController;
    setHistory(current => current.slice(-historyLimit));
    async function poll() {
      controller = new AbortController();
      timeout = setTimeout(() => controller.abort(), 4000);
      try {
        const result = await fetchJson<{ data: SensorReading[] }>(`/api/readings?limit=${historyLimit}`, controller.signal);
        if (!stopped) {
          setHistory(current => mergeHistorySnapshot(current, result.data, historyLimit));
          setHistoryStatus('online');
        }
      } catch {
        if (!stopped) setHistoryStatus('unreachable');
      } finally {
        clearTimeout(timeout);
        if (!stopped) timer = setTimeout(poll, 2500);
      }
    }
    void poll();
    return () => { stopped = true; clearTimeout(timer); clearTimeout(timeout); controller?.abort(); };
  }, [historyLimit]);
  return { latest, apiStatus, history, historyStatus };
}
