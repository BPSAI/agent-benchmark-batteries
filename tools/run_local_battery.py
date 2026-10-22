"""Run the fixtures against local Ollama models, N rounds, write raw + scored rows.

usage: run_local_battery.py ROUNDS RAW_DIR ROWS_CSV MODEL_ID [MODEL_ID ...]
       [--num-ctx N] [--temperature T]

Stateless chat per completion (system_prompt as system, input_prompt as user).
With more than one model the arms are interleaved: every round dispatches every
arm, fixture by fixture, so the arms share the same clock. Sampling options are
only sent when given on the command line; whatever was (or was not) sent is
recorded in each raw file, with the requested and the served model id.

RAW_DIR is the source of truth: each completion is written there atomically
(temp then rename) and ROWS_CSV is rebuilt from the raw files after every
completion, so an interruption can neither skip a completion nor leave a row
without its raw file. Raw completions stay in RAW_DIR; ROWS_CSV receives the
five-column rows only.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from score_completion import score

ROOT = Path(__file__).resolve().parent.parent
HOST = "http://127.0.0.1:11434"
COLUMNS = ["model_id", "fixture_id", "outcome", "format_variant", "base_task_id"]
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SCORER_SHA256 = hashlib.sha256(
    (Path(__file__).parent / "score_completion.py").read_bytes()
).hexdigest()


def _post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        HOST + path, json.dumps(payload).encode(), {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=1800) as resp:
        return json.load(resp)


class OllamaClient:
    def chat(self, model: str, system: str, user: str, options: dict) -> dict:
        body = {
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if options:
            body["options"] = options
        reply = _post("/api/chat", body)
        return {
            "content": reply["message"]["content"],
            "served_model": reply.get("model", ""),
        }

    def show(self, model: str) -> dict:
        info = _post("/api/show", {"model": model})
        return {
            "parameters": info.get("parameters", ""),
            "details": info.get("details", {}),
        }


def _slug(model: str) -> str:
    """Injective filename encoding of the exact model id (percent-encoding)."""
    return urllib.parse.quote(model, safe="")


def _raw_path(raw_dir: Path, rnd: int, model: str, fid: str) -> Path:
    return raw_dir / f"r{rnd}--{_slug(model)}--{fid}.json"


def _fixture_sha256(fx: dict) -> str:
    keys = ("id", "system_prompt", "input_prompt", "expected_shape")
    return hashlib.sha256(
        json.dumps({k: fx[k] for k in keys}, sort_keys=True).encode()
    ).hexdigest()


def _manifest(fx: dict, options: dict) -> dict:
    return {
        "fixture_sha256": _fixture_sha256(fx),
        "options": options,
        "scorer_sha256": SCORER_SHA256,
    }


def _check_existing(path: Path, model: str, manifest: dict) -> None:
    """Refuse to resume into a raw file made by a different id or a different run setup."""
    stored = json.loads(path.read_text())
    if stored.get("requested_model") != model:
        sys.exit(
            f"refusing: {path.name} holds requested_model "
            f"{stored.get('requested_model')!r}, not {model!r}"
        )
    old = stored.get("manifest", {})
    for field in ("fixture_sha256", "options", "scorer_sha256"):
        if old.get(field) != manifest[field]:
            sys.exit(
                f"refusing to resume: manifest field {field!r} differs from the stored "
                f"one in {path.name}"
            )


def _write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def rebuild_csv(raw_dir: Path, rows_csv: Path) -> None:
    """Rewrite rows_csv from every raw file in raw_dir (sorted, atomic)."""
    raws = [json.loads(p.read_text()) for p in raw_dir.glob("*.json")]
    raws.sort(key=lambda r: (r["requested_model"], r["round"], r["row"][1]))
    tmp = rows_csv.with_name(rows_csv.name + ".tmp")
    with tmp.open("w", newline="") as out:
        w = csv.writer(out, lineterminator="\n")
        w.writerow(COLUMNS)
        w.writerows(r["row"] for r in raws)
    os.replace(tmp, rows_csv)


def _guard_unbacked_csv(raw_dir: Path, rows_csv: Path) -> None:
    """Refuse when any existing CSV row has no raw file behind it (a rebuild would drop it)."""
    if not rows_csv.exists():
        return
    backed = Counter(
        tuple(json.loads(p.read_text())["row"][:2]) for p in raw_dir.glob("*.json")
    )
    have = Counter(
        (r["model_id"], r["fixture_id"]) for r in csv.DictReader(rows_csv.open())
    )
    missing = sorted(k for k, n in have.items() if n > backed[k])
    if missing:
        sys.exit(
            f"refusing: {rows_csv} has rows with no raw file in {raw_dir}: {missing[:10]}"
        )


def run(
    models, rounds, raw_dir: Path, rows_csv: Path, client, fixtures, options
) -> None:
    for fx in fixtures:
        if not SAFE_ID.match(fx["id"]):
            raise ValueError(f"unsafe fixture id {fx['id']!r}")
    raw_dir.mkdir(parents=True, exist_ok=True)
    _guard_unbacked_csv(raw_dir, rows_csv)
    shows = {m: client.show(m) for m in models}
    start = time.time()
    for rnd in range(1, rounds + 1):
        for fx in fixtures:
            for model in models:
                path = _raw_path(raw_dir, rnd, model, fx["id"])
                manifest = _manifest(fx, options)
                if path.exists():
                    _check_existing(path, model, manifest)
                    continue
                reply = client.chat(
                    model, fx["system_prompt"], fx["input_prompt"], options
                )
                outcome = score(reply["content"], fx["expected_shape"])
                meta = fx["metadata"]
                _write_atomic(
                    path,
                    json.dumps(
                        {
                            "round": rnd,
                            "requested_model": model,
                            "manifest": manifest,
                            "served_model": reply["served_model"],
                            "options": options,
                            "show": shows[model],
                            "completion": reply["content"],
                            "outcome": outcome,
                            "row": [
                                model,
                                fx["id"],
                                outcome,
                                meta["format_variant"],
                                meta["base_task_id"],
                            ],
                        }
                    ),
                )
                rebuild_csv(raw_dir, rows_csv)
        print(f"round {rnd} done at {time.time() - start:.0f}s", flush=True)
    rebuild_csv(raw_dir, rows_csv)
    print(f"total wall {time.time() - start:.0f}s", flush=True)


def _parse(argv: list[str]):
    options, pos, it = {}, [], iter(argv)
    for arg in it:
        if arg == "--num-ctx":
            options["num_ctx"] = int(next(it))
        elif arg == "--temperature":
            options["temperature"] = float(next(it))
        else:
            pos.append(arg)
    return int(pos[0]), Path(pos[1]), Path(pos[2]), pos[3:], options


if __name__ == "__main__":
    n, raw, csv_path, model_ids, opts = _parse(sys.argv[1:])
    fxs = [
        json.loads(p.read_text()) for p in sorted((ROOT / "fixtures").rglob("*.json"))
    ]
    run(model_ids, n, raw, csv_path, OllamaClient(), fxs, opts)
