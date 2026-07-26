#!/usr/bin/env python3
"""CI gate: every fixture under fixtures/ must carry the provenance stamp.

Fails (non-zero exit) if any *.json file under fixtures/ is missing
metadata.public_release == true or metadata.provenance == "original-authored".
This is the mechanical backstop for the repo's core governance promise: a
fixture cannot land here without an explicit, checked provenance claim.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "fixtures"

REQUIRED_PROVENANCE = "original-authored"


def find_fixture_files(fixtures_dir: Path) -> list[Path]:
    """All *.json files under fixtures_dir, sorted for stable output."""
    return sorted(fixtures_dir.rglob("*.json"))


def check_stamp(path: Path) -> str | None:
    """Return an error string for path, or None if it's correctly stamped."""
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        return f"{path}: could not parse as JSON ({exc})"

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        return f"{path}: missing 'metadata' object"

    if metadata.get("public_release") is not True:
        return f"{path}: metadata.public_release must be true"

    if metadata.get("provenance") != REQUIRED_PROVENANCE:
        return (
            f"{path}: metadata.provenance must be "
            f"{REQUIRED_PROVENANCE!r}, got {metadata.get('provenance')!r}"
        )

    return None


def main() -> int:
    if not FIXTURES_DIR.is_dir():
        print(f"ERROR: {FIXTURES_DIR} does not exist", file=sys.stderr)
        return 1

    fixture_files = find_fixture_files(FIXTURES_DIR)
    if not fixture_files:
        print(f"ERROR: no fixture files found under {FIXTURES_DIR}", file=sys.stderr)
        return 1

    errors = [msg for f in fixture_files if (msg := check_stamp(f))]

    if errors:
        print("Fixture provenance stamp check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"OK: {len(fixture_files)} fixture files carry a valid provenance stamp.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
