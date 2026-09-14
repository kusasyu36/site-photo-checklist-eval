"""試行ごとの集計と、試行間のばらつき。

  python -m spce.trials

results/pred_{condition}_t{N}.jsonl を全部読み、条件 × 試行ごとに採点して、
平均・最小・最大を results/trials.md と results/trials.json に書く。
同じ写真に対して、試行間で答えが変わったセルの数も数える（揺れの大きさ）。
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from .checklist import BY_KEY, KEYS
from .data import ROOT, load_labels, read_jsonl
from .failures import classify
from .metrics import score_run

CONDS = ("bare", "hinted", "framed")
METRICS = ("accuracy", "precision", "recall", "abstain", "miss", "false_alarm", "exact_match_rate")


def f(x, nd=2) -> str:
    return "-" if x is None else f"{x:.{nd}f}"


def load_trials(results: Path) -> dict[str, dict[int, list[dict]]]:
    out: dict[str, dict[int, list[dict]]] = defaultdict(dict)
    for p in sorted(results.glob("pred_*_t*.jsonl")):
        m = re.match(r"pred_(\w+)_t(\d+)\.jsonl$", p.name)
        if m:
            out[m.group(1)][int(m.group(2))] = read_jsonl(p)
    return out


def score_trial(recs: list[dict], labels: dict) -> dict:
    s = score_run(recs, labels)
    o = s.overall
    bt = classify(recs, labels)["by_type"]
    return {
        "n_records": s.n_photos, "accuracy": o.accuracy, "precision": o.precision, "recall": o.recall,
        "abstain": o.abstain, "miss": bt.get("miss", 0), "false_alarm": bt.get("false_alarm", 0),
        "exact_match_rate": s.exact_match_rate, "format_invalid": s.format_invalid, "llm_error": s.llm_error,
    }


def flips(trials: dict[int, list[dict]], labels: dict) -> tuple[int, int, dict[str, int]]:
    """採点対象のセルのうち、試行間で答え（yes/no/unclear）が1回でも変わったセルの数。"""
    by_photo: dict[str, list[dict]] = defaultdict(list)
    for recs in trials.values():
        for r in recs:
            if r["status"] == "ok":
                by_photo[r["photo_id"]].append(r["items"])
    changed = total = 0
    per_item: dict[str, int] = defaultdict(int)
    for pid, answers in by_photo.items():
        if len(answers) < 2:
            continue
        for k in KEYS:
            if labels[pid].get(k, "?") == "?":
                continue
            total += 1
            if len({a.get(k) for a in answers}) > 1:
                changed += 1
                per_item[k] += 1
    return changed, total, dict(per_item)


def summarize(results: Path, labels: dict) -> tuple[str, dict]:
    data = load_trials(results)
    js: dict = {}
    md = ["# 試行ごとの結果とばらつき", ""]
    md.append("同じ写真・同じプロンプト・同じモデルで繰り返したときに、数字がどれだけ揺れるかを見る。")
    md.append("")
    md.append("## 条件 × 試行")
    md.append("")
    md.append("| 条件 | 試行 | accuracy | precision | recall | 不明 | 見落とし | 誤検出 | 全項目一致率 | 形式不正 | 呼び出し失敗 |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in CONDS:
        if c not in data:
            continue
        js[c] = {"trials": {}, "summary": {}}
        for t in sorted(data[c]):
            r = score_trial(data[c][t], labels)
            js[c]["trials"][t] = r
            md.append(f"| {c} | {t} | {f(r['accuracy'], 3)} | {f(r['precision'])} | {f(r['recall'])} | {r['abstain']} | {r['miss']} | {r['false_alarm']} | {f(r['exact_match_rate'])} | {r['format_invalid']} | {r['llm_error']} |")
    md.append("")
    md.append("## 条件ごとの平均と範囲（最小〜最大）")
    md.append("")
    md.append("| 条件 | 試行数 | accuracy | 不明 | 見落とし | 誤検出 | 答えが試行間で変わったセル |")
    md.append("|---|---|---|---|---|---|---|")
    for c in CONDS:
        if c not in js:
            continue
        ts = list(js[c]["trials"].values())
        summ = {}
        for m in METRICS:
            vals = [x[m] for x in ts if x[m] is not None]
            summ[m] = {"mean": sum(vals) / len(vals), "min": min(vals), "max": max(vals)} if vals else {"mean": None, "min": None, "max": None}
        ch, tot, per_item = flips(data[c], labels)
        summ["flips"] = {"changed": ch, "total": tot, "per_item": per_item}
        js[c]["summary"] = summ
        a, u, mi, fa = summ["accuracy"], summ["abstain"], summ["miss"], summ["false_alarm"]
        top = ", ".join(f"{BY_KEY[k].label_ja} {v}" for k, v in sorted(per_item.items(), key=lambda x: -x[1])[:3])
        md.append(
            f"| {c} | {len(ts)} | {f(a['mean'], 3)}（{f(a['min'], 3)}〜{f(a['max'], 3)}） "
            f"| {u['mean']:.1f}（{u['min']}〜{u['max']}） | {mi['mean']:.1f}（{mi['min']}〜{mi['max']}） "
            f"| {fa['mean']:.1f}（{fa['min']}〜{fa['max']}） | {ch} / {tot}（多い項目: {top or 'なし'}） |"
        )
    md.append("")
    return "\n".join(md), js


def main(argv=None):
    results = ROOT / "results"
    md, js = summarize(results, load_labels())
    (results / "trials.md").write_text(md, encoding="utf-8")
    (results / "trials.json").write_text(json.dumps(js, ensure_ascii=False, indent=1), encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
