"""失敗の型の分類。

「精度が何%か」だけでは直し方が決まらない。どの型の失敗が、どの項目で起きたかを数えて、
プロンプト（観点の追加）で直すのか、別の部品（物体検出・高解像度化）を足すのか、
人の確認に回すのかを切り分けるための集計。
"""
from __future__ import annotations

from collections import Counter

from .checklist import KEYS

FAILURE_TYPES = (
    "format_invalid",   # JSONとして読めない・項目が欠ける
    "llm_error",        # 呼び出し失敗（タイムアウト等）
    "false_alarm",      # 写っていないものを「はい」と言った
    "miss",             # 写っているものを「いいえ」と言った
    "abstain_on_clear", # 作者が判定できた項目で「不明」と答えた
)


def classify(records: list[dict], labels: dict[str, dict]) -> dict:
    """戻り値: {"by_type": Counter, "by_item": {type: Counter(item)}, "examples": [...]}"""
    by_type: Counter = Counter()
    by_item: dict[str, Counter] = {t: Counter() for t in FAILURE_TYPES}
    examples: list[dict] = []
    for r in records:
        pid = r["photo_id"]
        if r["status"] in ("format_invalid", "llm_error"):
            by_type[r["status"]] += 1
            examples.append({"photo_id": pid, "type": r["status"], "detail": r.get("error", "")[:200]})
            continue
        truth = labels[pid]
        for k in KEYS:
            t = truth.get(k, "?")
            p = r["items"].get(k, "unclear")
            if t == "?":
                continue
            if p == "unclear":
                by_type["abstain_on_clear"] += 1
                by_item["abstain_on_clear"][k] += 1
                continue
            if int(t) == 1 and p == "no":
                by_type["miss"] += 1
                by_item["miss"][k] += 1
                examples.append({"photo_id": pid, "type": "miss", "item": k, "evidence": r.get("evidence", {}).get(k, "")})
            elif int(t) == 0 and p == "yes":
                by_type["false_alarm"] += 1
                by_item["false_alarm"][k] += 1
                examples.append({"photo_id": pid, "type": "false_alarm", "item": k, "evidence": r.get("evidence", {}).get(k, "")})
    return {"by_type": dict(by_type), "by_item": {t: dict(c) for t, c in by_item.items()}, "examples": examples}
