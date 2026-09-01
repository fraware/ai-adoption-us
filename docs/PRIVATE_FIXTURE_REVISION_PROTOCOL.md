# Private fixture revision and longitudinal regeneration protocol

Status: **mandatory governance procedure for any revision of the private RPS audit fixture**.

The private RPS observation fixture is not part of the public repository. This protocol exists to prevent a revised source file from silently changing derived longitudinal evidence or public claims.

## Invariant

Never replace `data/audit/private/rps_subgroup_5q_audit.json` with a candidate file before running the revision gate.

The current freeze is registered in `data/registry/private_fixture_freeze.json`. A candidate must remain at a separate private path until the staged revision has been validated and explicitly reviewed.

## What the gate enforces

Before staging:

1. the current private fixture must exist and its SHA-256 must match the public freeze registry;
2. the current fixture must pass the structural, scope, rights-marker, and value-domain contract;
3. the candidate fixture must independently pass that same contract;
4. the source-vintage record must identify a new freeze ID plus retrieval/checkpoint dates and preserve the current rights and construct definitions;
5. the current fixture and current derived freeze are copied to a private immutable archive keyed by the current freeze ID.

During staging:

1. the fixture-present longitudinal analytical test suite runs against the **candidate path**, without replacing the current fixture;
2. the same-freeze byte-for-byte canonical reproduction assertion is the single inapplicable test during revision staging, because candidate-versus-current artifact equality is evaluated separately through the revision diff;
3. candidate-suite stdout/stderr, return code, candidate SHA-256, and the explicit scope exception are retained in `private_suite.private.json` inside private staging;
4. the full deterministic longitudinal builder runs against the candidate fixture;
5. all four publication artifacts are generated into a new staging directory;
6. the candidate publication-validation record is retained;
7. a private cell-level diff is produced, keyed by entity × metric × quarter;
8. SHA-256 comparisons are produced for every longitudinal publication artifact;
9. any changed artifact conservatively marks every registered dependent public claim as requiring review;
10. the stage is fingerprinted and publication remains blocked.

Promotion is a separate command. It requires both the applicable candidate private suite and publication diagnostics to pass, plus a review attestation bound to:

- the exact stage fingerprint;
- the exact candidate-fixture SHA-256;
- the exact hashes of every staged publication artifact;
- every affected claim ID;
- explicit rights and definition review;
- reviewer identity and review time.

If any staged file changes after review, promotion fails. If the current fixture changes after staging, promotion fails and the candidate must be restaged.

## Stage command

Use a new immutable staging directory and a private archive root outside the public Git tree:

```bash
PYTHONPATH=src python scripts/private_fixture_revision_gate.py stage \
  --candidate-fixture /private/incoming/rps_subgroup_candidate.json \
  --source-vintage /private/incoming/source_vintage.json \
  --staging-dir /private/staging/rps-revision-2026-09-01 \
  --private-archive-root /private/archive/rps-fixtures
```

The default current fixture is:

`data/audit/private/rps_subgroup_5q_audit.json`

The stage writes, under the private staging directory:

- `stage_manifest.json`;
- `private_suite.private.json` — candidate fixture-present suite output; keep private;
- `fixture_diff.private.json` — contains cell-level values and must remain private;
- `artifact_diff.json`;
- `claim_review.json`;
- `publication_gate.json`;
- `derived/` containing the four regenerated artifacts.

Possible stage states:

- `REPRODUCED_CURRENT_FREEZE` — candidate checksum and artifacts are unchanged and applicable tests/diagnostics pass;
- `BLOCKED_REVIEW_REQUIRED` — candidate is structurally valid, applicable tests/diagnostics pass, and derived outputs changed; explicit review is required;
- `BLOCKED_PRIVATE_SUITE_FAILED` — one or more applicable fixture-present analytical tests failed; do not promote;
- `BLOCKED_DIAGNOSTICS_FAILED` — publication-validation expectations failed; do not promote.

A legitimate upstream revision may reveal that a pinned analytical expectation is no longer true. That is a research finding, not a reason to weaken the gate. Review and update the affected scientific/claim contract explicitly, then stage again; the revision must not bypass a failed test by assertion deletion without substantive review.

## Source-vintage record

The staging source-vintage JSON must contain at least:

```json
{
  "source_vintage_id": "rps-audit-2026-09-01",
  "new_freeze_id": "rps-private-5q-2026-09-01",
  "retrieved_at": "2026-09-01T13:00:00Z",
  "checkpoint_date": "2026-09-01",
  "rights_status": "Copyrighted: Citation Required",
  "definitions_status": "unchanged",
  "notes": "Describe the source revision and why the candidate exists."
}
```

A source revision may not reuse the existing freeze ID. A rights-status change fails closed and must be resolved through the source-rights decision process. A definition change fails closed and requires a new measurement specification; it must not be smuggled through as a source revision.

## Review attestation

For a changed but test- and diagnostics-valid stage, reviewers inspect the private suite result, private cell diff, artifact changes, affected public surfaces, and source-vintage record. The attestation must then bind the review to the exact staged hashes:

```json
{
  "stage_id": "<exact stage fingerprint>",
  "candidate_fixture_sha256": "<exact candidate SHA-256>",
  "reviewer": "<reviewer identity>",
  "reviewed_at": "2026-09-01T14:00:00Z",
  "rights_reviewed": true,
  "definitions_reviewed": true,
  "all_affected_claims_reviewed": true,
  "artifact_sha256": {
    "longitudinal_diagnostics.json": "<hash>",
    "validation_checks.json": "<hash>",
    "quarter_diagnostics.csv": "<hash>",
    "rank_stability.csv": "<hash>"
  },
  "reviewed_claim_ids": [
    "home-five-wave-summary",
    "industry-explorer-longitudinal",
    "occupation-explorer-longitudinal",
    "after-adoption-essay",
    "readme-longitudinal-status"
  ]
}
```

The review must update any affected public chart, table, or text statement before promotion. Passing numerical tests is not a substitute for claim review.

## Promote command

Only after the attestation exists:

```bash
PYTHONPATH=src python scripts/private_fixture_revision_gate.py promote \
  --candidate-fixture /private/incoming/rps_subgroup_candidate.json \
  --staging-dir /private/staging/rps-revision-2026-09-01 \
  --attestation /private/staging/rps-revision-2026-09-01/review_attestation.json \
  --private-archive-root /private/archive/rps-fixtures \
  --validation-record docs/validation/PRIVATE_FIXTURE_REVISION_2026-09-01.json
```

Promotion:

1. requires the staged applicable private suite and publication diagnostics to have passed;
2. re-verifies the current freeze and candidate SHA-256;
3. re-fingerprints the stage manifest;
4. re-hashes every staged artifact to detect post-review mutation;
5. re-validates attestation coverage;
6. preserves the old private fixture and old derived freeze in the private archive;
7. replaces the private current fixture;
8. promotes the reviewed derived artifacts;
9. advances `data/registry/private_fixture_freeze.json` with previous/new freeze identities;
10. creates a public validation record containing hashes, counts, source-vintage identity, test/diagnostic pass status, and review metadata but no raw private observations or cell values.

The resulting public changes must still go through normal review and CI before publication.

## Public/private boundary

The following must never be committed publicly:

- the current or candidate raw RPS fixture;
- archived private fixtures;
- `private_suite.private.json`;
- `fixture_diff.private.json`;
- any staging directory that contains observation-level values or private test output.

The public repository may contain:

- freeze IDs and fixture SHA-256 values;
- the contract registry;
- claim inventory;
- derived publication artifacts that satisfy the existing rights-safe publication policy;
- aggregate change counts and pass/fail states;
- reviewed source-vintage metadata;
- dated validation records.

## Relationship to future waves

This procedure governs **revision of an existing private five-wave source freeze**. Adding a new survey wave changes the longitudinal scope and belongs to the versioned update/release pipeline. A new wave must not be disguised as a fixture revision merely to bypass the broader specification and release review.
