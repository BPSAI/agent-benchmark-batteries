# Within-run comparison -- comparing two or more models in one run

This is the Drop 3 method kit. It is about one question: when you put
two or more models side by side on the same battery, what has to be true
for the difference you see to belong to the models and not to the day you
ran them, the harness you ran them through, or the grader that scored
them. The method is model-agnostic. The arms that happened to run in the
worked example (Sonnet 5.5, Sonnet 5, Haiku 4.5 and GPT 6.1 Sol) are
there to show the method at work, and nothing on this page ranks them.

Read [`running-the-battery.md`](running-the-battery.md) first for the base
dispatch protocol and [`drop2-method-power-math.md`](drop2-method-power-math.md)
for the paired, clustered analysis recipe this page reuses.

## Sections

1. [What "within-run" means](#what-within-run-means)
2. [The four things that must be shared](#the-four-things-that-must-be-shared)
3. [The sibling control](#the-sibling-control)
4. [Repetitions](#repetitions)
5. [Reporting intervals, and when to claim direction only](#reporting-intervals-and-when-to-claim-direction-only)
6. [What invalidates a comparison](#what-invalidates-a-comparison)
7. [Worked example: what ran and what it can and cannot support](#worked-example-what-ran-and-what-it-can-and-cannot-support)
8. [Reproduce it against your own agents](#reproduce-it-against-your-own-agents)

## What "within-run" means

A within-run comparison dispatches every arm from one session, against one
battery, through one harness build, and scores every row with one grader.
Arms are interleaved by round: round 1 dispatches every arm, then round 2
dispatches every arm, and so on. The alternative, finishing all rounds of
one arm before starting the next, puts the arms on different clocks, and
any vendor-side change, rate limit, or load shift that lands in between is
now confounded with the model.

A cross-run comparison is not worthless. It is a different instrument with
a wider error you cannot see. If you only have rows from two separate runs,
say so in the same sentence as the number.

## The four things that must be shared

Write each one down in a run manifest before the first dispatch, and
reread it before you publish.

- **Same date.** All arms dispatched in one session. Record the date and
  the start time of each round. "Same week" is not same-date.
- **Same battery.** The same fixture files, byte for byte. Hash the
  fixture set (every file path and its bytes, path-sorted) and record the
  hash. A cut that drops a fixture for one arm only is a different battery.
- **Same harness pin.** The same dispatch code at one commit, with a clean
  working tree at every round. Record the commit and check it before each
  round, and refuse to dispatch if it moved.
- **Same grader.** One scorer, identified by content (a hash of the scorer
  and of its checks), not by a version string. If you rescore, rescore every
  arm from every round, not the arm you were curious about.

Two more things must match even though they are not on the list people
remember. The **request shape** has to be the same wherever the models
support the same shape: output cap, temperature, and the thinking or effort
field. When a model cannot take a shape the others take, write the
difference into the manifest. And record **requested versus served**
model id on every row. A request for an alias can be served by a dated
snapshot, and a run where requested and served disagree is a run where the
arm is not the thing you named.

## The sibling control

A sibling control is an arm you already have a number for, re-dispatched in
the same run as the new arm. Pick a model with a previously published row
on the same battery, add it to the panel, and run it under exactly the
conditions of the new arms.

It buys you one specific thing. When the new arm differs from your old
number for some other model, you cannot tell whether the model changed or
the instrument did. The sibling control separates the two. If the
re-dispatched sibling reproduces its earlier row within sampling noise, the
instrument held and a difference involving the new arm is more likely the
model. If it does not, you have learned that the day, the harness or the
grader moved, and you have learned it before publishing a claim built on
the difference. Either result is worth having, and the control costs one
extra arm.

Two limits. A sibling that matches says the instrument held for that
model, not for every model. And a sibling needs the same n as the arms it
guards, or its agreement is noise matching noise.

## Repetitions

The rule from [`running-the-battery.md`](running-the-battery.md) carries
over without change: run every cell **n >= 3** times before computing a
rate, and report n with every rate. A cell is one
`(model_id, base_task_id, format_variant)` combination. A single dispatch
of a fixture is 0% or 100% for that cell and carries no weight.

Three consequences for a comparison:

- Every arm gets the same round count. If a spending cap halts a round,
  halt it for every arm together, which is what interleaving by round gives
  you for free. A cheap arm that ran five rounds beside an expensive one
  that ran four is a comparison of different sample sizes.
- Rounds are repeats of the same fixtures. They sharpen each fixture's
  estimate. They do not add independent base tasks, so they do not shrink
  the cluster count the interval is built on. See the power section of
  [`drop2-method-power-math.md`](drop2-method-power-math.md).
- Below n = 3 for any cell, publish the rows and no rate. This repo
  ships rows, never pre-aggregated rates.

## Reporting intervals, and when to claim direction only

For a difference between two arms, use the recipe in
[`drop2-method-power-math.md`](drop2-method-power-math.md): collapse rounds
to one pass rate per `(model, fixture)`, pair the two arms per fixture,
average within `base_task_id`, then take the mean and standard error of the
cluster means and a Student-t interval on `k - 1` degrees of freedom. Row-level
intervals overstate your precision, because the three format variants of a
base task are not independent evidence. Report `k` next to every interval.

Then pick the strongest claim the interval supports, and stop there:

| What the numbers show | What you may say |
|---|---|
| n < 3 in any cell | Nothing about a rate. Publish rows. |
| Interval excludes zero | A difference of that size and sign on this fixture set, with the interval and `k`. |
| Interval includes zero, cluster means not all zero | Direction only: which arm was ahead on the paired means, stated with the interval, and the sentence "no difference is established." No ranking. |
| Every cluster mean is zero (a saturated set) | That the battery did not separate these arms. No direction, because there is none to report. A harder battery is the next step. |

Direction-only is a statement about the sign of a mean. It is not a ranking,
it is not "probably better," and it should not appear in a headline. Cuts of
a battery are separate instruments and are never pooled into one number.
Compare within a cut, or say plainly which cuts a figure covers.

## What invalidates a comparison

Any one of these, and the comparison goes back to rows with no claim:

- **Cross-date.** Arms dispatched on different days, or in different
  sessions on the same day. The sibling control tells you how much that
  mattered once. Without one, you do not know.
- **Different cuts.** Arms scored on different fixture subsets, or a cut
  where one arm lost rows (a timeout, a cap, a refusal handled differently)
  and the others did not. Compare on the intersection and say so.
- **A different effort or thinking shape.** One arm with the reasoning field
  present and another with it absent is a different condition, whatever you
  call the arms. And omitting the field is not the same as turning it off
  on every model: see [`drop2-run-conditions.md`](drop2-run-conditions.md).
  Record the shape sent and the effective regime per arm.
- **A changed grader.** A scorer edit between arms or between rounds, or a
  rescore of some rows and not others. If the grader changes, rescore
  everything from raw completions, or start over.
- **A moved harness pin or a dirty tree.** The dispatch code is part of the
  instrument.
- **Requested and served model ids that disagree**, or a model id that
  changed mid-run.
- **Unequal rounds across arms.**

## Worked example: what ran and what it can and cannot support

On 2026-09-29 the maintainers dispatched three arms together, five rounds
per fixture, interleaved by round: Sonnet 5.5, Sonnet 5 and Haiku 4.5.
Sonnet 5 was the sibling control, because it already had a published row on
the same kind of battery. One harness pin and one grader covered all three
arms, the working tree was checked clean before every round, and the
requested and served model ids matched on every row. That is a within-run
comparison in the sense of this page.

The same day, GPT 6.1 Sol was dispatched on the same cuts, five rounds per
fixture, in a **separate run on a different harness pin**. It is the
example of what the method says not to do. The date matches, the battery
matches, and the two harness pins do not, so setting its rows beside the
three arms above is a cross-run comparison, and the first correction is to
re-dispatch it inside one run with the others.

One more limit belongs next to the example. Both runs used the maintainers'
own production fixture set, which is not the 30 fixtures in this repo and
has no matched-pairs variant structure. This repo's
[`results/drop3-within-run-reference.csv`](../results/drop3-within-run-reference.csv)
therefore carries the five-column header and no rows yet: none of those
rows map to a fixture here, and the repo does not invent a mapping. The
reasoning is in [`results/README.md`](../results/README.md). The method in
this kit does not depend on which fixtures you use. Point it at this repo's
30 and you have a file that fits.

## Reproduce it against your own agents

Everything below is provider-agnostic. Replace `dispatch` with whatever
call your agent makes.

1. **Write the manifest first.** Arms (model id as requested, plus the
   request shape you will send), date, harness commit, fixture-set hash,
   grader hash, rounds, and the cap that applies to every arm together.
   Include a sibling-control arm if you have an earlier row to check.
2. **Pin and check.** Refuse to start a round if the harness commit moved
   or the tree is dirty.
3. **Dispatch interleaved.** For each round, for each fixture, for each arm,
   one fresh stateless call. Write each round to its own file.
4. **Score once, with one grader.** Five columns per row
   (`model_id, fixture_id, outcome, format_variant, base_task_id`), plus the
   served model id in a private log you keep for the requested-versus-served
   check.
5. **Check before you compare.** Every arm has the same round count; served
   equals requested on every row; no arm lost rows the others kept.
6. **Count n per cell, then analyze.** The sketch below computes n per cell
   and the paired, clustered difference between two arms.

```python
import csv
import math
from collections import defaultdict
from statistics import mean, stdev

rows = list(csv.DictReader(open("results/your-run.csv")))

# n per (model, base task, variant) cell -- every one must be >= 3.
n = defaultdict(int)
for r in rows:
    n[(r["model_id"], r["base_task_id"], r["format_variant"])] += 1
assert min(n.values()) >= 3, "fewer than 3 rows in some cell: publish rows, not rates"

def fixture_rate(model):
    """Collapse rounds: one pass rate per fixture for this model."""
    acc = defaultdict(list)
    for r in rows:
        if r["model_id"] == model:
            acc[(r["base_task_id"], r["fixture_id"])].append(r["outcome"] == "pass")
    return {k: sum(v) / len(v) for k, v in acc.items()}

def paired_cluster_delta(model_a, model_b):
    a, b = fixture_rate(model_a), fixture_rate(model_b)
    clusters = defaultdict(list)
    for key in a.keys() & b.keys():
        clusters[key[0]].append(a[key] - b[key])
    d = [mean(v) for v in clusters.values()]  # one number per base task
    k = len(d)
    se = stdev(d) / math.sqrt(k) if k > 1 else float("nan")
    return mean(d), se, k  # interval: mean +/- t(0.975, k-1) * se; report k
```

If every cluster mean is zero, `se` is zero and no interval exists: the
battery did not separate your arms, so say that and get harder fixtures.
Otherwise apply the reporting table above.

Anything you publish from this should carry the manifest, the row file, and
the n per cell. If you want it in this repo, the contribution rules are in
[`CONTRIBUTING.md`](../CONTRIBUTING.md#submitting-results).
