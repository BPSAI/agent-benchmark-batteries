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
- **Field-present arm**: include it, with the model-specific shape below
  -- these are not interchangeable across models, and sending the wrong
  one (in particular, sending `budget_tokens` to a model that has removed
  it) gets you a 400, not a quietly-ignored field:

| model | field-present request shape |
|---|---|
| `opus` (Claude Opus 4.8) | `{"type": "enabled"}` -- no `budget_tokens`; sending one is rejected with a 400 on this model |
| `haiku` (Claude Haiku 4.5) | `{"type": "enabled", "budget_tokens": 4096}` -- `budget_tokens` is required here; this is the one model in the panel that still takes it |
| `opus-5` (Claude Opus 5) | `{"type": "adaptive"}`, optionally with an `effort` level -- no `budget_tokens`; sending one is rejected with a 400 |
| `sonnet` (Claude Sonnet 5) | `{"type": "adaptive"}` -- no `budget_tokens`; sending one is rejected with a 400 |
| `fable` (Claude Fable 5) | `{"type": "enabled"}` -- no `budget_tokens`; sending one is rejected with a 400 (this model is always-on regardless -- see the table below -- so this request shape is sent for symmetry with the other arms' construction, not because it changes anything) |
| `ollama-devstral` (local comparator) | no thinking field sent in either arm -- see "About the local comparator" below |

Everything else -- fixture, prompt, temperature, model, day -- stays fixed
between the two requests for a given `(fixture, model)` pair, **with one
observed exception**: `haiku`'s `tokens_in` is exactly 30 tokens higher on
all 30 field-present rows than the matching field-absent row for the same
fixture, while every other model's `tokens_in` is identical between its
two arms on all 30 of its fixtures. This file doesn't ship a byte-level
request log, so the cause isn't determinable from the shipped data alone
-- stated here as an observed fact, not explained by a mechanism this
repo can verify. If you rely on "only the thinking field changes" as an
invariant in your own run, check `tokens_in` per model the same way and
don't assume it holds for every model just because it holds for most.

Run both arms back-to-back so a same-day change on the vendor's side
can't land between them. (This file doesn't ship request timestamps, so
the gap between its own two arms isn't independently checkable from the
CSV -- "back-to-back" is the target to hit in your own run, not a number
this file lets you verify.)

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
| `fable` (Claude Fable 5) | always-on (request-shape fact -- see below for what the rows show) | `{"type": "disabled"}` rejected with a 400 |
| `ollama-devstral` (local comparator) | no thinking field was sent in either arm -- see "About the local comparator" below | not applicable |

**"Always-on" and "off" in this table are request-shape facts, not
per-row behavior claims.** They describe what the vendor's documentation
says about whether reasoning *can be switched off by request* --
`fable`'s "always-on" means there is no request that turns it off, full
stop. It does not mean `fable` reasons the same amount, or reasons at
all, on every row -- see the next section for what its rows actually do,
which is neither "always-on" nor "off" in any per-row sense.

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
twice. On `fable`, neither arm can be off by request -- the field-present
request and the field-absent request both land on the vendor's single
always-on state, and the explicit-disable shape that would test for an
off state is documented to fail with a 400 rather than being honored.

## What `fable`'s rows actually show: adaptive depth, not constant behavior

"Always-on" describes the request shape, and the request shape is the
whole story for the four models above -- but `fable` is different, and
the difference only shows up in the rows, not in the vendor's
documentation. Recomputed from `drop2-thinking-onoff-reference.csv`
alone:

- **`tokens_reasoning` is zero on 16 of `fable`'s 30 field-present rows
  and 14 of its 30 field-absent rows.** An always-on model that reasoned
  the same amount on every call would show mean-only variation, not a
  majority of rows at exactly zero token by token. This model reasons on
  some calls and not others, regardless of what was requested.
- **The two arms' means genuinely separate**: 86.5 reasoning tokens/row
  field-present vs. 40.7 field-absent, over the full 30-row samples --
  unlike `opus-5`/`sonnet` above, whose two arms overlap. Presence of the
  field correlates with more reasoning here, even though the vendor's own
  documentation says the field can't switch reasoning off.
- **All 33 refused rows in this entire 360-row file belong to `fable`**
  (17 in the field-present arm, 16 in the field-absent arm) -- no other
  model in the panel refused a single fixture. `fable`'s pass rate is
  correspondingly not saturated (13/30 field-present, 14/30 field-absent,
  vs. 30/30 for every other metered model in both arms -- see
  `docs/drop2-method-power-math.md` for the statistics this produces).
- **The refusals track `format_variant`, not chance**: `short` fixtures
  pass 8/10 in both arms; `embedded-neutral` passes 3/10 field-present vs.
  5/10 field-absent; `embedded-production` passes 2/10 field-present vs.
  1/10 field-absent. Recompute this yourself by grouping the CSV's
  `fable` rows on the fixture id's format suffix.

None of this contradicts the request-shape fact above -- there genuinely
is no request you can send this model that turns reasoning off. But
"always-on" is not the same claim as "constant," and this file's own
rows are the only place that distinction is visible; the vendor's
documentation alone would tell you nothing about the reasoning-token
zeros, the arm separation, or the refusal/format pattern.

**The tell is in the reasoning-token counts, not in what you sent.**
Compare mean reasoning tokens per row across your two arms for each
model. Every number below is `tokens_reasoning` averaged over the 30
rows/arm for that model in `drop2-thinking-onoff-reference.csv` --
recompute it yourself and it will match, because that CSV is the only
source for this table, covering all six models in the panel:

| model | reasoning tokens/row, field present | reasoning tokens/row, field absent |
|---|---|---|
| `opus` (off on omission) | 153.3 | 0.0 |
| `haiku` (off on omission) | 1,527.0 | 0.0 |
| `opus-5` (adaptive default) | 435.5 | 461.5 |
| `sonnet` (adaptive default) | 189.2 | 207.9 |
| `fable` (always-on by request, adaptive per row -- see above) | 86.5 | 40.7 |
| `ollama-devstral` (no thinking field sent) | 0.0 | 0.0 |

`opus` and `haiku` show the pattern you'd expect from an off-on-omission
model -- omitting the field drove reasoning tokens to zero. `opus-5` and
`sonnet` show reasoning tokens in the same range whether the field was
present or absent, because field-absent was never off for them -- it was
"let the model decide," and the model decided about the same thing both
times: that's the adaptive-default trap. `fable` is the third pattern --
its means separate for real (86.5 vs. 40.7, not overlapping ranges), even
though the vendor's documentation says the field cannot switch its
reasoning off; the per-row zero/nonzero split above is what makes that
consistent.

A naive reading of "I omitted the field" as "thinking was off" would
report a contrast that never happened on `opus-5`/`sonnet`, and a naive
reading of "the vendor says always-on" as "the field doesn't matter"
would miss a real effect on `fable`. The fix is mechanical, not a
vendor-documentation lookup: pull `tokens_reasoning` straight from your
own response payloads (the column already exists in
`drop2-thinking-onoff-reference.csv` if you want to see the raw numbers
behind the table above) and confirm what the two arms actually did, on
every model in your panel, before you compute anything downstream of it.
If a model has no documented way to reach a true off state at all -- an
explicit disable request that the vendor's own documentation says will
be rejected -- that is itself a result worth reporting (no off *state*
exists for that model), separately from whatever its per-row reasoning
behavior turns out to be.

## About the local comparator

`ollama-devstral` received no thinking field in either arm -- its two
"arms" are otherwise byte-for-byte identical requests, confirmed from
this file: `tokens_in` is identical between its field-present and
field-absent rows on all 30 of its fixtures (nothing else in this repo
sources a claim about this model's actual reasoning capability; the
request behavior above is all that's determinable from the shipped
data). It's included under two arms anyway because it's a free
comparator that costs nothing to run twice: since nothing varies in its
requests, any outcome difference between its two "arms," row for row,
would indicate non-determinism in the model or the harness rather than a
thinking effect -- a sanity check you get for free by including it,
without asserting anything about what the model does or doesn't support.

## Configuring the arm on other vendors

Everything above is this drop's own panel, which is Claude-only. If
you're running the A-B against a different vendor, you need that
vendor's own documented request shape -- it will not match the tables
above. This section covers the four non-Anthropic vendors whose
documentation could be fetched and read live in the session that wrote
this section; **every row below is a claim about that vendor's
documentation on the date it was fetched, not a claim this repo has
measured.** None of these vendors are in this drop's reference run --
`drop2-thinking-onoff-reference.csv` contains Claude and one local
Ollama model only. Treat every fact below as "documented request shape
as of the access date" and re-check it yourself before relying on it;
vendor docs change.

**Coverage.** This section covers OpenAI, Google Gemini, DeepSeek, and
xAI -- the only vendors whose live documentation was successfully
fetched while writing this section. If your vendor isn't here, that's
because its docs weren't fetched, not because they were checked and
found to have nothing -- go to the vendor's own current documentation
rather than assuming an omission means "no such parameter."

### OpenAI

Source: [developers.openai.com/api/docs/guides/reasoning](https://developers.openai.com/api/docs/guides/reasoning)
(redirects from `platform.openai.com/docs/guides/reasoning`), accessed
2026-08-21.

- **Field-absent means:** documented default, not a blanket "off" --
  the docs state "If you omit `reasoning.effort`, GPT-5.6 defaults to
  `medium` in both modes." Omitting the field does not stop reasoning on
  this model family.
- **Documented enable shape:** `reasoning: {"effort": "<value>"}` in the
  Responses API, where `<value>` is model-dependent and can include
  `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`.
- **Documented disable shape:** the docs don't name a separate disable
  flag. The lowest documented value, `none`, is described as being for
  "latency-critical tasks that do not benefit from any reasoning" --
  the closest documented approximation to off, but the docs frame it as
  the bottom of the effort scale, not a distinct boolean. Don't assume
  `effort: "none"` means zero reasoning tokens without checking the
  usage field below on your own rows.
- **Usage field for the verification step:** `usage.output_tokens_details.reasoning_tokens`
  on the response object (confirmed from a worked example in the fetched
  docs).

### Google Gemini

Source: [ai.google.dev/gemini-api/docs/thinking](https://ai.google.dev/gemini-api/docs/thinking),
accessed 2026-08-21.

- **Field-absent means:** per-model documented default, and it is not
  uniform across the panel. The docs state "Gemini models engage in
  dynamic thinking by default, automatically adjusting the amount of
  reasoning effort based on the complexity of the request," and publish
  a per-model default table -- most listed models default to thinking
  **On** at a specific level (e.g. `gemini-3.7-flash`: on, medium), but
  at least one, `gemini-2.5-flash-lite`, is documented as defaulting to
  **Off**. There is no single answer for "this vendor" -- check the
  specific model in the vendor's own table.
- **Documented enable shape:** `generation_config: {"thinking_level": "<value>"}`,
  where `<value>` is one of `minimal`, `low`, `medium`, `high` and the
  supported subset is model-dependent (not every model supports
  `minimal`).
  ```json
  {"model": "gemini-3.7-flash", "generation_config": {"thinking_level": "low"}}
  ```
- **Documented disable shape:** **the fetched docs don't answer this.**
  No `"off"` (or equivalent) value is listed among `thinking_level`'s
  documented values, and no separate boolean or budget-to-zero field is
  documented on this page. The one model that defaults to Off gets there
  from its own default, not from a request value you can send to any
  model. If you need a true off arm on a Gemini model, that's an open
  question this fetch didn't resolve -- don't assume a shape exists just
  because other vendors have one.
- **Usage field for the verification step:** the fetched docs show
  `total_thought_tokens` used as `interaction.usage.total_thought_tokens`
  in a worked example, but don't separately establish the full field
  path as a stable contract -- confirm the full path against your own
  response payload before wiring a script to it.

### DeepSeek

Source: [api-docs.deepseek.com/guides/thinking_mode](https://api-docs.deepseek.com/guides/thinking_mode/),
accessed 2026-08-21 (usage-field check also against
[api-docs.deepseek.com/quick_start/token_usage](https://api-docs.deepseek.com/quick_start/token_usage/),
same date).

- **Field-absent means:** on, not off. The docs state "Thinking mode is
  enabled by default, with the default effort being `high`."
- **Documented enable shape:** three documented request formats,
  depending on which API surface you're calling through --
  - OpenAI format: `{"thinking": {"type": "enabled"}}` plus
    `"reasoning_effort": "low"/"high"/"max"`.
  - Anthropic-compatible format: `{"reasoning": {"effort": "none/low/high/max"}}`.
  - Responses API format: `{"output_config": {"effort": "low/high/max"}}`.
- **Documented disable shape:** explicitly documented, unlike the other
  three vendors in this section -- OpenAI format
  `{"thinking": {"type": "disabled"}}`, or Anthropic-compatible format
  `{"reasoning": {"effort": "none"}}` (the docs say plainly: "`none`
  disables thinking mode").
- **Usage field for the verification step:** **the fetched docs don't
  name one.** Neither the thinking-mode guide nor the token-usage guide
  documents a dedicated reasoning-token count field at the URLs fetched;
  the chain-of-thought content itself streams back in a
  `reasoning_content` field (text, not a token count). If you need a
  reasoning-token count for the verification step on this vendor, that's
  unresolved by this fetch -- check your own response payloads directly
  rather than assuming a field name from another vendor carries over.

### xAI

Source: [docs.x.ai/developers/model-capabilities/text/reasoning](https://docs.x.ai/developers/model-capabilities/text/reasoning)
(redirects from `docs.x.ai/docs/guides/reasoning`), accessed 2026-08-21.

- **Field-absent means:** on, at the documented default effort. The docs
  state, for the models that support the parameter: "If not specified,
  `reasoning_effort` defaults to `high`."
- **Documented enable shape:** `reasoning_effort: "<value>"` (SDK) or
  `reasoning: {"effort": "<value>"}` (Responses API format), where
  `<value>` is `low`/`medium`/`high`/`xhigh` on models that support the
  parameter (`xhigh` only on newer models; older supported models treat
  `xhigh` requests as `high`). Not every model in the vendor's lineup
  supports the parameter at all -- check the specific model.
- **Documented disable shape:** none. Stated as flatly as any fact in
  this section: **"Reasoning cannot be disabled."** If you need a true
  off arm on this vendor's reasoning-capable models, the fetched docs
  say outright that no such request exists -- don't go looking for one.
- **Usage field for the verification step:** the docs state "Usage
  metrics expose `reasoning_tokens`"; the exact nesting path within the
  usage object wasn't shown in the fetched section -- confirm the full
  path against your own response payload before wiring a script to it.

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

**Running this on a non-Anthropic vendor:** the check is identical, but
the field name isn't `tokens_reasoning` -- use that vendor's own
documented usage field from "Configuring the arm on other vendors" above
(`usage.output_tokens_details.reasoning_tokens` for OpenAI,
`total_thought_tokens` for Gemini, `reasoning_tokens` somewhere in the
usage object for xAI -- confirm the exact path yourself for the latter
two; DeepSeek's fetched docs don't name one at all, so on that vendor
you'd need to find the field from your own response payload before this
check is possible).
