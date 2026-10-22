"""Red-first tests for tools/shape_rules.py, the one definition of an applicable check."""

import unittest

import shape_rules as sr

EMPTY = {
    "produces_code": False,
    "min_length": 0,
    "must_contain": [],
    "must_not_contain": [],
    "required_sections": [],
    "json_schema_keys": [],
}


class ShapeRulesTests(unittest.TestCase):
    def test_empty_shape_has_no_applicable_check(self):
        self.assertFalse(sr.has_applicable_check(EMPTY))

    def test_each_constraint_alone_is_applicable(self):
        for key, val in (
            ("produces_code", True),
            ("min_length", 5),
            ("must_contain", ["a"]),
            ("must_not_contain", ["a"]),
            ("required_sections", ["s"]),
            ("json_schema_keys", ["k"]),
        ):
            self.assertTrue(sr.has_applicable_check(dict(EMPTY, **{key: val})), key)

    def test_malformed_min_length_raises_value_error(self):
        with self.assertRaises(ValueError):
            sr.has_applicable_check(dict(EMPTY, min_length="lots"))

    def test_non_dict_shape_is_not_applicable(self):
        self.assertFalse(sr.has_applicable_check(None))


if __name__ == "__main__":
    unittest.main()
