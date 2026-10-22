"""Score one completion against a fixture's expected_shape.

Implements the substring/shape protocol in docs/running-the-battery.md with no
model in the loop. Each applicable check is satisfied or not:
  produces_code, min_length, must_contain (all), must_not_contain (none),
  required_sections (all), json_schema_keys (all).
invalid-fixture: the shape has no applicable check (a fixture defect; the
stamp check refuses such fixtures).
refused: empty / under 20 characters, or no code and an opening decline phrase.
pass: every applicable check satisfied. partial: at least half. fail: fewer.
"""

from __future__ import annotations

import re

from shape_rules import min_length_of, nonempty

DECLINE = re.compile(
    r"^\W*(i\s+(can'?t|cannot|can not|won'?t|am unable to|'m unable to|'m sorry)|"
    r"sorry|i'm sorry|unable to)",
    re.I,
)
CODE_HINT = re.compile(r"```|^\s*(def|class|import|from)\s", re.M)


def _checks(text: str, shape: dict) -> list[bool]:
    checks: list[bool] = []
    if shape.get("produces_code"):
        checks.append(bool(CODE_HINT.search(text)))
    if min_length_of(shape) > 0:
        checks.append(len(text) >= min_length_of(shape))
    checks.extend(s in text for s in nonempty(shape, "must_contain"))
    forbidden = nonempty(shape, "must_not_contain")
    if forbidden:
        checks.append(not any(s in text for s in forbidden))
    checks.extend(
        s.lower() in text.lower() for s in nonempty(shape, "required_sections")
    )
    checks.extend(k in text for k in nonempty(shape, "json_schema_keys"))
    return checks


def score(completion: str, shape: dict) -> str:
    text = completion or ""
    try:
        checks = _checks(text, shape)
    except ValueError:  # malformed shape (e.g. min_length): a fixture defect
        return "invalid-fixture"
    if not checks:  # a fixture defect, reported before any completion judgment
        return "invalid-fixture"
    stripped = text.strip()
    if len(stripped) < 20 or (
        DECLINE.match(stripped) and not CODE_HINT.search(stripped)
    ):
        return "refused"
    if all(checks):
        return "pass"
    return "partial" if sum(checks) * 2 >= len(checks) else "fail"
