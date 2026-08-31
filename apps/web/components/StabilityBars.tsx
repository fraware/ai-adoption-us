type Bar = {
  label: string;
  value: number;
  note?: string;
};

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}

export function StabilityBars({
  title,
  bars,
}: {
  title: string;
  bars: Bar[];
}) {
  return (
    <figure className="stability-figure" aria-label={title}>
      <figcaption>{title}</figcaption>
      <div className="stability-bars">
        {bars.map((bar) => (
          <div className="stability-row" key={bar.label}>
            <div className="stability-label">
              <span>{bar.label}</span>
              <strong>{bar.value.toFixed(2)}</strong>
            </div>
            <div className="stability-track" aria-hidden="true">
              <span style={{ width: `${clamp01(bar.value) * 100}%` }} />
            </div>
            {bar.note ? <small>{bar.note}</small> : null}
          </div>
        ))}
      </div>
    </figure>
  );
}
