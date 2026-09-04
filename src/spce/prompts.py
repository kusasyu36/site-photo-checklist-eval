"""プロンプト構築。

条件A (bare):  項目名と定義だけを渡す。
条件B (hinted): 加えて各項目に「確認観点」（現場側の判断基準を言語化したもの）を渡す。
AとBの差が「専門家の観点を入れると何が変わるか」の測定になる。
"""
from __future__ import annotations

from .checklist import ITEMS

CONDITIONS = ("bare", "hinted")


def build_prompt(image_path: str, condition: str) -> str:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition: {condition}")
    lines = [
        f"次の画像ファイルを Read ツールで開いて内容を確認してください: {image_path}",
        "",
        "あなたは工事現場の写真を点検チェックリストに照らして確認する担当者です。",
        "写真に写っているものだけから判断し、写っていないものを推測で「はい」にしないでください。",
        "判断できないときは「不明」を選んでください。",
        "",
        "## チェック項目",
    ]
    for it in ITEMS:
        lines.append(f"- {it.key}（{it.label_ja}）: {it.definition}")
        if condition == "hinted":
            lines.append(f"  確認観点: {it.hint}")
    lines += [
        "",
        "## 出力形式",
        "以下のJSONだけを出力してください。説明文やコードフェンスは付けないでください。",
        'present は "yes" / "no" / "unclear" のいずれか。evidence は判断の根拠を写真の中の見えるもので1文。',
        "notable_points は、現地で追加確認すべき点や見落としやすい点を、写真に基づいて最大5件。",
        "",
        "{",
        '  "items": {',
    ]
    keys = [it.key for it in ITEMS]
    for i, k in enumerate(keys):
        comma = "," if i < len(keys) - 1 else ""
        lines.append(f'    "{k}": {{"present": "yes|no|unclear", "evidence": "..."}}{comma}')
    lines += [
        "  },",
        '  "notable_points": ["...", "..."]',
        "}",
    ]
    return "\n".join(lines)
