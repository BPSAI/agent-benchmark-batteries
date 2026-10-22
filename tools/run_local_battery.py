"""Run the fixtures against one local Ollama model, N rounds, and write raw + scored rows.

usage: run_local_battery.py MODEL_ID ROUNDS RAW_DIR ROWS_CSV
Stateless chat per completion (system_prompt as system, input_prompt as user),
no sampling options sent, so the model's own defaults apply. Raw completions
go to RAW_DIR only; ROWS_CSV receives the five-column rows.
"""
from __future__ import annotations

import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

from score_completion import score

ROOT = Path(__file__).resolve().parent.parent


def chat(model: str, system: str, user: str) -> str:
    body = json.dumps({"model": model, "stream": False, "messages": [
        {"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat", body,
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as resp:
        return json.load(resp)["message"]["content"]


def main(model: str, rounds: int, raw_dir: Path, rows_csv: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    fixtures = [json.loads(p.read_text()) for p in sorted((ROOT / "fixtures").rglob("*.json"))]
    start = time.time()
    with rows_csv.open("a", newline="") as out:
        w = csv.writer(out)
        for rnd in range(1, rounds + 1):
            for fx in fixtures:
                path = raw_dir / f"r{rnd}--{fx['id']}.json"
                if path.exists():
                    continue
                text = chat(model, fx["system_prompt"], fx["input_prompt"])
                outcome = score(text, fx["expected_shape"])
                path.write_text(json.dumps({"completion": text, "outcome": outcome}))
                m = fx["metadata"]
                w.writerow([model, fx["id"], outcome, m["format_variant"], m["base_task_id"]])
                out.flush()
            print(f"round {rnd} done at {time.time() - start:.0f}s", flush=True)
    print(f"total wall {time.time() - start:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
