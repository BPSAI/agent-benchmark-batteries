"""Red-first tests for tools/run_local_battery.py, using a fake client (no network)."""

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run_local_battery as rlb

COLUMNS = ["model_id", "fixture_id", "outcome", "format_variant", "base_task_id"]
SHAPE = {
    "produces_code": False,
    "min_length": 1,
    "must_contain": [],
    "must_not_contain": [],
    "required_sections": [],
    "json_schema_keys": [],
}


def fixture(fid, base="b1", variant="short"):
    return {
        "id": fid,
        "system_prompt": "s",
        "input_prompt": "u",
        "expected_shape": SHAPE,
        "metadata": {"base_task_id": base, "format_variant": variant},
    }


class FakeClient:
    def __init__(self, served=None, fail_on_call=None, digests=None):
        self.calls, self.served, self.fail_on_call = [], served or {}, fail_on_call
        self.digests = digests or {}

    def digest(self, model):
        d = self.digests.get(model, "sha256:" + model)
        return d(len(self.calls)) if callable(d) else d

    def chat(self, model, system, user, options):
        self.calls.append(model)
        if self.fail_on_call == len(self.calls):
            raise RuntimeError("interrupted")
        return {
            "content": "some completion text",
            "served_model": self.served.get(model, model),
        }

    def show(self, model):
        return {"parameters": "temperature 1"}


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.raw, self.csv = self.tmp / "raw", self.tmp / "rows.csv"
        self.fx = [
            fixture("b1--short"),
            fixture("b1--embed-neutral", variant="embedded-neutral"),
        ]

    def run_it(self, client, models=("m1",), rounds=1, options=None):
        rlb.run(models, rounds, self.raw, self.csv, client, self.fx, options or {})

    def rows(self):
        with self.csv.open(newline="") as f:
            return list(csv.reader(f))

    def test_fresh_csv_has_header(self):
        self.run_it(FakeClient())
        self.assertEqual(self.rows()[0], COLUMNS)
        self.assertEqual(len(self.rows()), 3)

    def test_two_arms_share_raw_dir_without_collision(self):
        client = FakeClient()
        self.run_it(client, models=("m1", "m2"))
        self.assertEqual(len(client.calls), 4)
        self.assertEqual(len(self.rows()), 5)

    def test_interruption_never_omits_or_duplicates_a_row(self):
        with self.assertRaises(RuntimeError):
            self.run_it(FakeClient(fail_on_call=2), models=("m1", "m2"))
        self.run_it(FakeClient(), models=("m1", "m2"))
        keys = [(r[0], r[1]) for r in self.rows()[1:]]
        self.assertEqual(len(keys), 4)
        self.assertEqual(len(set(keys)), 4)

    def test_raw_file_records_requested_served_and_settings(self):
        opts = {"num_ctx": 16384, "temperature": 0.0}
        self.run_it(FakeClient(served={"m1": "m1:latest"}), options=opts)
        raw = json.loads(next(self.raw.glob("*.json")).read_text())
        self.assertEqual(raw["requested_model"], "m1")
        self.assertEqual(raw["served_model"], "m1:latest")
        self.assertEqual(raw["model_digest"], "sha256:m1")
        self.assertEqual(raw["options"], opts)
        self.assertEqual(raw["show"], {"parameters": "temperature 1"})

    def test_arms_interleave_within_each_round(self):
        client = FakeClient()
        self.run_it(client, models=("m1", "m2"), rounds=2)
        self.assertEqual(client.calls, ["m1", "m2"] * 4)

    def test_unsafe_fixture_id_is_rejected(self):
        self.fx = [fixture("../escape")]
        with self.assertRaises(ValueError):
            self.run_it(FakeClient())

    def test_refuses_to_overwrite_a_csv_that_has_no_raw_backing(self):
        self.csv.write_text(",".join(COLUMNS) + "\nm1,b1--short,pass,short,b1\n")
        with self.assertRaises(SystemExit):
            self.run_it(FakeClient())

    def test_guard_checks_every_row_not_just_any_raw_file(self):
        self.run_it(FakeClient(), models=("m1",))  # raw files now exist for m1
        with self.csv.open("a") as f:
            f.write("ghost,b1--short,pass,short,b1\n")  # a row with no raw backing
        with self.assertRaises(SystemExit) as cm:
            self.run_it(FakeClient(), models=("m1",))
        self.assertIn("ghost", str(cm.exception))
        self.assertIn("ghost", self.csv.read_text())  # nothing was deleted

    def test_ids_that_used_to_share_a_slug_stay_separate(self):
        client = FakeClient()
        self.run_it(client, models=("m:a", "m_a"))
        self.assertEqual(len(client.calls), 4)
        self.assertEqual(len(list(self.raw.glob("*.json"))), 4)

    def test_preexisting_path_with_other_requested_id_is_refused(self):
        self.run_it(FakeClient(), models=("m:a",))
        for p in self.raw.glob("*.json"):
            data = json.loads(p.read_text())
            data["requested_model"] = "someone-else"
            p.write_text(json.dumps(data))
        with self.assertRaises(SystemExit) as cm:
            self.run_it(FakeClient(), models=("m:a",))
        self.assertIn("requested_model", str(cm.exception))

    def test_resume_refuses_changed_options(self):
        self.run_it(FakeClient(), options={"num_ctx": 1})
        with self.assertRaises(SystemExit) as cm:
            self.run_it(FakeClient(), options={"num_ctx": 2})
        self.assertIn("options", str(cm.exception))

    def test_resume_refuses_changed_fixture_content(self):
        self.run_it(FakeClient())
        self.fx[0] = dict(self.fx[0], input_prompt="a different task")
        with self.assertRaises(SystemExit) as cm:
            self.run_it(FakeClient())
        self.assertIn("fixture_sha256", str(cm.exception))

    def test_resume_refuses_changed_scorer(self):
        self.run_it(FakeClient())
        with mock.patch.object(rlb, "SCORER_SHA256", "different"):
            with self.assertRaises(SystemExit) as cm:
                self.run_it(FakeClient())
        self.assertIn("scorer_sha256", str(cm.exception))


    # --- Findings carried from the Drop 3 kit review (PR #4) ---

    def test_adding_an_arm_to_an_existing_run_is_refused(self):
        """P1: arms added in a later invocation were never interleaved."""
        self.run_it(FakeClient(), models=("m1",))
        with self.assertRaises(SystemExit) as cm:
            self.run_it(FakeClient(), models=("m1", "m2"))
        self.assertIn("models", str(cm.exception))

    def test_raw_dir_with_files_but_no_run_manifest_is_refused(self):
        """P1: raw files of unknown provenance never enter a rebuilt CSV."""
        self.run_it(FakeClient(), models=("m1",))
        (self.raw / rlb.RUN_MANIFEST).unlink()
        with self.assertRaises(SystemExit) as cm:
            self.run_it(FakeClient(), models=("m1",))
        self.assertIn(rlb.RUN_MANIFEST, str(cm.exception))

    def test_rebuild_skips_nothing_and_admits_no_foreign_arm(self):
        """P1: a raw file whose arm is outside the run's panel is refused."""
        self.run_it(FakeClient(), models=("m1",))
        src = next(self.raw.glob("r1--m1--*.json"))
        data = json.loads(src.read_text())
        data["requested_model"] = "intruder"
        data["row"][0] = "intruder"
        (self.raw / "r1--intruder--b1--short.json").write_text(json.dumps(data))
        with self.assertRaises(SystemExit) as cm:
            rlb.rebuild_csv(self.raw, self.csv, ("m1",))
        self.assertIn("intruder", str(cm.exception))

    def test_resume_refuses_changed_fixture_metadata(self):
        """P2: metadata is part of the fixture digest."""
        self.run_it(FakeClient())
        self.fx[0] = fixture("b1--short", base="b9")
        with self.assertRaises(SystemExit) as cm:
            self.run_it(FakeClient())
        self.assertIn("fixture_sha256", str(cm.exception))

    def test_resume_refuses_a_replaced_model_digest(self):
        """P2: the same tag with new weights is a different arm."""
        self.run_it(FakeClient(), models=("m1",))
        with self.assertRaises(SystemExit) as cm:
            self.run_it(FakeClient(digests={"m1": "sha256:new-weights"}), models=("m1",))
        self.assertIn("digest", str(cm.exception))

    def test_served_model_that_differs_from_requested_is_refused(self):
        """Finding 4: the served id is compared, and nothing is written for it."""
        with self.assertRaises(SystemExit) as cm:
            self.run_it(FakeClient(served={"m1": "other-model"}), models=("m1",))
        self.assertIn("other-model", str(cm.exception))
        self.assertEqual(list(self.raw.glob("r*.json")), [])


    # --- Review round 1 on #5 ---

    def test_scorer_pin_covers_every_local_module_the_scorer_imports(self):
        """SERIOUS 1: a change to shape_rules.py must refuse a resume."""
        import ast

        tools = Path(rlb.__file__).parent
        tree = ast.parse((tools / "score_completion.py").read_text())
        local = {
            node.module + ".py"
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            and (tools / (node.module + ".py")).exists()
        }
        self.assertTrue(local)
        self.assertLessEqual(local | {"score_completion.py"}, set(rlb.SCORER_FILES))

    def test_resume_refuses_a_changed_runner(self):
        """MINOR 4: the harness itself is pinned per run."""
        self.run_it(FakeClient())
        with mock.patch.object(rlb, "RUNNER_SHA256", "different"):
            with self.assertRaises(SystemExit) as cm:
                self.run_it(FakeClient())
        self.assertIn("runner_sha256", str(cm.exception))

    def test_resume_refuses_a_changed_fixture_set(self):
        """MINOR 4: adding a fixture between invocations is a different run."""
        self.run_it(FakeClient())
        self.fx.append(fixture("b2--short", base="b2"))
        with self.assertRaises(SystemExit) as cm:
            self.run_it(FakeClient())
        self.assertIn("fixture_ids", str(cm.exception))

    def test_run_records_start_and_completion_times(self):
        """MINOR 4: the date is part of the run record."""
        self.run_it(FakeClient())
        manifest = json.loads((self.raw / rlb.RUN_MANIFEST).read_text())
        self.assertRegex(manifest["started_at_utc"], r"^\d{4}-\d\d-\d\dT")
        raw = json.loads(next(self.raw.glob("*.json")).read_text())
        self.assertRegex(raw["completed_at_utc"], r"^\d{4}-\d\d-\d\dT")

    def test_weights_replaced_mid_invocation_stop_the_run(self):
        """MINOR 2: the digest is re-read every round, not once per invocation."""
        client = FakeClient(digests={"m1": lambda n: "sha256:a" if n < 2 else "sha256:b"})
        with self.assertRaises(SystemExit) as cm:
            self.run_it(client, models=("m1",), rounds=2)
        self.assertIn("digest", str(cm.exception))

    def test_name_normalization_matches_ollama(self):
        """MINOR 3: default registry and namespace dropped, case-insensitive, :latest implied."""
        n = rlb._normalize_name
        self.assertEqual(n("library/gemma4:31b"), "gemma4:31b")
        self.assertEqual(n("registry.ollama.ai/library/gemma4:31b"), "gemma4:31b")
        self.assertEqual(n("Gemma4:31B"), "gemma4:31b")
        self.assertEqual(n("llama3.2"), "llama3.2:latest")
        self.assertEqual(n("hf.co/u/r"), "hf.co/u/r:latest")
        self.assertEqual(n("myuser/custom:v1"), "myuser/custom:v1")


if __name__ == "__main__":
    unittest.main()
