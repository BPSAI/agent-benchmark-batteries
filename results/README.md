# Reference results

`reference-results.csv` holds raw, per-fixture, per-model outcome rows --
exactly the columns below, nothing else:

| Column | Meaning |
|---|---|
| `model_id` | The model/agent identifier that produced the completion. |
| `fixture_id` | `<base_task_id>--<suffix>`, matches a file under `fixtures/`. |
| `outcome` | `pass` \| `partial` \| `fail` \| `refused`. |
| `format_variant` | `short` \| `embedded-neutral` \| `embedded-production`. |
| `base_task_id` | The matched-pairs triplet key (see `fixtures/README.md`). |

## What's in the current file

30 rows, one full pass over all 30 fixtures against a single local model
(`ollama-devstral`), run once (**n=1 per fixture**). This is a smoke run
demonstrating the protocol end to end, not a rate -- see
[`docs/running-the-battery.md`](../docs/running-the-battery.md#repetitions-are-required----n1-gives-no-usable-rate)
for why a single run can't be reported as a pass-rate or refusal-rate.
No paid/frontier models are represented yet.

Do not compute or publish a per-cell rate from this file until you (or a
combined set of PRs) have accumulated N >= 3 rows for a given
`(base_task_id, format_variant, model_id)` cell -- then group by that key
and compute the fraction yourself; this repo does not ship pre-aggregated
rates, only the raw rows.

## Contributing rows

See [`CONTRIBUTING.md`](../CONTRIBUTING.md#submitting-results). Only the
five columns above -- no prompts beyond what's already in `fixtures/`, no
internal telemetry or cost data from your run environment.

## `drop2-thinking-onoff-reference.csv` -- what these 360 rows are

This file is a maintainer-published worked example, not a community
submission -- that's why it carries more columns than the rule above:
`fixture_id`, `model`, `arm` (`thinking` | `bare`, i.e. the field
present/absent -- see
[`docs/drop2-run-conditions.md`](../docs/drop2-run-conditions.md) for why
"absent" is not the same as "off" on every model), `round` (always `1`
here), `outcome`, `tokens_in`, `tokens_out`, `tokens_reasoning`,
`cost_usd`. No prompt or response text, no fixture outside this repo's
30, no cost/token data from anything but these rows.

**What it is.** All 30 fixtures in this repo, dispatched once per arm
against six models (five metered, one free local comparator), the
thinking field present vs. absent, same day, one round per arm. 360 rows
(30 fixtures x 6 models x 2 arms). It is the reference dataset for the
method kit described in
[`docs/drop2-run-conditions.md`](../docs/drop2-run-conditions.md) (how
the two arms were configured, and what "field absent" actually means per
model) and
[`docs/drop2-method-power-math.md`](../docs/drop2-method-power-math.md)
(the paired/clustered analysis recipe) -- published so you can verify
your own harness reproduces the pipeline (dispatch, score, pair, cluster)
before pointing it at your own tasks.

**What this sample's own numbers show.** Recomputed straight from this
file, using the paired-per-fixture, clustered-on-base-task method in
`docs/drop2-method-power-math.md`: the two models where field-absent
means off in this panel (`opus`, `haiku`) go 30/30 in both arms on these
30 fixtures -- a flat delta of exactly 0.0 percentage points, zero
cluster variance, no interval computable. That is not this file telling
you thinking has no effect on anything; a zero-variance result on a
10-base-task, mostly easy-to-medium sample is a sample that saturated,
not a sample that measured -- see "This drop's own numbers, as a worked
example" in `docs/drop2-method-power-math.md` for what a zero-variance
pilot does and does not let you conclude, and what to do about it
(harder fixtures, not more of the same ones).

**Cost reproduces fine at this scale**, because it needs no contrast to
be real -- it's a direct sum over rows, not a difference-of-proportions
with a ceiling problem. Paid-model rows only (30 fixtures x 5 metered
models x 2 arms = 300 of the 360 rows): field-present arm totaled $5.91,
field-absent arm $5.56. The two models where field-absent means off:
`opus` cost $1.24 field-present vs. $1.08 field-absent (+14.6%); `haiku`
cost $0.48 vs. $0.34 (+42.8%). Recompute these yourself from the
`cost_usd` column to check them.
