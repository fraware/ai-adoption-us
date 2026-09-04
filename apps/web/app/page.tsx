import type { Metadata } from "next";
import Link from "next/link";
import { TimeSeriesPlot } from "../components/TimeSeriesPlot";
import { latestNational, loadObservations } from "../lib/data";

export const metadata: Metadata = {
  title: "Workplace AI, measured",
};

const labels: Record<string, string> = {
  adoption_work: "use GenAI for work",
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
  const rows = await loadObservations();
  const national = latestNational(rows);
  const chartMetricOrder = [
    "adoption_work",
    "work_use_last_week",
    "work_use_daily",
    "assisted_hours_share",
    "reported_time_savings_share",
  ];
  const featuredMetricOrder = [
    "adoption_work",
    "assisted_hours_share",
    "reported_time_savings_share",
  ];
  const timeSeries = rows
    .filter((row) => row.entity_id === "us" && chartMetricOrder.includes(row.metric_id))
    .map((row) => ({
      date: row.date,
      value: row.value,
      metric: row.metric_id,
      label: chartLabels[row.metric_id],
    }));

  return (
    <main>
      <section className="hero" aria-labelledby="home-title">
        <p className="eyebrow">U.S. workplace generative AI</p>
        <h1 id="home-title">AI adoption measures reach. The workday reveals depth.</h1>
        <p className="lede">
          GenAI at Work tracks how reported workplace use turns into recurring use, assisted working time,
          and reported time savings across U.S. workers.
        </p>

        {national.size === 0 ? (
          <div className="callout hero-callout">
            <p className="callout-label">Public aggregate view</p>
            <p>
              This build excludes the bounded national observation view. Derived evidence remains available
              through the promoted release.
            </p>
            <p><Link href="/sources">Read the source boundary →</Link></p>
          </div>
        ) : (
          <div className="hero-metrics" role="group" aria-label="Latest national headline measures">
            {featuredMetricOrder.map((metric) => {
              const row = national.get(metric);
              return row ? (
                <div className="hero-metric" key={metric}>
                  <span>{row.period}</span>
                  <strong>{row.value.toFixed(1)}%</strong>
                  <p>{labels[metric]}</p>
                </div>
              ) : null;
            })}
          </div>
        )}
      </section>

      {national.size > 0 ? (
        <section className="section section-chart" aria-labelledby="national-heading">
          <div className="section-intro">
            <p className="eyebrow">National record</p>
            <h2 id="national-heading">Five measures, one workday.</h2>
            <p className="kicker">
              Adoption, recurrence, assisted working time, and reported savings move together without
              representing the same construct.
            </p>
          </div>
          <TimeSeriesPlot data={timeSeries} />
        </section>
      ) : null}

      <section className="section section-split" aria-labelledby="explore-heading">
        <div>
          <p className="eyebrow">Cross-group evidence</p>
          <h2 id="explore-heading">Occupation structures the conversion from adoption to assisted time more tightly.</h2>
        </div>
        <div className="section-copy">
          <p>
            Across every audited wave, adoption and assisted working time align more tightly across
            occupations than across industries. Industry aggregates retain variation beyond occupation mix.
          </p>
          <p className="text-link"><Link href="/explore">Explore the data →</Link></p>
        </div>
      </section>

      <section className="section essay-promo" aria-labelledby="essay-heading">
        <p className="eyebrow">Technical essay</p>
        <h2 id="essay-heading">After adoption</h2>
        <p className="lede-small">
          A measurement argument about depth of use, reported savings, and the limits of productivity inference.
        </p>
        <p className="text-link"><Link href="/blog/after-adoption">Read the essay →</Link></p>
      </section>
    </main>
  );
}
