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
  const crossLevelAlignedQuarters = Object.values(longitudinal.cross_level_comparison).filter(
    (row) =>
      row.occupation_minus_industry_pearson_A_H > 0 &&
      row.occupation_minus_industry_spearman_A_H > 0,
  ).length;

  return (
    <main>
      <section className="hero hero-compact" aria-labelledby="occupation-title">
        <p className="eyebrow">{periods.length}-wave evidence</p>
        <h1 id="occupation-title">Occupation explorer</h1>
        <p className="lede">
          Across all {crossLevelAlignedQuarters} of {periods.length} audited waves, adoption and assisted
          working time align more tightly across occupations than across industries.
        </p>
      </section>

      <section className="section explorer-section" aria-labelledby="occupation-cross-section">
        <p className="eyebrow">Current structure</p>
        <h2 id="occupation-cross-section">Adoption and assisted time move together across occupations.</h2>
        {period && data.length > 0 ? (
          <>
            <p><strong>{period}</strong> · each point is a major RPS occupation group.</p>
            <ScatterPlot data={data} xLabel="Work adoption (%)" yLabel="Work hours assisted (%)" />
          </>
        ) : (
          <div className="callout">
            <p className="callout-label">Public aggregate view</p>
            <p>
              This build excludes the bounded public occupation cross-section. Longitudinal derived
              diagnostics remain available through the promoted release.
            </p>
          </div>
        )}
      </section>

      <section className="section explorer-section" aria-labelledby="occupation-persistence">
        <p className="eyebrow">Across waves</p>
        <h2 id="occupation-persistence">Adoption persists and tracks reported savings more consistently.</h2>

        <div className="evidence-facts" aria-label="Occupation longitudinal evidence summary">
          <div className="evidence-fact">
            <span>Rank-stability comparisons</span>
            <strong>{dominance.adoption_rank_corr_gt_assisted_hours_rank_corr}/{dominance.quarter_pairs}</strong>
            <p>Adoption exceeds assisted-hours persistence</p>
          </div>
          <div className="evidence-fact">
            <span>Savings regressions</span>
            <strong>{occupationABeatsHWaves}/{periods.length}</strong>
            <p>Waves where adoption has the higher univariate R²</p>
          </div>
          <div className="evidence-fact">
            <span>Leave-one-out checks</span>
            <strong>{occupationLooABeatsH}</strong>
            <p>Checks where adoption has the higher univariate R²</p>
          </div>
        </div>

        <StabilityBars
          title="Occupation rank persistence: median Spearman correlation across quarter pairs"
          bars={[
            { label: "Adoption", value: rank.A.median_pairwise },
            { label: "Assisted hours", value: rank.H.median_pairwise },
            { label: "Reported savings", value: rank.S.median_pairwise },
          ]}
        />

        <details className="technical-disclosure">
          <summary>Quarter-by-quarter occupation diagnostics</summary>
          <div className="technical-disclosure-body">
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
          </div>
        </details>

        <p className="note">
          These aggregate occupation patterns summarize major task bundles. Individual worker responses,
          employer policies, and causal productivity effects require microdata or separate identification.
        </p>
      </section>
    </main>
  );
}
