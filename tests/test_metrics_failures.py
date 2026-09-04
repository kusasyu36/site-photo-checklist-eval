from spce.checklist import KEYS
from spce.failures import classify
from spce.metrics import Counts, score_one, score_run


def _truth(**over):
    t = {k: 0 for k in KEYS}
    t.update(over)
    return t


def _pred(**over):
    p = {k: "no" for k in KEYS}
    p.update(over)
    return p


def test_counts_math():
    c = Counts(tp=3, fp=1, fn=1, tn=5)
    assert c.precision == 0.75 and c.recall == 0.75 and abs(c.f1 - 0.75) < 1e-9
    assert c.accuracy == 0.8 and c.n == 10
    assert Counts().precision is None and Counts().f1 is None


def test_score_one_tp_fp_fn_tn_and_skip():
    truth = _truth(scaffolding=1, workers=1, signage="?")
    pred = _pred(scaffolding="yes", workers="no", water_or_mud="yes", signage="yes")
    per, ok = score_one(pred, truth)
    assert per["scaffolding"].tp == 1
    assert per["workers"].fn == 1
    assert per["water_or_mud"].fp == 1
    assert per["signage"].skipped == 1 and per["signage"].n == 0
    assert per["excavation"].tn == 1
    assert ok is False


def test_unclear_counts_as_abstain_and_as_negative():
    truth = _truth(scaffolding=1, workers=0)
    per, _ = score_one(_pred(scaffolding="unclear", workers="unclear"), truth)
    assert per["scaffolding"].abstain == 1 and per["scaffolding"].fn == 1
    assert per["workers"].abstain == 1 and per["workers"].tn == 1


def test_score_run_handles_error_records():
    labels = {"a": _truth(scaffolding=1), "b": _truth()}
    recs = [
        {"photo_id": "a", "status": "ok", "items": _pred(scaffolding="yes")},
        {"photo_id": "b", "status": "format_invalid", "items": {}, "error": "x"},
    ]
    s = score_run(recs, labels)
    assert s.format_invalid == 1 and s.n_photos == 2
    assert s.exact_match_rate == 0.5
    assert s.overall.tp == 1 and s.overall.n == len(KEYS)


def test_classify_failure_types():
    labels = {"a": _truth(scaffolding=1, workers=1, signage="?"), "b": _truth()}
    recs = [
        {"photo_id": "a", "status": "ok", "items": _pred(scaffolding="no", workers="unclear", excavation="yes", signage="yes"), "evidence": {}},
        {"photo_id": "b", "status": "llm_error", "items": {}, "error": "timeout"},
    ]
    f = classify(recs, labels)
    assert f["by_type"] == {"miss": 1, "abstain_on_clear": 1, "false_alarm": 1, "llm_error": 1}
    assert f["by_item"]["miss"] == {"scaffolding": 1}
    assert f["by_item"]["false_alarm"] == {"excavation": 1}
    # 正解が "?" の項目は、どう答えても失敗に数えない
    assert "signage" not in f["by_item"]["false_alarm"]
