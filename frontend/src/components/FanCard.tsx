import type { FanMode } from '../types/sensors';

interface FanCardProps {
  active: boolean;
  mode: FanMode;
  onToggle: () => void;
}

export function FanCard({ active, mode, onToggle }: FanCardProps) {
  return (
    <article className="sensor-card fan-card card border-0 h-100">
      <div className="card-body p-4">
        <div className="d-flex justify-content-between align-items-start">
          <div>
            <span className="sensor-label text-body-secondary">Ventilação</span>
            <div className={`sensor-value mt-2 ${active ? 'text-success' : 'text-body'}`}>
              {active ? 'Ativa' : 'Inativa'}
            </div>
          </div>
          <div className={`sensor-icon ${active ? 'fan-active' : ''}`} aria-hidden="true">
            <i className="bi bi-fan" />
          </div>
        </div>
        <div className="d-flex align-items-center justify-content-between mt-3">
          <span className="text-body-secondary small">
            Modo {mode === 'automatic' ? 'automático' : 'manual'}
          </span>
          <button className="btn btn-sm btn-outline-success" type="button" onClick={onToggle}>
            {active ? 'Desativar' : 'Ativar'}
          </button>
        </div>
      </div>
    </article>
  );
}
