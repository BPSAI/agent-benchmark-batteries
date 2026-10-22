# Provenance: drop3-within-run-reference.csv

**Status: partial. Rows for the first model only; the second model is pending.**

- Date: 2026-10-22 (UTC)
- Host GPU: NVIDIA GeForce RTX 5090 (32 GB)
- Ollama version: 0.32.4
- Dispatch: local Ollama chat endpoint, non-streaming, fresh stateless
  conversation per completion, `system_prompt` as system and `input_prompt`
  as user. All 30 fixtures in this repo, 3 rounds per fixture (one round
  completed before the next began), 90 completions for this model.
- Sampling: no options were sent, so the model's own defaults applied
  (temperature 1, top_k 64, top_p 0.95 for the model below). The server
  loaded the model with a 32768-token context.
- Scorer: `tools/score_completion.py` (tests: `tools/test_score_completion.py`),
  at commit 6962531. Runner: `tools/run_local_battery.py`.
- No API call was made. Every completion came from a model running locally.
- Raw completions are not committed; only the five-column rows are.

| model_id | Ollama digest | rounds | wall time |
|---|---|---|---|
| `gemma4:31b` | `6316f0629137b426c9d9b853ffc4c8209589f30ee39aebede6285096c0ff47e7` | 3 | 3050 s |
