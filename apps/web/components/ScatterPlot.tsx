"use client";

import * as Plot from "@observablehq/plot";
import { useEffect, useRef } from "react";

type Datum = {
  entity: string;
  x: number;
  y: number;
};

export function ScatterPlot({
  data,
  xLabel,
  yLabel,
}: {
  data: Datum[];
  xLabel: string;
  yLabel: string;
}) {
  const container = useRef<HTMLDivElement>(null);
  const selected = new Set<string>();
  [...data].sort((a, b) => b.x - a.x).slice(0, 4).forEach((row) => selected.add(row.entity));
  [...data].sort((a, b) => b.y - a.y).slice(0, 4).forEach((row) => selected.add(row.entity));
  const labelled = data.filter((row) => selected.has(row.entity));

  useEffect(() => {
    const host = container.current;
    if (!host || data.length === 0) return;

    let plot: ReturnType<typeof Plot.plot> | null = null;
    let lastWidth = 0;
    const render = () => {
      const width = Math.min(host.clientWidth || 900, 1100);
      if (width < 280 || width === lastWidth) return;
      lastWidth = width;
      const height = Math.max(360, Math.min(520, Math.round(width * 0.55)));
      plot?.remove();
      const nextPlot = Plot.plot({
        width,
        height,
        marginLeft: 62,
        marginBottom: 55,
        x: { label: xLabel, grid: true },
        y: { label: yLabel, grid: true },
        marks: [
          Plot.dot(data, { x: "x", y: "y", r: 5, tip: true, title: "entity" }),
          Plot.text(labelled, {
            x: "x",
            y: "y",
            text: "entity",
            dx: 7,
            textAnchor: "start",
            fontSize: 10,
          }),
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
  }, [data, labelled, xLabel, yLabel]);

  const sorted = [...data].sort((a, b) => b.x - a.x);

  return (
    <>
      <figure className="chart-frame" aria-label={`${yLabel} versus ${xLabel}`}>
        <div className="chart-canvas" ref={container} aria-hidden="true" />
        <figcaption>
          Each point is one subgroup. Labels identify the highest-adoption and highest-assisted-hours
          groups; exact values are available in the table below.
        </figcaption>
      </figure>
      <details className="data-details">
        <summary>View chart data</summary>
        <div className="table-wrap" tabIndex={0} aria-label="Scrollable chart data table">
          <table>
            <caption>Values plotted above, ordered by {xLabel.toLowerCase()}.</caption>
            <thead>
              <tr>
                <th scope="col">Group</th>
                <th scope="col">{xLabel}</th>
                <th scope="col">{yLabel}</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((row) => (
                <tr key={row.entity}>
                  <th scope="row">{row.entity}</th>
                  <td>{row.x.toFixed(1)}%</td>
                  <td>{row.y.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
