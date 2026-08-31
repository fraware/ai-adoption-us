#!/usr/bin/env python3
"""Retired static FRED export path.

The original Phase-1 implementation wrote FRED API observations into a public web directory.
That architecture is intentionally disabled pending a rights-cleared production feed.
"""

raise SystemExit(
    "Static FRED export is retired. Use the private audit fixture for local research only, "
    "or configure an explicitly reviewed no-store live source. Do not write FRED observations "
    "into apps/web/public/data."
)
