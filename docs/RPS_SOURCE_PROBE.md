# Manual RPS authorized source probe

Status: **D-G1 operational tranche — manual live-source evidence path; D-G1 remains open**

Date: 2026-09-02

## Purpose

`.github/workflows/rps-source-probe.yml` provides a deliberately manual execution path for the authorized published-aggregate RPS/FRED source pipeline.

Its purpose is to answer a narrow operational question before any schedule or publication workflow is introduced: **does the current live provider state satisfy the registered 137-series provider contract, the 131-series observatory scope, the current definition/rights checks, and the deterministic RPS candidate build?**

The probe is not a release job. It cannot promote an observatory release and does not publish source observation bytes.

## Trigger and permissions

The workflow has only `workflow_dispatch` as a trigger. It has no `push`, `pull_request`, or scheduled trigger.

Repository permissions are restricted to:

```yaml
permissions:
  contents: read
```

This is intentional. D-G1 has not yet pinned a production source-check cadence, so the repository must not begin periodic source retrieval merely because the probe exists.

## Credential contract

The workflow requires the repository secret `FRED_API_KEY`.

The secret is supplied only to the probe job environment and is consumed by the existing `prepare_rps_refresh_candidate.py` API path. If the secret is absent, the workflow fails before source retrieval with an explicit credential error.

The workflow does not contain an HTML-scraping or manual-copy fallback.

The existence of this workflow does not establish that the secret is currently configured. A successful dispatched run is required evidence that the credential path is operational.

## Transient source-byte boundary

The live refresh writes its private snapshot under the runner's temporary filesystem:

```text
/tmp/rps-refresh/
```

The release-component build writes its private candidate package under:

```text
/tmp/rps-observatory/
```

Those locations are outside the checked-out public repository.

The temporary source materials include source observations and release `inputs/`. They exist only for the duration of the job and are not copied into the retained Actions artifact.

## Retained evidence

The workflow retains a 14-day GitHub Actions artifact containing only review-safe evidence:

```text
rps-probe-evidence/
  source-candidate-summary.json
  rps-component-release.json
  observatory-artifacts/
    longitudinal_diagnostics.json
    quarter_diagnostics.csv
    rank_stability.csv
    validation_checks.json
```

The artifact deliberately excludes:

- `rps_source_snapshot.json`;
- `rps_refresh_diff.json`;
- every release `inputs/` object;
- any copied raw/source observation bundle.

The source-candidate summary retains the scientific source-content hash, private snapshot-file hash, inventory counts, observation count, retrieval timestamp, and change-count summary without carrying the source observation rows.

The component release manifest retains source-object sizes and SHA-256 identities, source vintage identity, definition/taxonomy identity, derived artifact hashes, diagnostics, and claim traceability while declaring `data_mode = derived_only` and `source_input_bytes_publication = false`.

The derived longitudinal artifacts are within the already approved derived-aggregate publication scope.

## Why the detailed refresh diff is excluded

A revision diff may contain old and new source values for changed cells. The manual probe does not need to redistribute those values through a public-repository Actions artifact to establish whether a source change occurred.

The retained summary carries change counts and cryptographic identities. Detailed cell-level inspection remains part of a private source-review execution path.

## Candidate construction inside the probe

After live retrieval, the workflow immediately executes `prepare_rps_observatory_candidate.py` against the exact transient source snapshot. This verifies that the current source state can pass the source-to-derived transformation contract on the same runner.

Candidate construction remains non-promoting. The generated release ID is a run-scoped probe slug:

`rps-probe-<GitHub run ID>`

The workflow does not invoke `scripts/observatory_release.py`.

## Evidence checks before artifact upload

Before uploading evidence, the workflow checks that:

- no source snapshot was copied into the evidence directory;
- no `inputs/` directory exists in the evidence directory;
- no detailed refresh diff was copied into the evidence directory;
- the source-candidate summary says `public_raw_observations_included = false`;
- the component manifest says `source_input_bytes_publication = false`;
- the component manifest remains `data_mode = derived_only`.

Failure of any check prevents a successful probe artifact.

## Execution result categories

A dispatched run has four materially different outcomes:

1. **credential failure** — `FRED_API_KEY` is unavailable; no source claim follows;
2. **source-contract failure** — provider inventory, identity, rights, definition, period, value, or coverage checks fail; the source must not advance;
3. **candidate-build failure** — retrieval succeeds but deterministic RPS release-component validation or diagnostics fail; the source must not advance;
4. **successful probe** — the current source state satisfies the implemented source and component contracts and a rights-safe evidence artifact is retained.

A successful probe still does not authorize publication or establish a global observatory baseline.

## What this probe does not solve

The public repository does not currently provide a durable private source-byte archive suitable for later release staging. The Actions artifact intentionally omits those bytes.

Consequently, this manual probe is evidence of live source compatibility, not the durable private-vintage store required for a future production release system. A production refresh that must later be staged without re-fetching needs an explicitly approved private storage mechanism or another reproducible source-vintage strategy.

The probe also does not yet compare against a durable previous private source snapshot, so it cannot by itself provide the full cell-level historical revision audit required for recurring production updates.

## Remaining D-G1 sequence

After this workflow is merged:

1. confirm whether the `FRED_API_KEY` repository secret is configured;
2. dispatch the probe and inspect the actual live source evidence;
3. record the observed provider inventory, current source vintage hash, periods, definition/taxonomy hashes, diagnostic state, and derived artifact hashes;
4. resolve any provider or definition drift before proceeding;
5. choose the durable private-vintage storage/retrieval mechanism needed for recurring historical revision comparisons;
6. pin source-check cadence and release-date handling only after the live source behavior is observed;
7. compose and review the first complete global observatory baseline before any promotion;
8. rehearse a subsequent wave/revision against a frozen baseline.

D-G1 remains open until the production feed is reproducibly executable with retained provenance and the reviewed release controls are exercised end to end.
