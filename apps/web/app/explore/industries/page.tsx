import type { Metadata } from "next";
import { ScatterPlot } from "../../../components/ScatterPlot";
import { StabilityBars } from "../../../components/StabilityBars";
import { loadBtosRpsTriangulation } from "../../../lib/btosRpsTriangulation";
import { latestCommonPeriod, loadEntityNames, loadObservations, wideEntityRows } from "../../../lib/data";
import { loadLongitudinalDiagnostics } from "../../../lib/longitudinal";

export const metadata: Metadata = { title: "Industry explorer" };

export default async function IndustriesPage() {
  const [rows, longitudinal, names, triangulation] = await Promise.all([
    loadObservations(),
    loadLongitudinalDiagnostics(),
    loadEntityNames("industry"),
    loadBtosRpsTriangulation(),
  ]);
  const metrics = ["adoption_work", "assisted_hours_share"];
  const period = latestCommonPeriod(rows, "industry", metrics);
  const wide = period ? wideEntityRows(rows, "industry", period, metrics) : [];
  const data = wide.map((row) => ({
    entity: names.get(row.entityId) ?? row.entityId,
    x: row.values.adoption_work,
    y: row.values.assisted_hours_share,
  }));
  const crossSourceData = triangulation.pairs
    .filter((row) => row.included_primary)
    .map((row) => ({
      entity: row.entity_name,
      x: row.btos_estimate_pct,
      y: row.rps_adoption_work_pct,
    }));

  const rank = longitudinal.rank_stability.industry;
  const dominance = longitudinal.rank_stability_dominance.industry;
  const quarters = Object.entries(longitudinal.quarter_diagnostics.industry);
  const industryHBeatsAWaves = quarters.filter(([, d]) => d.r2_S_H > d.r2_S_A).length;

  return (
    <main>
      <p className="eyebrow">Industry evidence</p>
      <h1>Industry explorer</h1>
      <p className="lede">
        Employer-reported AI use and worker-reported GenAI adoption show a substantial cross-sector
        association, while the worker-side longitudinal evidence shows that adoption ranks are more
        persistent than workflow penetration.
      </p>

      <section className="section" aria-labelledby="cross-source-triangulation">
        <h2 id="cross-source-triangulation">Two different measures, one sector pattern</h2>
        <p>
          The preregistered primary comparison uses every published, non-suppressed BTOS sector with
          primary crosswalk comparability and the corresponding Q2 2026 RPS industry observation.
        </p>
        <div className="metric-row" aria-label="Primary BTOS and RPS triangulation summary">
          <div className="metric">
            <span>Primary sectors</span>
            <strong>{triangulation.primary.n}</strong>
            <div>Unweighted sector pairs</div>
          </div>
          <div className="metric">
            <span>Spearman rank correlation</span>
            <strong>{triangulation.primary.spearman_rho.toFixed(3)}</strong>
            <div>Descriptive cross-sector concordance</div>
          </div>
          <div className="metric">
            <span>Pearson correlation</span>
            <strong>{triangulation.primary.pearson_r.toFixed(3)}</strong>
            <div>Descriptive linear association</div>
          </div>
        </div>

        <div className="callout" id="btos-rps-measurement-boundary">
          <p className="callout-label">Measurement boundary</p>
          <p>
            BTOS measures the share of responding employer businesses reporting AI use in any business
            function during the last two weeks. RPS measures the share of employed adults in an industry
            reporting use of Generative AI for their job. Their units, denominators, technology scope,
            and reference periods differ. The correlations describe sector-level concordance only; they
            are not percentage-point gaps, construct equivalence, productivity estimates, or causal effects.
          </p>
        </div>

        <ScatterPlot
          data={crossSourceData}
          xLabel="BTOS business AI use (%)"
          yLabel="RPS worker GenAI adoption (%)"
        />

        <div className="comparison-grid">
          <div className="comparison-card">
            <h3>Primary comparison</h3>
            <dl>
              <div><dt>Sectors</dt><dd>{triangulation.primary.n}</dd></div>
              <div><dt>Spearman ρ</dt><dd>{triangulation.primary.spearman_rho.toFixed(3)}</dd></div>
              <div><dt>Pearson r</dt><dd>{triangulation.primary.pearson_r.toFixed(3)}</dd></div>
            </dl>
            <p>Primary-comparability sectors only; no imputation of suppressed BTOS values.</p>
          </div>
          <div className="comparison-card">
            <h3>Expanded sensitivity</h3>
            <dl>
              <div><dt>Sectors</dt><dd>{triangulation.expanded_sensitivity.n}</dd></div>
              <div><dt>Spearman ρ</dt><dd>{triangulation.expanded_sensitivity.spearman_rho.toFixed(3)}</dd></div>
              <div><dt>Pearson r</dt><dd>{triangulation.expanded_sensitivity.pearson_r.toFixed(3)}</dd></div>
            </dl>
            <p>
              Adds Transportation and Warehousing, Finance and Insurance, and Other Services as
              limited-comparability sectors. This sensitivity does not replace the primary result.
            </p>
          </div>
        </div>
        <p className="note">
          Management of Companies and Enterprises is excluded because its BTOS estimate is suppressed.
          Agriculture remains suppressed in the limited-comparability tier. Public Administration has no
          BTOS counterpart, and BTOS unclassified multi-sector businesses are not redistributed.
        </p>
      </section>

      <section className="section" aria-labelledby="industry-stability">
        <h2 id="industry-stability">Worker-side rank stability</h2>
        <StabilityBars
          title="Industry rank persistence: median Spearman correlation across quarter pairs"
          bars={[
            { label: "Adoption", value: rank.A.median_pairwise },
            { label: "Assisted hours", value: rank.H.median_pairwise },
            { label: "Reported savings", value: rank.S.median_pairwise },
          ]}
        />
        <p className="note">
          Adoption ranks are more stable than assisted-hours ranks in
          {` ${dominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${dominance.quarter_pairs} `}
          possible quarter-pair comparisons. These diagnostics use RPS only and are separate from the
          BTOS-RPS comparison above.
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
        <h2 id="industry-cross-section">Latest audited worker-side cross-section</h2>
        {period && data.length > 0 ? (
          <>
            <p><strong>{period}</strong> · each point is an RPS industry group.</p>
            <ScatterPlot data={data} xLabel="Work adoption (%)" yLabel="Work hours assisted (%)" />
          </>
        ) : (
          <div className="callout">
            <p className="callout-label">Derived-only mode</p>
            <p>
              The bounded public industry view is unavailable in this build. The longitudinal derived
              diagnostics remain available without exposing the historical subgroup source panel.
            </p>
          </div>
        )}
      </section>

      <section className="section" aria-labelledby="industry-boundary">
        <h2 id="industry-boundary">Interpretive boundary</h2>
        <p className="note">
          These are aggregate cross-sectional diagnostics. No residual, regression, or cross-source
          correlation is interpreted as efficiency, productivity, organizational quality, or a causal effect.
        </p>
      </section>
    </main>
  );
}
