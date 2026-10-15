import type { AIDiagnosis } from '../types/sensors';

interface AIDiagnosisCardProps {
  diagnosis?: AIDiagnosis;
  waitingForReading: boolean;
}

const riskLabels = {
  low: 'Baixo risco',
  moderate: 'Atenção',
  high: 'Risco elevado',
  critical: 'Risco crítico',
  unavailable: 'Indisponível',
};

export function AIDiagnosisCard({ diagnosis, waitingForReading }: AIDiagnosisCardProps) {
  const level = diagnosis?.risk_level ?? 'unavailable';
  const label = diagnosis ? riskLabels[diagnosis.risk_level] : waitingForReading ? 'Aguardando leitura' : 'Indisponível';
  const generatedAt = diagnosis ? new Date(diagnosis.generated_at).toLocaleTimeString('pt-BR') : null;

  return (
    <section className={`ai-diagnosis-card ai-risk-${level} card border-0 mb-4`} aria-labelledby="ai-diagnosis-title">
      <div className="card-body p-4 p-lg-5">
        <div className="d-flex flex-column flex-md-row justify-content-between gap-3">
          <div className="d-flex gap-3">
            <div className="ai-diagnosis-icon" aria-hidden="true">
              <i className="bi bi-robot" />
            </div>
            <div>
              <p className="text-uppercase small fw-semibold mb-1">Análise preventiva</p>
              <h2 id="ai-diagnosis-title" className="h4 fw-bold mb-2">Diagnóstico da IA</h2>
              <p className="mb-0 ai-diagnosis-message">
                {diagnosis?.message ?? (waitingForReading ? 'Aguardando dados dos sensores.' : 'O diagnóstico será exibido quando o modelo estiver disponível.')}
              </p>
            </div>
          </div>
          <div className="ai-risk-badge align-self-start">
            <span className="ai-risk-indicator" aria-hidden="true" />
            {label}
          </div>
        </div>

        {diagnosis && diagnosis.risk_level !== 'unavailable' && (
          <div className="row g-4 mt-3">
            <div className="col-12 col-md-4">
              <span className="small text-body-secondary d-block">Índice estimado de risco</span>
              <strong className="display-6 fw-bold">
                {diagnosis.risk_score === null ? '—' : `${Math.round(diagnosis.risk_score * 100)}%`}
              </strong>
            </div>
            <div className="col-12 col-md-8">
              <span className="small text-body-secondary d-block mb-2">Fatores observados</span>
              <ul className="ai-reasons mb-0">
                {diagnosis.reasons.map((reason) => <li key={reason}>{reason}</li>)}
              </ul>
            </div>
          </div>
        )}

        <div className="d-flex flex-wrap gap-3 mt-4 small text-body-secondary">
          <span><i className="bi bi-info-circle me-1" />Estimativa baseada em temperatura e umidade</span>
          {generatedAt && <span><i className="bi bi-clock me-1" />Atualizado às {generatedAt}</span>}
          {diagnosis?.model_version && <span>Modelo {diagnosis.model_version}</span>}
        </div>
      </div>
    </section>
  );
}
