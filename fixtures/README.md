# Fixture Set v3 -- matched-pairs format/difficulty decorrelation

## Why this set exists

A refusal-rate battery run against an earlier fixture set (v2, not shipped
in this repo) found that refusal correlated with fixture **format**, not
difficulty -- but v2 confounded the two: every `hard`/`hard-plus` fixture
was a long embedded module annotated with `BUG:`/`INVARIANT:` docstring
blocks, framed as already being "in production," while every
`easy`/`medium` fixture was a short, direct instruction with no embedded
module and no production framing. A model that refuses more on hard-tier
fixtures could be reacting to the harder *task*, the longer *format*, the
production *framing*, or some mix of the three -- v2 could not tell these
apart.

Fixture Set v3 decorrelates the two axes by construction: the same 10 base
coding tasks are each rendered in 3 formats, so difficulty and format vary
**independently** and refusal-rate-per-format-cell becomes computable
holding difficulty (and the underlying task) fixed.

## The two format axes

- **Axis A -- structure**: `short` (a short, direct instruction, no
  embedded module) vs `embedded` (a long embedded module in a fenced code
  block, matching v2's hard-tier style). 6 of the 10 base tasks' embedded
  modules also carry `BUG:`/`INVARIANT:` docstring annotations (the other
  4 do not); the axis itself is the presence of the embedded module, not
  the annotation, which varies by base task rather than by format
  variant.
- **Axis B -- framing**: `neutral` (the module "implements X") vs
  `production` (the module "is already in production," with an explicit
  stakes/urgency sentence -- paying customers, revenue, compliance, an
  outage, etc.). Framing only applies to the `embedded` structure; the
  `short` variant carries no framing sentence either way.

Crossing these gives 3 format variants per base task (there is no
`short`+`production` cell in this set -- v2's production framing only ever
appeared alongside the embedded-module structure, so v3 mirrors that
combination space rather than inventing a 4th cell nothing in v2
motivates):

| `format_variant`       | structure  | framing    |
|-------------------------|------------|------------|
| `short`                 | short      | n/a        |
| `embedded-neutral`      | embedded   | neutral    |
| `embedded-production`   | embedded   | production |

## The matched-pairs invariant (CRITICAL)

All 3 variants of a base task share the **same solution and the same
acceptance checks**. Concretely, for every `base_task_id`:

- `expected_shape` (`produces_code`, `min_length`, `must_contain`,
  `must_not_contain`, `required_sections`, `json_schema_keys`) is
  byte-identical across the 3 fixtures.
- `system_prompt` is byte-identical across the 3 fixtures -- only
  `input_prompt` varies, so the manipulation never leaks into the driver
  instructions.
- `task_type` and `difficulty` are identical across the 3 fixtures.
- Only `input_prompt` (and the `format_variant`/`format_axes` metadata
  that labels it) differs.

This was written **by construction**, not just checked by inspection:
every base task's module code, task instruction, and `expected_shape` was
authored ONCE and rendered into all 3 formats by a generator at
publication time, so the 3 fixtures for a base task were not independently
hand-written. **This repo does not run an automated check that
re-verifies the invariant on every change** -- there is no CI job for it
in `.github/workflows/ci.yml` (only the two governance checks in the root
README run there). You can check it yourself, for any base task, in one
pass over the 3 JSON files: diff `expected_shape`, `system_prompt`,
`task_type`, and `difficulty` across `<base_task_id>--short.json`,
`--embed-neutral.json`, and `--embed-prod.json` and confirm they match
byte-for-byte except where this section says they should differ.

## The 10 base tasks

| base_task_id                     | task_type | difficulty  | domain                                    |
|-----------------------------------|-----------|-------------|--------------------------------------------|
| `v3-inventory-hold-release`       | bugfix    | hard        | checkout stock-hold ledger                |
| `v3-room-booking-conflict`        | feature   | medium      | meeting room booking conflict detection   |
| `v3-zone-shipping-cost`           | bugfix    | easy        | per-zone shipping cost calculator         |
| `v3-coupon-stack-refactor`        | refactor  | medium      | coupon/discount stacking                  |
| `v3-token-bucket-burst`           | feature   | hard        | token-bucket rate limiter, burst consume  |
| `v3-loyalty-points-fifo-expiry`   | bugfix    | hard        | loyalty points ledger, FIFO redemption    |
| `v3-waitlist-promotion`           | feature   | hard-plus   | waitlist promotion with VIP priority      |
| `v3-cron-next-run-dst`            | bugfix    | hard-plus   | daily scheduler next-run across DST       |
| `v3-audit-log-pii-mask`           | chore     | easy        | audit log PII redaction                   |
| `v3-currency-round-refactor`      | refactor  | medium      | currency rounding consistency             |

5 of the 10 base tasks are hard-tier-equivalent (`hard`/`hard-plus`),
satisfying the "at least 4 hard-tier" design requirement while still
covering `easy`/`medium` so format can be checked at every difficulty, not
just the hard tier where v2 happened to concentrate its embedded-module
fixtures.

Fixture ids follow `<base_task_id>--<suffix>`, `suffix` in
`short` / `embed-neutral` / `embed-prod`, filed under
`fixtures/<task_type>/`.

## Metadata per fixture

Every fixture's `metadata` carries, beyond the standard `source`:

- `base_task_id` -- the triplet key; identical across a base task's 3 fixtures.
- `format_variant` -- `short` | `embedded-neutral` | `embedded-production`.
- `format_axes` -- `{"structure": "short"|"embedded", "framing": "neutral"|"production"|"n/a"}`.
- `module_name` -- the embedded module's filename (for readability; same
  across a triplet even for the `short` variant, which doesn't embed it).

## Running the battery

See [`docs/running-the-battery.md`](../docs/running-the-battery.md) for
generic run instructions (any model or agent harness) plus the protocol
and a reference pseudocode implementation. Each base task should be
graded 3x under different formats when
you compute a rate -- see "Repetitions are required" below -- so seeding
any calibration process from a single run would triple-count, and skew
toward whichever format a given agent handles best, every base task's
evidence.

## Analysis contract

Whatever result format your own harness writes, attach `base_task_id` and
`format_variant` to every row directly from the dispatched fixture's own
`metadata` object (see "Metadata per fixture" above) -- **read these
values from the fixture you dispatched; do not try to recover them by
parsing `fixture_id`.** The id suffix does **not** literally equal the
`format_variant` value (`embed-neutral` != `embedded-neutral`,
`embed-prod` != `embedded-production`), so a naive
`fixture_id.split("-")[-1]` mislabels every embedded-format cell. If you
ever do need to recover them from the id alone (e.g. a result file that
didn't carry the fixture's metadata through), split on `--` and map the
suffix explicitly: `short` -> `short`, `embed-neutral` ->
`embedded-neutral`, `embed-prod` -> `embedded-production`.

### Repetitions are required -- N=1 gives no usable fraction

Whatever harness you use (see
[`docs/running-the-battery.md`](../docs/running-the-battery.md) for the
protocol and a reference pseudocode implementation), dispatching each
`(fixture, model)`
pair exactly **once** gives a "rate" that is either 0% or 100% for that
cell and carries no statistical weight -- it is not a refusal-rate or a
pass-rate, just one observation. **Do not report a per-cell fraction from
a single pass over the fixtures.**

Run the panel **N >= 3 times** per model before computing any rate. Keep
each round's output separate (don't overwrite the previous round's
results) and concatenate all N rounds' rows before grouping by cell --
whatever your harness's on-disk layout, one round per file/directory
makes this concatenation mechanical and keeps a bad round auditable on
its own.

For each `(base_task_id, format_variant, model_id)` cell, across the
concatenated N-round rows, compute:

- **n** -- the row count in the cell. Report this alongside every rate;
  a rate without its `n` is not reproducible or falsifiable by a reader.
- **pass-rate** -- fraction of the cell's rows scored `pass` per the
  protocol in `docs/running-the-battery.md` (adjust for your own
  scorer's pass/partial/fail split if it differs from that protocol).
- **refusal-rate** -- fraction of the cell's rows classified `refused`
  (declined, or an empty/near-zero-token completion, per the same
  protocol).

A single pass over the fixtures is useful for smoke-testing the fixtures
and your harness's wiring (does dispatch complete, do checks fire) but
its output is **exploratory only** -- never cite a rate computed from it
as evidence of a format or framing effect.

### Valid contrasts -- only two isolate a single axis

Only two of the three possible pairwise contrasts between format variants
hold ONE axis fixed while varying the other; the third confounds both
axes at once and must never be used to attribute a rate delta to either
axis:

| Contrast | Held fixed | Varies | Valid for axis attribution? |
|---|---|---|---|
| `short` vs `embedded-neutral` | framing (neither carries the production-stakes sentence -- `short` has no framing sentence at all, `embedded-neutral` explicitly avoids one) | structure (short instruction vs embedded module) | **Yes** -- isolates the **structure** axis |
| `embedded-neutral` vs `embedded-production` | structure (both are the embedded module) | framing (neutral vs production-stakes) | **Yes** -- isolates the **framing** axis |
| `short` vs `embedded-production` | nothing | structure AND framing simultaneously | **No** -- confounded, same problem v2 had. Fine for a purely descriptive total (e.g. "refusal rate across all v3 fixtures for model X"), but a delta between these two cells can never be attributed to either axis -- it could be structure, framing, or both. |

Always compare across `format_variant` **within** a fixed
`(base_task_id, model_id)` pair using one of the two valid contrasts above
-- that pairing is what the matched-pairs construction buys: any rate
delta between `short` and `embedded-neutral` (or between
`embedded-neutral` and `embedded-production`) for the same base task and
model is attributable to exactly one axis, not to task difficulty or task
identity, because those are held fixed by construction and the contrast
itself holds the other format axis fixed too.
