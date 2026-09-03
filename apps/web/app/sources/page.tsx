import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Sources and provenance" };

export default function SourcesPage() {
  return (
    <main>
      <p className="eyebrow">Source registry &amp; release boundary</p>
      <h1>Sources, provenance, and what is not in this release.</h1>
      <p className="lede">
        Release 1 is intentionally narrower than the private research environment. It publishes
        rights-safe descriptive evidence without redistributing the reviewed raw RPS subgroup fixture.
      </p>

      <section className="section" aria-labelledby="source-status-heading">
        <h2 id="source-status-heading">Source status</h2>
        <div className="status-grid">
          <div className="status-card">
            <span className="status-tag ready">Validated research source</span>
            <h3>RPS / GenAI Adoption Tracker</h3>
            <p>
              Primary measurement family for worker adoption, recent/routine use, assisted work hours,
              and reported time savings. Published-aggregate project use is recorded as permitted. The
              public Release 1 bundle remains <code>derived_only</code>; the separate live refresh path is
              not activated until its durable private-backend gates pass.
            </p>
          </div>
          <div className="status-card">
            <span className="status-tag ready">Composition inputs validated</span>
            <h3>Current Population Survey</h3>
            <p>
              Official Q2 2025 and Q2 2026 Basic Monthly public-use files have been executed through the
              composition pipeline, producing versioned worker-share and actual-main-job-hour occupation
              weights plus reliability diagnostics. These CPS weights are composition inputs, not RPS residuals;
              occupation-adjusted residual evidence is produced separately as a derived descriptive artifact.
              Design-based uncertainty for custom pooled composition vectors remains unsupported.
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
            <span className="status-tag ready">Published triangulation</span>
            <h3>BTOS / firm-side context</h3>
            <p>
              The industry explorer includes the preregistered BTOS–RPS descriptive triangulation.
              Employer-business AI use and worker GenAI adoption have different units, denominators,
              technology scope, and reference periods; their correlation is descriptive sector context,
              not a percentage-point gap, productivity estimate, or causal effect.
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
          Public source links are preserved in the registry. Release 1 does not expose a downloadable
          static database of the reviewed RPS observations and does not silently fall back from a live
          source to the private audit fixture. The live source-check schedule remains disabled until the
          separate durable-private-backend activation contract is satisfied.
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
            versioned CPS/OEWS composition evidence, BTOS–RPS triangulation, methodology, and the technical
            publication. It runs in <code>derived_only</code> mode.
          </dd>
          <dt>Private research bundle</dt>
          <dd>
            Adds the reviewed five-wave subgroup fixture used to regenerate and regression-test the
            longitudinal publication artifacts.
          </dd>
          <dt>Produced composition evidence</dt>
          <dd>
            Q2 2025 and Q2 2026 CPS composition/reliability artifacts, occupation-adjusted descriptive
            residual evidence, and May 2025 OEWS robustness artifacts. These are not causal estimates and
            do not supply design-based confidence intervals for the custom pooled composition vectors.
          </dd>
          <dt>Still outside Release 1 claims</dt>
          <dd>
            A standalone public composition-residual explorer, design-based CPS covariance for the custom
            composition vectors, causal firm effects, and measured labor-productivity effects.
          </dd>
        </dl>
      </section>

      <section className="section" aria-labelledby="validation-heading">
        <h2 id="validation-heading">Validation boundary</h2>
        <p>
          Permanent GitHub Actions CI validates the public research and application surface with the
          public Python suite, compilation, Ruff, strict mypy, governance/privacy checks, locked
          <code>npm ci</code>, TypeScript validation, optimized <code>derived_only</code> builds, and
          production-route smoke tests.
        </p>
        <p>
          Rendered QA exercises stable Chrome, Firefox, WebKit, mobile device emulation, and native
          macOS Safari, with responsive, keyboard-entry, axe, runtime, resize, navigation, 404, and
          Lighthouse checks. Human screen-reader traversal, physical mobile devices, and field Core Web
          Vitals are not Release 1 evidence and are not claimed as completed.
        </p>
        <p className="note">
          GitHub Pages is the Release 1 hosting target. The public launch requires a successful live
          deployment audit bound to the exact release commit; the static host does not provide the
          application-controlled response-header policy available in the non-Pages server profile.
        </p>
        <p><Link href="/methodology">Read the measurement contract →</Link></p>
      </section>
    </main>
  );
}
