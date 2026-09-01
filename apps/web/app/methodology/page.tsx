import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Methodology" };

export default function MethodologyPage() {
  return (
    <main>
      <p className="eyebrow">Measurement contract</p>
      <h1>Methodology before interpretation.</h1>
      <p className="lede">
        The publication separates direct survey responses, reconstructed assisted-hours estimates,
        and self-reported counterfactual time savings. Those quantities do not have interchangeable
        denominators or economic interpretations.
      </p>

      <section className="section" aria-labelledby="constructs-heading">
        <h2 id="constructs-heading">Core constructs</h2>
        <dl className="definition-grid">
          <dt>Work adoption</dt>
          <dd>Share of employed adults aged 18–64 reporting that they use generative AI for their job.</dd>
          <dt>Used for work last week</dt>
          <dd>Share of the employed population reporting work use in the prior week.</dd>
          <dt>Used every workday</dt>
          <dd>Share of the employed population reporting GenAI use on every workday.</dd>
          <dt>Work hours assisted</dt>
          <dd>
            Share of total work hours actively using GenAI, reconstructed from reported use duration
            and days worked. Nonusers contribute zero active-use hours.
          </dd>
          <dt>Reported time savings</dt>
          <dd>
            Respondents&apos; counterfactual estimate of how much additional time the same work would have
            required without GenAI. Nonusers contribute zero reported saved hours.
          </dd>
        </dl>
        <div className="callout">
          <p className="callout-label">Non-negotiable interpretation rule</p>
          <p>
            Reported time savings are not an observed measure of labor productivity, output, GDP, or
            employer value added. The publication does not relabel them as productivity.
          </p>
        </div>
      </section>

      <section className="section" aria-labelledby="diagnostics-heading">
        <h2 id="diagnostics-heading">Longitudinal diagnostics</h2>
        <p>
          Subgroup results are evaluated wave by wave across Q2 2025–Q2 2026. Cross-sectional Pearson
          and Spearman correlations describe alignment between constructs. The reported R² values are
          descriptive fits across aggregate groups, not worker-level probabilities or causal estimates.
        </p>
        <p>
          Rank stability uses Spearman correlations between subgroup rankings for every pair of audited
          quarters. Reporting the median, endpoint, minimum, and maximum pairwise correlations prevents
          a single latest-quarter leaderboard from being mistaken for a persistent hierarchy.
        </p>
      </section>

      <section className="section" aria-labelledby="composition-heading">
        <h2 id="composition-heading">Composition analysis</h2>
        <p>
          The composition layer asks what an industry&apos;s aggregate value would be if it inherited the
          national occupation-specific GenAI rates through its own occupation mix. It is a
          standardization counterfactual, not a causal decomposition.
        </p>
        <dl className="definition-grid">
          <dt>Adoption counterfactual</dt>
          <dd>Uses CPS worker-share occupation weights within each industry.</dd>
          <dt>Assisted-hours counterfactual</dt>
          <dd>Uses actual-main-job-hour occupation weights within each industry.</dd>
          <dt>Reported-savings counterfactual</dt>
          <dd>Uses the same actual-main-job-hour weighting basis as the work-hour outcome.</dd>
          <dt>Residual</dt>
          <dd>
            Observed industry value minus its occupation-composition counterfactual. The code names this
            an <code>occupation_adjusted_industry_context_residual</code>.
          </dd>
        </dl>
        <p className="note">
          The CPS composition foundation has been executed and validated on official Q2 2025 and Q2 2026
          inputs. The current public candidate still does not publish occupation-adjusted RPS industry
          residuals because the compatible RPS observation path remains rights-gated; that join stays
          fail-closed until source permissions are resolved and the residual robustness checks can run.
        </p>
      </section>

      <section className="section" aria-labelledby="evidence-heading">
        <h2 id="evidence-heading">Evidence classes</h2>
        <div className="status-grid">
          <div className="status-card">
            <span className="status-tag ready">Direct</span>
            <h3>Survey measurements</h3>
            <p>RPS/FRED observations for adoption, recent/routine use, assisted hours, and reported savings.</p>
          </div>
          <div className="status-card">
            <span className="status-tag ready">Derived</span>
            <h3>Descriptive diagnostics</h3>
            <p>Changes, correlations, regressions, rank stability, and leave-one-group-out checks.</p>
          </div>
          <div className="status-card">
            <span className="status-tag gated">RPS join gated</span>
            <h3>Composition counterfactuals</h3>
            <p>
              CPS occupation weights are executed and validated; observed-versus-counterfactual RPS
              residuals remain blocked until a rights-cleared RPS observation path is available.
            </p>
          </div>
          <div className="status-card">
            <span className="status-tag gated">Not identified</span>
            <h3>Causal mechanisms</h3>
            <p>Organizational effects, productivity effects, and economic realization require stronger designs.</p>
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="release-heading">
        <h2 id="release-heading">Reproducibility and release boundary</h2>
        <p>
          The private research candidate retains the reviewed subgroup fixture and can regenerate the
          committed longitudinal publication artifacts. The public candidate uses <code>DATA_MODE=derived_only</code>
          and excludes the raw RPS audit fixture by construction.
        </p>
        <p>
          Source-series identities, crosswalk versions, deterministic validators, and interpretive
          guardrails are versioned with the code. A source-definition or rights change blocks automatic
          publication until it is reviewed.
        </p>
        <p><Link href="/sources">See source status and provenance →</Link></p>
      </section>
    </main>
  );
}
