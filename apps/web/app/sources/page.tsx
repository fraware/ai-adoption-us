import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Sources and provenance" };

export default function SourcesPage() {
  return (
    <main>
      <p className="eyebrow">Source registry &amp; release boundary</p>
      <h1>Sources, provenance, and what is not in this release.</h1>
      <p className="lede">
        The public candidate is intentionally narrower than the private research environment. It
        publishes derived descriptive evidence without redistributing the reviewed raw RPS subgroup
        fixture.
      </p>

      <section className="section" aria-labelledby="source-status-heading">
        <h2 id="source-status-heading">Source status</h2>
        <div className="status-grid">
          <div className="status-card">
            <span className="status-tag ready">Validated research source</span>
            <h3>RPS / GenAI Adoption Tracker</h3>
            <p>
              Primary measurement family for worker adoption, recent/routine use, assisted work hours,
              and reported time savings. Series metadata are retained in the public registry; reviewed
              subgroup observations remain private and the public observation path remains rights-gated.
            </p>
          </div>
          <div className="status-card">
            <span className="status-tag ready">Composition inputs validated</span>
            <h3>Current Population Survey</h3>
            <p>
              Official Q2 2025 and Q2 2026 Basic Monthly public-use files have been executed through the
              composition pipeline, producing versioned worker-share and actual-main-job-hour occupation
              weights plus reliability diagnostics. These are composition inputs, not RPS residuals.
            </p>
          </div>
          <div className="status-card">
            <span className="status-tag ready">Robustness input validated</span>
            <h3>May 2025 OEWS</h3>
            <p>
              Official staffing data have been executed as an independent establishment-side composition
              robustness source, with cross-vintage and coverage diagnostics. Population differences from
              CPS remain explicit; OEWS weights do not establish an organizational effect.
            </p>
          </div>
          <div className="status-card">
            <span className="status-tag gated">Future triangulation</span>
            <h3>BTOS / firm-side context</h3>
            <p>
              Potential later source for business-side adoption context. It is not mechanically joined
              to worker outcomes or used to label organizational effects in the current release.
            </p>
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="rps-heading">
        <h2 id="rps-heading">RPS measurement provenance</h2>
        <p>
          The core measurement source is the Real-Time Population Survey Generative AI Adoption Tracker
          by Bick, Blandin, and Deming, surfaced through FRED series. The canonical registry contains 131
          work-focused source-series records: five national constructs, 60 industry records, and 66
          occupation records.
        </p>
        <p>
          Public source links are preserved in the registry. This release does not expose a downloadable
          static database of the reviewed RPS observations and does not silently fall back from a live
          source to the private audit fixture.
        </p>
        <p>
          <a href="https://fred.stlouisfed.org/release?rid=6">FRED RPS release page</a>
          {" · "}
          <a href="https://doi.org/10.1287/mnsc.2025.02523">Peer-reviewed RPS paper</a>
        </p>
      </section>

      <section className="section" aria-labelledby="public-private-heading">
        <h2 id="public-private-heading">Public versus private evidence</h2>
        <dl className="definition-grid">
          <dt>Public bundle</dt>
          <dd>
            Source metadata, formulas, crosswalks, deterministic code, longitudinal derived diagnostics,
            versioned CPS/OEWS composition evidence, methodology, and the technical publication. It runs
            in <code>derived_only</code> mode.
          </dd>
          <dt>Private research bundle</dt>
          <dd>
            Adds the reviewed five-wave subgroup fixture used to regenerate and regression-test the
            longitudinal publication artifacts.
          </dd>
          <dt>Produced composition evidence</dt>
          <dd>
            Q2 2025 and Q2 2026 CPS composition/reliability artifacts and May 2025 OEWS robustness
            artifacts. These contain composition weights and diagnostics, not direct RPS observations.
          </dd>
          <dt>Still gated</dt>
          <dd>
            Occupation-adjusted RPS industry residuals, the public composition explorer, causal firm
            effects, and measured labor-productivity effects.
          </dd>
        </dl>
      </section>

      <section className="section" aria-labelledby="validation-heading">
        <h2 id="validation-heading">Validation boundary</h2>
        <p>
          Permanent GitHub Actions CI validates the public research and application surface with the
          public Python suite, compilation, Ruff, strict mypy, governance/privacy checks, locked
          <code>npm ci</code>, TypeScript validation, and an optimized <code>derived_only</code> Next.js
          production build. It also starts the production server and smoke-tests every public route.
        </p>
        <p>
          A separate rendered-browser workflow exercises the same production candidate across stable
          Chrome, Firefox, and a WebKit engine proxy, with responsive, keyboard, axe, runtime, and
          Lighthouse checks. That automated evidence does not substitute for real Safari/iOS,
          screen-reader traversal, manual interaction/color review, or production field-performance
          validation.
        </p>
        <p className="note">
          Public-launch accessibility and deployment claims remain gated until the outstanding manual
          browser/assistive-technology checks and the production deployment audit are complete.
        </p>
        <p><Link href="/methodology">Read the measurement contract →</Link></p>
      </section>
    </main>
  );
}
