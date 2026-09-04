# RPS source-use decision

**Decision date:** 2 September 2026  
**Status:** published-aggregate project use recorded as permitted

This document records the basis and scope under which GenAI at Work uses published aggregate observations from the Real-Time Population Survey (RPS) Generative AI Adoption Tracker.

It is a project provenance record, not a general license for third parties.

## Evidence basis

On 2 September 2026, the project owner stated that permission had been obtained from the RPS data owners for the published aggregate use required by this project.

The repository records that statement as a **project-owner attestation of source-owner permission**.

The underlying correspondence or agreement is not included in this public repository and was not independently inspected as part of the software review. This document therefore does not claim contractual wording, recipient identity, correspondence dates, or legal terms that are not present in the retained evidence.

## Use recorded as permitted

For the published aggregate Tracker series used by GenAI at Work, the project treats the recorded permission as covering:

- retrieval of the relevant published aggregate observations from the official distribution;
- private storage of versioned aggregate source files when needed for reproducibility;
- use of those observations in the project's analysis;
- display of selected attributed aggregate values in the public observatory;
- publication of derived aggregate analyses;
- refresh of the same aggregate source scope when later published Tracker waves become available.

The public RPS presentation in Release 1 is intentionally narrower than the complete registered source history. It contains national history plus the latest complete industry and occupation A/H/S cross-sections and derived analyses.

## Use not inferred from the evidence

The recorded permission should not be interpreted as establishing rights for:

- respondent-level or other non-public microdata;
- historical replication-package material not covered by the recorded aggregate scope;
- the separate occupation/task-adoption-index files;
- unrestricted bulk mirroring of the complete Tracker database;
- a generic public API that republishes the complete underlying source;
- downstream third-party redistribution beyond the source owners' own terms.

Those uses require their own documentary basis.

## Source and attribution

Primary source family:

- Real-Time Population Survey / Generative AI Adoption Tracker;
- authors associated with the Tracker series used here: Alexander Bick, Adam Blandin, and David Deming;
- Tracker: https://www.genaiadoptiontracker.com/;
- machine-readable distribution used by this project: FRED/ALFRED series registered in `data/registry/rps_source_series_manifest.json`.

The FRED/ALFRED service is treated as a distribution mechanism for the series, not as the party granting the underlying source-owner permission.

Public outputs should preserve appropriate attribution to the RPS / Generative AI Adoption Tracker and source-series provenance.

## Public data boundary

Release 1 does not publish the complete historical subgroup source panel as a general public dataset.

The public product includes a bounded presentation of source observations and derived analyses. Source files used during release preparation remain outside the public Git repository when their redistribution is not covered by the documented use scope.

This approach preserves reproducibility while avoiding an unsupported interpretation of the recorded permission as blanket redistribution rights.

## Scientific interpretation is separate from permission

Permission to use a source does not change what the source measures.

In particular:

- RPS worker-reported generative-AI adoption is different from BTOS employer-reported AI use;
- workplace adoption is different from AI-assisted working time;
- AI-assisted working time is different from reported time savings;
- reported time savings are not measured productivity;
- sector-level cross-source concordance is not a causal organizational effect;
- suppressed source values are not reconstructed;
- uncertainty claims require an appropriate statistical method and inputs.

## Change control

If the project's understanding of the source-use conditions changes, the source documentation and publication behavior should be reviewed before new source material is stored or released.

A future expansion to microdata, task-index data, unrestricted bulk download, or a public source API should not be inferred from this record; it requires a separate documented decision.
