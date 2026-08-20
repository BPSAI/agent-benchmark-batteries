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

## `drop2-thinking-onoff-reference.csv` -- what these 360 rows are, and are not

This file is a maintainer-published worked example, not a community
submission -- that's why it carries more columns than the rule above:
`fixture_id`, `model`, `arm` (`thinking` | `bare`, i.e. the field
present/absent), `round` (always `1` here), `outcome`, `tokens_in`,
`tokens_out`, `tokens_reasoning`, `cost_usd`. No prompt or response text,
no fixture outside this repo's 30, no cost/token data from anything but
these rows.

**What it is.** All 30 fixtures in this repo, dispatched once per arm
against six models (five metered, one free local comparator), thinking
field present vs. absent, same day, one round per arm. 360 rows
(30 fixtures x 6 models x 2 arms). It is the public, reproducible worked
example for the thinking-on/off A-B method described in
[`docs/drop2-run-conditions.md`](../docs/drop2-run-conditions.md) and
[`docs/drop2-method-power-math.md`](../docs/drop2-method-power-math.md).

**What it is not.** It is not the source of a published finding. The
essay behind this drop reports a paired pass-rate delta of -1.1
percentage points (95% CI [-3.4, +1.2]) between thinking-on and
thinking-off, on two of the five metered models. That number comes from
a 30-base-task corpus run under the same protocol, of which only these
10 base tasks (this repo's `fixtures/`) are public -- the other 20 are
production-shaped fixtures that stay private by the same governance rule
that keeps this repo fixture-only (see the root README's "Governance"
section). Recomputed on exactly the rows in this file, using the same
paired-per-fixture, clustered-on-base-task method (see
`docs/drop2-method-power-math.md`), the two models that showed a delta on
the full corpus (call them "opus" and "haiku" in this file's `model`
column) go 30/30 in both arms here -- a flat delta of exactly 0.0
percentage points, zero cluster variance, no interval computable. That is
expected, not a discrepancy: 10 base tasks is a third of the corpus the
published number needed to find a two-fixture effect, and both of the
fixtures that produced that effect are among the 20 that are not public.
This file verifies the harness runs end to end and gives you real rows to
practice the analysis on. It does not carry, and was never claimed to
carry, the published finding.

**Cost reproduces fine at this scale**, because it needs no contrast to
be real -- it's a direct sum over rows, not a difference-of-proportions
with a ceiling problem. Paid-model rows only (30 fixtures x 5 metered
models x 2 arms = 300 of the 360 rows): thinking arm totaled $5.91, bare
arm $5.56. The two models the essay's cost claim is about: "opus" cost
$1.24 with thinking on vs. $1.08 off (+14.6% on this subset); "haiku"
cost $0.48 on vs. $0.34 off (+42.8%). Those percentages will not match
the essay's +13.0%/+49.6% exactly -- this subset is 30 fixtures per arm,
a third of the 90-fixture corpus the published number was computed on --
but they land in the same direction and the same rough magnitude, which
is what a worked example is for.
