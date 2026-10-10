interface ConnectionStatusProps {
  label: string;
  online: boolean;
  lastUpdate?: string;
}

export function ConnectionStatus({ label, online, lastUpdate }: ConnectionStatusProps) {
  return (
    <div className="connection-status d-flex align-items-center gap-2" role="status">
      <span className={`status-dot ${online ? '' : 'status-dot-offline'}`} aria-hidden="true" />
      <div>
        <span className="d-block fw-semibold">{label}</span>
        <small className="text-body-secondary">
          {lastUpdate ? `Última leitura: ${new Date(lastUpdate).toLocaleString('pt-BR')}` : 'Nenhuma leitura recebida'}
        </small>
      </div>
    </div>
  );
}
