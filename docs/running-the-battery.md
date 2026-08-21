# Running the battery

This document explains how to run the `fixtures/` battery against any
model or coding agent. The fixture files are plain JSON and the protocol
below is provider-agnostic -- there is no required tool or SDK.

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

## Implementing the protocol yourself

The fixture contract and protocol above are the complete, provider-
agnostic spec -- there's no separate tool to install. Implementing the
dispatch loop against any HTTP client or agent SDK is about a page of
code:

```python
import glob
import json

MODEL_ID = "your-model-id"  # whatever your harness is dispatching this run

results = []
for path in glob.glob("fixtures/*/*.json"):
    fixture = json.load(open(path))

    # Fresh/stateless call -- no prior turns, no other fixtures in context.
    completion = your_agent_client.send(
        system=fixture["system_prompt"],
        user=fixture["input_prompt"],
    )

    # Score against expected_shape and classify per "Protocol" above
    # (produces_code / min_length / must_contain / must_not_contain /
    # required_sections / json_schema_keys -> pass/partial/fail/refused).
    outcome = score(completion, fixture["expected_shape"])

    results.append({
        "model_id": MODEL_ID,
        "fixture_id": fixture["id"],
        "base_task_id": fixture["metadata"]["base_task_id"],
        "format_variant": fixture["metadata"]["format_variant"],
        "outcome": outcome,
    })

# Repeat this entire loop N >= 3 times before computing any rate --
# see "Repetitions are required" below. Write each round's results
# somewhere separate (don't overwrite the last round) and concatenate
# before grouping by cell.
```

That's the whole loop: read a fixture, send it as a fresh system/user
turn, score the completion against `expected_shape`, record the five
columns above. Nothing here depends on a particular vendor SDK or CLI --
swap `your_agent_client.send` for whatever call your harness makes (an
HTTP POST, an SDK method, a CLI subprocess) and the rest of this document
applies unchanged.

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
