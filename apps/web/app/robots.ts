import type { MetadataRoute } from "next";
import { absoluteSiteUrl, configuredSiteBaseUrl } from "../lib/site";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = configuredSiteBaseUrl();
  const sitemapUrl = absoluteSiteUrl("/sitemap.xml");

  return {
    rules: {
      userAgent: "*",
      allow: "/",
    },
    ...(baseUrl && sitemapUrl ? { sitemap: sitemapUrl, host: baseUrl } : {}),
  };
}
