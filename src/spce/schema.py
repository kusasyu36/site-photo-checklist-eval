"""VLM出力の検証。

VLMの返答は信用しない。JSONとして読めるか、全項目があるか、値が許された3値かを検査し、
不正なら InvalidOutput を投げる（呼び出し側が failure として記録する）。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .checklist import KEYS

ALLOWED = ("yes", "no", "unclear")


class InvalidOutput(ValueError):
    pass


@dataclass
class Prediction:
    items: dict[str, str]  # key -> yes/no/unclear
    evidence: dict[str, str] = field(default_factory=dict)
    notable_points: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"items": self.items, "evidence": self.evidence, "notable_points": self.notable_points}


_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def extract_json(text: str) -> str:
    """コードフェンスや前置きが混ざっていても、最初の {…} を取り出す。"""
    m = _FENCE.search(text)
    if m:
        text = m.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise InvalidOutput("no JSON object found")
    return text[start : end + 1]


def parse_prediction(text: str) -> Prediction:
    try:
        data = json.loads(extract_json(text))
    except json.JSONDecodeError as e:
        raise InvalidOutput(f"json decode: {e}") from e
    if not isinstance(data, dict) or not isinstance(data.get("items"), dict):
        raise InvalidOutput("missing 'items' object")
    raw = data["items"]
    items: dict[str, str] = {}
    evidence: dict[str, str] = {}
    for k in KEYS:
        if k not in raw:
            raise InvalidOutput(f"missing item: {k}")
        v = raw[k]
        if isinstance(v, dict):
            present = v.get("present")
            ev = v.get("evidence", "")
        else:
            present, ev = v, ""
        if isinstance(present, bool):
            present = "yes" if present else "no"
        if not isinstance(present, str) or present.lower() not in ALLOWED:
            raise InvalidOutput(f"bad value for {k}: {present!r}")
        items[k] = present.lower()
        evidence[k] = str(ev)[:300]
    notes = data.get("notable_points", [])
    if not isinstance(notes, list):
        raise InvalidOutput("notable_points must be a list")
    return Prediction(items=items, evidence=evidence, notable_points=[str(n)[:300] for n in notes][:10])
