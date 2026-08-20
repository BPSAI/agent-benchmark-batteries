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
results/
  reference-results.csv               raw per-fixture per-model outcome rows
  drop2-thinking-onoff-reference.csv  reference rows for the thinking field-present/field-absent method kit
  README.md                           what those rows are (and aren't)
governance/
  denylist.txt                the content deny-list
  check_denylist.py           CI: scans every file against it
  check_fixture_stamps.py     CI: every fixture must carry its provenance stamp
.github/workflows/ci.yml      runs both governance checks on every push/PR
```

Start with [`fixtures/README.md`](fixtures/README.md) for the matched-pairs
methodology, then [`docs/running-the-battery.md`](docs/running-the-battery.md)
to run it yourself.

## Governance -- what this repo will never contain

This is a public fixtures repo maintained by a company that also builds
non-public agent tooling. That split is enforced structurally, not just
by intent, and we're publishing the mechanism, not just the promise:

1. **Every fixture is stamped.** `metadata.public_release: true` and
   `metadata.provenance: "original-authored"` are required on every file
   under `fixtures/`. CI (`governance/check_fixture_stamps.py`) fails any
   fixture missing either key -- see [CONTRIBUTING.md](CONTRIBUTING.md)
   for what the provenance claim means.
2. **A deny-list scanner runs on every push and PR.**
   `governance/check_denylist.py` regex-scans every tracked file against
   `governance/denylist.txt` -- internal product/codename vocabulary,
   internal infrastructure identifiers, credential-shaped strings, and
   personal names beyond the LICENSE copyright line. One narrow,
   explicit, per-file allowlist entry exists (the documented runner
   invocation in `docs/running-the-battery.md`) -- everything else, in
   every file including that one, is enforced.
3. **On the private side**, this repo is updated from our internal
   monorepo through exactly one script, which copies only from an
   explicit per-fixture allowlist and hard-refuses any path from our
   confidential reasoning-fixture family by construction (the receiving
   side of that promise -- the two governance checks in point 1 and
   point 2 above -- is the part you can verify yourself, from this repo
   alone).
4. **This repo will never contain**: real hypotheses, real fleet or
   customer data, internal telemetry or trace data, internal decision
   records, credentials, or the confidential fixture family referenced
   above. If you ever find something here that looks like it violates
   this, please open an issue -- that's a bug in our process, not a
   one-off mistake to quietly fix.
5. **The product boundary applies to drops, too.** A larger,
   production-shaped task corpus, its graders, and its harder fixture
   variants stay on the product side of the line in point 3 above and
   are never published here. What a drop publishes is a method kit: the
   sample fixtures (still just this repo's 30), reference rows over
   those fixtures, the analysis math, and guidance for building your own
   task set with the same construction -- never a private corpus's own
   figures.

## License

[MIT](LICENSE).
