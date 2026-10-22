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
    def __init__(self, served=None, fail_on_call=None):
        self.calls, self.served, self.fail_on_call = [], served or {}, fail_on_call

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
        self.run_it(FakeClient(served={"m1": "m1-snapshot"}), options=opts)
        raw = json.loads(next(self.raw.glob("*.json")).read_text())
        self.assertEqual(raw["requested_model"], "m1")
        self.assertEqual(raw["served_model"], "m1-snapshot")
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


if __name__ == "__main__":
    unittest.main()
