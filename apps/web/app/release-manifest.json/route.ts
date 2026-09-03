import { configuredSiteBaseUrl } from "../../lib/site";

export const dynamic = "force-static";

export function GET() {
  const commitSha = process.env.RELEASE_COMMIT_SHA?.trim() || "UNBOUND";
  const dataMode = process.env.DATA_MODE?.trim() || "UNSET";

  return Response.json({
    schemaVersion: 1,
    product: "GenAI at Work",
    hostingTarget: "github-pages",
    dataMode,
    commitSha,
    siteBaseUrl: configuredSiteBaseUrl(),
    analytics: "disabled",
    clientMonitoring: "disabled",
    sourceBytesPublished: false,
  });
}
