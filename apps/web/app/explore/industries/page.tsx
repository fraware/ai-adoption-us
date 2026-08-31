import type { Metadata } from "next";
import { ScatterPlot } from "../../../components/ScatterPlot";
import { StabilityBars } from "../../../components/StabilityBars";
import { latestCommonPeriod, loadEntityNames, loadObservations, wideEntityRows } from "../../../lib/data";
import { loadLongitudinalDiagnostics } from "../../../lib/longitudinal";

export const metadata: Metadata = { title: "Industry explorer" };

export default async function IndustriesPage() {
  const [rows, longitudinal, names] = await Promise.all([
    loadObservations(),
    loadLongitudinalDiagnostics(),
    loadEntityNames("industry"),
  ]);
  const metrics = ["adoption_work", "assisted_hours_share"];
  const period = latestCommonPeriod(rows, "industry", metrics);
  const wide = period ? wideEntityRows(rows, "industry", period, metrics) : [];
  const data = wide.map((row) => ({
    entity: names.get(row.entityId) ?? row.entityId,
    x: row.values.adoption_work,
    y: row.values.assisted_hours_share,
  }));

  const rank = longitudinal.rank_stability.industry;
  const quarters = Object.entries(longitudinal.quarter_diagnostics.industry);
  const industryHBeatsAWaves = quarters.filter(([, d]) => d.r2_S_H > d.r2_S_A).length;

  return (
    <main>
      <p className="eyebrow">Five-wave evidence</p>
      <h1>Industry explorer</h1>
      <p className="lede">
        Industry adoption is relatively persistent. Workflow penetration is less stable, and its
        descriptive relationship with reported savings changes by wave.
      </p>

      <section className="section" aria-labelledby="industry-stability">
        <h2 id="industry-stability">Rank stability</h2>
        <StabilityBars
          title="Industry rank persistence: median Spearman correlation across quarter pairs"
          bars={[
            { label: "Adoption", value: rank.A.median_pairwise },
            { label: "Assisted hours", value: rank.H.median_pairwise },
            { label: "Reported savings", value: rank.S.median_pairwise },
          ]}
        />
        <p className="note">
          Adoption ranks are more stable than assisted-hours ranks in all
          {` ${longitudinal.rank_stability_dominance.industry.quarter_pairs} `}
          possible quarter-pair comparisons.
        </p>
      </section>

      <section className="section" aria-labelledby="industry-savings">
        <h2 id="industry-savings">The savings relationship changes by wave</h2>
        <div className="table-wrap" tabIndex={0} aria-label="Scrollable industry wave diagnostics table">
          <table>
            <caption>Unweighted cross-industry descriptive regressions by quarter. A = adoption, H = assisted hours, S = reported savings.</caption>
            <thead>
              <tr>
                <th scope="col">Quarter</th>
                <th scope="col">R²(S ~ A)</th>
                <th scope="col">R²(S ~ H)</th>
                <th scope="col">Higher</th>
              </tr>
            </thead>
            <tbody>
              {quarters.map(([quarter, d]) => (
                <tr key={quarter}>
                  <th scope="row">{quarter}</th>
                  <td>{d.r2_S_A.toFixed(3)}</td>
                  <td>{d.r2_S_H.toFixed(3)}</td>
                  <td>{d.r2_S_H > d.r2_S_A ? "Assisted hours" : "Adoption"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="note">
          Assisted hours has the higher univariate R² in {industryHBeatsAWaves} of {longitudinal.input_scope.periods.length} waves.
          The Q2 2026 ordering is therefore a reproduced cross-section, not a stable structural law.
        </p>
      </section>

      <section className="section" aria-labelledby="industry-cross-section">
        <h2 id="industry-cross-section">Latest audited cross-section</h2>
        {period && data.length > 0 ? (
          <>
            <p><strong>{period}</strong> · each point is an RPS industry group.</p>
            <ScatterPlot data={data} xLabel="Work adoption (%)" yLabel="Work hours assisted (%)" />
          </>
        ) : (
          <div className="callout">
            <p className="callout-label">Derived-only mode</p>
            <p>
              Raw industry observations are unavailable in this public configuration. The five-wave
              diagnostics above remain available because they are derived publication artifacts.
            </p>
          </div>
        )}
      </section>

      <section className="section" aria-labelledby="industry-boundary">
        <h2 id="industry-boundary">Interpretive boundary</h2>
        <p className="note">
          These are aggregate cross-sectional diagnostics. No residual or regression is interpreted as
          efficiency, productivity, organizational quality, or a causal effect.
        </p>
      </section>
    </main>
  );
}
