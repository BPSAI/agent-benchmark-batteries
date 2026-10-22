# Provenance: drop3-local-protocol-demo.csv

repetitions: 3

**Status: a protocol demonstration, not a within-run comparison and not a
reference comparison.** Two local models, 30 public fixtures, 3 rounds each:
180 rows, 60 cells, n = 3 per cell. The rows show that the protocol and the
five-column shape work end to end on this repo's own fixtures. No claim about
either model rests on them.

## Rules of the within-run kit these rows did NOT meet

See [`docs/within-run-comparison.md`](../docs/within-run-comparison.md).

- **Arms were not interleaved by round.** Arm A ran to completion (all 3
  rounds) before arm B started, so model and run order are confounded.
- **Context differed.** Server-side context was 32768 tokens for arm A and
  16384 for arm B.
- **Sampling was each model's own default, and the two defaults differ.**
  No sampling options were sent. Arm A: temperature 1, top_k 64, top_p 0.95
  (from the model's own parameters). Arm B: the server's built-in defaults,
  because the model declares only stop tokens.
- **The served model id was never captured.** Only the requested id and the
  Ollama digest below were recorded, so requested-versus-served was not
  checked on any row.

## What the rows do show

Every one of the 180 rows is `pass`. The battery did not separate the two
arms. That is a finding about the fixtures' discriminating power under the
substring/shape scorer (these 30 fixtures, scored this way, are easy to
pass), not about either model. With zero variance across base tasks there is
no interval to compute and no direction to claim; see the saturated-set row
of the reporting table in the kit.

## Run facts

- Date: 2026-10-22 (UTC)
- Host GPU: NVIDIA GeForce RTX 5090 (32 GB)
- Ollama version: 0.32.4
- Dispatch: local Ollama chat endpoint, non-streaming, fresh stateless
  conversation per completion, `system_prompt` as system and `input_prompt`
  as user. All 30 fixtures, 3 rounds per fixture (one round completed before
  the next began), 90 completions per model, 180 total.
- Scorer: `tools/score_completion.py` (tests: `tools/test_score_completion.py`),
  at commit 6962531. The runner used for these rows was an earlier version of
  `tools/run_local_battery.py`; the current runner interleaves arms and
  records requested id, served id, context and sampling in every raw file.
- No API call was made. Every completion came from a model running locally.
- Raw completions are not committed; only the five-column rows are.

| model_id | Ollama digest | rounds | wall time |
|---|---|---|---|
| `gemma4:31b` | `6316f0629137b426c9d9b853ffc4c8209589f30ee39aebede6285096c0ff47e7` | 3 | 3050 s |
| `phi4:14b` | `ac896e5b8b34a1f4efa7b14d7520725140d5512484457fab45d2a4ea14c69dba` | 3 | 535 s |
