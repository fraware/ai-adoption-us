# RPS source-rights and production-feed decision

Status: **GRANTED — live aggregate observatory gate**

Decision date: 2026-09-02

This record governs use of published aggregate observations from the Real-Time Population Survey (RPS) Generative AI Adoption Tracker in GenAI at Work.

## Decision basis

On 2026-09-02, the project owner stated that permission has been obtained from the RPS data owners and explicitly authorized this project to proceed. The repository records that statement as a **project-owner attestation of source-owner permission**.

The underlying permission correspondence or agreement has not been attached to this repository and has not been independently inspected as part of this code change. Accordingly, this record does not invent an authorized contact, correspondence date, contractual wording, or legal term that is not in the retained project evidence.

The pre-permission fail-closed decision remains preserved in Git history at commit `a33926a234bffd9fb6fce9491377e71a7ed5ad22` and earlier.

## Operational scope cleared by this decision

For the published aggregate Tracker series used by this project, the live aggregate gate is treated as cleared for:

- retrieving published aggregate observations from the official Tracker distribution;
- storing versioned aggregate source checkpoints for reproducibility;
- using those observations in the project’s analytical pipeline;
- displaying selected attributed aggregate values in the observatory;
- computing and publishing derived aggregate analyses, including the preregistered BTOS-RPS industry triangulation;
- refreshing the aggregate source checkpoints as later published Tracker waves become available, subject to the normal revision gate.

This decision removes the source-rights block from the aggregate analysis pipeline. It does **not** collapse the source’s measurement constructs or remove scientific review requirements.

## Scope not inferred from the attestation

The following remain separate decisions unless documentary evidence establishing their scope is later retained:

- respondent-level or other non-public microdata;
- the historical replication package for *The Rapid Adoption of Generative AI*;
- the separate occupation/task-adoption-index artifact reviewed under R1.3-G1;
- unrestricted bulk mirroring of the entire source catalog through a public download service;
- a public API that republishes the complete underlying Tracker database.

Those items are not required for the current BTOS-RPS industry triangulation.

## Source and attribution contract

Primary measurement family:

- Real-Time Population Survey: Generative Artificial Intelligence Adoption Tracker;
- authors/source attribution: Alexander Bick, Adam Blandin, and David Deming;
- public Tracker: https://www.genaiadoptiontracker.com/;
- official series distribution used by the current reproducibility layer: FRED/ALFRED series identifiers already pinned in `data/registry/rps_source_series_manifest.json`.

Current FRED/ALFRED series notes identify the values as quarterly, not seasonally adjusted percentages and request citation of the underlying RPS work. Source identifiers, retrieval dates, observed values, and source URLs must remain attached to every versioned checkpoint.

FRED/ALFRED is treated as a distribution/transport layer, not as the party granting the underlying source-owner permission.

## Measurement guardrails unaffected by permission

Permission to use a source does not make unlike measures equivalent. In particular:

- RPS worker-reported GenAI adoption is not BTOS employer-business AI adoption;
- adoption is not assisted-hours penetration;
- adoption is not reported time savings or productivity;
- sector-level concordance is not an organizational or causal effect;
- source publication does not justify reconstructing suppressed values;
- uncertainty claims require an approved design and available uncertainty inputs.

## Engineering decision

The legacy static exporter that wrote raw FRED observations directly into the public web tree remains retired. That architectural safeguard is independent of the rights decision.

Authorized aggregate source values may instead enter through versioned source checkpoints with provenance and review. Analytical code consumes those checkpoints and produces derived artifacts. Direct full-database public redistribution can be added later only if its exact product scope is deliberately approved.

The first authorized checkpoint under this decision is:

`data/registry/rps_industry_adoption_q2_2026_v1.json`

The first analysis released from that checkpoint is governed by the canonical preregistration:

`data/registry/btos_rps_comparison_protocol_v1.json`

## Decision fields

- provider/data owner: Real-Time Population Survey / Generative AI Adoption Tracker data owners
- permission status: `granted` for the published aggregate project use described above
- evidence basis: project-owner attestation of source-owner permission
- attestation date: 2026-09-02
- documentary correspondence retained in repository: no
- delivery format used now: published aggregate series through official FRED/ALFRED distribution
- storage terms implemented: versioned aggregate checkpoints in the research repository
- direct observation display/publication: treated as granted for selected attributed aggregate values used by the project
- derived-result publication: treated as granted
- unrestricted bulk mirror/public API: not inferred; separate product decision
- historical replication package: unresolved/separate
- microdata: unresolved/separate
- task-index artifact: unresolved/separate
- attribution: retain RPS/Tracker authorship and source-series provenance
- engineering consequence: aggregate rights gate cleared; analysis may execute; legacy public-tree raw exporter remains retired
- effective date: 2026-09-02

## Current decision

**Granted for the live published aggregate use required by the observatory and the preregistered BTOS-RPS analysis, on the project owner’s attestation that source-owner permission has been obtained.** Scientific, provenance, revision, and release-review gates remain in force.
