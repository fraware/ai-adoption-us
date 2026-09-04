import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Data & methods" };

export default function MethodologyPage() {
  return (
    <main>
      <section className="hero hero-compact" aria-labelledby="methods-title">
        <p className="eyebrow">Data &amp; methods</p>
        <h1 id="methods-title">Measure each stage on its own terms.</h1>
        <p className="lede">
          The observatory separates adoption, recurring use, assisted working time, reported counterfactual
          savings, and realized outcomes. Each construct has its own denominator and evidentiary status.
        </p>
      </section>

      <section className="section methods-core" aria-labelledby="constructs-heading">
        <p className="eyebrow">Measurement</p>
        <h2 id="constructs-heading">Five constructs anchor the observatory.</h2>
        <dl className="definition-grid">
          <dt>Work adoption</dt>
          <dd>Share of employed adults aged 18–64 reporting generative AI use for their job.</dd>
          <dt>Used for work last week</dt>
          <dd>Share of the employed population reporting work use in the prior week.</dd>
          <dt>Used every workday</dt>
          <dd>Share of the employed population reporting GenAI use on every workday.</dd>
          <dt>Work hours assisted</dt>
          <dd>
            Share of total work hours actively using GenAI, reconstructed from reported use duration and
            days worked. Nonusers contribute zero active-use hours.
          </dd>
          <dt>Reported time savings</dt>
          <dd>
            Respondents&apos; counterfactual estimate of the additional time the same work would have required
            without GenAI. Nonusers contribute zero reported saved hours.
          </dd>
        </dl>
        <div className="callout">
          <p className="callout-label">Interpretation boundary</p>
          <p>
            Reported time savings are survey-based counterfactual estimates. Labor productivity, output,
            GDP, and employer value added require direct outcome evidence.
          </p>
        </div>
      </section>

      <section className="section methods-details" aria-labelledby="analysis-heading">
        <p className="eyebrow">Analysis</p>
        <h2 id="analysis-heading">Technical detail stays available on demand.</h2>

        <details className="technical-disclosure">
          <summary>Longitudinal diagnostics</summary>
          <div className="technical-disclosure-body">
            <p>
              Subgroup results are evaluated wave by wave over the complete common A/H/S window, currently
              Q4 2024 through Q2 2026. Cross-sectional Pearson and Spearman correlations describe alignment
              between constructs. Reported R² values are descriptive fits across aggregate groups.
              Worker-level probabilities and causal estimates require different designs.
            </p>
            <p>
              Rank stability uses Spearman correlations between subgroup rankings for every pair of audited
              quarters. The publication reports the median, endpoint, minimum, and maximum pairwise
              correlations across the full window.
            </p>
          </div>
        </details>

        <details className="technical-disclosure">
          <summary>Occupation-composition analysis</summary>
          <div className="technical-disclosure-body">
            <p>
              The composition layer estimates an industry value under national occupation-specific GenAI
              rates combined with that industry&apos;s occupation mix. This is a standardization counterfactual.
              Causal decomposition requires separate identification.
            </p>
            <dl className="definition-grid compact-definitions">
              <dt>Adoption counterfactual</dt>
              <dd>Uses CPS worker-share occupation weights within each industry.</dd>
              <dt>Assisted-hours counterfactual</dt>
              <dd>Uses actual-main-job-hour occupation weights within each industry.</dd>
              <dt>Reported-savings counterfactual</dt>
              <dd>Uses the same actual-main-job-hour weighting basis as the work-hour outcome.</dd>
              <dt>Residual</dt>
              <dd>
                Observed industry value minus its occupation-composition counterfactual. The code names this
                an <code>occupation_<wbr />adjusted_<wbr />industry_<wbr />context_<wbr />residual</code>.
              </dd>
            </dl>
            <p className="note">
              The CPS composition foundation uses official Q2 2025 and Q2 2026 inputs. Release 1 reports
              occupation-adjusted industry-context residuals as derived descriptive diagnostics.
              Organizational quality, efficiency, productivity, and causal firm effects sit outside the
              supported interpretation. Design-based confidence intervals for the custom pooled CPS
              composition vectors remain unsupported.
            </p>
          </div>
        </details>

        <details className="technical-disclosure">
          <summary>Evidence and release boundary</summary>
          <div className="technical-disclosure-body">
            <p>
              RPS/FRED supplies the registered aggregate measurements. Longitudinal diagnostics and
              composition counterfactuals form derived descriptive evidence. Outcome and causal inference
              require additional evidence.
            </p>
            <p>
              The authorized release pipeline retrieves the published aggregate RPS source into a private
              candidate workspace, validates the registered 131-series inventory, and builds deterministic
              publication artifacts. Release 1 uses <code>DATA_MODE=derived_only</code> and excludes private
              source-input bytes from the public bundle.
            </p>
            <p>
              Source identities, crosswalk versions, validators, and interpretive guardrails are versioned
              with the code. A source-definition, rights, or release-state change blocks publication until
              the candidate passes the project&apos;s release controls.
            </p>
          </div>
        </details>

        <p className="text-link"><Link href="/sources">See sources and provenance →</Link></p>
      </section>
    </main>
  );
}
