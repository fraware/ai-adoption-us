import type { Metadata } from "next";
import Link from "next/link";
import { StabilityBars } from "../../../components/StabilityBars";
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
      <article className="reading essay-reading">
        <p className="eyebrow">Technical essay</p>
        <h1>After adoption</h1>
        <p className="lede">
          Workplace GenAI is widespread enough that adoption alone no longer describes the workday. The
          next measurement problem is conversion: how reported adoption turns into recurring use, assisted
          working time, reported savings, and realized economic outcomes.
        </p>

        {adoption && weekly && daily && assisted && savings ? (
          <>
            <div className="essay-facts" aria-label={`National workplace GenAI measures for ${adoption.period}`}>
              <div className="essay-fact">
                <span>Work adoption</span>
                <strong>{adoption.value.toFixed(1)}%</strong>
                <p>{adoption.period}</p>
              </div>
              <div className="essay-fact">
                <span>Work hours assisted</span>
                <strong>{assisted.value.toFixed(1)}%</strong>
                <p>{assisted.period}</p>
              </div>
              <div className="essay-fact">
                <span>Reported time savings</span>
                <strong>{savings.value.toFixed(1)}%</strong>
                <p>{savings.period}</p>
              </div>
            </div>
            <p>
              In {adoption.period}, {weekly.value.toFixed(1)}% of employed U.S. adults aged 18–64 reported
              work use in the prior week and {daily.value.toFixed(1)}% reported use on every workday. The
              three headline measures above describe reach, active assistance, and reported time released.
            </p>
            {comparisonPeriod &&
            adoptionGrowth !== null &&
            weeklyGrowth !== null &&
            assistedGrowth !== null &&
            savingsGrowth !== null ? (
              <p>
                From {comparisonPeriod} to {adoption.period}, work adoption rose {adoptionGrowth.toFixed(1)}%,
                weekly use rose {weeklyGrowth.toFixed(1)}%, assisted hours rose {assistedGrowth.toFixed(1)}%,
                and reported savings rose {savingsGrowth.toFixed(1)}%. Their rates of movement differ across
                reach, recurrence, use intensity, and reported time released.
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

        <section className="section essay-section" aria-labelledby="reach-depth">
          <p className="eyebrow">01 · Reach and depth</p>
          <h2 id="reach-depth">Diffusion has a more stable map than workflow penetration.</h2>
          <p>
            Adoption counts workers who report using GenAI for work. Recurrence and time intensity answer
            different questions. Across {periods.length} common subgroup quarters from {firstPeriod} through
            {lastPeriod}, the cross-group ordering of adoption is more persistent than the ordering of
            assisted working time.
          </p>

          <StabilityBars
            title={`Median pairwise rank correlation across ${periods.length} audited waves`}
            bars={[
              { label: "Industry adoption", value: industry.A.median_pairwise },
              { label: "Industry assisted hours", value: industry.H.median_pairwise },
              { label: "Occupation adoption", value: occupation.A.median_pairwise },
              { label: "Occupation assisted hours", value: occupation.H.median_pairwise },
            ]}
          />

          <p className="note">
            Adoption rankings exceed assisted-hours rank stability in
            {` ${industryDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${industryDominance.quarter_pairs} `}
            industry quarter-pair comparisons and
            {` ${occupationDominance.adoption_rank_corr_gt_assisted_hours_rank_corr} of ${occupationDominance.quarter_pairs} `}
            occupation comparisons.
          </p>
        </section>

        <section className="section essay-section" aria-labelledby="occupation-structure">
          <p className="eyebrow">02 · Occupation structure</p>
          <h2 id="occupation-structure">Occupation organizes conversion more tightly.</h2>
          <p>
            In every audited quarter, both Pearson and Spearman correlations between adoption and assisted
            hours are higher across occupations than across industries. At the occupation level, adoption
            also has the higher univariate R² for reported savings in
            {` ${occupationABeatsHWaves} of ${periods.length} `}waves and all
            {` ${occupationLooABeatsH} `}leave-one-occupation checks.
          </p>
          <p>
            The repeated ordering makes occupation the strongest organizing layer in the current aggregate
            evidence. Industry-level relationships are less stable: assisted hours has the higher univariate
            R² for reported savings in {industryHBeatsAWaves} of {periods.length} waves, with the ordering
            changing across the audited window.
          </p>
          <p className="text-link"><Link href="/explore/occupations">Explore occupation evidence →</Link></p>
        </section>

        <section className="section essay-section" aria-labelledby="industry-context">
          <p className="eyebrow">03 · Industry context</p>
          <h2 id="industry-context">Occupation mix explains one layer of industry variation.</h2>
          <p>
            CPS occupation weights generate an industry counterfactual from national occupation-specific
            GenAI rates. Adoption uses worker-share weights; assisted hours and reported savings use
            actual-main-job-hour weights. Observed industry values minus these counterfactuals produce an
            occupation-adjusted industry-context residual.
          </p>
          <p>
            Release 1 treats that residual as a descriptive diagnostic. Organizational effects, management
            quality, efficiency, and productivity require separate identification. Full design-based
            uncertainty for the custom pooled CPS composition vectors remains unsupported. OEWS supplies an
            independent establishment-side robustness check.
          </p>
          <p className="text-link"><Link href="/explore/industries">Explore industry evidence →</Link></p>
        </section>

        <section className="section essay-section" aria-labelledby="reported-savings">
          <p className="eyebrow">04 · Interpretation</p>
          <h2 id="reported-savings">Reported savings stop short of productivity.</h2>
          <p>
            RPS users estimate the additional hours the same work would have required without GenAI. The
            resulting measure is a self-reported counterfactual estimate of released labor input.
            Productivity requires observed output or value added plus an identification strategy linking
            changes in AI use to changes in production.
          </p>
          <p>
            Adoption remains the first coordinate of workplace AI. Depth is the next: recurrence, assisted
            working time, reported time released, and eventually measured outcomes. Keeping those stages
            separate makes the observatory useful as the evidence expands.
          </p>
        </section>

        <div className="essay-endnote">
          <p>
            Numeric longitudinal claims on this page come from the same versioned derived diagnostic artifact
            used by the explorers. Public rendering uses release-bound evidence and excludes private
            source-input history.
          </p>
          <p>
            <Link href="/methodology">Data &amp; methods</Link>
            {" · "}
            <Link href="/sources">Sources and provenance</Link>
          </p>
        </div>
      </article>
    </main>
  );
}
