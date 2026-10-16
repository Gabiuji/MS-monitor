import { useState } from 'react';
import { ConnectionStatus } from './components/ConnectionStatus';
import { FanCard } from './components/FanCard';
import { AIDiagnosisCard } from './components/AIDiagnosisCard';
import { SensorCard } from './components/SensorCard';
import { useReadings } from './hooks/useReadings';
import { ReadingHistory } from './components/ReadingHistory';

export function App() {
  const [historyLimit, setHistoryLimit] = useState(300);
  const { latest, apiStatus, history, historyStatus } = useReadings(historyLimit);
  const sensorData = latest.data;
  const deviceLabel = { waiting: 'Aguardando primeira leitura', online: 'Recebendo dados', stale: 'Dispositivo sem dados recentes' }[latest.device_status];
  const label = apiStatus === 'unreachable' ? 'API inacessível' : apiStatus === 'loading' ? 'Conectando à API' : deviceLabel;
  const outdated = apiStatus !== 'online' || latest.device_status === 'stale';
  const dhtDescription = !sensorData ? 'Aguardando leitura' : !sensorData.dht_ok ? 'Falha na leitura do DHT22' : outdated ? 'Última leitura desatualizada' : 'Leitura do DHT22';
  const format = (value: number | null | undefined, unit: string, digits = 1) => value == null ? '—' : `${value.toLocaleString('pt-BR', { minimumFractionDigits: digits, maximumFractionDigits: digits })} ${unit}`;
  const probeValue = sensorData?.probe_ok === false ? 'Falha na leitura'
    : sensorData?.probe_ok == null || sensorData.probe_temperature_c == null ? 'Sem leitura da sonda'
    : format(sensorData.probe_temperature_c, '°C', 2);

  return (
    <div className="app-shell min-vh-100">
      <nav className="navbar navbar-expand-lg bg-white border-bottom">
        <div className="container py-2">
          <a className="navbar-brand d-flex align-items-center gap-2 fw-bold text-primary" href="/">
            <span className="brand-mark"><i className="bi bi-activity" /></span>
            MS-Monitor
          </a>
          <ConnectionStatus label={label} online={apiStatus === 'online' && latest.device_status === 'online'} lastUpdate={sensorData?.received_at} />
        </div>
      </nav>

      <main className="container py-5">
        <header className="mb-4">
          <p className="text-uppercase text-primary fw-semibold small mb-2">Mini-silo conectado</p>
          <h1 className="display-6 fw-bold mb-2">Monitoramento dos sensores</h1>
          <p className="text-body-secondary mb-0">
            Acompanhe as condições do silo em tempo real.
          </p>
        </header>

        <p className={`alert ${outdated || sensorData?.dht_ok === false || sensorData?.probe_ok === false ? 'alert-warning' : 'alert-info'}`} role="status">
          {label}.{sensorData && outdated ? ' Os valores exibidos correspondem à última leitura recebida.' : ''}
          {sensorData?.dht_ok === false ? ' Falha do DHT22: temperatura e umidade indisponíveis; telemetria de vibração preservada.' : ''}
          {sensorData?.probe_ok === false ? ' Falha na leitura da sonda MAX6675.' : ''}
        </p>
        <AIDiagnosisCard diagnosis={latest.diagnosis} waitingForReading={!sensorData} outdated={outdated} />
        <section aria-label="Leituras atuais" className="row g-4">
          <div className="col-12 col-md-6 col-xl">
            <SensorCard
              accent="temperature"
              icon="bi-thermometer-half"
              label="Temperatura do ar"
              value={format(sensorData?.temperature_c, '°C')}
              description={dhtDescription}
            />
          </div>
          <div className="col-12 col-md-6 col-xl">
            <SensorCard
              accent="temperature"
              icon="bi-thermometer"
              label="Temperatura da sonda"
              value={probeValue}
              description={sensorData && outdated ? 'Última leitura desatualizada • Termopar tipo K / MAX6675' : 'Temperatura no ponto da sonda • Termopar tipo K / MAX6675'}
            />
          </div>
          <div className="col-12 col-md-6 col-xl">
            <SensorCard
              accent="humidity"
              icon="bi-droplet-half"
              label="Umidade do ar"
              value={format(sensorData?.humidity_pct, '%')}
              description={dhtDescription}
            />
          </div>
          <div className="col-12 col-md-6 col-xl">
            <SensorCard
              accent="vibration"
              icon="bi-soundwave"
              label="Vibração"
              value={sensorData ? `${sensorData.vibration_transitions} transições` : '—'}
              description={sensorData ? `Janela: ${format(sensorData.window_ms / 1000, 's')} (${sensorData.window_ms} ms) • DO: ${sensorData.vibration_do}${outdated ? ' • Desatualizada' : ''}` : 'Aguardando telemetria do SW-420'}
            />
          </div>
          <div className="col-12 col-md-6 col-xl">
            <FanCard />
          </div>
        </section>

        <section className="row g-4 mt-1">
          <div className="col-12 col-lg-8">
            <ReadingHistory readings={history} status={historyStatus} outdated={outdated || latest.device_status === 'waiting'}
              limit={historyLimit} onLimitChange={setHistoryLimit} />
          </div>
          <div className="col-12 col-lg-4">
            <div className="card border-0 dashboard-card h-100">
              <div className="card-body p-4">
                <h2 className="h5 fw-bold mb-4">Status do sistema</h2>
                <div className="system-status-item">
                  <span><i className="bi bi-wifi me-2" />API</span>
                  <strong>{apiStatus === 'online' ? 'Acessível' : apiStatus === 'loading' ? 'Conectando' : 'Inacessível'}</strong>
                </div>
                <div className="system-status-item">
                  <span><i className="bi bi-cpu me-2 text-primary" />ESP32</span>
                  <strong>{apiStatus === 'online' ? deviceLabel : 'Estado desconhecido'}</strong>
                </div>
                <div className="system-status-item">
                  <span><i className="bi bi-thermometer me-2" />DHT22</span>
                  <strong>{!sensorData ? 'Aguardando' : sensorData.dht_ok ? 'Leitura válida' : 'Falha'}</strong>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
