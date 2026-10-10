import { useEffect, useState } from 'react';
import type { LatestReading } from '../types/sensors';

const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export function useReadings() {
  const [latest, setLatest] = useState<LatestReading>({ data: null, device_status: 'waiting', age_seconds: null });
  const [apiStatus, setApiStatus] = useState<'loading' | 'online' | 'unreachable'>('loading');
  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    let controller: AbortController;
    async function poll() {
      controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 4000);
      try {
        const response = await fetch(`${apiUrl}/api/readings/latest`, { signal: controller.signal, cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result: LatestReading = await response.json();
        if (!stopped) { setLatest(result); setApiStatus('online'); }
      } catch {
        if (!stopped) setApiStatus('unreachable');
      } finally {
        clearTimeout(timeout);
        if (!stopped) timer = setTimeout(poll, 2500);
      }
    }
    void poll();
    return () => { stopped = true; clearTimeout(timer); controller?.abort(); };
  }, []);
  return { latest, apiStatus };
}
