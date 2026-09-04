import type { Metadata } from "next";
import Link from "next/link";
import { StabilityBars } from "../components/StabilityBars";
import { TimeSeriesPlot } from "../components/TimeSeriesPlot";
import { latestNational, loadObservations } from "../lib/data";
import { loadLongitudinalDiagnostics } from "../lib/longitudinal";

export const metadata: Metadata = {
  title: "AI adoption is only the beginning",
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
      <h1>Adoption is only the beginning.</h1>
      <p className="lede">
        An auditable technical publication separating worker adoption, workflow penetration, and
        reported time savings—and testing which patterns persist across survey waves.
      </p>

      <section className="section" aria-labelledby="evidence-heading">
        <h2 id="evidence-heading">What persists across {periods.length} survey waves</h2>
        <p className="kicker">
          The durable evidence is about persistence and cross-level structure, not a latest-quarter
          leaderboard.
        </p>
        <div className="metric-row" role="group" aria-label={`${periods.length}-wave evidence summary`}>
          <div className="metric">
            <span>Audited window</span>
            <strong>{periods.length} waves</strong>
            <div>{firstPeriod} through {lastPeriod}</div>
          </div>
          <div className="metric">
            <span>Cross-level result</span>
            <strong>{crossLevelAlignedQuarters} / {periods.length}</strong>
            <div>quarters where occupation adoption–assisted-hours alignment exceeds industry alignment</div>
          </div>
          <div className="metric">
            <span>Rank persistence</span>
            <strong>
              {industryDominance.adoption_rank_corr_gt_assisted_hours_rank_corr}
              {" / "}
              {industryDominance.quarter_pairs}
            </strong>
            <div>industry quarter pairs; occupations show {occupationDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} / {occupationDominance.quarter_pairs}</div>
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
          Adoption rankings are more similar across quarters than assisted-hours rankings in
          {` ${industryDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${industryDominance.quarter_pairs} `}
          industry quarter pairs and
          {` ${occupationDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${occupationDominance.quarter_pairs} `}
          occupation quarter pairs. This is descriptive aggregate evidence; it does not identify a causal mechanism.
        </p>
      </section>

      <section className="section" aria-labelledby="measurement-heading">
        <h2 id="measurement-heading">One technology, several different measurements</h2>
        <p className="lede">
          Public discussion frequently collapses distinct stages into one “AI adoption” number. This
          publication keeps them separate because their denominators and economic meanings differ.
        </p>
        <div className="measurement-ladder" role="group" aria-label="Measurement ladder from adoption to realization">
          <div className="measurement-step">
            <span>01</span><strong>Adoption</strong><p>Who reports using GenAI for work.</p>
          </div>
          <div className="measurement-step">
            <span>02</span><strong>Recent use</strong><p>Who used it for work in the prior week.</p>
          </div>
          <div className="measurement-step">
            <span>03</span><strong>Routine use</strong><p>Who reports using it every workday.</p>
          </div>
          <div className="measurement-step">
            <span>04</span><strong>Workflow penetration</strong><p>Share of work hours actively assisted by GenAI.</p>
          </div>
          <div className="measurement-step">
            <span>05</span><strong>Reported benefit</strong><p>Counterfactual time respondents report saving.</p>
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="national-heading">
        <h2 id="national-heading">National snapshot</h2>
        {national.size === 0 ? (
          <div className="callout">
            <p className="callout-label">Rights-safe Release 1 boundary</p>
            <p>
              The bounded public observation view is unavailable in this build. The longitudinal
              publication artifacts remain available, while private source-input bytes stay outside the
              public bundle.
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
        <h2 id="wedge-heading">The unresolved industry wedge</h2>
        <p>
          Across every audited wave, adoption and assisted working time are more tightly coupled across
          occupations than across industries. The aggregate adoption-to-penetration relationship is therefore more tightly aligned across
          occupations than across broad industries. Broad industries contain an additional context wedge.
        </p>
        <p>
          The current aggregate data do not identify that wedge as an organizational effect. Firm
          composition, detailed task mix, workflow design, policy, regulation, worker selection,
          technology stacks, and sampling variation remain plausible contributors.
        </p>
        <p><Link href="/blog/after-adoption">Read the technical essay →</Link></p>
      </section>
    </main>
  );
}
