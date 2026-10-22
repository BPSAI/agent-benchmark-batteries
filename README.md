# agent-benchmark-batteries

Matched-pairs benchmark fixtures for coding agents. 10 base coding tasks
(bugfix / feature / refactor / chore, spanning easy through hard-plus),
each rendered in 3 formats that vary independently -- so you can measure
whether an agent's pass/refusal rate is driven by task difficulty, prompt
structure, or "in production" framing, instead of a single confounded
number. 30 fixtures total, plus a runner guide and reference results.
Run them against your own agents.

## What's here

```
fixtures/
  bugfix/      12 fixtures (4 base tasks x 3 format variants)
  chore/       3 fixtures (1 base task x 3 format variants)
  feature/     9 fixtures (3 base tasks x 3 format variants)
  refactor/    6 fixtures (2 base tasks x 3 format variants)
  README.md    the methodology -- read this first
docs/
  running-the-battery.md          how to run the fixtures against any model/agent
  drop2-run-conditions.md         how to configure a thinking field-present/field-absent A-B, incl. the adaptive-default trap
  drop2-method-power-math.md      paired/clustered analysis recipe + power math, worked with real numbers
  receipts-methods.md             where every figure on the Error Bars Receipts page comes from
  within-run-comparison.md        Drop 3 method kit: comparing two or more models in one run, with a sibling control
results/
  reference-results.csv               raw per-fixture per-model outcome rows
  drop2-thinking-onoff-reference.csv  reference rows for the thinking field-present/field-absent method kit
  drop3-within-run-reference.csv      Drop 3 reference file (five-column shape; no rows yet, see its README section)
  receipts-banked-rows.csv            the Receipts cost tables + context ladder, one row per cell
  README.md                           what those rows are (and aren't)
governance/
  denylist.txt                the content deny-list
  check_denylist.py           CI: scans every file against it
  check_fixture_stamps.py     CI: every fixture must carry its provenance stamp
  check_results_shape.py      CI: the five-column results files keep exactly that shape
.github/workflows/ci.yml      runs the three governance checks on every push/PR
```

Start with [`fixtures/README.md`](fixtures/README.md) for the matched-pairs
methodology, then [`docs/running-the-battery.md`](docs/running-the-battery.md)
to run it yourself.

## CI checks

CI runs three checks on every push: a generic-pattern content scan
(`governance/check_denylist.py`), fixture provenance-stamp
verification (`governance/check_fixture_stamps.py`), and a shape check on
the five-column results files (`governance/check_results_shape.py`).
Contributor PRs must pass all three.

## License

[MIT](LICENSE).
