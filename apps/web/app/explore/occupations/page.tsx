import type { Metadata } from "next";
import { ScatterPlot } from "../../../components/ScatterPlot";
import { StabilityBars } from "../../../components/StabilityBars";
import { latestCommonPeriod, loadEntityNames, loadObservations, wideEntityRows } from "../../../lib/data";
import { loadLongitudinalDiagnostics } from "../../../lib/longitudinal";

export const metadata: Metadata = { title: "Occupation explorer" };

export default async function OccupationsPage() {
  const [rows, longitudinal, names] = await Promise.all([
    loadObservations(),
    loadLongitudinalDiagnostics(),
    loadEntityNames("occupation"),
  ]);
  const metrics = ["adoption_work", "assisted_hours_share"];
  const period = latestCommonPeriod(rows, "occupation", metrics);
  const wide = period ? wideEntityRows(rows, "occupation", period, metrics) : [];
  const data = wide.map((row) => ({
    entity: names.get(row.entityId) ?? row.entityId,
    x: row.values.adoption_work,
    y: row.values.assisted_hours_share,
  }));

  const periods = longitudinal.input_scope.periods;
  const rank = longitudinal.rank_stability.occupation;
  const dominance = longitudinal.rank_stability_dominance.occupation;
  const quarters = Object.entries(longitudinal.quarter_diagnostics.occupation);
  const occupationABeatsHWaves = quarters.filter(([, d]) => d.r2_S_A > d.r2_S_H).length;
  const occupationLooABeatsH = quarters.reduce((total, [, d]) => total + d.loo_A_beats_H, 0);

  return (
    <main>
      <p className="eyebrow">{periods.length}-wave evidence</p>
      <h1>Occupation explorer</h1>
      <p className="lede">
        Occupations are bundles of tasks, not proxies for firms. Across all {periods.length} audited waves,
        the aggregate relationship between occupation adoption and assisted working time is tighter than
        the corresponding relationship across industries.
      </p>

      <section className="section" aria-labelledby="occupation-stability">
        <h2 id="occupation-stability">Rank stability</h2>
        <StabilityBars
          title="Occupation rank persistence: median Spearman correlation across quarter pairs"
          bars={[
            { label: "Adoption", value: rank.A.median_pairwise },
            { label: "Assisted hours", value: rank.H.median_pairwise },
            { label: "Reported savings", value: rank.S.median_pairwise },
          ]}
        />
        <p className="note">
          Adoption ranks are more stable than assisted-hours ranks in
          {` ${dominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${dominance.quarter_pairs} `}
          possible quarter-pair comparisons.
        </p>
      </section>

      <section className="section" aria-labelledby="occupation-savings">
        <h2 id="occupation-savings">Adoption remains highly informative about reported savings</h2>
        <div className="table-wrap" tabIndex={0} aria-label="Scrollable occupation wave diagnostics table">
          <table>
            <caption>Unweighted cross-occupation descriptive diagnostics by quarter. A = adoption, H = assisted hours, S = reported savings.</caption>
            <thead>
              <tr>
                <th scope="col">Quarter</th>
                <th scope="col">Corr(A, H)</th>
                <th scope="col">R²(S ~ A)</th>
                <th scope="col">R²(S ~ H)</th>
              </tr>
            </thead>
            <tbody>
              {quarters.map(([quarter, d]) => (
                <tr key={quarter}>
                  <th scope="row">{quarter}</th>
                  <td>{d.r_A_H.toFixed(3)}</td>
                  <td>{d.r2_S_A.toFixed(3)}</td>
                  <td>{d.r2_S_H.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="note">
          Adoption has the higher univariate R² for reported savings in {occupationABeatsHWaves} of {periods.length} occupation waves and
          in all {occupationLooABeatsH} leave-one-occupation checks. This is descriptive aggregate
          evidence, not an individual-level behavioral model.
        </p>
      </section>

      <section className="section" aria-labelledby="occupation-cross-section">
        <h2 id="occupation-cross-section">Latest audited cross-section</h2>
        {period && data.length > 0 ? (
          <>
            <p><strong>{period}</strong> · each point is a major RPS occupation group.</p>
            <ScatterPlot data={data} xLabel="Work adoption (%)" yLabel="Work hours assisted (%)" />
          </>
        ) : (
          <div className="callout">
            <p className="callout-label">Derived-only mode</p>
            <p>
              The bounded public occupation view is unavailable in this build. The longitudinal derived
              diagnostics remain available without exposing the historical subgroup source panel.
            </p>
          </div>
        )}
      </section>

      <section className="section" aria-labelledby="occupation-boundary">
        <h2 id="occupation-boundary">Interpretive boundary</h2>
        <p className="note">
          Occupation-level patterns describe major task bundles. They do not identify individual worker
          responses, employer policies, or causal productivity effects.
        </p>
      </section>
    </main>
  );
}
