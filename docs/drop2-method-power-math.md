# Drop 2 method kit -- paired analysis and power math

This is the core of the method kit: the exact recipe used to turn raw
per-fixture rows into the pass-rate delta and confidence interval you'd
report for a thinking on/off (or any other) A-B contrast, plus the power
math to tell you, before you run anything, how many fixtures and rounds
you need to resolve an effect of a given size. Every number below traces
to this drop's audited fixtures sheet; none of it is invented for this
document.

## Why row-level statistics are the wrong tool

Your rows are not independent draws. Every fixture belongs to a
`base_task_id` (a base coding task, rendered in three format variants --
see [`fixtures/README.md`](../fixtures/README.md)), and a model's
performance on the three variants of the same base task is correlated --
they share the same underlying task and the same solution. Treating 90
rows as 90 independent Bernoulli trials overstates your precision,
because you don't actually have 90 independent pieces of evidence about
whether thinking changes the pass rate; you have as many independent
pieces of evidence as you have distinct base tasks.

## The recipe

1. **Pair, don't pool.** For each `fixture_id` present in both arms,
   compute the per-fixture difference: `on_pass - off_pass`, where each
   side is `1.0` if `outcome == "pass"` and `0.0` otherwise.
2. **Cluster on `base_task_id`.** Average the per-fixture differences
   within each base task (its `format_variant` triplet) into one cluster
   mean. A base task with 3 format variants collapses to 1 number.
3. **Take the mean and standard error of the cluster means**, not of the
   raw rows. If you have `k` clusters with per-cluster mean difference
   `d_i`:
   - `mean = average(d_i)` across all `k` clusters
   - `se = stdev(d_i) / sqrt(k)` (sample standard deviation of the cluster
     means, divided by the square root of the cluster count)
4. **Build the interval with Student's t, not a normal approximation.**
   With `k` clusters, degrees of freedom `df = k - 1`. The 95% interval is
   `mean +/- t(0.975, df) * se`. Use `t`, not `z`, because you're doing
   inference on a small number of cluster means (tens, not thousands), and
   `t` is wider at small `df` to account for that.
5. **Report `k` (the cluster count) alongside every number.** A delta and
   an interval without the cluster count behind them cannot be checked or
   trusted.

This is the same convention -- paired-per-fixture, clustered-on-base-task,
Student-t on cluster means -- used throughout this drop's own analysis.

### Worked numbers, this drop's own run

The published essay's headline ran on a 30-base-task corpus (90 fixtures
per arm per model: 30 base tasks x 3 format variants), of which the 10
base tasks in this repo's `fixtures/` are a subset. On that 30-cluster
corpus, two models each lost exactly one fixture between arms:

- `mean = -0.011111` (-1.1111 percentage points)
- `se = 0.011111`
- `df = 29`, `t(0.975, 29) = 2.045230`
- `ci95 = mean +/- t*se = [-0.033836, +0.011614]` -> **[-3.4, +1.2] points**
- `t(29) = mean / se = -1.000`, `p = 0.326`

That -1.1 point, [-3.4, +1.2] result is **not reproducible from this
repo's public rows** -- see `results/README.md` for why (20 of the 30
base tasks that produced it are not public, including both fixtures that
carried the whole effect). Recomputed on exactly the 10 public base tasks
in `drop2-thinking-onoff-reference.csv`, using the identical recipe above
(`k = 10`, `df = 9`), the same two models go 30/30 in both arms: `mean =
0.0`, zero cluster variance, no interval computable. Run the recipe
yourself against that file to check both of these numbers.

## The power question: how many fixtures do you need?

Before you run a battery, you can ask what the smallest effect is that
your design could actually resolve, given how much your outcome varies
across base tasks. Two thresholds matter:

- **The smallest effect that would reach significance at all**, given the
  standard error you expect: `t(0.975, df) * se`.
- **The smallest effect you'd reliably detect** (80% power is a common
  bar), which needs a bigger margin because you also need to clear noise
  on the *true* effect side, not just avoid a false positive:
  `(t(0.975, df) + t(0.80, df)) * se`.

Both scale directly with your clustered standard error and with the
t-quantiles for your cluster count -- more clusters shrinks `se` (bigger
`k` in the denominator) *and* shrinks the t-multiplier (fatter-tailed at
low `df`), so both terms move in your favor as you add base tasks. More
rounds per fixture, at a fixed number of base tasks, shrinks the noise
that goes into each cluster's mean before it ever reaches the `se`
formula -- it does not raise `k` (clusters are base tasks, not rows), but
it does tighten each cluster's own estimate if a base task's outcome is
noisy round to round.

### This drop's own numbers, as a worked example

At `k = 30` clusters (`df = 29`), the observed clustered `se` was `0.011111`
(1.1111 points) -- itself a function of how close to the ceiling the
outcomes sat (two near-perfect models have almost no room to show
variance, so the observed `se` here is close to a floor, not a typical
value):

- smallest effect that could reach significance: `t(0.975, 29) x se =
  2.045230 x 1.1111 = 2.27 points` (the essay rounds this to "about 2.3").
- smallest effect resolvable at 80% power: `(t(0.975, 29) + t(0.80, 29))
  x se = (2.045230 + 0.85377) x 1.1111 = 3.22 points` (the essay rounds
  this to "about 3.2").

A second, harder-tier run in the same battery, at `k = 15` clusters
(`df = 14`, `t(0.975, 14) = 2.145`), had a *worse* resolution -- CI
half-width about 4.8 points, roughly double the 30-cluster run -- because
halving the cluster count outweighed moving the outcomes off the ceiling.
That is the general lesson, not a coincidence of this particular run:
adding base tasks is not automatically enough if your task set is
saturated (near 0% or 100% for the models you're testing) -- a design
near the ceiling has very little cluster-to-cluster variance to detect a
real effect against, and no number of additional clusters fixes a task
set that both models already pass or fail near-uniformly. If your pilot
run shows outcomes clustered near 0% or 100%, budget for harder tasks
before budgeting for more of them.

### Sizing your own run

To answer "how many fixtures x rounds at what difficulty do I need to
resolve X points" for your own panel and your own task set:

1. Run a pilot (even a small one, `k` in the low single digits) to get a
   rough clustered `se` for your outcome metric on your task set.
2. Check where your pilot's outcomes sit. If most cells are near 0% or
   100%, that `se` is likely near a floor for that task set -- harder
   tasks, not more of the same ones, will move it more than adding
   clusters will.
3. Plug your pilot `se` and a candidate `k` into
   `(t(0.975, k-1) + t(0.80, k-1)) x se` and see whether the result is
   smaller than the effect size you actually care about. If not, increase
   `k` (more base tasks) and/or increase rounds per base task (tightens
   each cluster's own mean, which lowers the `se` that feeds this whole
   calculation) and recompute.
4. Re-run the pilot math after your first real battery -- `se` is an
   estimate, and a bad pilot estimate (too few clusters, or an
   unrepresentative task mix) will mislead the sizing above just as
   easily as it misleads the eventual result.

## Extending the fixture set

The clustering above only works if your added tasks follow the same
matched-pairs pattern this repo's fixtures use: for a new base task, write
the underlying scenario and acceptance checks **once**, then render it
into your format variants so `expected_shape` and the core instruction
stay identical across variants and only the framing/structure you're
testing changes. See
["The matched-pairs invariant"](../fixtures/README.md#the-matched-pairs-invariant-critical)
for the full construction rule, and
["The two format axes"](../fixtures/README.md#the-two-format-axes) for how
this repo's own variants (`short` / `embedded-neutral` /
`embedded-production`) were built as one example of that pattern -- your
own axes (a different prompt framing, a different tool-call shape,
whatever your workflow actually varies) can follow the same construction
without reusing these particular axes. Without that invariant, a
format-variant delta is confounded with a task-identity delta and neither
this analysis nor the power math above means what it claims to.
