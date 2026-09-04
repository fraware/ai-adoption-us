import Link from "next/link";

export function ReleaseNotice() {
  const mode = process.env.DATA_MODE;

  if (mode === "audit_snapshot") {
    return (
      <div className="release-strip release-strip-private" role="status">
        <div>
          <strong>Private research mode</strong>
          <span>Audited subgroup observations are loaded locally under redistribution controls.</span>
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
            Public artifacts contain contracted aggregate presentation views and derived evidence. Private
            source-input bytes and unrestricted historical subgroup data stay outside the release.
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
          <span>The live adapter stays fail-closed until its operational activation gates pass.</span>
          <Link href="/sources">Source status</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="release-strip release-strip-warning" role="alert">
      <div>
        <strong>Data mode is unconfigured</strong>
        <span>Set DATA_MODE explicitly to run the publication.</span>
      </div>
    </div>
  );
}
