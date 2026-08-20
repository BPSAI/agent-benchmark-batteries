# Drop 2 run conditions -- configuring a thinking field-present/field-absent A-B

This is the second half of the method kit: how the two arms in
[`results/drop2-thinking-onoff-reference.csv`](../results/drop2-thinking-onoff-reference.csv)
were configured, so you can reproduce the same contrast against your own
model panel and your own tasks. Read
[`docs/running-the-battery.md`](running-the-battery.md) first for the base
dispatch protocol -- this document only covers the one field that varies
between the two arms.

## The two arms: field-present vs. field-absent

- **Field-absent arm**: omit the extended-thinking/reasoning field from
  the request entirely.
- **Field-present arm**: include it, with an explicit budget where the
  vendor requires one (`{"type": "enabled", "budget_tokens": 4096}` for
  legacy-shape thinking models) or an adaptive/auto mode where the vendor
  only offers that shape (`{"type": "adaptive"}`).

Everything else -- fixture, prompt, temperature, model, day -- stays fixed
between the two requests for a given `(fixture, model)` pair. Only the
thinking field changes. Run both arms back-to-back (the worked example's
two arms started about twenty-four minutes apart) so a same-day change on
the vendor's side can't land between them.

**Do not call either arm "on" or "off."** That's the whole subject of the
next section: what omitting the field actually does depends on the
model, and only one of the three possible outcomes below is "off."

## What field-absent actually means, per model

Do not assume "I didn't send the field" means "the model didn't reason."
Per each vendor's current documentation, omitting the thinking field
resolves to one of three different behaviors depending on the model
family, and an explicit disable request (`{"type": "disabled"}`) is
handled differently again per model:

| model (as it appears in the CSV's `model` column) | field-absent means | documented explicit-disable shape |
|---|---|---|
| `opus` (Claude Opus 4.8) | off -- no reasoning happens | not needed; field-absent already produces off |
| `haiku` (Claude Haiku 4.5) | off -- no reasoning happens | not needed; field-absent already produces off |
| `opus-5` (Claude Opus 5) | adaptive -- the model decides per call | `{"type": "disabled"}` accepted at effort `high` or below; rejected with a 400 at effort `xhigh`/`max` |
| `sonnet` (Claude Sonnet 5) | adaptive -- the model decides per call | `{"type": "disabled"}` accepted outright |
| `fable` (Claude Fable 5) | always-on -- there is no off state | `{"type": "disabled"}` rejected with a 400 |
| `ollama-devstral` (local comparator) | not applicable -- this model family has no thinking/reasoning field | not applicable |

**On the two models where field-absent already means off, no further
action is needed to run a true off arm.** On the two adaptive models,
field-absent is a *third* condition (let the model decide), not off --
getting a true off arm on those two requires sending the explicit
`{"type": "disabled"}` shape, and on Opus 5 that request is only honored
at effort `high` or below. **This reference CSV did not send that
request to any model** -- both of its arms are "field present" (an
explicit `enabled`/`adaptive` request) and "field absent" (nothing sent),
never an explicit disable. So for `opus-5` and `sonnet` in this file, the
field-absent arm is not an off arm; it is the adaptive default, observed
twice. On `fable`, neither arm can be off -- the field-present request
and the field-absent request both land on the vendor's single always-on
state, and the explicit-disable shape that would test for an off state
is documented to fail with a 400 rather than being honored.

**The tell is in the reasoning-token counts, not in what you sent.**
Compare mean reasoning tokens per row across your two arms for each
model. Every number below is `tokens_reasoning` averaged over the 30
rows/arm for that model in `drop2-thinking-onoff-reference.csv` --
recompute it yourself and it will match, because that CSV is the only
source for this table. The two off-on-omission models show the pattern
you'd expect -- omitting the field drove reasoning tokens to zero:

| model | reasoning tokens/row, field present | reasoning tokens/row, field absent |
|---|---|---|
| `opus` | 153.3 | 0.0 |
| `haiku` | 1,527.0 | 0.0 |

The two adaptive models show reasoning tokens in the same range whether
the field was present or absent, because field-absent was never off for
them -- it was "let the model decide," and the model decided about the
same thing both times:

| model | reasoning tokens/row, field present | reasoning tokens/row, field absent |
|---|---|---|
| `opus-5` | 435.5 | 461.5 |
| `sonnet` | 189.2 | 207.9 |

Those two rows are the trap: a naive reading of "I omitted the field" as
"thinking was off" would report a contrast that never happened. The fix
is mechanical, not a vendor-documentation lookup: pull `tokens_reasoning`
straight from your own response payloads (the column already exists in
`drop2-thinking-onoff-reference.csv` if you want to see the raw numbers
behind the table above) and confirm the two arms actually differ in the
metric you're claiming to manipulate, on every model in your panel,
before you compute anything downstream of it. If a model has no
documented way to reach a true off state at all -- an explicit disable
request that the vendor's own documentation says will be rejected -- that
is itself a result worth reporting (no off state exists for that model),
not a gap to paper over with an assumed contrast.

## Verification step, restated

Before trusting any A-B result from your own run:

1. For each model in your panel, compute mean reasoning tokens per row in
   both arms.
2. If the two means are clearly separated (zero vs. nonzero, or otherwise
   non-overlapping given your sample size), you have a real field-present
   vs. field-absent contrast for that model -- proceed to the paired
   analysis in
   [`docs/drop2-method-power-math.md`](drop2-method-power-math.md).
3. If the two means sit in the same range, you have measured "the same
   condition twice." Report that as-is (it's informative on its own -- it
   tells a reader that omitting the field is not a usable lever for that
   model) and do not compute a pass-rate delta between the two arms for
   that model. If you need a true off arm on a model like this, check
   whether the vendor documents an explicit disable shape and confirm
   with the same reasoning-token check that it actually zeroes out --
   don't assume the documented shape is honored either.

This check costs nothing extra -- the reasoning-token count is already in
every response you're scoring for `pass`/`fail` anyway.
