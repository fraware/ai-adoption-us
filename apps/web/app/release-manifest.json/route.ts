import { configuredSiteOrigin } from "../../lib/site";

export const dynamic = "force-static";

export function GET() {
  const commitSha =
    process.env.RELEASE_COMMIT_SHA?.trim() ||
    process.env.VERCEL_GIT_COMMIT_SHA?.trim() ||
    "UNBOUND";
  const dataMode = process.env.DATA_MODE?.trim() || "UNSET";

  return Response.json(
    {
      schemaVersion: 1,
      product: "GenAI at Work",
      dataMode,
      commitSha,
      siteOrigin: configuredSiteOrigin(),
      analytics: "disabled",
      clientMonitoring: "disabled",
    },
    {
      headers: {
        "Cache-Control": "public, max-age=0, must-revalidate",
      },
    },
  );
}
