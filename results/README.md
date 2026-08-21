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
submission (see "A note on repetitions," below, for the one rule that
doesn't carry over from that) -- that's why it carries more columns than
the rule above: `fixture_id`, `model`, `arm` (`thinking` | `bare`, i.e.
the field present/absent -- see
[`docs/drop2-run-conditions.md`](../docs/drop2-run-conditions.md) for why
"absent" is not the same as "off" on every model), `round` (always `1`
here), `outcome`, `tokens_in`, `tokens_out`, `tokens_reasoning`,
`cost_usd`. No prompt or response text, no fixture outside this repo's
30, no cost/token data from anything but these rows.

`tokens_reasoning` never exceeds `tokens_out` on any of the 360 rows,
which is consistent with reasoning tokens being counted *inside*
`tokens_out`, not billed as a separate line item -- refitting `cost_usd`
per model as a function of `tokens_in` and `tokens_out` alone (no
`tokens_reasoning` term) reproduces every row's cost exactly, zero
residual. So `tokens_reasoning` carries no cost coefficient of its own in
this data; budget from `tokens_out`, and treat `tokens_reasoning` as
diagnostic (it's what makes the field-present/field-absent contrast in
`docs/drop2-run-conditions.md` checkable), not a second cost line.

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
`docs/drop2-method-power-math.md`: four of the five metered models in
this panel (`opus`, `haiku`, `opus-5`, `sonnet`) go 30/30 in both arms on
these 30 fixtures -- a flat delta of exactly 0.0 percentage points per
model, zero cluster variance, no interval computable. That is not this
file telling you thinking has no effect on anything; a zero-variance
result on this repo's 10-base-task set (2 easy, 3 medium, 3 hard, 2
hard-plus by design -- see `fixtures/README.md`) is a sample that
saturated for those four models, not a sample that measured -- see "This
drop's own numbers, as a worked example" in
`docs/drop2-method-power-math.md` for what a zero-variance pilot does and
does not let you conclude, and what to do about it (harder fixtures, not
more of the same ones).

**The fifth metered model, `fable`, is this file's own counterexample.**
Its pass rate is not saturated (13/30 field-present, 14/30 field-absent),
its refusals (33 of the file's 360 rows, all of them `fable`'s) are the
reason why, and its clustered pass-delta has real, computable variance:
`k = 10` clusters, mean -3.33 percentage points, cluster sd 18.92 points,
`se` 5.98 points, 95% CI [-16.9, +10.2] points, `t(9) = -0.56`,
`p = 0.59` -- not significant, but not degenerate either, unlike the four
models above. See `docs/drop2-run-conditions.md` for what drives it
(a real per-row separation in `fable`'s reasoning-token counts between
arms, and a refusal pattern that tracks `format_variant`). The lesson
this file actually supports: compute your own cluster variance per model
before concluding anything about a sample's power -- this one file
contains both a saturated case and a non-saturated one, and the saturated
majority doesn't tell you what the fifth model will do.

**Cost reproduces fine at this scale**, because it needs no contrast to
be real -- it's a direct sum over rows, not a difference-of-proportions
with a ceiling problem. Paid-model rows only (30 fixtures x 5 metered
models x 2 arms = 300 of the 360 rows): field-present arm totaled $5.65,
field-absent arm $5.30. The two models where field-absent means off:
`opus` cost $1.24 field-present vs. $1.08 field-absent (+14.6%); `haiku`
cost $0.48 vs. $0.34 (+42.8%). Recompute these yourself from the
`cost_usd` column to check them.

**Prices used.** `cost_usd` is computed at each model's published
per-million-token input/output rate, in effect when this reference run
was dispatched: `opus` $5/$25, `haiku` $1/$5, `opus-5` $5/$25, `sonnet`
$2/$10, `fable` $10/$50 (list price -- a cross-check of this rate
against actual billing is not complete, so this one figure is stated as
list price only, nothing more).

**A note on repetitions.** The "Contributing rows" rule above (N >= 3 per
cell, no publishing a rate from a single pass) is a contributor-submission
rule, and this file doesn't follow it -- it's one round per arm (n=1 per
`(fixture_id, model, arm)` cell), published by the maintainers as a
worked example of the harness and the analysis method, not as a rate
claim about any model. That's an intentional asymmetry, not an oversight:
the community rule exists to keep aggregated rates trustworthy, and this
file explicitly isn't one (see the "What this sample's own numbers show"
and "counterexample" sections above for what single-round data can and
can't tell you here).
