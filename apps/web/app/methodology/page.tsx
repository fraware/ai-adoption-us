import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Methodology" };

export default function MethodologyPage() {
  return (
    <main>
      <p className="eyebrow">Measurement contract</p>
      <h1>Measure each stage on its own terms.</h1>
      <p className="lede">
        The observatory separates survey adoption, recurring use, reconstructed assisted hours, reported
        counterfactual savings, and realized outcomes. Each construct has its own denominator and
        evidentiary status.
      </p>

      <section className="section" aria-labelledby="constructs-heading">
        <h2 id="constructs-heading">Core constructs</h2>
        <dl className="definition-grid">
          <dt>Work adoption</dt>
          <dd>Share of employed adults aged 18–64 reporting generative AI use for their job.</dd>
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
            Respondents&apos; counterfactual estimate of the additional time the same work would have
            required without GenAI. Nonusers contribute zero reported saved hours.
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

      <section className="section" aria-labelledby="diagnostics-heading">
        <h2 id="diagnostics-heading">Longitudinal diagnostics</h2>
        <p>
          Subgroup results are evaluated wave by wave over the complete common A/H/S window, currently
          Q4 2024 through Q2 2026. Cross-sectional Pearson and Spearman correlations describe alignment
          between constructs. Reported R² values are descriptive fits across aggregate groups. Worker-level
          probabilities and causal estimates require different designs.
        </p>
        <p>
          Rank stability uses Spearman correlations between subgroup rankings for every pair of audited
          quarters. The publication reports the median, endpoint, minimum, and maximum pairwise
          correlations so the longitudinal hierarchy remains visible across the full window.
        </p>
      </section>

      <section className="section" aria-labelledby="composition-heading">
        <h2 id="composition-heading">Composition analysis</h2>
        <p>
          The composition layer estimates an industry value under national occupation-specific GenAI
          rates combined with that industry&apos;s occupation mix. This is a standardization counterfactual.
          Causal decomposition requires separate identification.
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
      </section>

      <section className="section" aria-labelledby="evidence-heading">
        <h2 id="evidence-heading">Evidence classes</h2>
        <div className="status-grid">
          <div className="status-card">
            <span className="status-tag ready">Direct source construct</span>
            <h3>Survey measurements</h3>
            <p>
              RPS/FRED supplies the registered aggregate measurements for adoption, recent and routine use,
              assisted hours, and reported savings. Release 1 publishes the bounded attributed aggregate
              views authorized by the release contract, alongside derived publication evidence.
            </p>
          </div>
          <div className="status-card">
            <span className="status-tag ready">Derived descriptive</span>
            <h3>Longitudinal diagnostics</h3>
            <p>Wave-by-wave associations and rank-stability checks summarize the derived descriptive layer.</p>
          </div>
          <div className="status-card">
            <span className="status-tag ready">Derived descriptive</span>
            <h3>Composition counterfactuals</h3>
            <p>
              CPS occupation weights support standardized industry counterfactuals and occupation-adjusted
              industry-context residuals, with OEWS as an establishment-side robustness source.
            </p>
          </div>
          <div className="status-card">
            <span className="status-tag gated">Future evidence layer</span>
            <h3>Outcome and causal inference</h3>
            <p>
              Organizational mechanisms, productivity effects, and design-based uncertainty for custom
              pooled CPS composition vectors require additional evidence.
            </p>
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="release-heading">
        <h2 id="release-heading">Reproducibility and release boundary</h2>
        <p>
          The authorized release pipeline retrieves the published aggregate RPS source into a private
          candidate workspace, validates the registered 131-series inventory, and builds deterministic
          publication artifacts. Release 1 uses <code>DATA_MODE=derived_only</code> and excludes private
          source-input bytes from the public bundle.
        </p>
        <p>
          Source identities, crosswalk versions, validators, and interpretive guardrails are versioned
          with the code. A source-definition, rights, or release-state change blocks publication until the
          candidate passes the project&apos;s release controls.
        </p>
        <p><Link href="/sources">See source status and provenance →</Link></p>
      </section>
    </main>
  );
}
