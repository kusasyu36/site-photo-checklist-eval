# site-photo-checklist-eval

工事現場の写真を、点検チェックリスト12項目に照らして Vision-Language Model（VLM）に判定させ、
人手ラベルと突き合わせて **どの項目をどう間違えるか** を数える評価ハーネスです。

「精度が何%か」だけでなく、**見落とし・誤検出・不明の逃げ** の型と、項目ごとの偏りを出し、
プロンプトに現場側の確認観点を足すと何が変わるかを同じ写真で比較します。

```
写真 + チェックリスト ──► VLM（Claude、Read ツールのみ許可） ──► JSON（項目ごとに yes/no/unclear + 根拠）
                                                                 │
   人手ラベル（1/0/?） ◄──── 採点（P/R/F1・全項目一致・不明回数） ◄──┘
                                    │
                          失敗の型（miss / false_alarm / abstain / format_invalid / llm_error）× 項目
```

## 結果（claude-sonnet-5、写真20枚、各条件1試行）

RESULTS_PLACEHOLDER

## 何を測っているか

### 題材
- 写真: Wikimedia Commons の CC ライセンス写真 20枚（足場、クレーン、掘削、仮囲い、道路工事、解体など）。
  リポジトリには含めず `scripts/download_images.py` で取得する。出典は [data/CREDITS.md](data/CREDITS.md)。
- チェックリスト: 12項目（[src/spce/checklist.py](src/spce/checklist.py)）。
  足場／建設機械／作業員／ヘルメット未着用の作業員／仮囲い・バリケード／掘削・土留め／資材の仮置き／
  隣接する既存構造物／公道・交通／看板・標識／水・泥／架空線。
- 正解ラベル: 作者（建設の専門家ではない）が写真を見て 1 / 0 / "?" を付けた。
  "?" は作者にも判断できなかった項目で、**採点から除外**する（240セル中 36 が "?"）。

### 2つの条件
| 条件 | プロンプトに入れるもの | 何を模しているか |
|---|---|---|
| bare | 項目名と定義だけ | チェックリストをそのまま渡した状態 |
| hinted | 定義に加えて各項目の「確認観点」（何を見て判断するか、迷ったら不明にする基準） | 現場の判断基準を言語化して渡した状態 |

「確認観点」は作者が書いたもので、本物の現場のノウハウではない。この差分が測っているのは
**判断基準を文章で足したときに、VLMの答えがどの項目で・どの向きに動くか** であって、観点の正しさではない。

### 指標
- 項目ごとの precision / recall / F1。`unclear` は「答えなかった」として no 扱いで採点し、別に **不明回数** を数える
- 写真ごとの **全項目一致率**（採点対象の項目が全部合っていた写真の割合）
- **失敗の型**: miss（見落とし）/ false_alarm（誤検出）/ abstain_on_clear（作者が判定できた項目で不明）/
  format_invalid（JSON崩れ・項目欠け）/ llm_error（呼び出し失敗）。型ごとに、どの項目で多いかを出す

### ハーネス側の設計
- VLM の出力は信用しない。JSONの取り出し、全項目の存在、値が3値のいずれかであることを検証し、
  不正なら `format_invalid` として記録する（[src/spce/schema.py](src/spce/schema.py)）
- VLM 呼び出しは `claude -p` の子プロセス。画像を開くための **Read ツールだけを許可**し、
  シェルや書き込み、Webは使わせない。タイムアウトと再試行つき（[src/spce/vlm.py](src/spce/vlm.py)）
- 結果は1枚ごとに JSONL に追記。途中で落ちても済んだ分は残り、再実行は未処理の写真だけ回す
- 集計は VLM を使わずコードで行う。テスト17本は Mock バックエンドで動き、ネットワークも API も要らない

## 使い方

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest -q                      # 17 passed
.venv/bin/python scripts/download_images.py        # 画像20枚を取得

# VLM で評価（claude CLI が必要。Read ツールのみ許可して実行される）
.venv/bin/python -m spce.run_eval --condition bare   --trial 1
.venv/bin/python -m spce.run_eval --condition hinted --trial 1
.venv/bin/python -m spce.report results/pred_bare_t1.jsonl results/pred_hinted_t1.jsonl
```

`--backend mock` でオフラインの決定的バックエンド、`MOCK_INVALID=1` で不正出力の経路を試せる。

## 正直に書いておくこと

- **ラベルは非専門家1人の判断**。"?" を除外しているので、難しい項目ほど採点から抜けている。
  専門家が同じ写真をラベルすれば、正解自体が動く項目がある（隣接構造物、掘削、資材）
- **各条件1試行**。VLM の出力は同じ入力でも揺れるので、条件間の差は試行を重ねないと確定しない。
  `--trial 2` 以降を回して同じ集計にかけられるようにしてある
- 写真は Commons の 1280px 縮小版。ヘルメットや架空線のような小さい対象は解像度の影響を受ける
- 「確認観点」は作者が書いたもの。現場の実際の判断基準とは違う
- 20枚・12項目の小さな評価。傾向を見るためのもので、モデルの優劣を決めるものではない

## 構成

```
src/spce/
  checklist.py   12項目の定義と確認観点
  prompts.py     bare / hinted のプロンプト構築
  vlm.py         claude -p バックエンド（Read のみ許可）と Mock
  schema.py      出力の検証（InvalidOutput）
  run_eval.py    実行 CLI（追記型 JSONL）
  metrics.py     採点（P/R/F1・全項目一致・不明）
  failures.py    失敗の型の分類
  report.py      条件別の集計と Markdown / JSON 出力
data/
  manifest.jsonl 画像の URL・ライセンス・作者
  labels.jsonl   正解ラベル（1 / 0 / "?"）
  CREDITS.md     出典一覧
results/
  pred_*.jsonl   VLM の生出力（根拠と要確認ポイントを含む）
  summary.md / summary.json
tests/           17本（Mock で完結）
```

## ライセンス

コードは MIT。写真は各作者のライセンス（[data/CREDITS.md](data/CREDITS.md)）に従う。
