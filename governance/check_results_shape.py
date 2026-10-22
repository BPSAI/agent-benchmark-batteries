#!/usr/bin/env python3
"""CI gate: every results/*.csv must be the five-column shape.

Every `results/*.csv` except the two files with a different schema
(`EXCLUDED_FILES`) carries raw per-fixture per-model rows with exactly the
columns `results/README.md` prescribes. This check fails on a wrong header,
an unknown outcome or format variant, a `model_id` that is not a plain
identifier, a fixture id with no file under `fixtures/`, a
`base_task_id`/`format_variant` that disagrees with that fixture's metadata,
a file whose sibling `<name>.PROVENANCE.md` lacks `repetitions: N` (1 to 10),
and any model that does not cover every fixture with exactly N rows. It
prints n per cell; it never computes a rate.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from shape_rules import OUTCOMES  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "fixtures"
RESULTS_DIR = REPO_ROOT / "results"

# Results files with a different schema; every other results/*.csv is checked.
EXCLUDED_FILES = ("drop2-thinking-onoff-reference.csv", "receipts-banked-rows.csv")
COLUMNS = ["model_id", "fixture_id", "outcome", "format_variant", "base_task_id"]
VARIANTS = {"short", "embedded-neutral", "embedded-production"}
MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*\Z")
MAX_REPETITIONS = 10
FIXTURE_IDS = re.compile(r"^fixture_ids:[ \t]*(\S.*?)[ \t]*$", re.M)
REPETITIONS = re.compile(r"^repetitions:[ \t]*(\d+)[ \t]*$", re.M)


def load_fixture_index(
    fixtures_dir: Path,
) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """(fixture id -> (base_task_id, format_variant), problems); bad files are reported."""
    index: dict[str, tuple[str, str]] = {}
    problems: list[str] = []
    owner: dict[str, str] = {}
    for path in sorted(fixtures_dir.rglob("*.json")):
        try:
            data = json.loads(path.read_text())
            meta = data.get("metadata", {})
            if data["id"] in index:
                problems.append(
                    f"duplicate fixture id {data['id']!r} in {owner[data['id']]} "
                    f"and {path.name}"
                )
                continue
            owner[data["id"]] = path.name
            index[data["id"]] = (meta.get("base_task_id"), meta.get("format_variant"))
        except (OSError, ValueError, KeyError, AttributeError) as exc:
            problems.append(f"{path.name}: unreadable fixture ({exc!r})")
    return index, problems


def check_row(row: dict, index: dict[str, tuple[str, str]]) -> str | None:
    """Return an error string for one row, or None if it is valid."""
    if row["outcome"] not in OUTCOMES:
        return f"unknown outcome {row['outcome']!r}"
    if row["format_variant"] not in VARIANTS:
        return f"unknown format_variant {row['format_variant']!r}"
    if not MODEL_ID.match(row["model_id"]):
        return f"model_id {row['model_id']!r} is empty or not a plain identifier"
    expected = index.get(row["fixture_id"])
    if expected is None:
        return f"fixture_id {row['fixture_id']!r} matches no file under fixtures/"
    if (row["base_task_id"], row["format_variant"]) != expected:
        return (
            f"base_task_id/format_variant disagree with fixture {row['fixture_id']!r}"
        )
    return None


def discover_files(results_dir: Path) -> list[Path]:
    """Every results/*.csv except the files with a different schema."""
    return [
        p for p in sorted(results_dir.glob("*.csv")) if p.name not in EXCLUDED_FILES
    ]


def declared_repetitions(path: Path) -> int | None:
    """`repetitions: N` from the sibling PROVENANCE file, or None when absent."""
    prov = path.with_name(path.stem + ".PROVENANCE.md")
    if prov.is_file():
        match = REPETITIONS.search(prov.read_text())
        if match:
            return int(match.group(1))
    return None


def recorded_fixture_ids(path: Path) -> set[str] | None:
    """`fixture_ids: a, b, ...` from the sibling PROVENANCE file (the set the file was
    produced from), or None when absent."""
    prov = path.with_name(path.stem + ".PROVENANCE.md")
    if prov.is_file():
        match = FIXTURE_IDS.search(prov.read_text())
        if match:
            return {x.strip() for x in match.group(1).split(",") if x.strip()}
    return None


def check_file(
    path: Path, index: dict[str, tuple[str, str]]
) -> tuple[list[str], Counter]:
    errors: list[str] = []
    cells: Counter = Counter()
    per_fixture: Counter = Counter()
    limit = declared_repetitions(path)
    if limit is None:
        return [
            f"{path.name}: sibling {path.stem}.PROVENANCE.md must declare "
            f"`repetitions: N`"
        ], cells
    if not 1 <= limit <= MAX_REPETITIONS:
        return [
            f"{path.name}: declared repetitions {limit} is outside the cap "
            f"1..{MAX_REPETITIONS}"
        ], cells
    recorded = recorded_fixture_ids(path)
    if not recorded:  # absent or empty both fail closed
        return [
            f"{path.name}: sibling {path.stem}.PROVENANCE.md must record a non-empty "
            f"fixture set as `fixture_ids: a, b, ...`"
        ], cells
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COLUMNS:
            return [f"{path.name}: header must be exactly {','.join(COLUMNS)}"], cells
        for lineno, row in enumerate(reader, start=2):
            if None in row or None in row.values():
                errors.append(f"{path.name}:{lineno}: wrong number of columns")
                continue
            problem = check_row(row, index)
            if problem:
                errors.append(f"{path.name}:{lineno}: {problem}")
            else:
                cells[
                    (row["model_id"], row["base_task_id"], row["format_variant"])
                ] += 1
                per_fixture[(row["model_id"], row["fixture_id"])] += 1
                if row["fixture_id"] not in recorded:
                    errors.append(
                        f"{path.name}:{lineno}: fixture_id {row['fixture_id']!r} is "
                        f"not in the recorded fixture_ids set"
                    )
    for (model, fid), n in sorted(per_fixture.items()):
        if n > limit:
            errors.append(
                f"{path.name}: duplicate rows for ({model}, {fid}): {n} > "
                f"declared repetitions {limit}"
            )
        elif n < limit:
            errors.append(
                f"{path.name}: every cell must carry exactly {limit} rows; "
                f"({model}, {fid}) has {n}"
            )
    if not per_fixture and not errors:
        errors.append(f"{path.name}: no rows (a results file must carry data)")
    for model in sorted({m for m, _ in per_fixture}):
        for fid in sorted(recorded):
            if (model, fid) not in per_fixture:
                errors.append(
                    f"{path.name}: model {model!r} is missing fixture {fid!r}; every "
                    f"model must cover every recorded fixture with exactly {limit} rows"
                )
    return errors, cells


def check_all(files: list[Path], index: dict[str, tuple[str, str]]) -> list[str]:
    """Check every file; a failure in one never stops the rest."""
    all_errors: list[str] = []
    for path in files:
        try:
            errors, cells = check_file(path, index)
        except Exception as exc:  # report per file and continue
            all_errors.append(f"{path.name}: could not be checked ({exc!r})")
            continue
        all_errors.extend(errors)
        print(
            f"{path.name}: {sum(cells.values())} rows in {len(cells)} cells "
            f"(max n per cell: {max(cells.values(), default=0)}, "
            f"declared repetitions: {declared_repetitions(path)})"
        )
    return all_errors


def main() -> int:
    index, problems = load_fixture_index(FIXTURES_DIR)
    all_errors = problems + check_all(discover_files(RESULTS_DIR), index)
    if all_errors:
        print("Results shape check FAILED:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("OK: results files are the five-column shape.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
