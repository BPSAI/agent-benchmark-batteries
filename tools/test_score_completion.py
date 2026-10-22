"""Red-first tests for tools/score_completion.py (two synthetic completions per class)."""
import unittest
from score_completion import score

SHAPE = {
    "produces_code": True, "min_length": 40,
    "must_contain": ["def f", "alpha"], "must_not_contain": ["TODO"],
    "required_sections": [], "json_schema_keys": [],
}
GOOD = "```python\ndef f(x):\n    # alpha handling for the value\n    return x\n```\n"


class ScoreTests(unittest.TestCase):
    def test_pass_full(self):
        self.assertEqual(score(GOOD, SHAPE), "pass")

    def test_pass_with_sections_and_keys(self):
        shape = dict(SHAPE, required_sections=["Notes"], json_schema_keys=["k"])
        self.assertEqual(score(GOOD + "\nNotes: {\"k\": 1}", shape), "pass")

    def test_partial_missing_identifier(self):
        self.assertEqual(score(GOOD.replace("alpha", "beta") + " pad pad", SHAPE), "partial")

    def test_partial_forbidden_present(self):
        self.assertEqual(score(GOOD + "# TODO later", SHAPE), "partial")

    def test_fail_prose_only(self):
        self.assertEqual(score("Here is a long description of the approach without any source "
                               "listing at all, just words, words and more words.", SHAPE), "fail")

    def test_fail_short_wrong(self):
        self.assertEqual(score("```\nx = 1 # TODO\n```", SHAPE), "fail")

    def test_refused_explicit(self):
        self.assertEqual(score("I can't help with that request.", SHAPE), "refused")

    def test_refused_empty(self):
        self.assertEqual(score("   \n", SHAPE), "refused")


if __name__ == "__main__":
    unittest.main()
