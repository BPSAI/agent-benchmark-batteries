#!/usr/bin/env python3
"""CI gate: fail on denylisted content anywhere in the tracked tree.

Regex patterns live in governance/denylist.txt (one per line, '#' comments
and blank lines ignored). Matching is case-insensitive.

This scanner has NO whole-file, whole-path, or per-pattern exemptions.
Every tracked file is scanned against every pattern, including this
script and the pattern file itself -- see the design note at the top of
denylist.txt for why the patterns are written the way they are.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DENYLIST_FILE = REPO_ROOT / "governance" / "denylist.txt"


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
    return [REPO_ROOT / rel for rel in result.stdout.splitlines() if rel]


def scan_file(path: Path, patterns: list[str]) -> list[str]:
    """Return violation strings ('pattern @ line N') for one file."""
    rel_path = path.relative_to(REPO_ROOT).as_posix()
    try:
        text = path.read_text()
    except (UnicodeDecodeError, OSError):
        return []  # binary or unreadable -- not a text-content leak vector

    violations = []
    for pattern in patterns:
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
        print("Denylist scan FAILED -- denylisted content detected:", file=sys.stderr)
        for v in all_violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    print(
        f"OK: denylist scan clean ({len(patterns)} patterns, "
        f"{len(tracked_files())} files, zero exemptions)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
