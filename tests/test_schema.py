import json

import pytest

from spce.checklist import KEYS
from spce.schema import InvalidOutput, extract_json, parse_prediction


def _full(present="no", **over):
    items = {k: {"present": present, "evidence": "e"} for k in KEYS}
    items.update(over)
    return {"items": items, "notable_points": ["a", "b"]}


def test_parse_valid():
    p = parse_prediction(json.dumps(_full(scaffolding={"present": "yes", "evidence": "pipes"})))
    assert p.items["scaffolding"] == "yes"
    assert all(p.items[k] == "no" for k in KEYS if k != "scaffolding")
    assert p.evidence["scaffolding"] == "pipes"
    assert p.notable_points == ["a", "b"]


def test_parse_accepts_bool_and_bare_string():
    d = _full()
    d["items"]["workers"] = True
    d["items"]["signage"] = "UNCLEAR"
    p = parse_prediction(json.dumps(d))
    assert p.items["workers"] == "yes"
    assert p.items["signage"] == "unclear"


def test_parse_strips_code_fence_and_prose():
    text = "はい、結果です。\n```json\n" + json.dumps(_full()) + "\n```\n以上です。"
    assert parse_prediction(text).items["workers"] == "no"


def test_missing_item_is_invalid():
    d = _full()
    del d["items"]["overhead_lines"]
    with pytest.raises(InvalidOutput):
        parse_prediction(json.dumps(d))


def test_bad_value_is_invalid():
    d = _full()
    d["items"]["workers"] = {"present": "maybe"}
    with pytest.raises(InvalidOutput):
        parse_prediction(json.dumps(d))


def test_not_json_is_invalid():
    with pytest.raises(InvalidOutput):
        parse_prediction("{'items': nope")
    with pytest.raises(InvalidOutput):
        extract_json("no braces here")


def test_notable_points_capped_and_stringified():
    d = _full()
    d["notable_points"] = list(range(20))
    p = parse_prediction(json.dumps(d))
    assert len(p.notable_points) == 10 and p.notable_points[0] == "0"
