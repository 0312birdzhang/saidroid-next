#!/usr/bin/env python3
"""Retired API 23 device probe: never deploy obsolete mixed framework artifacts."""
raise SystemExit(
    "The API 23 activity-manager probe is retired. "
    "Build with scripts/api29/build-product.py and use the API 29 verification "
    "commands documented in docs/API29-WIP-2026-10-25.md. "
    "No device files were changed."
)
