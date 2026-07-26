#!/usr/bin/env python3
"""CI gate: fail on internal vocabulary anywhere in the tracked tree.

Regex patterns live in governance/denylist.txt (one per line, '#' comments
and blank lines ignored). Matching is case-insensitive.

ALLOWLIST below carves out narrow, explicit (path, pattern) exceptions --
never a whole-file exemption. This keeps the "paircoder matrix-run
invocation is documented in exactly one place" governance promise
mechanically enforced: only the named pattern is permitted in the named
file, every other denylist pattern (secrets, personal names, the
confidential fixture family, etc.) still applies there too.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DENYLIST_FILE = REPO_ROOT / "governance" / "denylist.txt"

# (relative file path, denylist pattern string) pairs that are permitted.
# The runner guide documents the `bpsai-pair`/paircoder CLI invocation as
# ONE way to run the battery -- see docs/running-the-battery.md.
ALLOWLIST: set[tuple[str, str]] = {
    ("docs/running-the-battery.md", "bpsai"),
    ("docs/running-the-battery.md", "paircoder"),
}

# Top-level path components the scanner never descends into (VCS internals).
EXCLUDED_PATHS: set[str] = {".git"}

# Whole files exempt from scanning entirely (not per-pattern, per-file like
# ALLOWLIST above): the denylist definition and scanner source themselves
# necessarily *name* every pattern in comments/docstrings/string literals.
# That is the tooling describing its own rules, not a content leak -- no
# confidential vocabulary, secrets, or fleet content ever lives here.
EXCLUDED_FILES: set[str] = {
    "governance/denylist.txt",
    "governance/check_denylist.py",
}


def load_patterns(path: Path) -> list[str]:
    patterns = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(stripped)
    return patterns


def tracked_files() -> list[Path]:
    """Every git-tracked file (respects .gitignore, skips .git internals)."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        REPO_ROOT / rel
        for rel in result.stdout.splitlines()
        if rel and Path(rel).parts[0] not in EXCLUDED_PATHS
    ]


def scan_file(path: Path, patterns: list[str]) -> list[str]:
    """Return violation strings ('pattern @ line N') for one file."""
    rel_path = path.relative_to(REPO_ROOT).as_posix()
    if rel_path in EXCLUDED_FILES:
        return []
    try:
        text = path.read_text()
    except (UnicodeDecodeError, OSError):
        return []  # binary or unreadable -- not a text-content leak vector

    violations = []
    for pattern in patterns:
        if (rel_path, pattern) in ALLOWLIST:
            continue
        regex = re.compile(pattern, re.IGNORECASE)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                violations.append(f"{rel_path}:{lineno}: matched /{pattern}/ -- {line.strip()!r}")
    return violations


def main() -> int:
    if not DENYLIST_FILE.is_file():
        print(f"ERROR: {DENYLIST_FILE} not found", file=sys.stderr)
        return 1

    patterns = load_patterns(DENYLIST_FILE)
    if not patterns:
        print("ERROR: denylist.txt has no patterns", file=sys.stderr)
        return 1

    all_violations: list[str] = []
    for f in tracked_files():
        all_violations.extend(scan_file(f, patterns))

    if all_violations:
        print("Denylist scan FAILED -- internal vocabulary detected:", file=sys.stderr)
        for v in all_violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    print(f"OK: denylist scan clean ({len(patterns)} patterns, {len(tracked_files())} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
