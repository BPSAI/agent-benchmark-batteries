# Drop 2 run conditions -- configuring a thinking on/off A-B

This is the second half of the method kit: how the two arms in
[`results/drop2-thinking-onoff-reference.csv`](../results/drop2-thinking-onoff-reference.csv)
were configured, so you can reproduce the same contrast against your own
model panel and your own tasks. Read
[`docs/running-the-battery.md`](running-the-battery.md) first for the base
dispatch protocol -- this document only covers the one field that varies
between the two arms.

## The two arms

- **Thinking-off arm**: omit the extended-thinking/reasoning field from the
  request entirely.
- **Thinking-on arm**: include it, with an explicit budget where the vendor
  requires one (`{"type": "enabled", "budget_tokens": 4096}` for
  legacy-style thinking models) or an adaptive/auto mode where the vendor
  only offers that shape (`{"type": "adaptive"}`).

Everything else -- fixture, prompt, temperature, model, day -- stays fixed
between the two requests for a given `(fixture, model)` pair. Only the
thinking field changes. Run both arms back-to-back (the worked example's two arms started about
twenty-four minutes apart) so a same-day change on the vendor's side
can't land between them.

## The adaptive-default trap

Do not assume "I didn't send the field" means "the model didn't reason."
Some model families treat omission as a hint, not a shutoff: their default
*is* adaptive thinking, and the model decides per call whether to spend
reasoning tokens whether or not you asked for it. If your "off" arm and
your "on" arm are both landing on the adaptive default, you have run the
same condition twice and any pass-rate or refusal-rate delta you compute
between them is noise, not a thinking effect.

**The tell is in the reasoning-token counts, not in what you sent.**
Compare mean reasoning tokens per row across your two arms for each model.
On this drop's worked panel, two of the five metered models showed exactly
the pattern you want -- omitting the field drove reasoning tokens to zero:

| model | reasoning tokens/row, field present | reasoning tokens/row, field absent |
|---|---|---|
| a legacy-thinking-shape model | 71.7 | 0.0 |
| another legacy-thinking-shape model | 1,390.9 | 0.0 |

Two other models on the same panel showed the adaptive-default pattern --
reasoning tokens stayed in the same range whether the field was present or
absent, because omission was never "off," it was "let the model decide,"
and the model decided about the same thing both times:

| model | reasoning tokens/row, field present | reasoning tokens/row, field absent |
|---|---|---|
| an adaptive-thinking model | 265.7 | 289.0 |
| another adaptive-thinking model | 102.1 | 104.9 |

Those two rows are the trap: a naive reading of "I omitted the field" as
"thinking was off" would report a contrast that never happened. The fix is
mechanical, not a vendor-documentation lookup: pull `tokens_reasoning`
straight from your own response payloads (the column already exists in
`drop2-thinking-onoff-reference.csv` if you want to see the raw numbers
behind the table above) and confirm the two arms actually differ in the
metric you're claiming to manipulate, on every model in your panel, before
you compute anything downstream of it. If a model has no documented way to
force reasoning off -- some vendors return an error for an explicit
disable request rather than honoring it -- that is itself a finding worth
reporting (no off switch exists for that model), not a gap to paper over
with an assumed contrast.

## Verification step, restated

Before trusting any A/B result from your own run:

1. For each model in your panel, compute mean reasoning tokens per row in
   both arms.
2. If the two means are clearly separated (zero vs. nonzero, or otherwise
   non-overlapping given your sample size), you have a real contrast for
   that model -- proceed to the paired analysis in
   [`docs/drop2-method-power-math.md`](drop2-method-power-math.md).
3. If the two means sit in the same range, you have measured "the same
   condition twice." Report that finding as-is (it's informative on its
   own -- it tells a reader that field is not a usable lever for that
   model) and do not compute a pass-rate delta between the two arms for
   that model.

This check costs nothing extra -- the reasoning-token count is already in
every response you're scoring for `pass`/`fail` anyway.
