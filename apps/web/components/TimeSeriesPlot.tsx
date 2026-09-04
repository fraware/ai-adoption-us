"use client";

import * as Plot from "@observablehq/plot";
import { useEffect, useRef } from "react";

type Point = {
  date: string;
  value: number;
  metric: string;
  label: string;
};

export function TimeSeriesPlot({ data }: { data: Point[] }) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = container.current;
    if (!host || data.length === 0) return;

    const parsed = data.map((row) => ({ ...row, date: new Date(`${row.date}T00:00:00Z`) }));
    let plot: ReturnType<typeof Plot.plot> | null = null;
    let lastWidth = 0;
    const render = () => {
      const width = Math.min(host.clientWidth || 900, 1100);
      if (width < 280 || width === lastWidth) return;
      lastWidth = width;
      const height = Math.max(340, Math.min(470, Math.round(width * 0.48)));
      plot?.remove();
      const nextPlot = Plot.plot({
        width,
        height,
        marginLeft: 52,
        marginBottom: 50,
        x: { label: null, grid: false },
        y: { label: "Percent", domain: [0, 100], grid: true },
        color: { legend: true },
        marks: [
          Plot.ruleY([0]),
          Plot.lineY(parsed, { x: "date", y: "value", stroke: "label", strokeWidth: 2 }),
          Plot.dot(parsed, { x: "date", y: "value", fill: "label", r: 3, tip: true }),
        ],
      });
      plot = nextPlot;
      host.replaceChildren(nextPlot);
    };

    render();
    const observer = new ResizeObserver(render);
    observer.observe(host);
    return () => {
      observer.disconnect();
      plot?.remove();
    };
  }, [data]);

  const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date) || a.label.localeCompare(b.label));

  return (
    <>
      <figure className="chart-frame" aria-label="National generative AI work-use time series">
        <div className="chart-canvas" ref={container} aria-hidden="true" />
        <figcaption>
          National work-use constructs are plotted separately; each measure has its own denominator and interpretation.
        </figcaption>
      </figure>
      <details className="data-details">
        <summary>View chart data</summary>
        <div className="table-wrap" tabIndex={0} aria-label="Scrollable national time-series data table">
          <table>
            <caption>National values plotted above.</caption>
            <thead>
              <tr><th scope="col">Date</th><th scope="col">Measure</th><th scope="col">Value</th></tr>
            </thead>
            <tbody>
              {sorted.map((row) => (
                <tr key={`${row.date}-${row.metric}`}>
                  <th scope="row">{row.date}</th>
                  <td>{row.label}</td>
                  <td>{row.value.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
