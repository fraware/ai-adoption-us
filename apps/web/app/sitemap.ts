import type { MetadataRoute } from "next";
import { configuredSiteOrigin } from "../lib/site";

const publicRoutes = [
  "/",
  "/explore/industries",
  "/explore/occupations",
  "/blog/after-adoption",
  "/methodology",
  "/sources",
] as const;

export default function sitemap(): MetadataRoute.Sitemap {
  const origin = configuredSiteOrigin();
  if (!origin) return [];

  return publicRoutes.map((path) => ({
    url: new URL(path, origin).toString(),
    changeFrequency: "weekly",
    priority: path === "/" ? 1 : 0.8,
  }));
}
