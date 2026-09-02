#!/usr/bin/env python3
"""Retired legacy static RPS public-tree exporter.

The live published aggregate RPS gate is now cleared in
``docs/source-rights/RPS_SOURCE_DECISION.md``. That rights decision does not revive the
old architecture that wrote source observations directly into the web public tree.

Authorized RPS observations enter the repository as versioned source checkpoints with
provenance and review. Derived analytical artifacts are built from those checkpoints.
The first such source checkpoint is
``data/registry/rps_industry_adoption_q2_2026_v1.json``.
"""

raise SystemExit(
    "Static FRED export is retired. Aggregate RPS use is authorized, but the legacy public-tree "
    "raw exporter remains disabled. Use versioned authorized source checkpoints and the reviewed "
    "analysis pipelines instead."
)
