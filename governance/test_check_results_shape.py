"""Red-first tests for governance/check_results_shape.py."""
import tempfile
import unittest
from pathlib import Path

import check_results_shape as crs

HEADER = "model_id,fixture_id,outcome,format_variant,base_task_id\n"
INDEX = {"b--short": ("b", "short"), "b--embed-neutral": ("b", "embedded-neutral")}


def write(directory: Path, name: str, rows: list[str], provenance: str | None = None) -> Path:
    path = directory / name
    path.write_text(HEADER + "".join(r + "\n" for r in rows))
    if provenance is not None:
        (directory / (path.stem + ".PROVENANCE.md")).write_text(provenance)
    return path


class ShapeTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_discovery_globs_csvs_and_skips_excluded_schemas(self):
        for name in ("a.csv", "drop2-thinking-onoff-reference.csv", "receipts-banked-rows.csv"):
            write(self.dir, name, [])
        found = [p.name for p in crs.discover_files(self.dir)]
        self.assertEqual(found, ["a.csv"])

    def test_duplicate_beyond_declared_repetition_fails(self):
        row = "m,b--short,pass,short,b"
        path = write(self.dir, "x.csv", [row, row])
        errors, _ = crs.check_file(path, INDEX)
        self.assertTrue(any("duplicate" in e for e in errors))

    def test_declared_repetitions_allow_repeats_and_report_n(self):
        row = "m,b--short,pass,short,b"
        path = write(self.dir, "x.csv", [row] * 3, provenance="repetitions: 3\n")
        errors, cells = crs.check_file(path, INDEX)
        self.assertEqual(errors, [])
        self.assertEqual(cells[("m", "b", "short")], 3)

    def test_more_than_declared_repetitions_fails(self):
        row = "m,b--short,pass,short,b"
        path = write(self.dir, "x.csv", [row] * 4, provenance="repetitions: 3\n")
        errors, _ = crs.check_file(path, INDEX)
        self.assertTrue(any("duplicate" in e for e in errors))

    def test_formula_leading_model_id_fails(self):
        path = write(self.dir, "x.csv", ["=cmd,b--short,pass,short,b"])
        errors, _ = crs.check_file(path, INDEX)
        self.assertTrue(any("model_id" in e for e in errors))

    def test_valid_local_model_ids_pass(self):
        path = write(self.dir, "x.csv", ["gemma4:31b,b--short,pass,short,b",
                                         "hf.co/org/m:Q4_K_M,b--short,pass,short,b"])
        errors, _ = crs.check_file(path, INDEX)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
