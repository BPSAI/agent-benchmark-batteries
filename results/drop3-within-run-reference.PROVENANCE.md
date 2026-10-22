# Provenance: drop3-within-run-reference.csv

**Status: complete. Two models (arms), 3 rounds each.** Arm B ran after arm A's model was unloaded, on the same host and the same day.

- Date: 2026-10-22 (UTC)
- Host GPU: NVIDIA GeForce RTX 5090 (32 GB)
- Ollama version: 0.32.4
- Dispatch: local Ollama chat endpoint, non-streaming, fresh stateless
  conversation per completion, `system_prompt` as system and `input_prompt`
  as user. All 30 fixtures in this repo, 3 rounds per fixture (one round
  completed before the next began), 90 completions per model, 180 total.
- Sampling: no options were sent, so the model's own defaults applied
  (arm A: temperature 1, top_k 64, top_p 0.95 from the model's own
  parameters; arm B: the server's built-in defaults, since the model
  declares only stop tokens). Server-side context: 32768 tokens for arm A,
  16384 for arm B.
- Scorer: `tools/score_completion.py` (tests: `tools/test_score_completion.py`),
  at commit 6962531. Runner: `tools/run_local_battery.py`.
- No API call was made. Every completion came from a model running locally.
- Raw completions are not committed; only the five-column rows are.

| model_id | Ollama digest | rounds | wall time |
|---|---|---|---|
| `gemma4:31b` | `6316f0629137b426c9d9b853ffc4c8209589f30ee39aebede6285096c0ff47e7` | 3 | 3050 s |
| `phi4:14b` | `ac896e5b8b34a1f4efa7b14d7520725140d5512484457fab45d2a4ea14c69dba` | 3 | 535 s |
