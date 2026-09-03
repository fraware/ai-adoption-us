# RPS live-source validation

Status: **D-G1 live validation passed; durable private-backend activation remains pending; non-promoting**

Date: 2026-09-03

## Purpose

`.github/workflows/rps-live-validation.yml` is the repository's canonical live-source validation path for the authorized published-aggregate RPS/FRED feed.

It replaces the earlier manual-only `rps-source-probe.yml`. The prior file was present in the repository but was not reliably surfaced as a runnable workflow in the GitHub Actions UI, so the project no longer depends on an operator finding or manually dispatching it.

The live-validation workflow answers a narrow, auditable question: **can the current live provider state be retrieved with the authorized credential, satisfy the exact provider and observatory inventory contracts, pass rights and construct checks, rehearse immutable private-vintage storage, and produce deterministic derived RPS evidence without publication or promotion?**

It is not a release-staging or publication job.

## Verified live run

The required live path has now been exercised successfully on merged `main`.

GitHub Actions run `33687737639`, workflow `RPS live validation`, completed successfully on commit `3fb2cff4a9b1cbc2f340c8db00328efaa2c30130`. The retained rights-safe artifact is `9868969207`, artifact digest `sha256:fd8b4ed3f828755efaaa00c80b7d444480f7d0e058b88dddf2ffae8f17539de7`.

Inspection of the retained artifact establishes the following exact run state:

- source ID: `rps-genai-tracker-fred-release-6`;
- provider series: 137;
- observatory series: 131;
- intentional exclusions: 6;
- provider inventory status: `pass`;
- source observations: 962;
- source classification: `baseline`;
- source scientific content SHA-256: `fe8bffa7cacd029cc23e2ba7e310d925e8c05322f6d53bd89e8234f02e825b73`;
- exact source-snapshot file SHA-256: `66b3ffbaebf43c3c8434556eec9329a232d8f17483ba3a613e6b00d214af3f74`;
- private-vintage archive contract rehearsed: `true`;
- archive persisted durably: `false`;
- RPS observatory candidate built: `true`;
- CPS composition-residual evidence built: `true`;
- OEWS-weighted robustness evidence built: `true`;
- promotion performed: `false`;
- public raw observations included: `false`.

The corresponding private-vintage rehearsal manifest records provider release ID `6`, exact snapshot size `422458` bytes, rights status `approved`, storage scope `private`, and `public_archive=false`. That manifest was retained without the source snapshot itself.

This run establishes successful live retrieval, provider-inventory validation, the execution-environment credential path, transient archive-contract rehearsal, and deterministic downstream evidence construction for that exact commit. It does **not** establish durable private retention or release approval.

## Trigger

The workflow runs automatically on pushes to `main` when the live-source contract itself changes, including the workflow file, the RPS retrieval/release/archive modules, operator commands, and registered source manifests. The workflow also retains a `workflow_dispatch` trigger as an optional operator convenience.

No periodic schedule is enabled here. Periodic source-check activation is governed separately by `data/registry/rps_refresh_policy.json`.

## Permissions and credential contract

Repository permissions remain restricted to:

```yaml
permissions:
  contents: read
```

The workflow requires the repository Actions secret `FRED_API_KEY`.

The credential is supplied only to the validation job environment. A fail-fast gate rejects an absent or empty credential before source retrieval. There is no HTML-scraping or manual-copy fallback.

Because run `33687737639` passed the credential gate and subsequently completed live source retrieval and validation, that run is evidence that the configured credential path was operational in its execution environment. This is not evidence of the secret value, and no credential material is retained in the repository or artifact.

## Live transaction

The workflow performs ordered stages on one runner:

1. retrieve and validate the live RPS aggregate source into runner-temporary storage;
2. report the rights-safe period topology;
3. rehearse the immutable private-vintage archive contract under `/tmp/rps-private-vintage`;
4. build the non-promoting RPS observatory component;
5. build snapshot-native CPS composition-residual evidence;
6. build independent OEWS-weighted RPS adoption robustness evidence;
7. assemble and upload only rights-safe review evidence.

The archive rehearsal verifies exact-byte package identity, scientific content identity, the private rights boundary, immutable namespace semantics, and archive implementation. Its root is runner-local and transient, so it must not be interpreted as durable production archival.

## Source-byte boundary

Raw/source observation material remains on runner-temporary storage. The retained GitHub Actions artifact deliberately excludes:

- `rps_source_snapshot.json`;
- `rps_refresh_diff.json`;
- all release `inputs/` source objects;
- any copied raw/source observation bundle.

No source-observation file is written into the checked-out public repository.

## Retained rights-safe evidence

The artifact for run `33687737639` contains:

```text
live-validation-summary.json
source-candidate-summary.json
private-vintage-manifest.json
rps-component-release.json
observatory-artifacts/
composition-residuals/
oews-rps-adoption/
```

`live-validation-summary.json` binds the run identity to the source scientific hash, exact private snapshot-file hash, inventory counts, observation count, source revision status, downstream build status, archive-rehearsal status, and explicit non-promotion/no-raw-publication flags.

`source-candidate-summary.json` records the source candidate as `source-candidate-only`, with 962 new observations in the baseline comparison and no definition, revision, or removal events.

`private-vintage-manifest.json` contains hashes, rights metadata, inventory, comparison state, and package provenance only; the exact archived source bytes remain transient in this workflow.

## Rights and release safeguards

Before artifact upload, the workflow verifies that:

- `public_raw_observations_included = false`;
- `source_input_bytes_publication = false`;
- the component remains `data_mode = derived_only`;
- the archive manifest remains `public_archive = false`;
- archive and source-summary scientific content hashes agree;
- composition and OEWS evidence are bound to the same live source scientific identity;
- no source snapshot, detailed diff, or `inputs/` tree enters retained evidence.

The workflow never stages or promotes a global release.

## Result interpretation

The successful run closes two activation gates in the source-check policy:

1. **successful live validation** — passed;
2. **`FRED_API_KEY` operational in the execution environment** — passed.

Two activation gates remain unresolved:

3. **operator-controlled durable private-vintage backend configured** — pending;
4. **independent private-backend write/read/verify rehearsal passed** — pending.

The distinction is strict. A runner-local `/tmp` rehearsal validates package semantics but provides no recovery after the runner disappears. A GitHub Actions artifact retains only rights-safe evidence and explicitly excludes source bytes, so it is also not the private source-vintage backend.

## Periodic source checking

The operating cadence is pinned separately as weekly Wednesday 18:00 UTC checking. The schedule remains disabled until all four activation gates pass.

Live retrieval success alone is insufficient to activate recurrence. If a future check detects changed source content, the exact source bytes must be durably retainable before dependent evidence can enter a reproducible release process.

Source checking and publication remain separate decisions: unchanged checks do not generate releases, while changed source states require archive/build/review and remain non-promoting until the normal reviewed release controls pass.

## Durable archive boundary

`src/genai_at_work/private_vintage.py`, `src/genai_at_work/private_vintage_store.py`, and `scripts/archive_rps_private_vintage.py` define the immutable private-vintage package and local create-only storage contract. The repository deliberately does not invent or silently select a remote storage service.

Production durable archival requires an operator-controlled private filesystem/object-store backend reachable from the refresh execution environment and capable of preserving the package's immutable event identity and exact bytes. That backend must then pass an independent write/read/verify rehearsal before scheduled checking is activated.

Public GitHub Actions artifacts are not the durable raw-source vault.

## D-G1 completion interpretation

The repository-controlled live-source and credential paths are now evidenced. The complete v1 global-baseline composition software is also merged on `main` through PR #57 at commit `28e2141869c35f92faf20d796f3b2b2f003e4c3a`.

D-G1 is still open because the production execution environment has no evidenced durable private-vintage backend and no independent backend recovery rehearsal. Until those gates pass:

- the periodic weekly schedule remains disabled;
- no first global candidate should be built from transient-only source bytes as though they were a durable release input;
- no source release should be staged or promoted on the basis of this live-validation artifact alone.

The next legitimate activation step is infrastructure, not a scientific shortcut: configure the operator-controlled private backend, write an exact source vintage through the immutable package contract, independently read it back, verify all hashes and provenance bindings, and record that evidence before enabling recurrence.
