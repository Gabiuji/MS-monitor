import { useState } from 'react';
import { ConnectionStatus } from './components/ConnectionStatus';
import { FanCard } from './components/FanCard';
import { SensorCard } from './components/SensorCard';
import { mockSensorData } from './data/mockSensorData';

export function App() {
  const [sensorData, setSensorData] = useState(mockSensorData);

  function toggleFan() {
    setSensorData((current) => ({
      ...current,
      fanActive: !current.fanActive,
      fanMode: 'manual',
      timestamp: new Date(),
    }));
  }

  return (
    <div className="app-shell min-vh-100">
      <nav className="navbar navbar-expand-lg bg-white border-bottom">
        <div className="container py-2">
          <a className="navbar-brand d-flex align-items-center gap-2 fw-bold text-primary" href="/">
            <span className="brand-mark"><i className="bi bi-activity" /></span>
            MS-Monitor
          </a>
          <ConnectionStatus lastUpdate={sensorData.timestamp} />
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

        <section aria-label="Leituras atuais" className="row g-4">
          <div className="col-12 col-md-6 col-xl-3">
            <SensorCard
              accent="temperature"
              icon="bi-thermometer-half"
              label="Temperatura"
              value={`${sensorData.temperature.toFixed(1)} °C`}
              description="Dentro da faixa monitorada"
            />
          </div>
          <div className="col-12 col-md-6 col-xl-3">
            <SensorCard
              accent="humidity"
              icon="bi-droplet-half"
              label="Umidade do ar"
              value={`${sensorData.humidity.toFixed(1)}%`}
              description="Nível atual no interior do silo"
            />
          </div>
          <div className="col-12 col-md-6 col-xl-3">
            <SensorCard
              accent="vibration"
              icon="bi-soundwave"
              label="Vibração"
              value={`${sensorData.vibration.toFixed(2)} g`}
              description="Sem comportamento anormal"
            />
          </div>
          <div className="col-12 col-md-6 col-xl-3">
            <FanCard active={sensorData.fanActive} mode={sensorData.fanMode} onToggle={toggleFan} />
          </div>
        </section>

        <section className="row g-4 mt-1">
          <div className="col-12 col-lg-8">
            <div className="card border-0 dashboard-card h-100">
              <div className="card-body p-4">
                <div className="d-flex justify-content-between align-items-center mb-4">
                  <div>
                    <h2 className="h5 fw-bold mb-1">Histórico das leituras</h2>
                    <p className="text-body-secondary small mb-0">Próxima etapa: dados da API</p>
                  </div>
                  <button className="btn btn-sm btn-light" type="button" disabled>
                    Últimas 24h
                  </button>
                </div>
                <div className="chart-placeholder d-flex align-items-center justify-content-center">
                  <div className="text-center text-body-secondary">
                    <i className="bi bi-bar-chart-line fs-2 d-block mb-2" />
                    <span>O gráfico histórico será conectado à API.</span>
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
                  <span><i className="bi bi-wifi me-2 text-success" />Conectividade</span>
                  <strong className="text-success">Normal</strong>
                </div>
                <div className="system-status-item">
                  <span><i className="bi bi-cpu me-2 text-primary" />ESP32</span>
                  <strong className="text-success">Online</strong>
                </div>
                <div className="system-status-item">
                  <span><i className="bi bi-shield-check me-2 text-success" />Alertas</span>
                  <strong className="text-success">Nenhum</strong>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
