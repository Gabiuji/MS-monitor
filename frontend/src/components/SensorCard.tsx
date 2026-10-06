interface SensorCardProps {
  icon: string;
  label: string;
  value: string;
  description: string;
  accent: 'temperature' | 'humidity' | 'vibration';
}

export function SensorCard({ icon, label, value, description, accent }: SensorCardProps) {
  return (
    <article className={`sensor-card card border-0 h-100 accent-${accent}`}>
      <div className="card-body p-4">
        <div className="d-flex justify-content-between align-items-start">
          <div>
            <span className="sensor-label text-body-secondary">{label}</span>
            <div className="sensor-value mt-2">{value}</div>
          </div>
          <div className="sensor-icon" aria-hidden="true">
            <i className={`bi ${icon}`} />
          </div>
        </div>
        <p className="mb-0 mt-3 text-body-secondary small">{description}</p>
      </div>
    </article>
  );
}
