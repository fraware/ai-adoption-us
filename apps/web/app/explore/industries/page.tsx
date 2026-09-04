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
        Industries reveal a second layer of workplace AI: worker adoption and assisted time move together
        less tightly than they do across occupations, and firm-side BTOS data provide an independent sector
        lens.
      </p>

      <section className="section" aria-labelledby="cross-source-triangulation">
        <h2 id="cross-source-triangulation">Worker adoption and firm AI use move together across sectors</h2>
        <p>
          The preregistered primary comparison pairs Q2 2026 RPS industry adoption with BTOS sectors that
          meet the primary crosswalk and suppression rules.
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
          Suppression rules leave Management of Companies and Enterprises outside the primary analysis and
          Agriculture outside the limited-comparability sensitivity. Public Administration lacks a BTOS
          counterpart; unclassified multi-sector businesses stay unallocated.
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
          Across RPS waves, adoption rankings exceed assisted-hours rank stability in
          {` ${dominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${dominance.quarter_pairs} `}
          quarter-pair comparisons. These diagnostics use the worker-side RPS series.
        </p>
      </section>

      <section className="section" aria-labelledby="industry-savings">
        <h2 id="industry-savings">Industry savings relationships shift across waves</h2>
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
          Q2 2026 fits that recurrent pattern, with the ordering changing across the full audited window.
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
            <p className="callout-label">Public aggregate view</p>
            <p>
              This build excludes the bounded public industry cross-section. Longitudinal derived
              diagnostics remain available through the promoted release.
            </p>
          </div>
        )}
      </section>

      <section className="section" aria-labelledby="industry-boundary">
        <h2 id="industry-boundary">Interpretive boundary</h2>
        <p className="note">
          These are aggregate cross-sectional diagnostics. Efficiency, productivity, organizational
          quality, and causal effects require separate identification.
        </p>
      </section>
    </main>
  );
}
