import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Explore",
};

export default function ExplorePage() {
  return (
    <main>
      <section className="hero hero-compact" aria-labelledby="explore-title">
        <p className="eyebrow">Explore</p>
        <h1 id="explore-title">Two views of workplace AI.</h1>
        <p className="lede">
          Occupation and industry reveal different structure in how GenAI spreads through work.
        </p>
      </section>

      <section className="explore-index" aria-label="Explore workplace AI by analytical view">
        <article className="explore-index-row">
          <div>
            <p className="eyebrow">01</p>
            <h2>Occupations</h2>
          </div>
          <div>
            <p>
              Across every audited wave, adoption and assisted working time align more tightly across
              occupations than across industries.
            </p>
            <p className="text-link"><Link href="/explore/occupations">Explore occupations →</Link></p>
          </div>
        </article>

        <article className="explore-index-row">
          <div>
            <p className="eyebrow">02</p>
            <h2>Industries</h2>
          </div>
          <div>
            <p>
              Industry data expose variation beyond occupation mix and add a separate firm-side comparison
              through BTOS.
            </p>
            <p className="text-link"><Link href="/explore/industries">Explore industries →</Link></p>
          </div>
        </article>
      </section>

      <section className="section compact-note" aria-labelledby="methods-link-heading">
        <p className="eyebrow">Measurement</p>
        <h2 id="methods-link-heading">Definitions and source boundaries stay close to the data.</h2>
        <p className="text-link"><Link href="/methodology">Read data &amp; methods →</Link></p>
      </section>
    </main>
  );
}
