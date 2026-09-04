"""結果の集計とレポート出力。

  python -m spce.report results/pred_bare_t1.jsonl results/pred_hinted_t1.jsonl ...

条件ごとに全試行をまとめて採点し、Markdown の要約と JSON を results/summary.* に書く。
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from .checklist import BY_KEY, KEYS
from .data import ROOT, load_labels, read_jsonl
from .failures import classify
from .metrics import score_run


def fmt(x: float | None) -> str:
    return "-" if x is None else f"{x:.2f}"


def summarize(paths: list[Path], labels: dict[str, dict]) -> tuple[str, dict]:
    by_cond: dict[str, list[dict]] = defaultdict(list)
    for p in paths:
        for r in read_jsonl(p):
            by_cond[r["condition"]].append(r)

    md = ["# 評価結果", ""]
    js: dict = {}
    md.append("## 条件別の全体指標（全項目を合算）")
    md.append("")
    md.append("| 条件 | 写真×試行 | 採点項目数 | precision | recall | F1 | accuracy | 全項目一致率 | 不明の回数 | 形式不正 | 呼び出し失敗 |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for cond, recs in by_cond.items():
        s = score_run(recs, labels)
        o = s.overall
        md.append(
            f"| {cond} | {s.n_photos} | {o.n} | {fmt(o.precision)} | {fmt(o.recall)} | {fmt(o.f1)} | {fmt(o.accuracy)} "
            f"| {fmt(s.exact_match_rate)} | {o.abstain} | {s.format_invalid} | {s.llm_error} |"
        )
        js[cond] = {
            "n_records": s.n_photos, "n_scored": o.n,
            "precision": o.precision, "recall": o.recall, "f1": o.f1, "accuracy": o.accuracy,
            "exact_match_rate": s.exact_match_rate, "abstain": o.abstain,
            "format_invalid": s.format_invalid, "llm_error": s.llm_error,
            "per_item": {}, "failures": classify(recs, labels),
        }
        for k in KEYS:
            c = s.per_item[k]
            js[cond]["per_item"][k] = {
                "n": c.n, "tp": c.tp, "fp": c.fp, "fn": c.fn, "tn": c.tn, "abstain": c.abstain, "skipped": c.skipped,
                "precision": c.precision, "recall": c.recall, "f1": c.f1,
            }
    md.append("")

    md.append("## 項目別（recall / precision / 不明）")
    md.append("")
    conds = list(by_cond)
    head = "| 項目 | " + " | ".join(f"{c} R / P / 不明" for c in conds) + " | 採点数 |"
    md.append(head)
    md.append("|---|" + "---|" * (len(conds) + 1))
    for k in KEYS:
        cells = []
        n = 0
        for c in conds:
            it = js[c]["per_item"][k]
            cells.append(f"{fmt(it['recall'])} / {fmt(it['precision'])} / {it['abstain']}")
            n = it["n"]
        md.append(f"| {k}（{BY_KEY[k].label_ja}） | " + " | ".join(cells) + f" | {n} |")
    md.append("")

    md.append("## 失敗の型")
    md.append("")
    md.append("| 条件 | 見落とし(miss) | 誤検出(false_alarm) | 判定可能なのに不明 | 形式不正 | 呼び出し失敗 |")
    md.append("|---|---|---|---|---|---|")
    for c in conds:
        bt = js[c]["failures"]["by_type"]
        md.append(f"| {c} | {bt.get('miss',0)} | {bt.get('false_alarm',0)} | {bt.get('abstain_on_clear',0)} | {bt.get('format_invalid',0)} | {bt.get('llm_error',0)} |")
    md.append("")
    for c in conds:
        bi = js[c]["failures"]["by_item"]
        md.append(f"### {c}: 型ごとに多い項目")
        for t in ("miss", "false_alarm", "abstain_on_clear"):
            top = sorted(bi.get(t, {}).items(), key=lambda x: -x[1])[:4]
            if top:
                md.append(f"- {t}: " + ", ".join(f"{k} {v}" for k, v in top))
        md.append("")
    return "\n".join(md), js


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--out-md", type=Path, default=ROOT / "results" / "summary.md")
    ap.add_argument("--out-json", type=Path, default=ROOT / "results" / "summary.json")
    args = ap.parse_args(argv)
    labels = load_labels()
    md, js = summarize(args.paths, labels)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(md, encoding="utf-8")
    args.out_json.write_text(json.dumps(js, ensure_ascii=False, indent=1), encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
