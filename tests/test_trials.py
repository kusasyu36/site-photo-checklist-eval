"""試行間の集計（Mock で完結）。"""
import json

from spce.checklist import KEYS
from spce.trials import flips, summarize


def _rec(pid, cond, trial, value):
    return {"photo_id": pid, "condition": cond, "trial": trial, "status": "ok", "items": {k: value for k in KEYS}}


def test_flips_counts_cells_that_change_between_trials():
    labels = {"p01": {k: 1 for k in KEYS}}
    trials = {1: [_rec("p01", "bare", 1, "yes")], 2: [_rec("p01", "bare", 2, "no")]}
    changed, total, per_item = flips(trials, labels)
    assert (changed, total) == (len(KEYS), len(KEYS))
    trials[2] = [_rec("p01", "bare", 2, "yes")]
    assert flips(trials, labels)[0] == 0


def test_summarize_reports_mean_and_range(tmp_path):
    labels = {"p01": {k: 1 for k in KEYS}}
    for t, v in ((1, "yes"), (2, "no")):
        (tmp_path / f"pred_bare_t{t}.jsonl").write_text(json.dumps(_rec("p01", "bare", t, v)) + "\n", encoding="utf-8")
    md, js = summarize(tmp_path, labels)
    s = js["bare"]["summary"]
    assert s["accuracy"]["min"] == 0.0 and s["accuracy"]["max"] == 1.0 and s["accuracy"]["mean"] == 0.5
    assert s["flips"]["changed"] == len(KEYS)
    assert "bare" in md and "0.500" in md
