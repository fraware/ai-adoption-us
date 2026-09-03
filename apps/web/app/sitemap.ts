import type { MetadataRoute } from "next";
import { absoluteSiteUrl } from "../lib/site";

const publicRoutes = [
  "/",
  "/explore/industries",
  "/explore/occupations",
  "/blog/after-adoption",
  "/methodology",
  "/sources",
] as const;

export default function sitemap(): MetadataRoute.Sitemap {
  return publicRoutes.flatMap((path) => {
    const url = absoluteSiteUrl(path);
    return url
      ? [
          {
            url,
            changeFrequency: "weekly" as const,
            priority: path === "/" ? 1 : 0.8,
          },
        ]
      : [];
  });
}
