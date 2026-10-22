"""The one definition of an applicable check in a fixture's expected_shape.

Imported by the scorer (tools/score_completion.py) and by the fixture stamp
check (governance/check_fixture_stamps.py) so the two can never disagree.
"""

from __future__ import annotations


def min_length_of(shape: dict) -> int:
    """The shape's min_length as an int; ValueError when it is not a number."""
    try:
        return int(shape.get("min_length") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"min_length {shape.get('min_length')!r} is not an integer"
        ) from exc


def has_applicable_check(shape: object) -> bool:
    """True when the shape constrains at least one thing (else scoring is vacuous)."""
    if not isinstance(shape, dict):
        return False
    return bool(
        shape.get("produces_code")
        or min_length_of(shape) > 0
        or shape.get("must_contain")
        or shape.get("must_not_contain")
        or shape.get("required_sections")
        or shape.get("json_schema_keys")
    )
