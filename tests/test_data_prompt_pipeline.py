import json
import os

from spce.checklist import ITEMS, KEYS
from spce.data import load_labels, load_manifest
from spce.prompts import build_prompt
from spce.report import summarize
from spce.run_eval import run
from spce.vlm import MockBackend


def test_manifest_and_labels_are_consistent():
    manifest = load_manifest()
    labels = load_labels()
    ids = [m["photo_id"] for m in manifest]
    assert len(ids) == len(set(ids)) == 20
    assert set(ids) == set(labels)
    for m in manifest:
        assert m["image_url"].startswith(("https://upload.wikimedia.org/", "https://thumb.wikimedia.org/"))
        assert m["license"] and m["page_url"].startswith("https://commons.wikimedia.org/")
        assert "NC" not in m["license"] and "ND" not in m["license"]
    for pid, lab in labels.items():
        assert set(lab) == set(KEYS)
        # ヘルメット未着用は、作業員がいない写真では必ず 0
        if lab["workers"] == 0:
            assert lab["worker_no_helmet"] == 0, pid


def test_labels_leave_enough_scored_cells():
    labels = load_labels()
    scored = sum(1 for lab in labels.values() for v in lab.values() if v != "?")
    assert scored >= 0.8 * 20 * len(KEYS)


def test_prompt_contains_all_items_and_hints_only_when_hinted():
    bare = build_prompt("/x/p01.jpg", "bare")
    hinted = build_prompt("/x/p01.jpg", "hinted")
    for it in ITEMS:
        assert it.key in bare and it.key in hinted
        assert it.hint in hinted and it.hint not in bare
    assert "/x/p01.jpg" in bare
    assert "unclear" in bare


def test_mock_pipeline_end_to_end(tmp_path):
    manifest = load_manifest()[:4]
    out = tmp_path / "pred.jsonl"
    recs = run(manifest, "hinted", 1, MockBackend(), out, log=lambda *_: None)
    assert len(recs) == 4 and all(r["status"] == "ok" for r in recs)
    # 追記型: 再実行しても済んだ写真は飛ばす
    again = run(manifest, "hinted", 1, MockBackend(), out, log=lambda *_: None)
    assert again == []
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 4
    rec = json.loads(lines[0])
    assert set(rec["items"]) == set(KEYS) and rec["items"]["worker_no_helmet"] == "unclear"

    md, js = summarize([out], load_labels())
    assert "hinted" in js and js["hinted"]["n_records"] == 4
    assert "| hinted |" in md


def test_mock_invalid_output_is_recorded_not_raised(tmp_path, monkeypatch):
    monkeypatch.setenv("MOCK_INVALID", "1")
    out = tmp_path / "bad.jsonl"
    recs = run(load_manifest()[:2], "bare", 1, MockBackend(), out, log=lambda *_: None)
    assert [r["status"] for r in recs] == ["format_invalid", "format_invalid"]
    md, js = summarize([out], load_labels())
    assert js["bare"]["format_invalid"] == 2
