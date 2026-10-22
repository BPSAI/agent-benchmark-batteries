"""Score one completion against a fixture's expected_shape.

Implements the substring/shape protocol in docs/running-the-battery.md with no
model in the loop. Each applicable check is satisfied or not:
  produces_code, min_length, must_contain (all), must_not_contain (none),
  required_sections (all), json_schema_keys (all).
refused: empty / under 20 characters, or no code and an opening decline phrase.
pass: every applicable check satisfied. partial: at least half. fail: fewer.
"""

from __future__ import annotations

import re

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
    if int(shape.get("min_length") or 0) > 0:
        checks.append(len(text) >= int(shape["min_length"]))
    checks.extend(s in text for s in shape.get("must_contain", []))
    if shape.get("must_not_contain"):
        checks.append(not any(s in text for s in shape["must_not_contain"]))
    checks.extend(s.lower() in text.lower() for s in shape.get("required_sections", []))
    checks.extend(k in text for k in shape.get("json_schema_keys", []))
    return checks


def score(completion: str, shape: dict) -> str:
    text = completion or ""
    stripped = text.strip()
    if len(stripped) < 20 or (
        DECLINE.match(stripped) and not CODE_HINT.search(stripped)
    ):
        return "refused"
    checks = _checks(text, shape)
    if all(checks):
        return "pass"
    return "partial" if sum(checks) * 2 >= len(checks) else "fail"
