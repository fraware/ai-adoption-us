import type { MetadataRoute } from "next";
import { configuredSiteOrigin } from "../lib/site";

export default function robots(): MetadataRoute.Robots {
  const origin = configuredSiteOrigin();

  return {
    rules: {
      userAgent: "*",
      allow: "/",
    },
    ...(origin ? { sitemap: `${origin}/sitemap.xml`, host: origin } : {}),
  };
}
