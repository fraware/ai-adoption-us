# GenAI at Work — Release 1 candidate notes

**Status:** pre-release. No formal Observatory Release 1 has been promoted, deployed through the release-only authorization path, tagged, or published as a GitHub Release yet.

The formal release date will be the date of the GitHub Release created only after exact-candidate review, exact source rehydration, explicit promotion, release-only deployment, and live deployment audit all succeed.

## What Release 1 establishes

Release 1 is the first governed public baseline of the U.S. GenAI-at-work observatory. The product separates workplace GenAI adoption from routine use, AI-assisted working time, reported counterfactual time savings, composition-adjusted descriptive evidence, and firm-side triangulation instead of collapsing them into one adoption indicator.

The public product is designed for static GitHub Pages deployment in `derived_only` mode. Private RPS source-input bytes and private audit material are excluded from the public Git tree and promoted release bundle.

## Evidence intended for the release

The current Release 1 candidate architecture composes the rights-safe evidence already validated in the repository:

- national workplace GenAI adoption/use indicators and seven-quarter longitudinal conversion diagnostics;
- bounded industry and occupation adoption, assisted-hours, and reported-savings views on the authorized public surface;
- executed Q2 2025 and Q2 2026 CPS industry × occupation composition evidence;
- occupation-adjusted industry-context residual diagnostics with descriptive-only interpretation;
- May 2025 OEWS staffing robustness evidence;
- preregistered BTOS–RPS descriptive triangulation with construct differences and suppression boundaries preserved;
- methodology, source/provenance, and technical-essay surfaces cryptographically bound to the reviewed repository files.

The final release is defined by its promoted immutable release directory and registry entry, not by these notes alone.

## Scientific boundaries

Release 1 does not convert reported time savings into measured productivity, output, TFP, GDP, or wage growth. The occupation-adjusted industry-context residual is not an identified organizational, management-quality, efficiency, productivity, or causal effect. RPS worker-side constructs and BTOS firm-side current-use constructs are not treated as equivalent.

Custom pooled CPS composition vectors do not have a supported full design-based covariance model in Release 1. Existing composition stability and reliability diagnostics remain descriptive. Marginal generalized-variance-function borrowing is not used to manufacture a missing 22-dimensional covariance structure.

The CPS Q4 2025 composition quarter remains explicitly unavailable because October 2025 CPS data were not collected; the project does not construct a replacement quarter from November–December observations.

## Rights and source boundaries

Published-aggregate RPS project use is recorded as permitted under the project source-rights decision. That permission is not generalized to respondent-level microdata, the separate task-index artifact, unrestricted bulk mirroring, a historical subgroup database, or a generic public raw-source API.

The release pipeline retrieves the authorized aggregate RPS source into a private candidate workspace. It records source identity, validates the registered inventory, detects release-relevant changes, derives the bounded public observation surface, and excludes source-input bytes from public candidate-review and release artifacts.

## Release and QA contract

Release 1 is not authorized by a successful build alone. The exact final candidate must satisfy the release checklist in `docs/RELEASE_CHECKLIST.md`, including:

- release CI on the exact candidate commit;
- rendered browser/accessibility QA and native Safari QA on the applicable final web state;
- GitHub Pages static artifact audit;
- exact candidate-review package with zero release-contract failures;
- human scientific, editorial, and source-rights review of that exact package;
- exact source rehydration that reproduces the reviewed scientific/candidate/stage identities;
- human attestation bound to the deterministic rehydration identity and exact CI evidence;
- explicit promotion into a new immutable `data/releases/<release-id>/` directory and release-registry transition;
- validation of the single release-only authorization commit;
- GitHub Pages deployment from that authorization commit and successful live-origin audit;
- final catastrophic-error/manual content inspection before the formal tag and GitHub Release are created.

Historical CI, browser, or deployment results remain useful engineering evidence but do not substitute for exact final release execution.

## Publication target

The intended production site is:

`https://fraware.github.io/ai-adoption-us/`

A previously deployed site state must not be interpreted as the formal Release 1 artifact unless it is tied to the final promoted release and passes the release-only live deployment audit.

## Update model after Release 1

Release 1 establishes a reviewed baseline, not unattended publication. Future source changes flow through source identity, validation, rights-safe derivation, revision diagnostics, complete candidate composition, governed claim-surface binding, exact staging, review, exact rehydration, promotion, and release-only deployment.

## Post-Release-1 research

Current non-blocking research directions are tracked as GitHub issues and in `docs/ROADMAP.md`. They include design-based uncertainty for custom CPS composition vectors, the experimental composition explorer, task-exposure versus realized-adoption analysis under its separate provenance/rights gate, and richer worker/task/occupation/industry/time mechanism research.
