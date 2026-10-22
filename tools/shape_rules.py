"""The one definition of an applicable check in a fixture's expected_shape.

Imported by the scorer (tools/score_completion.py) and by the fixture stamp
check (governance/check_fixture_stamps.py) so the two can never disagree.
"""

from __future__ import annotations

# The one outcome vocabulary: everything score() can return, and what results files accept.
OUTCOMES = frozenset({"pass", "partial", "fail", "refused", "invalid-fixture"})


def min_length_of(shape: dict) -> int:
    """The shape's min_length as an int; ValueError when it is not a number."""
    try:
        return int(shape.get("min_length") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"min_length {shape.get('min_length')!r} is not an integer"
        ) from exc


def nonempty(shape: dict, key: str) -> list[str]:
    """The constraint list's non-blank strings; blanks constrain nothing."""
    return [x for x in (shape.get(key) or []) if isinstance(x, str) and x.strip()]


def has_applicable_check(shape: object) -> bool:
    """True when the shape constrains at least one thing (else scoring is vacuous)."""
    if not isinstance(shape, dict):
        return False
    min_len = min_length_of(shape)  # always validated, never short-circuited
    return bool(
        shape.get("produces_code")
        or min_len > 0
        or nonempty(shape, "must_contain")
        or nonempty(shape, "must_not_contain")
        or nonempty(shape, "required_sections")
        or nonempty(shape, "json_schema_keys")
    )
