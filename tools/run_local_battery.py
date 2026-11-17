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

One RAW_DIR is one run. RAW_DIR/run.manifest (JSON) pins the model panel, sampling
options, scorer and each model's weights digest on first use; a later
invocation that changes any of them is refused, so a CSV rebuilt from RAW_DIR
is always a single interleaved run. The served model id must match the
requested one, or the run stops before anything is written for that cell.
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
RUN_MANIFEST = "run.manifest"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\Z")
TOOLS = Path(__file__).resolve().parent
# The scorer and every local module it imports: a change to any of them is a
# different grader. A test parses score_completion.py's imports to keep this
# list complete.
SCORER_FILES = ("score_completion.py", "shape_rules.py")


def _files_sha256(names) -> str:
    h = hashlib.sha256()
    for name in sorted(names):
        h.update(name.encode() + b"\0" + (TOOLS / name).read_bytes() + b"\0")
    return h.hexdigest()


SCORER_SHA256 = _files_sha256(SCORER_FILES)
RUNNER_SHA256 = _files_sha256(("run_local_battery.py",))
DEFAULT_REGISTRY = "registry.ollama.ai/"


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

    def digest(self, model: str) -> str:
        """The local weights' digest for this tag, from /api/tags."""
        req = urllib.request.Request(HOST + "/api/tags")
        with urllib.request.urlopen(req, timeout=60) as resp:
            tags = json.load(resp).get("models", [])
        want = _normalize_name(model)
        for t in tags:
            if want in (_normalize_name(t.get("name", "")), _normalize_name(t.get("model", ""))):
                return t.get("digest", "")
        sys.exit(f"refusing: {model!r} is not in the local model list")

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
    keys = ("id", "system_prompt", "input_prompt", "expected_shape", "metadata")
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


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def _normalize_name(name: str) -> str:
    """Ollama's own name rules: the default registry and `library/` namespace
    are implied, names compare case-insensitively, and a missing tag is
    `:latest`."""
    n = name.strip().lower()
    if n.startswith(DEFAULT_REGISTRY):
        n = n[len(DEFAULT_REGISTRY):]
    if n.startswith("library/"):
        n = n[len("library/"):]
    last = n.rsplit("/", 1)[-1]
    return n if ":" in last else n + ":latest"


def _same_model(requested: str, served: str) -> bool:
    """Ollama echoes the requested id, so this mainly catches a proxy that
    rewrites it. The weights digest, re-read every round, is what pins the
    weights."""
    return _normalize_name(requested) == _normalize_name(served)


def _raw_files(raw_dir: Path) -> list[Path]:
    return list(raw_dir.glob("*.json"))


def _check_run(raw_dir: Path, run_manifest: dict) -> None:
    """One RAW_DIR is one run: the panel, options, scorer and model digests are
    pinned on first use. Arms added later were never interleaved with the
    first ones, and a tag whose weights changed is a different arm."""
    path = raw_dir / RUN_MANIFEST
    if not path.exists():
        if _raw_files(raw_dir):
            sys.exit(
                f"refusing: {raw_dir} holds raw files but no {RUN_MANIFEST}; "
                "start a fresh RAW_DIR"
            )
        _write_atomic(path, json.dumps(run_manifest, indent=1, sort_keys=True))
        return
    stored = json.loads(path.read_text())
    for field in (
        "models",
        "options",
        "scorer_sha256",
        "runner_sha256",
        "fixture_ids",
        "model_digests",
    ):
        if stored.get(field) != run_manifest[field]:
            what = "digest" if field == "model_digests" else field
            sys.exit(
                f"refusing to resume: run {what} differs from {path.name} "
                f"({stored.get(field)!r} != {run_manifest[field]!r}); "
                "start a fresh RAW_DIR"
            )


def rebuild_csv(raw_dir: Path, rows_csv: Path, models) -> None:
    """Rewrite rows_csv from every raw file in raw_dir (sorted, atomic).
    A raw file whose arm is outside the run's panel is refused, not mixed in."""
    raws = [json.loads(p.read_text()) for p in _raw_files(raw_dir)]
    foreign = sorted({r["requested_model"] for r in raws} - set(models))
    if foreign:
        sys.exit(f"refusing: {raw_dir} holds raw files for arms outside this run: {foreign}")
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
        tuple(json.loads(p.read_text())["row"][:2]) for p in _raw_files(raw_dir)
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
    digests = {m: client.digest(m) for m in models}
    _check_run(
        raw_dir,
        {
            "models": list(models),
            "options": options,
            "scorer_sha256": SCORER_SHA256,
            "runner_sha256": RUNNER_SHA256,
            "fixture_ids": sorted(fx["id"] for fx in fixtures),
            "model_digests": digests,
            "started_at_utc": _now(),
        },
    )
    shows = {m: client.show(m) for m in models}
    start = time.time()
    for rnd in range(1, rounds + 1):
        now = {m: client.digest(m) for m in models}
        if now != digests:
            sys.exit(
                f"refusing: model weights digest changed during the run "
                f"({digests!r} -> {now!r}); start a fresh RAW_DIR"
            )
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
                if not _same_model(model, reply["served_model"]):
                    sys.exit(
                        f"refusing: requested {model!r} but the server answered as "
                        f"{reply['served_model']!r}; nothing written for this cell"
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
                            "model_digest": digests[model],
                            "completed_at_utc": _now(),
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
                rebuild_csv(raw_dir, rows_csv, models)
        print(f"round {rnd} done at {time.time() - start:.0f}s", flush=True)
    if {m: client.digest(m) for m in models} != digests:
        sys.exit(
            "refusing: model weights digest changed during the last round; "
            "start a fresh RAW_DIR"
        )
    rebuild_csv(raw_dir, rows_csv, models)
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
