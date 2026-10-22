"""Red-first tests for governance/check_fixture_stamps.py (applicable-check rule)."""

import json
import tempfile
import unittest
from pathlib import Path

import check_fixture_stamps as cfs

STAMP = {"public_release": True, "provenance": "original-authored"}


def fixture(shape: dict) -> Path:
    path = Path(tempfile.mkdtemp()) / "f.json"
    path.write_text(json.dumps({"metadata": STAMP, "expected_shape": shape}))
    return path


class ApplicableCheckTests(unittest.TestCase):
    def test_fixture_with_no_applicable_check_is_refused(self):
        shape = {
            "produces_code": False,
            "min_length": 0,
            "must_contain": [],
            "must_not_contain": [],
            "required_sections": [],
            "json_schema_keys": [],
        }
        err = cfs.check_stamp(fixture(shape))
        self.assertIn("applicable", err)

    def test_fixture_with_one_applicable_check_passes(self):
        shape = {
            "produces_code": False,
            "min_length": 5,
            "must_contain": [],
            "must_not_contain": [],
            "required_sections": [],
            "json_schema_keys": [],
        }
        self.assertIsNone(cfs.check_stamp(fixture(shape)))

    def test_malformed_min_length_is_a_named_fixture_error_not_a_crash(self):
        shape = {
            "produces_code": False,
            "min_length": "lots",
            "must_contain": ["a"],
            "must_not_contain": [],
            "required_sections": [],
            "json_schema_keys": [],
        }
        path = fixture(shape)
        err = cfs.check_stamp(path)
        self.assertIn(str(path), err)
        self.assertIn("min_length", err)


if __name__ == "__main__":
    unittest.main()
