import Link from "next/link";

export function ReleaseNotice() {
  const mode = process.env.DATA_MODE;

  if (mode === "audit_snapshot") {
    return (
      <div className="release-strip release-strip-private" role="status">
        <div>
          <strong>Private research mode</strong>
          <span>Audited subgroup observations are loaded locally and are not cleared for redistribution.</span>
        </div>
      </div>
    );
  }

  if (mode === "derived_only") {
    return (
      <div className="release-strip" role="status">
        <div>
          <strong>Public candidate · derived diagnostics only</strong>
          <span>Raw RPS observations are excluded from this bundle.</span>
          <Link href="/sources">Source and rights boundary</Link>
        </div>
      </div>
    );
  }

  if (mode === "fred_live_no_store") {
    return (
      <div className="release-strip" role="status">
        <div>
          <strong>Reviewed live-source mode</strong>
          <span>The live adapter remains fail-closed in this candidate.</span>
          <Link href="/sources">Source status</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="release-strip release-strip-warning" role="alert">
      <div>
        <strong>Data mode is not configured</strong>
        <span>Set DATA_MODE explicitly before running the publication.</span>
      </div>
    </div>
  );
}
