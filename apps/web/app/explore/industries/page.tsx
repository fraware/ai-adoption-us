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
      <section className="hero hero-compact" aria-labelledby="industry-title">
        <p className="eyebrow">Industry evidence</p>
        <h1 id="industry-title">Industry explorer</h1>
        <p className="lede">
          Industry data expose variation beyond occupation mix and add a separate firm-side view of current
          AI use through BTOS.
        </p>
      </section>

      <section className="section explorer-section" aria-labelledby="cross-source-triangulation">
        <p className="eyebrow">Firm and worker views</p>
        <h2 id="cross-source-triangulation">Worker adoption and firm AI use show substantial sector concordance</h2>
        <p>
          The primary comparison pairs Q2 2026 RPS worker adoption with BTOS sectors that satisfy the
          preregistered crosswalk and suppression rules.
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
            BTOS reports the share of responding employer businesses using AI in any business function over
            the prior two weeks. RPS reports the share of employed adults in an industry using generative AI
            for work. The correlation is sector-level descriptive concordance across distinct constructs.
            Percentage-point gaps, productivity interpretation, and causal interpretation require evidence
            beyond this comparison.
          </p>
        </div>

        <ScatterPlot
          data={crossSourceData}
          xLabel="BTOS business AI use (%)"
          yLabel="RPS worker GenAI adoption (%)"
        />

        <details className="technical-disclosure">
          <summary>Sensitivity and crosswalk detail</summary>
          <div className="technical-disclosure-body">
            <div className="comparison-grid">
              <div className="comparison-card">
                <h3>Primary comparison</h3>
                <dl>
                  <div><dt>Sectors</dt><dd>{triangulation.primary.n}</dd></div>
                  <div><dt>Spearman ρ</dt><dd>{triangulation.primary.spearman_rho.toFixed(3)}</dd></div>
                  <div><dt>Pearson r</dt><dd>{triangulation.primary.pearson_r.toFixed(3)}</dd></div>
                </dl>
                <p>Primary-comparability sectors; suppressed BTOS values remain excluded.</p>
              </div>
              <div className="comparison-card">
                <h3>Expanded sensitivity</h3>
                <dl>
                  <div><dt>Sectors</dt><dd>{triangulation.expanded_sensitivity.n}</dd></div>
                  <div><dt>Spearman ρ</dt><dd>{triangulation.expanded_sensitivity.spearman_rho.toFixed(3)}</dd></div>
                  <div><dt>Pearson r</dt><dd>{triangulation.expanded_sensitivity.pearson_r.toFixed(3)}</dd></div>
                </dl>
                <p>
                  Adds Transportation and Warehousing, Finance and Insurance, and Other Services under the
                  preregistered limited-comparability tier.
                </p>
              </div>
            </div>
            <p className="note">
              Suppression rules leave Management of Companies and Enterprises outside the primary analysis
              and Agriculture outside the limited-comparability sensitivity. Public Administration lacks a
              BTOS counterpart; unclassified multi-sector businesses stay unallocated.
            </p>
          </div>
        </details>
      </section>

      <section className="section explorer-section" aria-labelledby="industry-structure">
        <p className="eyebrow">Worker-side structure</p>
        <h2 id="industry-structure">Adoption is more persistent than assisted working time.</h2>

        {period && data.length > 0 ? (
          <>
            <p><strong>{period}</strong> · each point is an RPS industry group.</p>
            <ScatterPlot data={data} xLabel="Work adoption (%)" yLabel="Work hours assisted (%)" />
          </>
        ) : (
          <div className="callout">
            <p className="callout-label">Public aggregate view</p>
            <p>
              This build excludes the bounded public industry cross-section. Longitudinal derived
              diagnostics remain available through the promoted release.
            </p>
          </div>
        )}

        <StabilityBars
          title="Industry rank persistence: median Spearman correlation across quarter pairs"
          bars={[
            { label: "Adoption", value: rank.A.median_pairwise },
            { label: "Assisted hours", value: rank.H.median_pairwise },
            { label: "Reported savings", value: rank.S.median_pairwise },
          ]}
        />
        <p className="note">
          Adoption rankings exceed assisted-hours rank stability in
          {` ${dominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${dominance.quarter_pairs} `}
          quarter-pair comparisons. Assisted hours has the higher univariate R² for reported savings in
          {` ${industryHBeatsAWaves} of ${longitudinal.input_scope.periods.length} `}waves.
        </p>

        <details className="technical-disclosure">
          <summary>Quarter-by-quarter savings diagnostics</summary>
          <div className="technical-disclosure-body">
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
          </div>
        </details>

        <p className="note">
          These aggregate cross-sectional diagnostics describe association and persistence. Efficiency,
          productivity, organizational quality, and causal effects require separate identification.
        </p>
      </section>
    </main>
  );
}
