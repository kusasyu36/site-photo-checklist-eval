# 評価結果

## 条件別の全体指標（全項目を合算）

| 条件 | 写真×試行 | 採点項目数 | precision | recall | F1 | accuracy | 全項目一致率 | 不明の回数 | 形式不正 | 呼び出し失敗 |
|---|---|---|---|---|---|---|---|---|---|---|
| bare | 20 | 204 | 0.93 | 0.95 | 0.94 | 0.96 | 0.65 | 23 | 0 | 0 |
| hinted | 20 | 204 | 0.92 | 0.93 | 0.93 | 0.95 | 0.60 | 25 | 0 | 0 |
| framed | 20 | 204 | 0.91 | 0.93 | 0.92 | 0.94 | 0.60 | 16 | 0 | 0 |

## 項目別（recall / precision / 不明）

| 項目 | bare R / P / 不明 | hinted R / P / 不明 | framed R / P / 不明 | 採点数 |
|---|---|---|---|---|
| scaffolding（足場） | 1.00 / 1.00 / 0 | 1.00 / 1.00 / 0 | 1.00 / 1.00 / 0 | 19 |
| heavy_machinery（建設機械） | 0.91 / 1.00 / 0 | 0.91 / 1.00 / 1 | 0.91 / 1.00 / 0 | 17 |
| workers（作業員） | 1.00 / 1.00 / 3 | 1.00 / 1.00 / 4 | 1.00 / 1.00 / 3 | 20 |
| worker_no_helmet（ヘルメット未着用の作業員） | 1.00 / 1.00 / 4 | 1.00 / 0.50 / 4 | 1.00 / 0.50 / 1 | 19 |
| perimeter_barrier（仮囲い・バリケード） | 0.89 / 0.89 / 3 | 0.89 / 0.89 / 5 | 0.89 / 0.89 / 1 | 18 |
| excavation（掘削・土留め） | 0.67 / 1.00 / 1 | 0.33 / 1.00 / 1 | 0.67 / 1.00 / 1 | 16 |
| stacked_materials（資材の仮置き） | 1.00 / 0.86 / 4 | 1.00 / 0.75 / 2 | 1.00 / 0.75 / 4 | 15 |
| adjacent_structures（隣接する既存構造物） | 1.00 / 0.73 / 1 | 1.00 / 0.80 / 2 | 1.00 / 0.73 / 1 | 16 |
| public_road_or_traffic（公道・交通） | 1.00 / 1.00 / 2 | 1.00 / 1.00 / 2 | 1.00 / 1.00 / 2 | 14 |
| signage（看板・標識） | 0.89 / 1.00 / 1 | 0.89 / 1.00 / 1 | 0.78 / 1.00 / 1 | 15 |
| water_or_mud（水・泥） | 1.00 / 1.00 / 1 | 1.00 / 1.00 / 0 | 1.00 / 1.00 / 0 | 18 |
| overhead_lines（架空線） | 1.00 / 1.00 / 3 | 1.00 / 1.00 / 3 | 1.00 / 1.00 / 2 | 17 |

## 失敗の型

| 条件 | 見落とし(miss) | 誤検出(false_alarm) | 判定可能なのに不明 | 形式不正 | 呼び出し失敗 |
|---|---|---|---|---|---|
| bare | 1 | 5 | 23 | 0 | 0 |
| hinted | 1 | 6 | 25 | 0 | 0 |
| framed | 4 | 7 | 16 | 0 | 0 |

### bare: 型ごとに多い項目
- miss: heavy_machinery 1
- false_alarm: adjacent_structures 3, perimeter_barrier 1, stacked_materials 1
- abstain_on_clear: stacked_materials 4, worker_no_helmet 4, perimeter_barrier 3, workers 3

### hinted: 型ごとに多い項目
- miss: excavation 1
- false_alarm: adjacent_structures 2, stacked_materials 2, perimeter_barrier 1, worker_no_helmet 1
- abstain_on_clear: perimeter_barrier 5, workers 4, worker_no_helmet 4, overhead_lines 3

### framed: 型ごとに多い項目
- miss: heavy_machinery 1, perimeter_barrier 1, signage 1, excavation 1
- false_alarm: adjacent_structures 3, stacked_materials 2, perimeter_barrier 1, worker_no_helmet 1
- abstain_on_clear: stacked_materials 4, workers 3, public_road_or_traffic 2, overhead_lines 2
