# Running the battery

This document explains how to run the `fixtures/` battery against any
model or coding agent, and points to one worked example (our own
`bpsai-pair` CLI) so the instructions aren't purely abstract. Nothing
below requires that tool -- the fixture files are plain JSON and the
protocol is provider-agnostic.

## The fixture contract

Every file under `fixtures/<task_type>/` is a single JSON object:

| Field | Meaning |
|---|---|
| `id` | Unique fixture id, `<base_task_id>--<suffix>`. |
| `system_prompt` | The instruction to give the agent as its system/developer message. |
| `input_prompt` | The task itself -- give this as the user message. |
| `task_type` | `bugfix` \| `feature` \| `refactor` \| `chore`. |
| `difficulty` | `easy` \| `medium` \| `hard` \| `hard-plus`. |
| `expected_shape` | Machine-checkable acceptance criteria (see below). |
| `metadata` | Provenance + matched-pairs attribution (`base_task_id`, `format_variant`, `format_axes`). |

## Protocol

For each fixture:

1. Send `system_prompt` as the system message and `input_prompt` as the
   user message to the agent under test, in a fresh/stateless
   conversation (no prior turns, no other fixtures in context).
2. Capture the raw completion.
3. Score it against `expected_shape`:
   - `produces_code` (bool) -- the completion contains at least one code
     block / looks like source, not a refusal or pure prose.
   - `min_length` -- completion length (characters) is at least this.
   - `must_contain` -- every listed substring/identifier appears verbatim
     in the completion.
   - `must_not_contain` -- none of the listed substrings appear.
   - `required_sections` -- when non-empty, each named section/heading
     must be present.
   - `json_schema_keys` -- when non-empty, the completion (or its JSON
     payload) must include these keys.
4. Classify the outcome as `pass` (all checks satisfied), `partial` (some
   satisfied), `fail` (checks run, none/most fail), or `refused` (the
   agent declined, or returned an empty/near-zero-token completion).

This is intentionally a simple substring/shape check, not an LLM judge --
it is meant to be reproducible without another model in the loop. Bring
your own judge/grader on top if you want a richer score; report both if
you do.

## One worked example: `bpsai-pair`

Our own CLI, `bpsai-pair`, ships a runner that implements the protocol
above end to end, if you'd rather not write your own harness. It bundles
its own copy of this same fixture set internally (kept in sync with
`fixtures/` here), so the invocation doesn't take a path argument:

```bash
pip install bpsai-pair
bpsai-pair benchmark matrix-run --family fixture-set-v3
bpsai-pair benchmark matrix-run --family fixture-set-v3 --include-paid  # add paid providers
```

This dispatches all 30 fixtures against the configured model panel and
writes a `matrix.json`/`matrix.csv` with one row per `(fixture, model)`
pair, scored per the protocol above.

This is one option among many, provided for convenience -- the fixture
files and scoring rules above are the actual contract, and work against
any harness that can send a system/user prompt pair and inspect the
completion.

## Repetitions are required -- N=1 gives no usable rate

A rate computed from a single dispatch of a fixture is either 0% or 100%
for that cell and carries no statistical weight. Run the battery **N >=
3 times** per agent under test before computing any pass-rate or
refusal-rate, and report `n` (the row count) alongside every rate you
publish.

## Matched-pairs contrasts

See [`fixtures/README.md`](../fixtures/README.md#the-matched-pairs-invariant-critical)
for the full methodology. In short: only two of the three pairwise
`format_variant` contrasts isolate a single axis (structure or framing)
-- the third confounds both and must never be used to attribute a rate
delta to either axis. Always compare within a fixed
`(base_task_id, model_id)` pair.
