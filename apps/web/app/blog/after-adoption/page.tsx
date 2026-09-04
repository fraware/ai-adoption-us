import type { Metadata } from "next";
import Link from "next/link";
import { latestNational, loadObservations } from "../../../lib/data";
import { loadLongitudinalDiagnostics } from "../../../lib/longitudinal";

export const metadata: Metadata = { title: "After adoption" };

function priorYearPeriod(period: string): string | null {
  const match = /^(\d{4})-Q([1-4])$/.exec(period);
  if (!match) return null;
  return `${Number(match[1]) - 1}-Q${match[2]}`;
}

function percentGrowth(current: number, prior: number): number | null {
  if (prior <= 0) return null;
  return ((current / prior) - 1) * 100;
}

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

  const comparisonPeriod = adoption ? priorYearPeriod(adoption.period) : null;
  const priorNational = (metricId: string) =>
    comparisonPeriod
      ? rows.find(
          (row) =>
            row.entity_id === "us" && row.metric_id === metricId && row.period === comparisonPeriod,
        )
      : undefined;
  const priorAdoption = priorNational("adoption_work");
  const priorWeekly = priorNational("work_use_last_week");
  const priorAssisted = priorNational("assisted_hours_share");
  const priorSavings = priorNational("reported_time_savings_share");
  const adoptionGrowth = adoption && priorAdoption ? percentGrowth(adoption.value, priorAdoption.value) : null;
  const weeklyGrowth = weekly && priorWeekly ? percentGrowth(weekly.value, priorWeekly.value) : null;
  const assistedGrowth = assisted && priorAssisted ? percentGrowth(assisted.value, priorAssisted.value) : null;
  const savingsGrowth = savings && priorSavings ? percentGrowth(savings.value, priorSavings.value) : null;

  return (
    <main>
      <article className="reading">
        <p className="eyebrow">Technical essay</p>
        <h1>After adoption: measuring AI inside the workday</h1>
        <p className="lede">
          Workplace GenAI is now widespread enough to make adoption an incomplete summary. The central
          measurement problem is conversion: how reported adoption turns into recurring use, assisted
          working time, reported savings, and eventually realized economic outcomes.
        </p>

        {adoption && weekly && daily && assisted && savings ? (
          <>
            <p>
              In {adoption.period}, {adoption.value.toFixed(1)}% of employed U.S. adults aged 18–64
              reported using generative AI for work. {weekly.value.toFixed(1)}% reported work use in the
              prior week and {daily.value.toFixed(1)}% reported use on every workday. GenAI assisted
              {` ${assisted.value.toFixed(1)}% `}of total work hours; respondents reported counterfactual
              time savings equal to {savings.value.toFixed(1)}% of total work hours. These figures describe
              the same technology at different depths of use.
            </p>
            {comparisonPeriod &&
            adoptionGrowth !== null &&
            weeklyGrowth !== null &&
            assistedGrowth !== null &&
            savingsGrowth !== null ? (
              <p>
                From {comparisonPeriod} to {adoption.period}, work adoption rose {adoptionGrowth.toFixed(1)}%,
                weekly use rose {weeklyGrowth.toFixed(1)}%, assisted hours rose {assistedGrowth.toFixed(1)}%,
                and reported savings rose {savingsGrowth.toFixed(1)}%. The common direction still leaves
                distinct rates of movement across reach, recurrence, use intensity, and reported time released.
              </p>
            ) : null}
          </>
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

        <section className="section" aria-labelledby="conversion">
          <h2 id="conversion">Adoption measures reach. Conversion measures depth.</h2>
          <p>
            An adoption rate is a diffusion statistic: it counts workers who report using GenAI for work.
            Recurrence and time intensity require separate measurements. The observatory follows reported
            use through recent use, workday recurrence, assisted hours, reported time released, and the
            later outcome measures needed to study economic effects. Each stage changes the denominator and
            the claim that the data can support.
          </p>
          <p>
            Across {periods.length} common subgroup quarters from {firstPeriod} through {lastPeriod}, this
            separation is visible in the structure of the data. The cross-group map of adoption is more
            persistent than the map of assisted working time, and the relationship between the two changes
            with the level of aggregation.
          </p>
        </section>

        <section className="section" aria-labelledby="persistence">
          <h2 id="persistence">The geography of adoption is more stable than the geography of use</h2>
          <p>
            Across industries, the median pairwise rank correlation over the audited window is
            {` ${industry.A.median_pairwise.toFixed(2)} `}for adoption and
            {` ${industry.H.median_pairwise.toFixed(2)} `}for assisted hours. Across occupations, the
            corresponding values are {occupation.A.median_pairwise.toFixed(2)} and
            {` ${occupation.H.median_pairwise.toFixed(2)}.`} Adoption rankings exceed assisted-hours rank
            stability in
            {` ${industryDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${industryDominance.quarter_pairs} `}
            industry quarter-pair comparisons and
            {` ${occupationDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${occupationDominance.quarter_pairs} `}
            occupation comparisons.
          </p>
          <p>
            Groups retain their relative positions in adoption more consistently than their positions in
            assisted-hour share. Diffusion has a more persistent cross-group map than workflow penetration.
            The changing depth of use is a distinct empirical object, even among groups with comparatively
            stable adoption ranks.
          </p>
        </section>

        <section className="section" aria-labelledby="occupation-structure">
          <h2 id="occupation-structure">Occupations tie adoption to assisted time more tightly</h2>
          <p>
            In every audited quarter, both Pearson and Spearman correlations between adoption and assisted
            hours are higher across occupations than across industries. The repeated ordering places
            occupation structure at the center of the current conversion evidence.
          </p>
          <p>
            Industry aggregates combine occupation mix with firm context and sampling variation. The gap
            between the two aggregation levels defines a research target: explain the remaining industry
            variation with data that separate those channels. Causal attribution requires that stronger
            evidence.
          </p>
        </section>

        <section className="section" aria-labelledby="savings-structure">
          <h2 id="savings-structure">Reported savings split the occupation and industry stories</h2>
          <p>
            Across occupations, adoption has the higher univariate R² for reported savings in
            {` ${occupationABeatsHWaves} of ${periods.length} `}waves and every one of the
            {` ${occupationLooABeatsH} `}leave-one-occupation comparisons. Across industries, assisted
            hours has the higher univariate R² in {industryHBeatsAWaves} of {periods.length} waves, with the
            ordering changing across the audited window.
          </p>
          <p>
            At the occupation level, breadth of adoption contains more cross-group information about
            reported savings than assisted-hour share throughout the window. Industry-level relationships
            are less stable, leaving a larger role for composition and context in the descriptive pattern.
          </p>
        </section>

        <section className="section" aria-labelledby="composition-frontier">
          <h2 id="composition-frontier">Composition isolates one part of the industry variation</h2>
          <p>
            CPS occupation weights generate an industry counterfactual from national occupation-specific
            GenAI rates. Adoption uses worker-share weights; assisted hours and reported savings use
            actual-main-job-hour weights. Comparing observed industry values with these counterfactuals
            produces an occupation-adjusted industry-context residual.
          </p>
          <p>
            Release 1 treats that residual as a descriptive diagnostic. Organizational effects, management
            quality, efficiency, and productivity require separate identification. Full design-based
            uncertainty for the custom pooled CPS composition vectors remains unsupported. OEWS supplies an
            independent establishment-side robustness check.
          </p>
        </section>

        <section className="section" aria-labelledby="reported-savings">
          <h2 id="reported-savings">Reported savings stop short of productivity</h2>
          <p>
            The RPS asks users to estimate the additional hours the same work would have required without
            GenAI. The resulting measure is a self-reported counterfactual estimate of released labor input.
            Productivity requires observed output or value added plus an identification strategy linking
            changes in AI use to changes in production. The observatory reserves productivity claims for
            evidence that supports that link.
          </p>
        </section>

        <p>
          Adoption remains the first coordinate of workplace AI. The next coordinate is depth: how use
          recurs, how much working time receives AI assistance, how much time users report releasing, and
          how those changes connect to measured outcomes. A useful observatory keeps those stages separate
          as the evidence expands.
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
