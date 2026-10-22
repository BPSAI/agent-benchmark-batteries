"""Red-first tests for governance/check_results_shape.py."""

import json
import tempfile
import unittest
from pathlib import Path

import sys
from pathlib import Path as _P

sys.path.insert(0, str(_P(__file__).resolve().parent.parent / "tools"))
import check_results_shape as crs

HEADER = "model_id,fixture_id,outcome,format_variant,base_task_id\n"
INDEX1 = {"b--short": ("b", "short")}
INDEX = {"b--short": ("b", "short"), "b--embed-neutral": ("b", "embedded-neutral")}


def write(
    directory: Path,
    name: str,
    rows: list[str],
    provenance: str | None = "repetitions: 1\nfixture_ids: b--short\n",
) -> Path:
    path = directory / name
    path.write_text(HEADER + "".join(r + "\n" for r in rows))
    if provenance is not None:
        (directory / (path.stem + ".PROVENANCE.md")).write_text(provenance)
    return path


class ShapeTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_discovery_globs_csvs_and_skips_excluded_schemas(self):
        for name in (
            "a.csv",
            "drop2-thinking-onoff-reference.csv",
            "receipts-banked-rows.csv",
        ):
            write(self.dir, name, [])
        found = [p.name for p in crs.discover_files(self.dir)]
        self.assertEqual(found, ["a.csv"])

    def test_duplicate_beyond_declared_repetition_fails(self):
        row = "m,b--short,pass,short,b"
        path = write(
            self.dir,
            "x.csv",
            [row, row],
            provenance="repetitions: 1\nfixture_ids: b--short\n",
        )
        errors, _ = crs.check_file(path, INDEX1)
        self.assertTrue(any("duplicate" in e for e in errors))

    def test_declared_repetitions_allow_repeats_and_report_n(self):
        row = "m,b--short,pass,short,b"
        path = write(
            self.dir,
            "x.csv",
            [row] * 3,
            provenance="repetitions: 3\nfixture_ids: b--short\n",
        )
        errors, cells = crs.check_file(path, INDEX1)
        self.assertEqual(errors, [])
        self.assertEqual(cells[("m", "b", "short")], 3)

    def test_more_than_declared_repetitions_fails(self):
        row = "m,b--short,pass,short,b"
        path = write(
            self.dir,
            "x.csv",
            [row] * 4,
            provenance="repetitions: 3\nfixture_ids: b--short\n",
        )
        errors, _ = crs.check_file(path, INDEX1)
        self.assertTrue(any("duplicate" in e for e in errors))

    def test_formula_leading_model_id_fails(self):
        path = write(self.dir, "x.csv", ["=cmd,b--short,pass,short,b"])
        errors, _ = crs.check_file(path, INDEX1)
        self.assertTrue(any("model_id" in e for e in errors))

    def test_valid_local_model_ids_pass(self):
        path = write(
            self.dir,
            "x.csv",
            [
                "gemma4:31b,b--short,pass,short,b",
                "hf.co/org/m:Q4_K_M,b--short,pass,short,b",
            ],
        )
        errors, _ = crs.check_file(path, INDEX1)
        self.assertEqual(errors, [])

    def test_missing_provenance_line_is_refused_not_defaulted(self):
        path = write(self.dir, "x.csv", ["m,b--short,pass,short,b"], provenance=None)
        errors, _ = crs.check_file(path, INDEX1)
        self.assertTrue(any("repetitions" in e for e in errors))
        path2 = write(
            self.dir, "y.csv", ["m,b--short,pass,short,b"], provenance="no line here\n"
        )
        errors, _ = crs.check_file(path2, INDEX1)
        self.assertTrue(any("repetitions" in e for e in errors))

    def test_declared_value_above_cap_is_refused(self):
        row = "m,b--short,pass,short,b"
        path = write(
            self.dir,
            "x.csv",
            [row],
            provenance="repetitions: 9999\nfixture_ids: b--short\n",
        )
        errors, _ = crs.check_file(path, INDEX1)
        self.assertTrue(any("cap" in e for e in errors))

    def test_every_cell_must_carry_exactly_the_declared_n(self):
        rows = ["m,b--short,pass,short,b"] * 3 + [
            "m,b--embed-neutral,pass,embedded-neutral,b"
        ] * 2
        path = write(
            self.dir,
            "x.csv",
            rows,
            provenance="repetitions: 3\nfixture_ids: b--short, b--embed-neutral\n",
        )
        errors, _ = crs.check_file(path, INDEX)
        self.assertTrue(any("exactly" in e and "b--embed-neutral" in e for e in errors))

    def test_model_missing_a_fixture_is_refused(self):
        rows = ["m,b--short,pass,short,b"] + ["n,b--short,pass,short,b"] * 1
        rows += ["n,b--embed-neutral,pass,embedded-neutral,b"]
        path = write(
            self.dir,
            "x.csv",
            rows,
            provenance="repetitions: 1\nfixture_ids: b--short, b--embed-neutral\n",
        )
        errors, _ = crs.check_file(path, INDEX)
        self.assertTrue(
            any("m" in e and "b--embed-neutral" in e and "missing" in e for e in errors)
        )

    def test_trailing_newline_in_model_id_is_rejected(self):
        row = {
            "model_id": "m\n",
            "fixture_id": "b--short",
            "outcome": "pass",
            "format_variant": "short",
            "base_task_id": "b",
        }
        self.assertIsNotNone(crs.check_row(row, INDEX))
        self.assertIsNone(crs.check_row(dict(row, model_id="m"), INDEX))

    def test_header_only_file_is_refused(self):
        path = write(
            self.dir, "x.csv", [], provenance="repetitions: 1\nfixture_ids: b--short\n"
        )
        errors, _ = crs.check_file(path, INDEX1)
        self.assertTrue(any("no rows" in e for e in errors))

    def test_one_bad_file_does_not_stop_the_others(self):
        good = write(
            self.dir,
            "good.csv",
            ["m,b--short,pass,short,b"],
            provenance="repetitions: 1\nfixture_ids: b--short\n",
        )
        bad = self.dir / "bad.csv"
        bad.write_text("not,the,header\n")
        errors = crs.check_all([bad, good], INDEX1)
        self.assertTrue(any("bad.csv" in e for e in errors))
        self.assertFalse(any("good.csv" in e for e in errors))

    def test_malformed_fixture_is_reported_and_indexing_continues(self):
        fx = self.dir / "fx"
        fx.mkdir()
        (fx / "broken.json").write_text("{not json")
        (fx / "ok.json").write_text(
            json.dumps(
                {
                    "id": "a--short",
                    "metadata": {"base_task_id": "a", "format_variant": "short"},
                }
            )
        )
        index, problems = crs.load_fixture_index(fx)
        self.assertIn("a--short", index)
        self.assertTrue(any("broken.json" in p for p in problems))

    def test_repetitions_number_on_the_next_line_is_not_accepted(self):
        path = write(
            self.dir,
            "x.csv",
            ["m,b--short,pass,short,b"],
            provenance="repetitions:\n1\n",
        )
        errors, _ = crs.check_file(path, INDEX1)
        self.assertTrue(any("repetitions" in e for e in errors))

    def test_duplicate_fixture_ids_are_refused_naming_both_files(self):
        fx = self.dir / "fx2"
        fx.mkdir()
        body = json.dumps(
            {
                "id": "a--short",
                "metadata": {"base_task_id": "a", "format_variant": "short"},
            }
        )
        (fx / "one.json").write_text(body)
        (fx / "two.json").write_text(body)
        _, problems = crs.load_fixture_index(fx)
        self.assertTrue(any("one.json" in p and "two.json" in p for p in problems))

    def test_coverage_uses_the_recorded_fixture_set_not_the_live_one(self):
        # a fixture added after the file was produced must not break the file
        live = dict(INDEX, **{"b--new": ("b", "embedded-production")})
        path = write(self.dir, "x.csv", ["m,b--short,pass,short,b"])
        errors, _ = crs.check_file(path, live)
        self.assertEqual(errors, [])

    def test_missing_fixture_ids_line_is_refused(self):
        path = write(
            self.dir,
            "x.csv",
            ["m,b--short,pass,short,b"],
            provenance="repetitions: 1\n",
        )
        errors, _ = crs.check_file(path, INDEX1)
        self.assertTrue(any("fixture_ids" in e for e in errors))

    def test_invalid_fixture_outcome_is_in_the_shared_vocabulary(self):
        import shape_rules
        import score_completion

        self.assertIn("invalid-fixture", shape_rules.OUTCOMES)
        self.assertEqual(crs.OUTCOMES, shape_rules.OUTCOMES)
        row = {
            "model_id": "m",
            "fixture_id": "b--short",
            "outcome": "invalid-fixture",
            "format_variant": "short",
            "base_task_id": "b",
        }
        self.assertIsNone(crs.check_row(row, INDEX1))
        for shape in ({}, {"must_contain": ["x"]}):
            self.assertIn(score_completion.score("y" * 30, shape), shape_rules.OUTCOMES)


if __name__ == "__main__":
    unittest.main()
