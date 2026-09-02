# RPS live-source validation

Status: **D-G1 live validation path — automatically exercised on relevant `main` changes; non-promoting**

Date: 2026-09-02

## Purpose

`.github/workflows/rps-live-validation.yml` is the repository's canonical live-source validation path for the authorized published-aggregate RPS/FRED feed.

It replaces the earlier manual-only `rps-source-probe.yml`. The prior file was present in the repository but was not reliably surfaced as a runnable workflow in the GitHub Actions UI, so the project no longer depends on an operator finding or manually dispatching it.

The live-validation workflow answers a narrower, auditable question: **can the current live provider state be retrieved with the authorized credential, satisfy the exact 137-series provider inventory / 131-series observatory contract, pass rights and construct checks, rehearse immutable private-vintage storage, and produce the deterministic derived RPS observatory component?**

It is not a publication or promotion job.

## Trigger

The workflow runs automatically on pushes to `main` when the live-source contract itself changes, including the workflow file, the RPS retrieval/release/archive modules, operator commands, and registered source manifests. The workflow also retains a `workflow_dispatch` trigger as an optional operator convenience, but D-G1 no longer depends on manual dispatch for validation.

The first merge that adds this workflow therefore constitutes an automatic live execution attempt on the exact merged code, assuming the configured repository secret is available.

No periodic schedule is enabled here. Periodic source-check activation remains governed separately by `data/registry/rps_refresh_policy.json`.

## Permissions and credential contract

Repository permissions remain restricted to:

```yaml
permissions:
  contents: read
```

The workflow requires the repository Actions secret:

`FRED_API_KEY`

The credential is supplied only to the validation job environment. Absence of the secret fails explicitly before source retrieval. There is no HTML-scraping or manual-copy fallback.

A successful workflow run is evidence that the credential path was operational for that run. Merely having the workflow file or secret configuration is not treated as successful live retrieval.

## Live transaction

The workflow performs four ordered stages on one runner:

1. retrieve and validate the live RPS aggregate source into `/tmp/rps-refresh`;
2. rehearse the immutable private-vintage archive contract under `/tmp/rps-private-vintage`;
3. build the non-promoting RPS observatory component under `/tmp/rps-observatory`;
4. assemble and upload only rights-safe review evidence.

The archive rehearsal verifies the exact-byte package, scientific content identity, private rights boundary, immutable namespace, and archive implementation. The rehearsal root is intentionally transient and therefore does **not** claim durable production archival.

## Source-byte boundary

Raw/source observation material remains on the runner temporary filesystem. The retained GitHub Actions artifact deliberately excludes:

- `rps_source_snapshot.json`;
- `rps_refresh_diff.json`;
- all release `inputs/` objects;
- any copied raw/source observation bundle.

No source observation file is written into the checked-out public repository.

## Retained evidence

The 14-day rights-safe Actions artifact contains:

```text
rps-live-validation-evidence/
  live-validation-summary.json
  source-candidate-summary.json
  private-vintage-manifest.json
  rps-component-release.json
  observatory-artifacts/
    longitudinal_diagnostics.json
    quarter_diagnostics.csv
    rank_stability.csv
    validation_checks.json
```

`live-validation-summary.json` records run identity, source scientific hash, exact private snapshot-file hash, inventory and observation counts, source revision status, archive-rehearsal result, candidate-build result, and explicit non-promotion / no-raw-publication flags.

`private-vintage-manifest.json` contains hashes and provenance only; the exact archived source bytes remain transient in this workflow.

## Rights and release safeguards

Before artifact upload, the workflow verifies that:

- `public_raw_observations_included = false`;
- `source_input_bytes_publication = false`;
- the component remains `data_mode = derived_only`;
- the archive manifest remains `public_archive = false`;
- archive and source-summary scientific content hashes agree;
- no source snapshot, detailed diff, or `inputs/` tree entered the retained evidence directory.

The workflow never invokes `scripts/observatory_release.py`, never stages a global release automatically, and never promotes a release.

## Result categories

A run can end in:

1. **credential failure** — the configured secret is unavailable or invalid;
2. **transport/source-contract failure** — the official API request, provider inventory, identity, rights, definition, period, value, or coverage contract fails;
3. **archive-contract failure** — the current source cannot pass exact-byte private-vintage packaging/verification;
4. **candidate-build failure** — retrieval succeeds but deterministic derived component construction or diagnostics fail;
5. **successful live validation** — the current source satisfies all implemented source/archive/component contracts and rights-safe evidence is retained.

Only the fifth outcome establishes that the live feed worked on that exact Git commit. Even then, it does not establish durable private storage, a complete global observatory baseline, or publication approval.

## Periodic source checking

The operational cadence is defined separately in `data/registry/rps_refresh_policy.json` as weekly Wednesday 18:00 UTC checking, with activation fail-closed until the required production gates are satisfied. Source checking and publication remain separate decisions: unchanged checks do not generate releases, while changed source states require archive/build/review and remain non-promoting until the normal reviewed release controls pass.

## Durable archive boundary

`src/genai_at_work/private_vintage.py` and `scripts/archive_rps_private_vintage.py` define the durable private-vintage package contract, but the repository does not silently choose a storage vendor. This workflow rehearses that contract only on runner-local temporary storage.

Production durable archival still requires an operator-controlled private filesystem/object-store mount or a future adapter implementing the same create-only and verification semantics. Public GitHub Actions artifacts are not used as the durable raw-source vault.

## D-G1 completion interpretation

Repository engineering is considered complete when the live workflow, source contracts, archive contract, cadence policy, candidate generation, regression tests, and reviewed release handoff are all implemented and green. A successful automatic live run supplies the missing runtime evidence for the configured FRED path.

No claim of successful live retrieval is made until an actual `RPS live validation` run completes successfully and its rights-safe evidence has been inspected.
