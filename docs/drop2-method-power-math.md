# Drop 2 method kit -- paired analysis and power math

This is the core of the method kit: the exact recipe used to turn raw
per-fixture rows into the pass-rate delta and confidence interval you'd
report for a thinking field-present/field-absent (or any other) A-B
contrast, plus the power math to tell you, before you run anything, how
many fixtures and rounds you need to resolve an effect of a given size.
Every number below traces to
[`results/drop2-thinking-onoff-reference.csv`](../results/drop2-thinking-onoff-reference.csv);
none of it is invented for this document.

## Why row-level statistics are the wrong tool

Your rows are not independent draws. Every fixture belongs to a
`base_task_id` (a base coding task, rendered in three format variants --
see [`fixtures/README.md`](../fixtures/README.md)), and a model's
performance on the three variants of the same base task is correlated --
they share the same underlying task and the same solution. Treating a
model's 30 rows in `drop2-thinking-onoff-reference.csv` as 30 independent
Bernoulli trials overstates your precision, because you don't actually
have 30 independent pieces of evidence about whether thinking changes the
pass rate; you have as many independent pieces of evidence as you have
distinct base tasks -- 10, in this file.

## The recipe

1. **If you ran more than one round per fixture, collapse rounds to one
   number per fixture first.** For each `(model, fixture_id)`, compute
   the pass rate across all rounds you ran for it -- 2 of 3 rounds
   passing is `0.667`, not `1.0` or `0.0` -- *before* pairing. Aggregate
   by `(model, fixture_id)`, not by `(model, fixture_id, round)`: pairing
   on individual rounds treats every round as its own cluster-eligible
   observation, which silently over-weights any fixture you happened to
   run more rounds on if your round count isn't perfectly uniform, and it
   makes `k` in step 4 ambiguous -- base tasks, or base-task-rounds?
   Aggregating to one pass-rate number per fixture first keeps `k`
   unambiguously equal to the number of distinct base tasks no matter how
   many rounds you ran, and keeps every base task's contribution to the
   eventual cluster mean equally weighted. (This drop's own worked
   example ran one round per arm, so this step is a no-op for it --
   `present_pass`/`absent_pass` below are already single 0/1 values --
   but define it before you run more than one round.)
2. **Pair, don't pool.** For each `fixture_id` present in both arms,
   compute the per-fixture difference: `present_pass - absent_pass`,
   using the (possibly rounds-collapsed, per step 1) pass rate on each
   side.
3. **Cluster on `base_task_id`.** Average the per-fixture differences
   within each base task (its `format_variant` triplet) into one cluster
   mean. A base task with 3 format variants collapses to 1 number.
4. **Take the mean and standard error of the cluster means**, not of the
   raw rows. If you have `k` clusters with per-cluster mean difference
   `d_i`:
   - `mean = average(d_i)` across all `k` clusters
   - `se = stdev(d_i) / sqrt(k)` (sample standard deviation of the cluster
     means, divided by the square root of the cluster count)
5. **Build the interval with Student's t, not a normal approximation.**
   With `k` clusters, degrees of freedom `df = k - 1`. The 95% interval is
   `mean +/- t(0.975, df) * se`. Use `t`, not `z`, because you're doing
   inference on a small number of cluster means (tens, not thousands), and
   `t` is wider at small `df` to account for that.
6. **Report `k` (the cluster count) alongside every number.** A delta and
   an interval without the cluster count behind them cannot be checked or
   trusted.

This is the same convention -- paired-per-fixture, clustered-on-base-task,
Student-t on cluster means -- used throughout this drop's own analysis.

### Worked numbers, this drop's own run

Applying the recipe above to `drop2-thinking-onoff-reference.csv`, for
**four of the five metered models in this panel** (`opus`, `haiku`,
`opus-5`, `sonnet` -- see `docs/drop2-run-conditions.md` for what
field-present/field-absent means for each): `k = 10` clusters, `df = 9`.
Every one of these four models goes 30/30 in both arms on all 10 base
tasks, so every one of the 10 cluster means is exactly `0.0` for each of
them:

- `mean = 0.0`
- `stdev(d_i) = 0.0` across all 10 clusters -> `se = 0.0`
- **No interval is computable.** `t(0.975, 9) * se` and every other
  quantity below that multiplies by `se` evaluates to exactly `0`,
  regardless of the t-quantile, because there is no cluster-to-cluster
  variance in this sample to build an interval from.

**The fifth metered model, `fable`, does not saturate, and its numbers
are not zero.** Applying the identical recipe: `k = 10` clusters,
`df = 9`, `mean = -0.0333` (-3.33 percentage points), `stdev(d_i) =
0.1892` across the 10 clusters, `se = 0.0598`. This time `se` is not
zero, so the interval is computable: `t(0.975, 9) = 2.262157`, `ci95 =
mean +/- t*se = [-0.1687, +0.1020]` -> **[-16.9, +10.2] points**,
`t(9) = mean / se = -0.557`, `p = 0.591`. Not a significant result, but a
*real* one, in the sense that matters here: this is what the recipe
produces when the pilot isn't degenerate. Run the recipe yourself against
this model's rows to check both this and the four-model result above.

Two categorically different outcomes came out of the identical procedure
applied to six values of the `model` column in the same 360-row file.
That is the entire point of the next section.

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

This is where this drop's own sample becomes the lesson rather than a
sizing example -- and the lesson is per-model, not per-file, because this
one file contains both kinds of pilot.

**For `opus`, `haiku`, `opus-5`, and `sonnet`**, `se = 0.0` (previous
section), and you cannot plug that pilot into the power-sizing procedure
below at all. Try it and see why -- `s = se_pilot * sqrt(k_pilot) = 0.0 *
sqrt(10) = 0.0`, so every candidate `k` you try in step 4 below still
gives `se_candidate = 0.0 / sqrt(k) = 0.0`, and `(t(0.975, k-1) +
t(0.80, k-1)) x 0.0 = 0` no matter how large or small `k` is. Read
literally, that says this design could detect an effect of size zero at
any sample size -- which is nonsense, and the nonsense is the diagnostic.
A zero-variance pilot has not measured "no effect is detectable here even
at scale"; it has measured "these 10 base tasks, at this difficulty,
produced no cluster where the outcome ever moved between arms for this
model." That is a property of the task set for that model (each of these
four passed all 30 fixtures in both arms, on every base task), not a
property of the effect you're trying to size for.

**For `fable`, the same file gives you a real `se` to size from**:
`s = se_pilot * sqrt(k_pilot) = 0.059835 * sqrt(10) = 0.189215` -- the
cluster standard deviation recovered in the previous section, which is
exactly the number the recipe computed directly there (shown here at
higher precision than the `se = 0.0598` in that section so the
multiplication reproduces at the printed digits). Plugging that
into step 4 below for a candidate `k` produces a real, nonzero sizing
answer, unlike the other four models' pilots. The difference between the
two outcomes isn't the fixtures or the recipe -- it's whether the model's
outcomes moved at all across arms and clusters, which is not something
you can tell in advance of running the pilot.

**The honest lesson from this file: compute your own cluster variance per
model before concluding anything about a sample's power.** A pilot at or
near the ceiling (models passing nearly everything, in both arms) cannot
produce the variance the sizing formula needs, and no amount of
additional same-difficulty base tasks fixes that for a saturated model --
`s` stays at or near zero for it specifically, even in a file where
another model's `s` is very much not zero. Before you trust any `k` this
procedure recommends for a given model, check that model's own pilot
outcomes aren't clustered at 0% or 100% pass rate. If they are for that
model, either add base tasks difficult enough to produce a mixed
pass/fail outcome for it, or -- if refusals or another mechanism are
already producing real variance for it, the way they do for `fable` here
-- size directly from that model's own recovered `s`, per model, not from
a single file-wide assumption about whether your task set has "enough"
variance.

### Sizing your own run

To answer "how many fixtures x rounds at what difficulty do I need to
resolve X points" for your own panel and your own task set:

1. Run a pilot (even a small one, `k_pilot` in the low single digits) to
   get a clustered `se_pilot` for your outcome metric on your task set,
   per steps 1-4 of the recipe above.
2. Check where your pilot's outcomes sit. If most cells are near 0% or
   100%, your pilot's cluster-to-cluster variance is likely near a floor
   for that task set -- harder tasks, not more of the same ones, will
   move it more than adding clusters will.
3. **Recover the underlying cluster standard deviation before you vary
   `k`.** `se_pilot` already has your pilot's `k_pilot` baked into it
   (`se = sd / sqrt(k)`), so plugging `se_pilot` straight into a formula
   for a *different* candidate `k` only moves the t-quantile -- it can't
   show you the benefit of running more base tasks, because the `se`
   itself never changes. Undo the division first:
   `s = se_pilot * sqrt(k_pilot)`. `s` is your estimate of the
   fixture-to-fixture (cluster-to-cluster) standard deviation itself,
   independent of how many clusters you happened to pilot with.
4. For each candidate `k` you're considering, recompute the standard
   error at that `k`: `se_candidate = s / sqrt(k)`. Plug that -- not
   `se_pilot` -- into `(t(0.975, k-1) + t(0.80, k-1)) x se_candidate` and
   see whether the result is smaller than the effect size you actually
   care about. Increasing `k` now visibly shrinks both the `se_candidate`
   term and the t-quantile, which is the whole point of running more base
   tasks. If it's still not small enough, also consider more rounds per
   base task (tightens each fixture's own pass-rate estimate before
   pairing, per recipe step 1, which can shrink `s` itself) and recompute.
5. **Caveat: `s` is only as representative as your pilot.** It's an
   estimate from `k_pilot` clusters on your pilot's specific task mix and
   difficulty. If the base tasks you add at a larger `k` are harder,
   easier, or otherwise different in kind from your pilot's, the true
   cluster-to-cluster variance at that new `k` will differ from `s`, and
   this sizing will be optimistic or pessimistic accordingly -- it is a
   planning estimate, not a guarantee.
6. Re-run the pilot math after your first real battery -- `s` is an
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
