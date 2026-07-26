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
