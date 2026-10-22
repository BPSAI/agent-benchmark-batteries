"""Red-first tests for tools/run_local_battery.py, using a fake client (no network)."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

import run_local_battery as rlb

COLUMNS = ["model_id", "fixture_id", "outcome", "format_variant", "base_task_id"]
SHAPE = {"produces_code": False, "min_length": 1, "must_contain": [],
         "must_not_contain": [], "required_sections": [], "json_schema_keys": []}


def fixture(fid, base="b1", variant="short"):
    return {"id": fid, "system_prompt": "s", "input_prompt": "u", "expected_shape": SHAPE,
            "metadata": {"base_task_id": base, "format_variant": variant}}


class FakeClient:
    def __init__(self, served=None, fail_on_call=None):
        self.calls, self.served, self.fail_on_call = [], served or {}, fail_on_call

    def chat(self, model, system, user, options):
        self.calls.append(model)
        if self.fail_on_call == len(self.calls):
            raise RuntimeError("interrupted")
        return {"content": "some completion text", "served_model": self.served.get(model, model)}

    def show(self, model):
        return {"parameters": "temperature 1"}


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.raw, self.csv = self.tmp / "raw", self.tmp / "rows.csv"
        self.fx = [fixture("b1--short"), fixture("b1--embed-neutral", variant="embedded-neutral")]

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


if __name__ == "__main__":
    unittest.main()
