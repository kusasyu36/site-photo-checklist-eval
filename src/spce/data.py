"""データの読み込みと画像取得。

画像はリポジトリに含めない。data/manifest.jsonl に Wikimedia Commons の URL・ライセンス・作者を置き、
download_images() で取得する。data/labels.jsonl は作者が付けた正解（1 / 0 / "?"）。
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .checklist import KEYS

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
IMAGES = DATA / "images"
UA = "site-photo-checklist-eval/0.1 (https://github.com/kusasyu36/site-photo-checklist-eval)"


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_manifest(path: Path = DATA / "manifest.jsonl") -> list[dict]:
    return read_jsonl(path)


def load_labels(path: Path = DATA / "labels.jsonl") -> dict[str, dict]:
    rows = read_jsonl(path)
    out: dict[str, dict] = {}
    for r in rows:
        pid = r["photo_id"]
        labels = {k: r["labels"][k] for k in KEYS}
        for k, v in labels.items():
            if v not in (0, 1, "?"):
                raise ValueError(f"{pid}.{k}: label must be 0/1/'?', got {v!r}")
        out[pid] = labels
    return out


def image_path(photo_id: str) -> Path:
    return IMAGES / f"{photo_id}.jpg"


def download_images(manifest: list[dict], dest: Path = IMAGES, force: bool = False) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    paths = []
    for m in manifest:
        p = dest / f"{m['photo_id']}.jpg"
        if force or not p.exists():
            subprocess.run(["curl", "-sSL", "-A", UA, "-o", str(p), m["image_url"]], check=True)
        paths.append(p)
    return paths
