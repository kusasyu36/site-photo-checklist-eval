"""評価の実行。

例:
  python -m spce.run_eval --condition bare   --trial 1
  python -m spce.run_eval --condition hinted --trial 1
  python -m spce.run_eval --backend mock --condition bare --out /tmp/x.jsonl

1枚ごとに {photo_id, condition, trial, status, items, evidence, notable_points, error, seconds} を
JSONL に追記する。途中で落ちても、済んだ分は残る。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .data import ROOT, load_manifest, image_path, download_images
from .prompts import CONDITIONS, build_prompt
from .schema import InvalidOutput, parse_prediction
from .vlm import ClaudeCLIBackend, MockBackend, VLMError


def run(manifest: list[dict], condition: str, trial: int, backend, out_path: Path, log=print) -> list[dict]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    done.add(json.loads(line)["photo_id"])
    records = []
    with open(out_path, "a", encoding="utf-8") as f:
        for m in manifest:
            pid = m["photo_id"]
            if pid in done:
                continue
            prompt = build_prompt(str(image_path(pid)), condition)
            t0 = time.time()
            rec = {"photo_id": pid, "condition": condition, "trial": trial}
            text = ""
            try:
                text = backend.complete(prompt)
                pred = parse_prediction(text)
                rec.update(status="ok", **pred.to_dict())
            except InvalidOutput as e:
                rec.update(status="format_invalid", error=str(e), items={}, raw=str(text)[:500])
            except VLMError as e:
                rec.update(status="llm_error", error=str(e), items={})
            rec["seconds"] = round(time.time() - t0, 1)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            records.append(rec)
            log(f"{pid} {condition} t{trial}: {rec['status']} ({rec['seconds']}s)")
    return records


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", choices=CONDITIONS, required=True)
    ap.add_argument("--trial", type=int, default=1)
    ap.add_argument("--backend", choices=("claude", "mock"), default="claude")
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    manifest = load_manifest()
    if args.limit:
        manifest = manifest[: args.limit]
    if args.backend == "claude":
        download_images(manifest)
    backend = ClaudeCLIBackend(model=args.model) if args.backend == "claude" else MockBackend()
    out = args.out or ROOT / "results" / f"pred_{args.condition}_t{args.trial}.jsonl"
    run(manifest, args.condition, args.trial, backend, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
