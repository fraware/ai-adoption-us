import type { Metadata } from "next";
import Link from "next/link";
import { ReleaseNotice } from "../components/ReleaseNotice";
import { absoluteSiteUrl, configuredSiteBaseUrl } from "../lib/site";
import "./globals.css";

const siteBaseUrl = configuredSiteBaseUrl();
const homeUrl = absoluteSiteUrl("/");
const staticContentSecurityPolicy = [
  "default-src 'self'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
  "img-src 'self' data:",
  "font-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "script-src 'self' 'unsafe-inline'",
  "connect-src 'self'",
].join("; ");

export const metadata: Metadata = {
  ...(siteBaseUrl ? { metadataBase: new URL(`${siteBaseUrl}/`) } : {}),
  title: {
    default: "GenAI at Work",
    template: "%s · GenAI at Work",
  },
  description:
    "An auditable technical data publication separating workplace GenAI adoption, workflow penetration, and reported time savings.",
  referrer: "strict-origin-when-cross-origin",
  ...(homeUrl ? { alternates: { canonical: homeUrl } } : {}),
  openGraph: {
    type: "website",
    siteName: "GenAI at Work",
    title: "GenAI at Work",
    description:
      "An auditable technical data publication separating workplace GenAI adoption, workflow penetration, and reported time savings.",
    ...(homeUrl ? { url: homeUrl } : {}),
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <meta httpEquiv="Content-Security-Policy" content={staticContentSecurityPolicy} />
      </head>
      <body>
        <a className="skip-link" href="#main-content">Skip to main content</a>
        <ReleaseNotice />
        <header className="site">
          <div className="site-header-inner">
            <Link className="brand" href="/">GenAI at Work</Link>
            <nav aria-label="Primary navigation">
              <Link href="/explore/industries">Industries</Link>
              <Link href="/explore/occupations">Occupations</Link>
              <Link href="/blog/after-adoption">Essay</Link>
              <Link href="/methodology">Methodology</Link>
              <Link href="/sources">Sources</Link>
            </nav>
          </div>
        </header>
        <div id="main-content" tabIndex={-1}>{children}</div>
        <footer className="site-footer">
          <div>
            <p><strong>GenAI at Work</strong> is a measurement-first technical publication.</p>
            <p>
              Reported time savings are self-reported counterfactual estimates, not observed labor
              productivity. Longitudinal subgroup results are descriptive and aggregate.
            </p>
            <p className="footer-links">
              <Link href="/methodology">Methodology</Link>
              <Link href="/sources">Sources &amp; provenance</Link>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
