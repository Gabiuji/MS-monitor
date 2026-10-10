import { ConnectionStatus } from './components/ConnectionStatus';
import { FanCard } from './components/FanCard';
import { SensorCard } from './components/SensorCard';
import { useReadings } from './hooks/useReadings';

export function App() {
  const { latest, apiStatus } = useReadings();
  const sensorData = latest.data;
  const deviceLabel = { waiting: 'Aguardando primeira leitura', online: 'Recebendo dados', stale: 'Dispositivo sem dados recentes' }[latest.device_status];
  const label = apiStatus === 'unreachable' ? 'API inacessível' : apiStatus === 'loading' ? 'Conectando à API' : deviceLabel;
  const outdated = apiStatus !== 'online' || latest.device_status === 'stale';
  const dhtDescription = !sensorData ? 'Aguardando leitura' : !sensorData.dht_ok ? 'Falha na leitura do DHT22' : outdated ? 'Última leitura desatualizada' : 'Leitura do DHT22';
  const format = (value: number | null | undefined, unit: string) => value == null ? '—' : `${value.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} ${unit}`;

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

        <p className={`alert ${outdated || sensorData?.dht_ok === false ? 'alert-warning' : 'alert-info'}`} role="status">
          {label}.{sensorData && outdated ? ' Os valores exibidos correspondem à última leitura recebida.' : ''}
          {sensorData?.dht_ok === false ? ' Falha do DHT22: temperatura e umidade indisponíveis; telemetria de vibração preservada.' : ''}
        </p>
        <section aria-label="Leituras atuais" className="row g-4">
          <div className="col-12 col-md-6 col-xl-3">
            <SensorCard
              accent="temperature"
              icon="bi-thermometer-half"
              label="Temperatura"
              value={format(sensorData?.temperature_c, '°C')}
              description={dhtDescription}
            />
          </div>
          <div className="col-12 col-md-6 col-xl-3">
            <SensorCard
              accent="humidity"
              icon="bi-droplet-half"
              label="Umidade do ar"
              value={format(sensorData?.humidity_pct, '%')}
              description={dhtDescription}
            />
          </div>
          <div className="col-12 col-md-6 col-xl-3">
            <SensorCard
              accent="vibration"
              icon="bi-soundwave"
              label="Vibração"
              value={sensorData ? `${sensorData.vibration_transitions} transições` : '—'}
              description={sensorData ? `Janela: ${format(sensorData.window_ms / 1000, 's')} (${sensorData.window_ms} ms) • DO: ${sensorData.vibration_do}${outdated ? ' • Desatualizada' : ''}` : 'Aguardando telemetria do SW-420'}
            />
          </div>
          <div className="col-12 col-md-6 col-xl-3">
            <FanCard />
          </div>
        </section>

        <section className="row g-4 mt-1">
          <div className="col-12 col-lg-8">
            <div className="card border-0 dashboard-card h-100">
              <div className="card-body p-4">
                <div className="d-flex justify-content-between align-items-center mb-4">
                  <div>
                    <h2 className="h5 fw-bold mb-1">Histórico das leituras</h2>
                    <p className="text-body-secondary small mb-0">Reservado para uma próxima etapa</p>
                  </div>
                  <button className="btn btn-sm btn-light" type="button" disabled>
                    Últimas 24h
                  </button>
                </div>
                <div className="chart-placeholder d-flex align-items-center justify-content-center">
                  <div className="text-center text-body-secondary">
                    <i className="bi bi-bar-chart-line fs-2 d-block mb-2" />
                    <span>Histórico ainda não implementado.</span>
                  </div>
                </div>
              </div>
            </div>
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
