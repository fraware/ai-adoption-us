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
          <strong>Release 1 · rights-bounded public evidence</strong>
          <span>
            The public bundle is limited to contracted aggregate presentation views and derived artifacts;
            private source-input bytes and unrestricted historical subgroup data remain excluded.
          </span>
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
          <span>The live adapter remains fail-closed until its operational activation gates pass.</span>
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
