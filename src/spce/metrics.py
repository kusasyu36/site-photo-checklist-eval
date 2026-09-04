"""評価指標。

正解ラベルは 1 / 0 / "?"。"?" は作者が写真から判断できなかった項目で、採点から除外する。
予測の unclear は「答えなかった」として扱い、precision/recall では no と同じ扱いにしつつ、
abstain として別に数える（VLMが慎重すぎるか、雑かを分けて見るため）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .checklist import KEYS


@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0
    abstain: int = 0  # unclear を返した回数（採点対象の項目のみ）
    skipped: int = 0  # 正解が "?" で採点しなかった回数

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    @property
    def precision(self) -> float | None:
        d = self.tp + self.fp
        return self.tp / d if d else None

    @property
    def recall(self) -> float | None:
        d = self.tp + self.fn
        return self.tp / d if d else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None or r is None or (p + r) == 0:
            return None
        return 2 * p * r / (p + r)

    @property
    def accuracy(self) -> float | None:
        return (self.tp + self.tn) / self.n if self.n else None

    def add(self, other: "Counts") -> None:
        for f in ("tp", "fp", "fn", "tn", "abstain", "skipped"):
            setattr(self, f, getattr(self, f) + getattr(other, f))


@dataclass
class Scored:
    per_item: dict[str, Counts] = field(default_factory=lambda: {k: Counts() for k in KEYS})
    per_photo_exact: dict[str, bool] = field(default_factory=dict)
    format_invalid: int = 0
    llm_error: int = 0
    n_photos: int = 0

    @property
    def overall(self) -> Counts:
        c = Counts()
        for v in self.per_item.values():
            c.add(v)
        return c

    @property
    def exact_match_rate(self) -> float | None:
        if not self.per_photo_exact:
            return None
        return sum(self.per_photo_exact.values()) / len(self.per_photo_exact)


def score_one(pred_items: dict[str, str], truth: dict[str, int | str]) -> tuple[dict[str, Counts], bool]:
    """1枚分を採点。戻り値は (項目別カウント, 採点対象の全項目が一致したか)。"""
    out: dict[str, Counts] = {}
    all_match = True
    for k in KEYS:
        c = Counts()
        t = truth.get(k, "?")
        p = pred_items.get(k, "unclear")
        if t == "?":
            c.skipped = 1
        else:
            t_yes = int(t) == 1
            if p == "unclear":
                c.abstain = 1
            p_yes = p == "yes"
            if t_yes and p_yes:
                c.tp = 1
            elif t_yes and not p_yes:
                c.fn = 1
                all_match = False
            elif not t_yes and p_yes:
                c.fp = 1
                all_match = False
            else:
                c.tn = 1
        out[k] = c
    return out, all_match


def score_run(records: list[dict], labels: dict[str, dict]) -> Scored:
    """records: run_eval が書く1行ずつの結果（photo_id, status, items）。labels: photo_id -> 正解。"""
    s = Scored()
    for r in records:
        s.n_photos += 1
        pid = r["photo_id"]
        if r["status"] == "format_invalid":
            s.format_invalid += 1
            s.per_photo_exact[pid] = False
            continue
        if r["status"] == "llm_error":
            s.llm_error += 1
            s.per_photo_exact[pid] = False
            continue
        per, ok = score_one(r["items"], labels[pid])
        for k, c in per.items():
            s.per_item[k].add(c)
        s.per_photo_exact[pid] = ok
    return s
