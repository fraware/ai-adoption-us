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

const siteDescription =
  "A U.S. data observatory measuring how reported GenAI adoption turns into recurring use, assisted working time, and reported time savings.";

export const metadata: Metadata = {
  ...(siteBaseUrl ? { metadataBase: new URL(`${siteBaseUrl}/`) } : {}),
  title: {
    default: "GenAI at Work",
    template: "%s · GenAI at Work",
  },
  description: siteDescription,
  referrer: "strict-origin-when-cross-origin",
  ...(homeUrl ? { alternates: { canonical: homeUrl } } : {}),
  openGraph: {
    type: "website",
    siteName: "GenAI at Work",
    title: "GenAI at Work",
    description: siteDescription,
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
            <p><strong>GenAI at Work</strong> measures diffusion and depth of use in U.S. workplace generative AI.</p>
            <p>
              Reported time savings are survey-based counterfactual estimates. Labor productivity and other
              realized outcomes require separate outcome evidence.
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
