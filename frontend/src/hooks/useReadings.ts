import { useEffect, useState } from 'react';
import type { LatestReading, SensorReading } from '../types/sensors';
import { fetchJson } from '../services/api';

export function useReadings(historyLimit = 300) {
  const [latest, setLatest] = useState<LatestReading>({ data: null, device_status: 'waiting', age_seconds: null });
  const [apiStatus, setApiStatus] = useState<'loading' | 'online' | 'unreachable'>('loading');
  const [history, setHistory] = useState<SensorReading[]>([]);
  const [historyStatus, setHistoryStatus] = useState<'loading' | 'online' | 'unreachable'>('loading');
  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    let controller: AbortController;
    async function poll() {
      controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 4000);
      const [current, records] = await Promise.allSettled([
        fetchJson<LatestReading>('/api/readings/latest', controller.signal),
        fetchJson<{ data: SensorReading[] }>(`/api/readings?limit=${historyLimit}`, controller.signal),
      ]);
      clearTimeout(timeout);
      if (!stopped) {
        if (current.status === 'fulfilled') { setLatest(current.value); setApiStatus('online'); }
        else setApiStatus('unreachable');
        if (records.status === 'fulfilled') { setHistory(records.value.data); setHistoryStatus('online'); }
        else setHistoryStatus('unreachable');
        timer = setTimeout(poll, 2500);
      }
    }
    void poll();
    return () => { stopped = true; clearTimeout(timer); controller?.abort(); };
  }, [historyLimit]);
  return { latest, apiStatus, history, historyStatus };
}
