import type { Metadata } from "next";
import Link from "next/link";
import { latestNational, loadObservations } from "../../../lib/data";
import { loadLongitudinalDiagnostics } from "../../../lib/longitudinal";

export const metadata: Metadata = { title: "From adoption to workflow" };

export default async function AfterAdoptionPage() {
  const [rows, longitudinal] = await Promise.all([
    loadObservations(),
    loadLongitudinalDiagnostics(),
  ]);
  const national = latestNational(rows);
  const adoption = national.get("adoption_work");
  const weekly = national.get("work_use_last_week");
  const daily = national.get("work_use_daily");
  const assisted = national.get("assisted_hours_share");
  const savings = national.get("reported_time_savings_share");

  const periods = longitudinal.input_scope.periods;
  const firstPeriod = periods[0];
  const lastPeriod = periods[periods.length - 1];
  const industry = longitudinal.rank_stability.industry;
  const occupation = longitudinal.rank_stability.occupation;
  const industryDominance = longitudinal.rank_stability_dominance.industry;
  const occupationDominance = longitudinal.rank_stability_dominance.occupation;
  const industryQuarters = Object.values(longitudinal.quarter_diagnostics.industry);
  const occupationQuarters = Object.values(longitudinal.quarter_diagnostics.occupation);
  const industryHBeatsAWaves = industryQuarters.filter((d) => d.r2_S_H > d.r2_S_A).length;
  const occupationABeatsHWaves = occupationQuarters.filter((d) => d.r2_S_A > d.r2_S_H).length;
  const occupationLooABeatsH = occupationQuarters.reduce((total, d) => total + d.loo_A_beats_H, 0);

  return (
    <main>
      <article className="reading">
        <p className="eyebrow">Technical essay</p>
        <h1>From adoption to workflow: measuring AI at work</h1>
        <p className="lede">
          Workplace GenAI diffusion is now large enough that adoption alone compresses too much
          information. {periods.length} common subgroup quarters from {firstPeriod} through {lastPeriod}
          reveal a second research problem: how reported use converts into recurring use, assisted working
          time, and reported savings.
        </p>

        {adoption && weekly && daily && assisted && savings ? (
          <p>
            In {adoption.period}, {adoption.value.toFixed(1)}% of employed U.S. adults aged 18–64
            reported using generative AI for work. {weekly.value.toFixed(1)}% reported work use in the
            prior week and {daily.value.toFixed(1)}% reported use on every workday. GenAI assisted
            {` ${assisted.value.toFixed(1)}% `}of total work hours, alongside reported counterfactual time
            savings equal to {savings.value.toFixed(1)}% of total work hours. Read together, these measures
            trace the distance between diffusion and depth of use.
          </p>
        ) : (
          <div className="callout">
            <p className="callout-label">Public release boundary</p>
            <p>
              This build excludes the bounded national observation view. The longitudinal findings below
              come from validated derived diagnostics, with private source-input bytes kept outside the
              public bundle.
            </p>
          </div>
        )}

        <section className="section" aria-labelledby="separate-objects">
          <h2 id="separate-objects">Adoption and conversion are separate empirical objects</h2>
          <p>
            Adoption measures reach. Recent and routine use measure recurrence. Assisted hours measure the
            share of working time in which GenAI is active. Reported savings ask respondents to estimate
            the additional time the same work would have required without GenAI. A single adoption rate
            cannot encode movement across these layers.
          </p>
          <p>
            This separation changes the economic question. Diffusion asks how widely a technology spreads
            across workers. Conversion asks how reported adoption translates into recurring workflow use,
            time allocation, and reported labor input released. Realized output sits further downstream and
            requires its own evidence.
          </p>
        </section>

        <section className="section" aria-labelledby="persistence">
          <h2 id="persistence">Adoption is more stable than workflow penetration</h2>
          <p>
            Across industries, the median pairwise rank correlation over the {periods.length} audited waves
            is {industry.A.median_pairwise.toFixed(2)} for adoption and {industry.H.median_pairwise.toFixed(2)}
            for assisted hours. Across occupations, the corresponding values are
            {` ${occupation.A.median_pairwise.toFixed(2)} and ${occupation.H.median_pairwise.toFixed(2)}.`}
            Adoption ranks exceed assisted-hours rank stability in
            {` ${industryDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${industryDominance.quarter_pairs} `}
            industry quarter-pair comparisons and
            {` ${occupationDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${occupationDominance.quarter_pairs} `}
            occupation comparisons.
          </p>
          <p>
            The cross-group geography of diffusion is more persistent than the geography of use intensity.
            Groups can retain similar relative positions in adoption and move more strongly in the share of
            working time assisted by GenAI. That difference places conversion at the center of the unresolved
            measurement problem.
          </p>
        </section>

        <section className="section" aria-labelledby="occupation-structure">
          <h2 id="occupation-structure">Occupations organize conversion more strongly than industries</h2>
          <p>
            In every audited quarter, both Pearson and Spearman correlations between adoption and assisted
            hours are higher across occupations than across industries. The adoption-to-penetration
            relationship is consistently tighter at the occupation level.
          </p>
          <p>
            Occupations encode task structure more directly than broad industries. Industry aggregates mix
            occupation composition with firm context and sampling variation. The additional industry wedge
            is an empirical target for further work; causal attribution requires data that resolve those
            channels separately.
          </p>
        </section>

        <section className="section" aria-labelledby="savings-structure">
          <h2 id="savings-structure">Reported savings organize differently across occupations and industries</h2>
          <p>
            Across occupations, adoption has the higher univariate R² for reported savings in
            {` ${occupationABeatsHWaves} of ${periods.length} `}waves and every one of the
            {` ${occupationLooABeatsH} `}leave-one-occupation comparisons. Across industries, assisted
            hours has the higher univariate R² in {industryHBeatsAWaves} of {periods.length} waves. The
            industry ordering shifts across quarters.
          </p>
          <p>
            The contrast constrains simple explanations of reported savings. Across occupations, breadth
            of adoption contains more cross-group information about reported savings than assisted-hour
            share throughout the audited window. Industry-level relationships display a less stable
            ordering, consistent with a larger role for composition and context at that level.
          </p>
        </section>

        <section className="section" aria-labelledby="composition-frontier">
          <h2 id="composition-frontier">Composition separates workforce mix from industry context</h2>
          <p>
            CPS occupation weights generate an industry counterfactual from national occupation-specific
            GenAI rates. Adoption uses worker-share weights; assisted hours and reported savings use
            actual-main-job-hour weights. Comparing observed industry values with these counterfactuals
            produces an occupation-adjusted industry-context residual.
          </p>
          <p>
            Release 1 treats that residual as a descriptive diagnostic. Organizational effects, management
            quality, efficiency, and productivity require separate identification. Full design-based
            uncertainty for the custom pooled CPS composition vectors remains unsupported, and OEWS
            provides an independent establishment-side robustness check.
          </p>
        </section>

        <section className="section" aria-labelledby="reported-savings">
          <h2 id="reported-savings">Reported savings measure perceived released time</h2>
          <p>
            The RPS asks users to estimate how many additional hours the same work would have required
            without GenAI. The resulting measure is a self-reported counterfactual estimate of released
            labor input. Observed productivity requires output data and an identification strategy linking
            AI use to changes in production.
          </p>
        </section>

        <p>
          The first workplace-AI question asked how widely GenAI had diffused. The evidence now supports a
          richer question: how adoption converts into recurring use, assisted working time, reported
          savings, and eventually realized outcomes. The observatory is built to keep those stages separate
          as the data improve.
        </p>

        <p className="note">
          Numeric longitudinal claims on this page are generated from the same versioned derived diagnostic
          artifact used by the explorers. Public rendering uses release-bound evidence and excludes private
          source-input history.
        </p>
        <p>
          <Link href="/explore/industries">Industry evidence</Link>
          {" · "}
          <Link href="/explore/occupations">Occupation evidence</Link>
          {" · "}
          <Link href="/methodology">Measurement contract</Link>
          {" · "}
          <Link href="/sources">Sources and provenance</Link>
        </p>
      </article>
    </main>
  );
}
