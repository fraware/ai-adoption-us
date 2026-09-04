import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Sources and release scope" };

export default function SourcesPage() {
  return (
    <main>
      <section className="hero hero-compact" aria-labelledby="sources-title">
        <p className="eyebrow">Sources and release scope</p>
        <h1 id="sources-title">Every public claim is tied to a source, vintage, and release.</h1>
        <p className="lede">
          Worker measurement, occupation composition, establishment staffing, and firm-side AI use enter the
          observatory under explicit source and interpretation boundaries.
        </p>
      </section>

      <section className="section" aria-labelledby="source-status-heading">
        <p className="eyebrow">Source register</p>
        <h2 id="source-status-heading">Four sources support distinct parts of the evidence.</h2>
        <div className="source-index">
          <article className="source-row">
            <div>
              <span className="status-tag ready">Primary worker measurement</span>
              <h3>RPS / GenAI Adoption Tracker</h3>
            </div>
            <p>
              RPS supplies worker adoption, recurrence, assisted work hours, and reported time savings. The
              authorized aggregate release path uses registered FRED series to generate bounded attributed
              public views plus derived publication artifacts.
            </p>
          </article>

          <article className="source-row">
            <div>
              <span className="status-tag ready">Industry composition</span>
              <h3>Current Population Survey</h3>
            </div>
            <p>
              Official Q2 2025 and Q2 2026 Basic Monthly public-use files supply worker-share and
              actual-main-job-hour occupation weights. Composition results are descriptive; design-based
              uncertainty for custom pooled composition vectors remains unsupported.
            </p>
          </article>

          <article className="source-row">
            <div>
              <span className="status-tag ready">Establishment robustness</span>
              <h3>OEWS · 2025-05</h3>
            </div>
            <p>
              Official staffing data provide an independent establishment-side check on industry occupation
              composition. Population differences from CPS remain explicit.
            </p>
          </article>

          <article className="source-row">
            <div>
              <span className="status-tag ready">Firm-side triangulation</span>
              <h3>BTOS</h3>
            </div>
            <p>
              BTOS supplies current employer-business AI use by sector. The industry explorer uses its
              relationship with worker RPS adoption as cross-construct descriptive triangulation.
            </p>
          </article>
        </div>
      </section>

      <section className="section source-details" aria-labelledby="provenance-heading">
        <p className="eyebrow">Provenance</p>
        <h2 id="provenance-heading">Publication detail stays inspectable.</h2>

        <details className="technical-disclosure">
          <summary>RPS provenance and public scope</summary>
          <div className="technical-disclosure-body">
            <p>
              The core worker source is the Real-Time Population Survey Generative AI Adoption Tracker by
              Bick, Blandin, and Deming, surfaced through FRED. The canonical registry contains 131
              work-focused series records: five national constructs, 60 industry records, and 66 occupation
              records.
            </p>
            <p>
              The source registry records owner permission for published aggregate project use and derived
              aggregate analysis. Release 1 publishes seven complete national-history quarters through Q2
              2026 plus the latest complete industry and occupation A/H/S cross-sections. Historical subgroup
              panels, bulk download, and generic source-query access remain outside the current public scope.
              Private source-input bytes are excluded from public release artifacts.
            </p>
            <p>
              <a href="https://fred.stlouisfed.org/release?rid=6">FRED RPS release page</a>
              {" · "}
              <a href="https://doi.org/10.1287/mnsc.2025.02523">Peer-reviewed RPS paper</a>
            </p>
          </div>
        </details>

        <details className="technical-disclosure">
          <summary>Public, private, and validation boundaries</summary>
          <div className="technical-disclosure-body">
            <dl className="definition-grid compact-definitions">
              <dt>Public release</dt>
              <dd>
                Contains source metadata, formulas, crosswalks, bounded attributed RPS views, longitudinal
                diagnostics, CPS/OEWS composition evidence, BTOS triangulation, methodology, and the technical
                essay.
              </dd>
              <dt>Private release-candidate workspace</dt>
              <dd>
                Holds authorized RPS source inputs used to validate the registered source history and
                regenerate release artifacts. Source-input files are hash-bound to each candidate and
                excluded from public review and release bundles.
              </dd>
              <dt>Composition evidence</dt>
              <dd>
                Contains Q2 2025 and Q2 2026 CPS composition artifacts, occupation-adjusted industry-context
                residual diagnostics, and 2025-05 OEWS robustness artifacts.
              </dd>
              <dt>Outside current claims</dt>
              <dd>
                Full historical RPS subgroup distribution, custom CPS design covariance, causal firm effects,
                and measured labor-productivity effects require additional evidence or publication rights.
              </dd>
            </dl>
            <p>
              Each promoted release passes source and data contracts, governance checks, type validation,
              optimized production builds, route smoke tests, and rendered browser accessibility checks. The
              release process binds those checks to the exact candidate and preserves prior release history.
            </p>
            <p>
              Human screen-reader traversal, physical mobile-device testing, and field Core Web Vitals remain
              outside current validation evidence. The public deployment is audited against the exact
              promoted release commit.
            </p>
          </div>
        </details>

        <p className="text-link"><Link href="/methodology">Read data &amp; methods →</Link></p>
      </section>
    </main>
  );
}
