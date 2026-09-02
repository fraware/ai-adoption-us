# RPS source-check and release cadence policy

Status: **D-G1 cadence pinned; periodic execution not activated**

Date: 2026-09-02

## Decision

The RPS production feed separates three clocks that must never be conflated:

1. **source observation frequency** — quarterly;
2. **source-check cadence** — weekly, Wednesday at 18:00 UTC;
3. **publication cadence** — no fixed schedule; publication occurs only after a changed source has produced a reviewed, CI-passed, globally composed observatory release candidate.

The source-check cadence is pinned in `data/registry/rps_refresh_policy.json`. Periodic execution is intentionally **not activated yet**.

## Evidence basis

Current FRED metadata for the Real-Time Population Survey Generative Artificial Intelligence Adoption Tracker reports:

- source frequency: `Quarterly`;
- latest currently observed period: Q2 2026;
- current series update: August 4, 2026;
- `Next Release Date: Not Available` on the FRED series surface.

Primary reference surfaces checked on September 2, 2026:

- `https://fred.stlouisfed.org/series/RPSGENAIUSAGESHAREIND9`
- `https://fred.stlouisfed.org/series/RPSGENAIUSAGESHAREALL`

The weekly check is therefore an observatory operating policy, not a claim about the source publisher's release calendar.

## Why weekly

A quarterly series does not justify daily production retrieval absent evidence of daily revision behavior. Conversely, waiting for a presumed quarterly release date is unsafe because the current FRED surface provides no next-release date.

A weekly check provides:

- a maximum nominal detection lag of seven days for an upstream change;
- low retrieval burden relative to daily polling;
- no dependence on an unpublished release calendar;
- enough separation between source detection and scientific/editorial publication review.

Wednesday 18:00 UTC is a stable operational slot. It is not inferred from a guaranteed publisher weekday. The weekday/time may be changed only through an explicit policy revision with recorded rationale.

## Activation remains deferred

The periodic schedule remains disabled until all four activation conditions are evidenced:

1. an actual `RPS live validation` run succeeds on merged `main`;
2. `FRED_API_KEY` is thereby verified in the actual execution environment;
3. an operator-controlled private vintage backend is configured;
4. a write/read/verify rehearsal against that private backend passes.

`.github/workflows/rps-live-validation.yml` may run automatically on relevant `main` changes and may also be dispatched manually. That validation trigger is deliberately distinct from the **periodic weekly source-check schedule**, which remains absent until all activation gates pass.

This separation allows the live credential/source path to be proven without creating recurring network retrievals before exact source bytes can be retained durably in the production environment.

## Source-check state machine

The executable policy is implemented in `src/genai_at_work/rps_refresh_policy.py`.

### Unchanged source

When the validated source summary reports `revision_status = unchanged` with zero changes:

- do not archive the exact source snapshot durably;
- do not rebuild an observatory candidate;
- do not stage a release;
- do not publish;
- retain only review-safe check evidence.

The source bytes may remain transient because the scientific content is identical to the already archived predecessor. This avoids accumulating redundant private snapshots that differ only in retrieval/realtime envelopes.

### Baseline, new wave, or ordinary revision

For `baseline`, `new_wave`, `revision`, or `mixed` source content without definition drift:

- archive the exact source snapshot privately;
- retain the detailed private diff when a predecessor exists;
- build the RPS observatory candidate component;
- require human scientific/editorial/rights review;
- do not stage automatically;
- do not publish automatically.

Staging remains an explicit release operation because the global observatory release may contain components beyond RPS.

### Definition or taxonomy change

A detected definition/taxonomy change is archived privately for provenance and then blocked from the ordinary candidate path.

It requires an explicit specification decision before the release pipeline may reinterpret the source under a new definition contract.

### Rights change

A rights change blocks source advancement and requires an explicit rights decision. Review of scientific results cannot override a changed rights contract.

### Inventory or coverage failure

Missing/unexpected series, missing periods, or failed coverage block progression and require source-contract review.

### Data-mode change

A change from `derived_only` or another data-mode migration is a release-contract migration and cannot occur through ordinary wave processing.

## Publication is event-driven, not scheduled

A successful source check is not a publication trigger.

A source change is not a publication trigger.

A successful candidate build is not a publication trigger.

Publication requires all of the following:

- exact changed source content archived privately;
- deterministic dependent artifacts regenerated;
- required diagnostics passed;
- affected public claims identified;
- complete global observatory release composition resolved;
- CI passed on the exact candidate implementation;
- scientific/editorial/source-rights review bound to the exact staged hashes;
- explicit promotion through the observatory release engine.

There is no weekly, monthly, or quarterly automatic-publication rule.

## Retention policy

The cadence policy distinguishes check evidence from source-vintage evidence.

### Unchanged checks

Exact source bytes remain transient. Rights-safe live-validation/check evidence may be retained for 14 days in GitHub Actions.

### Content-changing vintages

Exact source bytes are retained in the private vintage archive until an explicit rights or retention decision changes that policy. This includes blocked definition revisions because they are part of the upstream provenance history.

### Release-referenced vintages

A private vintage referenced by a promoted release is retained for the lifetime of the corresponding release history, subject to any later source-rights requirement that legally or contractually changes storage permission.

No automatic deletion policy may remove bytes required to reproduce a still-governed immutable release without an explicit release/rights migration decision.

## Future periodic schedule activation

Once the four activation gates are evidenced, the implementation may add a scheduled workflow equivalent to:

```text
weekly / Wednesday / 18:00 UTC
```

That future periodic workflow must:

1. retrieve and validate the source;
2. compare against the exact prior private vintage;
3. route the result through the pinned policy state machine;
4. archive only baseline/content-changing source bytes;
5. preserve review-safe operational evidence for unchanged checks;
6. never stage or publish automatically.

The schedule change must be its own reviewed repository change. It must not be smuggled into an unrelated data or website update.

## Remaining D-G1 dependencies

Cadence is specified independently of backend selection. The remaining runtime dependencies are:

- a successful automatic live validation on merged `main`;
- confirmation of the actual current 137/131/6 provider state from that run;
- a configured operator-controlled private vintage backend;
- private backend write/read/verify evidence;
- activation of the pinned weekly schedule only after those gates pass;
- complete global observatory baseline composition/review/promotion before any global release claim;
- subsequent-wave or source-revision rehearsal against a frozen predecessor.

Until the periodic activation conditions are met, the policy remains `PINNED_NOT_ACTIVATED` even though one-off live validation may run automatically on relevant repository changes.
