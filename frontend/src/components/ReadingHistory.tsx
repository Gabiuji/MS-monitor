import { useState } from 'react';
import type { SensorReading } from '../types/sensors';
import { apiUrl } from '../services/api';

type Metric = 'temperature' | 'humidity' | 'vibration';
interface Props {
  readings: SensorReading[];
  status: 'loading' | 'online' | 'unreachable';
  outdated: boolean;
  limit: number;
  onLimitChange: (limit: number) => void;
}

const metrics: Record<Metric, { label: string; unit: string; series: { field: 'temperature_c' | 'probe_temperature_c' | 'humidity_pct' | 'vibration_transitions'; label: string; color: string }[] }> = {
  temperature: { label: 'Temperaturas', unit: '°C', series: [
    { field: 'temperature_c', label: 'Ar', color: '#e03131' },
    { field: 'probe_temperature_c', label: 'Sonda', color: '#f08c00' },
  ] },
  humidity: { label: 'Umidade', unit: '%', series: [{ field: 'humidity_pct', label: 'Umidade do ar', color: '#1971c2' }] },
  vibration: { label: 'Vibração', unit: 'transições', series: [{ field: 'vibration_transitions', label: 'Transições por janela', color: '#7048e8' }] },
};
const number = (value: number) => value.toLocaleString('pt-BR', { maximumFractionDigits: 2 });
const time = (value: number) => new Date(value).toLocaleTimeString('pt-BR');

function measurement(reading: SensorReading, field: typeof metrics[Metric]['series'][number]['field']) {
  if ((field === 'temperature_c' || field === 'humidity_pct') && !reading.dht_ok) return null;
  if (field === 'probe_temperature_c' && reading.probe_ok !== true) return null;
  return reading[field] ?? null;
}

export function ReadingHistory({ readings, status, outdated, limit, onLimitChange }: Props) {
  const [metric, setMetric] = useState<Metric>('temperature');
  const config = metrics[metric];
  const values = readings.flatMap(reading => config.series.map(series => measurement(reading, series.field)))
    .filter((value): value is number => value != null);
  const start = readings.length ? Date.parse(readings[0].received_at) : 0;
  const end = readings.length ? Date.parse(readings[readings.length - 1].received_at) : 0;
  const minimum = values.length ? Math.min(...values) : 0;
  const maximum = values.length ? Math.max(...values) : 1;
  const padding = Math.max((maximum - minimum) * 0.1, 1);
  const low = metric === 'humidity' ? 0 : metric === 'vibration' ? 0 : minimum - padding;
  const high = metric === 'humidity' ? 100 : maximum + padding;
  const x = (timestamp: number) => start === end ? 380 : 64 + (timestamp - start) / (end - start) * 632;
  const y = (value: number) => 230 - (value - low) / (high - low) * 200;

  return (
    <div className="card border-0 dashboard-card h-100">
      <div className="card-body p-4">
        <div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-3">
          <div>
            <h2 className="h5 fw-bold mb-1">Histórico das leituras</h2>
            <p className="text-body-secondary small mb-0">{readings.length} leituras • Horário de recebimento</p>
          </div>
          <a className="btn btn-sm btn-outline-primary" href={`${apiUrl}/api/readings/export`}>
            <i className="bi bi-download me-2" aria-hidden="true" />Baixar CSV completo
          </a>
        </div>
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
          <div className="btn-group btn-group-sm" role="group" aria-label="Medição do histórico">
            {(Object.keys(metrics) as Metric[]).map(key => (
              <button key={key} type="button" className={`btn ${metric === key ? 'btn-primary' : 'btn-outline-primary'}`}
                aria-pressed={metric === key} onClick={() => setMetric(key)}>{metrics[key].label}</button>
            ))}
          </div>
          <label className="d-flex align-items-center gap-2 small text-body-secondary">
            Exibir
            <select className="form-select form-select-sm w-auto" value={limit} onChange={event => onLimitChange(Number(event.target.value))}>
              {[100, 300, 1000, 3600].map(value => <option key={value} value={value}>Últimas {value}</option>)}
            </select>
          </label>
        </div>
        {status === 'unreachable' && <p className="text-warning-emphasis small" role="status">Não foi possível atualizar o histórico. Os dados exibidos podem estar desatualizados.</p>}
        {status === 'online' && outdated && readings.length > 0 && <p className="text-warning-emphasis small" role="status">Sem leituras recentes. Exibindo os dados já coletados.</p>}
        {!readings.length ? (
          <div className="history-empty text-body-secondary" role="status">
            {status === 'loading' ? 'Carregando histórico…' : status === 'unreachable' ? 'Histórico indisponível.' : 'Aguardando leituras para iniciar o gráfico.'}
          </div>
        ) : !values.length ? (
          <div className="history-empty text-body-secondary">Sem leituras válidas para esta medição no período.</div>
        ) : (
          <>
            <svg className="history-chart" viewBox="0 0 720 274" role="img" aria-label={`Histórico de ${config.label.toLowerCase()} em ${config.unit}`}>
              <title>{config.label} — {new Date(start).toLocaleString('pt-BR')} a {new Date(end).toLocaleString('pt-BR')}</title>
              <text x="64" y="16" className="history-axis">{config.unit}</text>
              {[0, 0.25, 0.5, 0.75, 1].map(fraction => {
                const value = low + (high - low) * fraction;
                return <g key={fraction}>
                  <line x1="64" x2="696" y1={y(value)} y2={y(value)} stroke="#edf0f2" />
                  <text x="56" y={y(value) + 4} textAnchor="end" className="history-axis">{number(value)}</text>
                </g>;
              })}
              {config.series.map(series => {
                let drawing = false;
                let previous: SensorReading | undefined;
                const segments: { x: number; y: number; title: string }[][] = [];
                for (const reading of readings) {
                  const value = measurement(reading, series.field);
                  const timestamp = Date.parse(reading.received_at);
                  if (value == null) { drawing = false; continue; }
                  if (!drawing || (previous && (timestamp - Date.parse(previous.received_at) >= 10000 || previous.device_id !== reading.device_id))) segments.push([]);
                  segments[segments.length - 1].push({ x: x(timestamp), y: y(value), title: `${series.label}: ${number(value)} ${config.unit} • ${new Date(timestamp).toLocaleString('pt-BR')} • Janela: ${reading.window_ms} ms` });
                  drawing = true;
                  previous = reading;
                }
                return <g key={series.field}>
                  <path d={segments.map(segment => segment.map((point, index) => `${index ? 'L' : 'M'}${point.x},${point.y}`).join(' ')).join(' ')}
                    fill="none" stroke={series.color} strokeWidth="2" vectorEffect="non-scaling-stroke" />
                  {segments.map((segment, index) => {
                    const point = segment[segment.length - 1];
                    return <circle key={index} cx={point.x} cy={point.y} r="3" fill={series.color}><title>{point.title}</title></circle>;
                  })}
                </g>;
              })}
              {(start === end ? [0] : [0, 0.5, 1]).map(fraction => (
                <text key={fraction} x={x(start + (end - start) * fraction)} y="256" textAnchor={start === end ? 'middle' : fraction === 0 ? 'start' : fraction === 1 ? 'end' : 'middle'} className="history-axis">{time(start + (end - start) * fraction)}</text>
              ))}
            </svg>
            <div className="d-flex flex-wrap gap-3 small" aria-label="Legenda do gráfico">
              {config.series.map(series => <span key={series.field} className="d-inline-flex align-items-center gap-2"><span className="history-legend-dot" style={{ backgroundColor: series.color }} />{series.label}</span>)}
            </div>
            <p className="small text-body-secondary mt-2 mb-0">{new Date(start).toLocaleString('pt-BR')} — {new Date(end).toLocaleString('pt-BR')}</p>
          </>
        )}
        {metric === 'vibration' && <p className="small text-body-secondary mt-2 mb-0">Contagem de transições por janela medida; não representa intensidade ou RPM. A duração de cada janela está no CSV.</p>}
      </div>
    </div>
  );
}
