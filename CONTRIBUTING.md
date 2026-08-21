# Contributing

This repo accepts two kinds of contribution: **result submissions** (you
ran the battery against a model/agent and want to share what happened)
and **new fixtures** (you want to add a base task or format variant).
Both go through a normal PR; both require the provenance stamp below.

## The provenance stamp

Every fixture file's `metadata` must carry:

```json
"public_release": true,
"provenance": "original-authored"
```

`provenance: "original-authored"` is a claim -- it means the task
scenario, the embedded module (if any), and the prompt text are your own
original writing, not derived from or copied from any other codebase or
dataset. CI (`governance/check_fixture_stamps.py`) fails any fixture
file missing these two keys, and the denylist scanner
(`governance/check_denylist.py`) fails any file (fixture or otherwise)
matching an entry in `governance/denylist.txt`. Both must be green before
a PR can merge.

If your fixture is inspired by a real bug or a real system you've worked
on, that's fine and common -- rewrite it as an original, generic scenario
(the existing 30 fixtures in `fixtures/` are all written this way; see
`fixtures/README.md` for the format) rather than copying identifiers,
comments, or structure from the source.

## Submitting results

Add your rows to `results/reference-results.csv` (see that file's header
for the exact columns) or open a PR adding a new file under `results/` if
you'd rather keep your submission separate. Only these columns are
accepted: `model_id`, `fixture_id`, `outcome`, `format_variant`,
`base_task_id`. Do not include prompts beyond what's already in
`fixtures/`, and do not include telemetry, cost data, or infrastructure
detail from your own run environment.

Report `n` (how many times you ran each cell) in your PR description --
see [`docs/running-the-battery.md`](docs/running-the-battery.md) for why
a single run isn't a usable rate on its own.

## New fixtures

- One base task, rendered as the `short` / `embedded-neutral` /
  `embedded-production` triplet described in `fixtures/README.md`, with
  byte-identical `expected_shape` and `system_prompt` across all three.
- Original-authored business logic (see the provenance stamp section
  above) -- no real company names, no real infrastructure, no content
  derived from another codebase.
- File under `fixtures/<task_type>/`, id `<base_task_id>--<suffix>`.

## What we will not merge

Anything that trips the denylist scanner, anything without the
provenance stamp, and anything that looks like it was lifted from a real
production system rather than written as a generic scenario for this
purpose.
