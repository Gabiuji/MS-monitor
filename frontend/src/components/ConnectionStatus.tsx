interface ConnectionStatusProps {
  lastUpdate: Date;
}

export function ConnectionStatus({ lastUpdate }: ConnectionStatusProps) {
  return (
    <div className="connection-status d-flex align-items-center gap-2">
      <span className="status-dot" aria-hidden="true" />
      <div>
        <span className="d-block fw-semibold">ESP32 conectado</span>
        <small className="text-body-secondary">
          Atualizado às {lastUpdate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
        </small>
      </div>
    </div>
  );
}
