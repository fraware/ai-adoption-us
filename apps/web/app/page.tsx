import type { Metadata } from "next";
import Link from "next/link";
import { StabilityBars } from "../components/StabilityBars";
import { TimeSeriesPlot } from "../components/TimeSeriesPlot";
import { latestNational, loadObservations } from "../lib/data";
import { loadLongitudinalDiagnostics } from "../lib/longitudinal";

export const metadata: Metadata = {
  title: "From adoption to workflow",
};

const labels: Record<string, string> = {
  adoption_work: "use GenAI for work",
  work_use_last_week: "used it for work last week",
  work_use_daily: "used it every workday",
  assisted_hours_share: "of work hours were AI-assisted",
  reported_time_savings_share: "of work hours were reported as saved",
};

const chartLabels: Record<string, string> = {
  adoption_work: "Work adoption",
  work_use_last_week: "Used for work last week",
  work_use_daily: "Used every workday",
  assisted_hours_share: "Work hours assisted",
  reported_time_savings_share: "Reported time savings",
};

export default async function HomePage() {
  const [rows, longitudinal] = await Promise.all([
    loadObservations(),
    loadLongitudinalDiagnostics(),
  ]);
  const national = latestNational(rows);
  const metricOrder = [
    "adoption_work",
    "work_use_last_week",
    "work_use_daily",
    "assisted_hours_share",
    "reported_time_savings_share",
  ];
  const timeSeries = rows
    .filter((row) => row.entity_id === "us" && metricOrder.includes(row.metric_id))
    .map((row) => ({
      date: row.date,
      value: row.value,
      metric: row.metric_id,
      label: chartLabels[row.metric_id],
    }));

  const periods = longitudinal.input_scope.periods;
  const firstPeriod = periods[0];
  const lastPeriod = periods[periods.length - 1];
  const crossLevelAlignedQuarters = Object.values(longitudinal.cross_level_comparison).filter(
    (row) =>
      row.occupation_minus_industry_pearson_A_H > 0 &&
      row.occupation_minus_industry_spearman_A_H > 0,
  ).length;
  const industryRank = longitudinal.rank_stability.industry;
  const occupationRank = longitudinal.rank_stability.occupation;
  const industryDominance = longitudinal.rank_stability_dominance.industry;
  const occupationDominance = longitudinal.rank_stability_dominance.occupation;

  return (
    <main>
      <p className="eyebrow">U.S. workplace generative AI</p>
      <h1>Measure how AI moves from adoption into work.</h1>
      <p className="lede">
        GenAI at Work tracks the conversion of reported adoption into recurring use, assisted working
        time, and reported time savings across U.S. workers, industries, and occupations.
      </p>

      <section className="section" aria-labelledby="evidence-heading">
        <h2 id="evidence-heading">What persists across {periods.length} survey waves</h2>
        <p className="kicker">
          Across the audited window, adoption rankings are more stable than assisted-hours rankings, and
          occupation-level adoption–penetration alignment exceeds industry-level alignment in every wave.
        </p>
        <div className="metric-row" role="group" aria-label={`${periods.length}-wave evidence summary`}>
          <div className="metric">
            <span>Audited window</span>
            <strong>{periods.length} waves</strong>
            <div>{firstPeriod} through {lastPeriod}</div>
          </div>
          <div className="metric">
            <span>Cross-level alignment</span>
            <strong>{crossLevelAlignedQuarters} / {periods.length}</strong>
            <div>quarters with stronger occupation adoption–assisted-hours alignment</div>
          </div>
          <div className="metric">
            <span>Rank persistence</span>
            <strong>
              {industryDominance.adoption_rank_corr_gt_assisted_hours_rank_corr}
              {" / "}
              {industryDominance.quarter_pairs}
            </strong>
            <div>
              industry quarter pairs; occupations show
              {` ${occupationDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} / ${occupationDominance.quarter_pairs}`}
            </div>
          </div>
        </div>

        <StabilityBars
          title={`Median pairwise rank correlation across the ${periods.length}-wave window`}
          bars={[
            { label: "Industry adoption", value: industryRank.A.median_pairwise },
            { label: "Industry assisted hours", value: industryRank.H.median_pairwise },
            { label: "Occupation adoption", value: occupationRank.A.median_pairwise },
            { label: "Occupation assisted hours", value: occupationRank.H.median_pairwise },
          ]}
        />
        <p className="note">
          Adoption rankings exceed assisted-hours rank stability in
          {` ${industryDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${industryDominance.quarter_pairs} `}
          industry quarter pairs and
          {` ${occupationDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${occupationDominance.quarter_pairs} `}
          occupation quarter pairs. These are descriptive aggregate diagnostics. Causal mechanisms require
          separate identification.
        </p>
      </section>

      <section className="section" aria-labelledby="measurement-heading">
        <h2 id="measurement-heading">A measurement chain from adoption to outcomes</h2>
        <p className="lede">
          Each stage answers a different question and uses a different denominator. Reading them together
          reveals how diffusion converts into workflow depth and reported savings.
        </p>
        <div className="measurement-ladder" role="group" aria-label="Measurement chain from adoption to outcomes">
          <div className="measurement-step">
            <span>01</span><strong>Adoption</strong><p>Share of employed adults reporting GenAI use for work.</p>
          </div>
          <div className="measurement-step">
            <span>02</span><strong>Recent use</strong><p>Share reporting work use in the prior week.</p>
          </div>
          <div className="measurement-step">
            <span>03</span><strong>Routine use</strong><p>Share reporting use on every workday.</p>
          </div>
          <div className="measurement-step">
            <span>04</span><strong>Workflow penetration</strong><p>Share of total work hours actively assisted by GenAI.</p>
          </div>
          <div className="measurement-step">
            <span>05</span><strong>Reported savings</strong><p>Counterfactual share of work hours respondents report saving.</p>
          </div>
          <div className="measurement-step">
            <span>06</span><strong>Realized outcomes</strong><p>Changes in output, productivity, wages, employment, or firm performance require separate outcome data and identification.</p>
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="national-heading">
        <h2 id="national-heading">National snapshot</h2>
        {national.size === 0 ? (
          <div className="callout">
            <p className="callout-label">Public aggregate view</p>
            <p>
              This build excludes the bounded national observation view. Longitudinal derived evidence
              remains available through the promoted release.
            </p>
            <p><Link href="/sources">Read the source and redistribution boundary →</Link></p>
          </div>
        ) : (
          <>
            <section className="metric-row" aria-label="Latest national snapshot">
              {metricOrder.map((metric) => {
                const row = national.get(metric);
                return row ? (
                  <div className="metric" key={metric}>
                    <span>{row.period}</span>
                    <strong>{row.value.toFixed(1)}%</strong>
                    <div>{labels[metric]}</div>
                  </div>
                ) : null;
              })}
            </section>
            <TimeSeriesPlot data={timeSeries} />
          </>
        )}
      </section>

      <section className="section" aria-labelledby="wedge-heading">
        <h2 id="wedge-heading">Why occupations and industries diverge</h2>
        <p>
          Across every audited wave, adoption and assisted working time are more tightly coupled across
          occupations than across industries. The difference points to an industry-context research
          question beyond occupation mix alone.
        </p>
        <p>
          Industry aggregates combine occupation composition with firm context and sampling variation.
          The current evidence reports the remaining variation descriptively; causal attribution requires
          richer firm, task, and outcome data.
        </p>
        <p><Link href="/blog/after-adoption">Read the technical essay →</Link></p>
      </section>
    </main>
  );
}
