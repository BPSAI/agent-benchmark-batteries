# How the receipts are made

This page accompanies the Error Bars Receipts page and explains where every figure there comes from.

The Receipts page shows what each model costs to run on real coding tasks, with one interval plot per task cut. Here you get the basis of every figure: how each cost was sourced, the full per-model tables, every known issue, and the long-context and disclosure runs.

## Terms used here

- A **cut** is one kind of coding task; this page has three (code, review format, documentation chore).
- A **fixture** is one task instance a model is asked to complete.
- An **arm** is one variant of a run — the same models under a specific set of conditions.
- A **panel** is the set of models a run was dispatched against.
- A **route** is the path used to reach a model: a direct API, a local install, or a reseller such as OpenRouter.
- **Mtok** means one million tokens; published rates are quoted per Mtok.
- A bracket like **[0.85, 0.96]** is a confidence interval on the pass rate.

## What a figure rests on

A **completed task** is a row the model attempted and the scorer marked pass.

Spend is the provider's invoice where we have one. Otherwise it is our own token count times the provider's published rate.

Rows from a run in which a model hit an output cap are dropped from the cut's count entirely, not scored as failures. Where the same model also ran without a cap, that uncapped run is the one we score. So a printed Anthropic figure is the uncapped run's own spend, never a fold-in of capped runs.

An error row (a timeout or a provider error) counts as spend and stays in the count, but never as a completion.

We do not silently fix a withdrawn or repriced figure in place. It is listed, with the correction, under Known issues.

Every figure carries a **basis** — the class of evidence behind it, not the tool that produced it:

| basis | meaning |
|---|---|
| invoice | The provider's posted invoice for the rows it covers. |
| rate estimate | Our own token count times the provider's published rate, used where the invoice has not yet posted. |
| re-scored | Spend is the provider's invoice, divided by a corrected completion count after a scoring bug. |
| repriced | Re-derived from token counts at a corrected, published rate. |
| doc-quoted | A total we published earlier, not re-derived here. |
| rate not confirmed | We could not confirm the rate against an invoice, so no figure is printed. |
| no bill | The model ran locally; there is no bill because there is no API. |
| withdrawn | A scoring bug corrupted this cell's pass count, so no cost-per-task figure is printed; the spend total stays. |
| invoice + rate estimate | One run split across two providers, added together: one share from the invoice, the other from our token count times the rate. |
| invoice + estimate, shared date | The same split on a date whose invoice covers several runs at once; the shared portion stays an estimate. |

As of 2026-09-28, the provider's invoice had posted for seven dates. Those dates: 2026-08-01, 2026-08-02, 2026-08-12, 2026-08-13, 2026-08-14, 2026-08-25 and 2026-08-28. Rows on other dates use the rate estimate.

The full column set — lab, access route, and rounds per fixture — ships as a CSV in this repo's `results/` directory; see its README.

## Code cut

| model | completed | spend | $/completed task | basis | date |
|---|---|---|---|---|---|
| claude-fable-5 | 68/300 | — | — | rate not confirmed | 2026-08-13 – 2026-08-14 |
| claude-haiku-4-5 | 98/100 | $2.0849 | $0.0211 | re-scored | 2026-08-14 |
| claude-opus-4-8 | 286/300 | $19.2233 | $0.0649 | re-scored | 2026-08-13 – 2026-08-14 |
| claude-opus-5 | 96/100 | $15.0332 | $0.1534 | re-scored | 2026-08-14 |
| claude-sonnet-5 | 98/100 | $3.3689 | $0.0344 | invoice | 2026-08-14 |
| DeepSeek V4 Flash (0731) | 97/100 | $0.1900 | $0.0019 | re-scored | 2026-08-13 |
| DeepSeek V4 Pro | 98/100 | $0.9591 | $0.0098 | invoice | 2026-08-13 |
| Devstral | 92/100 | — | — | no bill | 2026-08-14 |
| Gemini 3.1 Pro (preview) | 100/100 | $6.7758 | $0.0678 | invoice | 2026-08-13 |
| Gemini 3.6 Flash | 100/100 | $4.6218 | $0.0462 | invoice | 2026-08-13 |
| Gemma 4 31B | 100/100 | — | — | no bill | 2026-08-13 |
| GLM 4.7 Flash | 93/100 | — | — | no bill | 2026-08-13 |
| GLM 5.2 | 98/100 | $0.9274 | $0.0095 | invoice | 2026-08-13 – 2026-08-14 |
| GPT-5.6 Luna | 93/100 | $0.1107 | $0.0012 | invoice | 2026-08-13 – 2026-08-14 |
| GPT-5.6 Sol | 92/100 | $5.4973 | $0.0598 | invoice | 2026-08-13 – 2026-08-14 |
| GPT-5.6 Terra | 95/100 | $1.0342 | $0.0109 | invoice | 2026-08-13 |
| Granite 4.1 30B | 97/100 | — | — | no bill | 2026-08-13 |
| Grok 4.5 | 95/100 | $1.3261 | $0.0140 | invoice | 2026-08-13 – 2026-08-14 |
| Kimi K3 | 94/100 | $10.4069 | $0.1107 | invoice | 2026-08-13 – 2026-08-14 |
| Nemotron 3 Nano 30B | 92/100 | — | — | no bill | 2026-08-13 |
| Phi-4 14B | 94/100 | — | — | no bill | 2026-08-13 |
| Qwen3 8B | 183/200 | — | — | no bill | 2026-08-13 – 2026-08-14 |
| Qwen3.6 27B (GGUF Q4_K_M build) | 95/100 | — | — | no bill | 2026-08-13 |
| Qwen3.8 Max | 100/100 | $9.3443 | $0.0934 | invoice | 2026-08-13 – 2026-08-14 |

## Review format cut

| model | completed | spend | $/completed task | basis | date |
|---|---|---|---|---|---|
| claude-fable-5 | 30/90 | — | — | rate not confirmed | 2026-08-13 – 2026-08-14 |
| claude-haiku-4-5 | 23/30 | $0.0903 | $0.0039 | invoice | 2026-08-14 |
| claude-opus-4-8 | 71/90 | $2.5354 | $0.0357 | invoice | 2026-08-13 – 2026-08-14 |
| claude-opus-5 | 27/30 | $3.2559 | $0.1206 | invoice | 2026-08-14 |
| claude-sonnet-5 | 21/30 | $0.8223 | $0.0392 | invoice | 2026-08-14 |
| DeepSeek V4 Flash (0731) | 14/30 | $0.0330 | $0.0024 | invoice | 2026-08-13 |
| DeepSeek V4 Pro | 14/30 | $0.1815 | $0.0130 | invoice | 2026-08-13 |
| Devstral | 22/30 | — | — | no bill | 2026-08-14 |
| Gemini 3.1 Pro (preview) | 12/30 | $1.1289 | $0.0941 | invoice | 2026-08-13 |
| Gemini 3.6 Flash | 9/30 | $0.6468 | $0.0719 | invoice | 2026-08-13 |
| Gemma 4 31B | 6/30 | — | — | no bill | 2026-08-13 |
| GLM 4.7 Flash | 16/30 | — | — | no bill | 2026-08-13 |
| GLM 5.2 | 14/30 | $0.1378 | $0.0098 | invoice | 2026-08-13 – 2026-08-14 |
| GPT-5.6 Luna | 6/30 | $0.0182 | $0.0030 | invoice | 2026-08-13 – 2026-08-14 |
| GPT-5.6 Sol | 7/30 | $0.6534 | $0.0933 | invoice | 2026-08-13 – 2026-08-14 |
| GPT-5.6 Terra | 7/30 | $0.1224 | $0.0175 | invoice | 2026-08-13 |
| Granite 4.1 30B | 26/30 | — | — | no bill | 2026-08-13 |
| Grok 4.5 | 2/30 | $0.3050 | $0.1525 | invoice | 2026-08-13 – 2026-08-14 |
| Kimi K3 | 22/30 | $2.2738 | $0.1034 | invoice | 2026-08-13 – 2026-08-14 |
| Nemotron 3 Nano 30B | 26/30 | — | — | no bill | 2026-08-13 |
| Phi-4 14B | 24/30 | — | — | no bill | 2026-08-13 |
| Qwen3 8B | 41/60 | — | — | no bill | 2026-08-13 – 2026-08-14 |
| Qwen3.6 27B (GGUF Q4_K_M build) | 21/30 | — | — | no bill | 2026-08-13 |
| Qwen3.8 Max | 14/30 | $1.4978 | $0.1070 | invoice | 2026-08-13 – 2026-08-14 |

## Documentation chore cut

| model | completed | spend | $/completed task | basis | date |
|---|---|---|---|---|---|
| claude-fable-5 | 29/75 | — | — | rate not confirmed | 2026-08-13 – 2026-08-14 |
| claude-haiku-4-5 | 25/25 | $0.0310 | $0.0012 | invoice | 2026-08-14 |
| claude-opus-4-8 | 75/75 | $0.6109 | $0.0081 | invoice | 2026-08-13 – 2026-08-14 |
| claude-opus-5 | 5/25 | $0.5727 | — | withdrawn | 2026-08-14 |
| claude-sonnet-5 | 25/25 | $0.0963 | $0.0039 | invoice | 2026-08-14 |
| DeepSeek V4 Flash (0731) | 25/25 | $0.0101 | $0.0004 | invoice | 2026-08-13 |
| DeepSeek V4 Pro | 23/25 | $0.0735 | $0.0032 | invoice | 2026-08-13 |
| Devstral | 25/25 | — | — | no bill | 2026-08-14 |
| Gemini 3.1 Pro (preview) | 25/25 | $0.3393 | $0.0136 | invoice | 2026-08-13 |
| Gemini 3.6 Flash | 25/25 | $0.2601 | $0.0104 | invoice | 2026-08-13 |
| Gemma 4 31B | 25/25 | — | — | no bill | 2026-08-13 |
| GLM 4.7 Flash | 24/25 | — | — | no bill | 2026-08-13 |
| GLM 5.2 | 25/25 | $0.0385 | $0.0015 | invoice | 2026-08-13 – 2026-08-14 |
| GPT-5.6 Luna | 25/25 | $0.0050 | $0.0002 | invoice | 2026-08-13 – 2026-08-14 |
| GPT-5.6 Sol | 25/25 | $0.1853 | $0.0074 | invoice | 2026-08-13 – 2026-08-14 |
| GPT-5.6 Terra | 25/25 | $0.0300 | $0.0012 | invoice | 2026-08-13 |
| Granite 4.1 30B | 24/25 | — | — | no bill | 2026-08-13 |
| Grok 4.5 | 25/25 | $0.0736 | $0.0029 | invoice | 2026-08-13 – 2026-08-14 |
| Kimi K3 | 9/25 | $0.3304 | — | withdrawn | 2026-08-13 – 2026-08-14 |
| Nemotron 3 Nano 30B | 25/25 | — | — | no bill | 2026-08-13 |
| Phi-4 14B | 23/25 | — | — | no bill | 2026-08-13 |
| Qwen3 8B | 41/50 | — | — | no bill | 2026-08-13 – 2026-08-14 |
| Qwen3.6 27B (GGUF Q4_K_M build) | 25/25 | — | — | no bill | 2026-08-13 |
| Qwen3.8 Max | 21/25 | $0.2726 | $0.0130 | invoice | 2026-08-13 – 2026-08-14 |

## Known issues on this page

Each row is one issue: what it touches, what happened, and how it is shown.

| what | what happened | how it is shown |
|---|---|---|
| DeepSeek V4 Flash, compliance-control run, 2026-08-28 | A $0.0037 row landed on the wrong route and was never part of the scored total. | Left out, not corrected. |
| Kimi K3, documentation chore cut, cost per task | A scoring bug corrupted this cell's pass count, and no corrected count is available. | Withdrawn, not corrected; no figure printed. |
| claude-opus-5, documentation chore cut, cost per task | A scoring bug corrupted this cell's pass count, and no corrected count is available. | Withdrawn, not corrected; no figure printed. |
| DeepSeek V4 Flash, code cut, spend | 1 of 100 rows has no invoice entry, so its spend is not counted and this cell understates. | Uncounted, not estimated; the invoice covers 99 of 100 rows. |
| Kimi K3, review format cut, spend | 1 of 30 rows has no invoice entry, so its spend is not counted and this cell understates. | Uncounted, not estimated; the invoice covers 29 of 30 rows. |
| Long-context replicate run, 2026-08-28 | First published at $61.29, then at an old Sonnet rate; on the invoice basis it is $38.41. The earlier $58.51 was an upper bound. | Repriced. |
| Long-context Haiku arm, 2026-08-01 | The provider billed the Haiku arm at twice this day's own run log, likely a doubly executed arm. | Billed figure printed, not corrected. |
| Anthropic-path rows, every cut | An 8,192-token output cap was sent on Anthropic calls only; other providers got no limit. | 930 of 5,425 rows are withheld: every row of a model once any one of its rows hit the cap. |
| Anthropic-path rows, capped spend | The withheld rows still cost money, not shown in any table: Haiku $4.4467, Opus 5 $33.7654, Sonnet 5 $8.8167. | $47.0288 total, all on an invoiced run; withheld, not shown elsewhere. |
| claude-fable-5, every cut | The provider billed $12.9985 for this model, but the implied rate is not round, so we cannot confirm it against an invoice. | Every cut prints "rate not confirmed"; the implied $2.5591 input and $49.9214 output per Mtok are not printed as rates. |
| Claude runs, 2026-08-28 | The invoice for that date totals $25.4025 across every Claude run that day, $2.6393 more than these rows' own $22.7631 of token supplements. | The invoice covers several runs at once, so no dollar figure is moved between rows. |
| claude-haiku-4-5, code cut, cost per task | The measured count carries a scoring bug, but a corrected count exists, so the cell reprices instead of being withdrawn. | Measured 98/100, corrected 99/100; cost is spend divided by 99 = $0.0211, not $0.0213. |
| claude-opus-4-8, code cut, cost per task | The measured count carries a scoring bug, but a corrected count exists, so the cell reprices instead of being withdrawn. | Measured 286/300, corrected 296/300; cost is spend divided by 296 = $0.0649, not $0.0672. |
| claude-opus-5, code cut, cost per task | The measured count carries a scoring bug, but a corrected count exists, so the cell reprices instead of being withdrawn. | Measured 96/100, corrected 98/100; cost is spend divided by 98 = $0.1534, not $0.1566. |
| DeepSeek V4 Flash, code cut, cost per task | The measured count carries a scoring bug, but a corrected count exists, so the cell reprices instead of being withdrawn. | Measured 97/100, corrected 98/100; cost is spend divided by 98 = $0.0019, not $0.0020. |
| Devstral, code cut, accuracy | One check in the scoring rule moves for this model on one fixture, the same scoring bug as the withdrawn cell above. | Printed as measured, 92/100 [0.85, 0.96]; a re-score gives 94/100 [0.88, 0.97], not applied to the count. Every move is upward. |
| Nemotron 3 Nano 30B, code cut, accuracy | One check in the scoring rule moves for this model on one fixture, the same scoring bug as the withdrawn cell above. | Printed as measured, 92/100 [0.85, 0.96]; a re-score gives 95/100 [0.89, 0.98], not applied to the count. Every move is upward. |
| Phi-4 14B, code cut, accuracy | One check in the scoring rule moves for this model on one fixture, the same scoring bug as the withdrawn cell above. | Printed as measured, 94/100 [0.88, 0.97]; a re-score gives 97/100 [0.92, 0.99], not applied to the count. Every move is upward. |
| Qwen3 8B, code cut, accuracy | One check in the scoring rule moves for this model on one fixture, the same scoring bug as the withdrawn cell above. | Printed as measured, 183/200 [0.87, 0.95]; a re-score gives 187/200 [0.89, 0.96], not applied to the count. Every move is upward. |

## Long-context and disclosure runs

These use a different instrument from the coding cuts above. They probe how models handle very long inputs and how they behave under pressure to disclose or withhold. They are never pooled with the coding cuts. There is one row per run, not per model, because the runs measure different things at different panel sizes.

The short labels in the descriptions below — neutral, instructed, compliance-control, authority — name the pressure a run applied, not a metric. Spend here is the actual billing for the row, never a catalog upper bound.

| date | what ran | basis | spend | correction |
|---|---|---|---|---|
| 2026-08-01 | Three frontier Claude models (Opus 5, Sonnet 5, Haiku 4.5) against a graded context ladder, top rung about 394K tokens, 48 rounds. | invoice | $12.7071 | First published at $13.89; refitting to $2/$10 per Mtok gave Sonnet $3.3547, down from $5.03. Once the invoice posted, that became this row's spend. |
| 2026-08-25 | Compliance-control surfacing arm, authority variant: Haiku 4.5 at 32K, Sonnet 5 at 32K and 384K, stopped when it hit a spending cap. The two DeepSeek models never ran. | invoice | $4.6920 | An old Sonnet rate, the same one fixed on the 2026-08-01 row, moved this total from $7.0034 to $4.6920. |
| 2026-08-28 | DeepSeek V4 Flash re-run on a pinned route: neutral, instructed, and compliance-control arms at default and double budget, summed over 30 rows. | invoice | $0.3976 | The default budget truncated the instructed and compliance-control cells; doubling it on the first rung recovered usable rounds. |
| 2026-08-28 | Compliance-control panel: four non-Opus models plus Opus 5, run last under its own cap. A fifth model's single row landed on the wrong route and was excluded. | invoice + estimate, shared date | $11.3862 | $11.3862 is the four models' own invoiced total, $5.6419, plus Opus at the published rate, $5.744375. The excluded row was $0.0037. A separate published piece prints $17.1257 on a different basis; neither figure is being corrected. |
| 2026-08-28 | Confirmatory replicate of the neutral and instructed arms, eight-model panel, fresh corpus. | invoice + estimate, shared date | $38.4090 | $21.3902 is the OpenRouter models' own invoiced total. An old Sonnet rate sums the full panel to $58.5087, but that leans on catalog rates and is only an upper bound. This row's spend is that invoiced total plus the Claude models at the corrected rate: $38.4090, shown as $38.41. It reads about a cent under the earlier $61.29, which summed pre-rounded cells, one rounded up from $10.6336 to $10.64. Some retry spend was never recorded, so this understates the run's real total. Cell figures were amended 2026-08-31 after review; costs were unaffected. |
