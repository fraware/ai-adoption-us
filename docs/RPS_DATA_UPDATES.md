# RPS data updates

This document explains how GenAI at Work checks for new or revised Generative AI Adoption Tracker data and how a source change becomes a new observatory release.

The machine-readable operating policy is `data/registry/rps_refresh_policy.json`. This page translates that policy into maintainer-facing language.

## Current status

As of 4 September 2026:

- live retrieval through the official FRED interface has been validated;
- the registered provider inventory contains 137 series;
- 131 series are in the observatory's workplace scope;
- 6 national overall/outside-work series are intentionally excluded;
- the validated source history contains 962 published aggregate observations;
- the execution environment has successfully used the configured FRED credential;
- a durable private source archive has **not** yet been configured;
- scheduled weekly source checking is therefore **not active**.

The published Release 1 data remain versioned and valid. The missing durable archive affects future automated source-update operations, not the interpretation of the existing release.

## Why source checks and publication are separate

The upstream RPS series are quarterly. The project distinguishes three different timelines:

1. **source frequency:** the data are published quarterly;
2. **source checking:** the repository may periodically check whether the upstream source changed;
3. **publication:** the observatory publishes a new version only after the changed source and resulting analyses have been reviewed.

A successful source check does not automatically update the website.

## Source-check cadence

The current policy specifies a weekly check on **Wednesday at 18:00 UTC** once the automated schedule is enabled.

This is an observatory operating choice, not a claim about the publisher's release calendar. FRED currently exposes the registered source as quarterly and does not provide a next-release date for the series used to define the policy.

A weekly check limits nominal detection delay to seven days without polling a quarterly source every day.

## Live source validation

The repository contains a GitHub Actions workflow for validating the current source path. The validated run used the configured `FRED_API_KEY`, retrieved the registered source, checked the provider inventory and definitions, and regenerated downstream RPS, CPS-composition, and OEWS-robustness evidence without publishing raw source files.

The recorded scientific source identity for that validated source state is:

```text
fe8bffa7cacd029cc23e2ba7e310d925e8c05322f6d53bd89e8234f02e825b73
```

The exact source snapshot used in that validation remained outside the public repository.

## Source identity

The update system distinguishes the scientific content of a source from incidental transport metadata.

A retrieval can change at the byte level because an API response contains different envelope metadata even when the selected scientific observations are identical. Source-update decisions therefore compare normalized scientific content as well as exact retrieved-file identity.

A transport-level difference alone is not treated as a data revision.

## What happens when the source is unchanged

If the registered scientific observations and definitions are unchanged:

- no new observatory release is created;
- the website is not republished simply because a check ran;
- redundant exact source bytes do not need to be retained as a new private vintage;
- a small rights-safe operational record may be retained to document that the check succeeded.

## What happens when observations change

A source update can take several forms:

- a new quarter is added;
- a historical observation is revised;
- both occur together;
- source definitions, classifications, or publication conditions change.

For a normal new observation or historical revision, the intended process is:

1. retain the changed source version privately where the documented source-use conditions permit it;
2. compare it with the previous version;
3. regenerate affected RPS observations and longitudinal diagnostics;
4. regenerate downstream CPS/OEWS/BTOS-dependent analyses where necessary;
5. run scientific and software validation;
6. review changed values, definitions, provenance, and public interpretation;
7. publish a new immutable observatory version if the public evidence changes.

The source itself does not trigger publication automatically.

## Definition or classification changes

A change in survey wording, metric definition, classification system, or registered series inventory is not treated as an ordinary data refresh.

The affected measurement must first be reviewed to determine whether:

- a new series should begin;
- historical and new observations remain comparable;
- a visible series break is required;
- crosswalks or public labels must change.

The project should not preserve visual continuity by silently applying an old definition to a new measurement regime.

## Source-use changes

If the storage or publication conditions for an upstream source change, source processing stops until the new use boundary has been documented.

Scientific review does not override source-use restrictions.

## Private source archive

A changed RPS source version may need to be retained privately so that a published observatory release can later be reproduced exactly.

The repository contains code for packaging and verifying an immutable private source version, but the current production environment does not yet have a durable operator-controlled private storage backend. GitHub Actions artifacts and runner-local temporary files are not treated as durable source archives.

For that reason, the scheduled weekly check remains disabled in the current machine-readable policy.

Before enabling the schedule, maintainers should:

1. configure a durable private storage location appropriate for the source-use conditions;
2. write a source version through the repository's archive code;
3. read it back independently;
4. verify the exact bytes and recorded scientific identity;
5. confirm that the storage location is not exposed to the public build.

## Credentials

The live retrieval workflow uses the repository secret `FRED_API_KEY`.

The key is required only in the source-acquisition environment. It must not be written to source files, logs, generated public artifacts, or the web application.

There is no HTML-scraping or manual-copy fallback when the authorized source interface is unavailable.

## Public/private boundary

The source-update workflow may retain public evidence such as:

- source identity;
- registered inventory counts;
- observation counts;
- source-change classification;
- generated public artifact checksums;
- validation status.

It does not publish the private source snapshot or a generic historical subgroup source database.

## Enabling scheduled checking

The current policy specifies the intended weekly schedule but marks it inactive. Enabling it should be a separate reviewed repository change after durable private source storage has been configured and verified.

The scheduled job should be limited to source detection, validation, and preparation of reviewable evidence. It should never publish a new observatory version without the release process described in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).
