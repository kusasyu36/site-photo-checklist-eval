"""プロンプト構築。

条件は3つ。README と同じ名前で呼ぶ。
  bare:   項目名と定義だけを渡す
  hinted: 加えて各項目に、作者が書いた仮の確認観点を渡す
  framed: bare に、写真に写っていなければ no とし範囲外の可能性は考えない、という判定規則を足す
bare と hinted の差は、確認観点を文章で足すと出力がどう変わるか。bare と framed の差は、判定規則を明示すると出力がどう変わるか。
プロンプトの文面は評価に使ったものをそのまま残している（結果の再現性のため変更しない）。
"""
from __future__ import annotations

from .checklist import ITEMS

CONDITIONS = ("bare", "hinted", "framed")


def build_prompt(image_path: str, condition: str) -> str:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition: {condition}")
    lines = [
        f"次の画像ファイルを Read ツールで開いて内容を確認してください: {image_path}",
        "",
        "あなたは工事現場の写真を点検チェックリストに照らして確認する担当者です。",
        "写真に写っているものだけから判断し、写っていないものを推測で「はい」にしないでください。",
        "判断できないときは「不明」を選んでください。",
    ]
    if condition == "framed":
        lines += [
            "",
            "## 判定の規則",
            "- この写真に写っているかどうかだけを答えます。写真の範囲外に存在する可能性は考えません。",
            "- 写真の中に見当たらなければ「いいえ」です。「不明」は、写ってはいるが何であるか判別できないときだけに使います。",
            "- 作業員が写っていなければ、ヘルメット未着用の作業員は「いいえ」です。",
        ]
    lines += [
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
