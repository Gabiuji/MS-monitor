export function FanCard() {
  return (
    <article className="sensor-card fan-card card border-0 h-100">
      <div className="card-body p-4">
        <div className="d-flex justify-content-between align-items-start">
          <div>
            <span className="sensor-label text-body-secondary">Ventilação</span>
            <div className="sensor-value mt-2">
              Não avaliado
            </div>
          </div>
          <div className="sensor-icon" aria-hidden="true">
            <i className="bi bi-fan" />
          </div>
        </div>
        <div className="d-flex align-items-center justify-content-between mt-3">
          <span className="text-body-secondary small">
            IA ainda não integrada. Sem controle de motor nesta etapa.
          </span>
        </div>
      </div>
    </article>
  );
}
