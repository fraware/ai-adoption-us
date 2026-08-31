import type { Metadata } from "next";
import { latestNational, loadObservations } from "../../../lib/data";
import { loadLongitudinalDiagnostics } from "../../../lib/longitudinal";

export const metadata: Metadata = { title: "After adoption" };

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

  const industry = longitudinal.rank_stability.industry;
  const occupation = longitudinal.rank_stability.occupation;
  const industryQuarters = Object.values(longitudinal.quarter_diagnostics.industry);
  const industryHBeatsAWaves = industryQuarters.filter((d) => d.r2_S_H > d.r2_S_A).length;

  return (
    <main>
      <article className="reading">
        <p className="eyebrow">Technical essay</p>
        <h1>After adoption: where AI enters actual work</h1>
        <p className="lede">
          Adoption is the most visible workplace-AI statistic. Five waves of subgroup data show why it
          is only the first layer of the economic story.
        </p>

        {adoption && weekly && daily && assisted && savings ? (
          <p>
            In {adoption.period}, {adoption.value.toFixed(1)}% of employed U.S. adults aged 18–64
            reported using generative AI for work. {weekly.value.toFixed(1)}% had used it for work in
            the prior week, while {daily.value.toFixed(1)}% used it every workday. GenAI was actively
            assisting about {assisted.value.toFixed(1)}% of total work hours, and respondents reported
            time savings equal to {savings.value.toFixed(1)}% of total work hours.
          </p>
        ) : (
          <div className="callout">
            <p className="callout-label">Public release boundary</p>
            <p>
              This release does not contain a rights-cleared national observation feed. The empirical
              claims below are generated from the validated five-wave derived diagnostics.
            </p>
          </div>
        )}

        <section className="section" aria-labelledby="five-objects">
          <h2 id="five-objects">Five objects that public discussion collapses into one</h2>
          <p>
            Availability, adoption, routine use, workflow penetration, and economic realization are not
            synonyms. A worker can have adopted a model without using it this week. A weekly user can
            spend only a small fraction of working time actively using it. Time released by a tool need
            not translate one-for-one into measured output.
          </p>
        </section>

        <section className="section" aria-labelledby="persistence">
          <h2 id="persistence">Adoption looks more persistent than depth of use</h2>
          <p>
            Across industries, the median pairwise rank correlation over the five audited waves is
            {` ${industry.A.median_pairwise.toFixed(2)} `}for adoption and {industry.H.median_pairwise.toFixed(2)} for assisted hours.
            Across occupations the corresponding values are {occupation.A.median_pairwise.toFixed(2)} and
            {` ${occupation.H.median_pairwise.toFixed(2)}.`} Adoption ranks are more stable than
            assisted-hours ranks in every one of the ten possible quarter-pair comparisons at both
            aggregation levels.
          </p>
          <p>
            This supports a useful empirical distinction. The relative ranking of industries and occupations on adoption is comparatively persistent, while
            their rankings on the share of working time assisted by GenAI are considerably more variable. That does not prove a mechanism, but it locates the unexplained
            variation more precisely.
          </p>
        </section>

        <section className="section" aria-labelledby="occupation-structure">
          <h2 id="occupation-structure">Adoption and penetration are more tightly aligned across occupations</h2>
          <p>
            In every audited quarter, both Pearson and Spearman correlations between adoption and
            assisted hours are higher across occupations than across industries. The aggregate adoption-to-penetration relationship is therefore more tightly aligned across
            occupations than across broad industry categories.
          </p>
          <p>
            The interpretation must remain limited. Occupations capture task bundles, while industries
            combine occupations with firm composition, workflow design, policy, regulation, worker
            selection, technology stacks, and sampling variation. The additional industry wedge is a
            research object; the current aggregate data do not identify it as an organizational effect.
          </p>
        </section>

        <section className="section" aria-labelledby="wave-dependence">
          <h2 id="wave-dependence">One attractive Q2 result does not survive as a universal rule</h2>
          <p>
            In Q2 2026, assisted hours explain more cross-industry variation in reported savings than
            adoption does. Across the full five-wave window, however, that ordering occurs in only
            {` ${industryHBeatsAWaves} of ${longitudinal.input_scope.periods.length} waves.`} The relationship changes direction. The publication therefore reports the wave-by-wave
            evidence instead of turning the latest quarter into a structural claim.
          </p>
        </section>

        <section className="section" aria-labelledby="savings-not-productivity">
          <h2 id="savings-not-productivity">Reported time saved is not productivity</h2>
          <p>
            The RPS asks users how many additional hours they believe the same work would have required
            without GenAI. That is a counterfactual survey measure of perceived released labor input. It
            is not observed labor productivity. Released time may become more output, higher quality,
            additional checking, different work, or something else entirely.
          </p>
        </section>

        <section className="section" aria-labelledby="composition-frontier">
          <h2 id="composition-frontier">The next empirical frontier is composition</h2>
          <p>
            The next test is whether industry differences remain once occupational composition is held
            fixed. That requires worker-share weights for adoption and actual-main-job-hour weights for
            assisted-hours and reported-savings counterfactuals. Until the required CPS microdata are
            executed, this project does not label the remaining industry variation as organizational
            amplification.
          </p>
        </section>

        <p className="note">
          All numeric longitudinal claims on this page are generated from the same versioned derived
          diagnostic artifact used by the explorers. The public release does not require the private raw
          audit fixture to render them.
        </p>
      </article>
    </main>
  );
}
