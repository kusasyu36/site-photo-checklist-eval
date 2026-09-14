# 評価結果

## 条件別の全体指標（全項目を合算）

| 条件 | 写真×試行 | 採点項目数 | precision | recall | F1 | accuracy | 全項目一致率 | 不明の回数 | 形式不正 | 呼び出し失敗 |
|---|---|---|---|---|---|---|---|---|---|---|
| bare | 60 | 612 | 0.95 | 0.94 | 0.95 | 0.96 | 0.70 | 74 | 0 | 0 |
| hinted | 60 | 612 | 0.96 | 0.93 | 0.94 | 0.96 | 0.65 | 69 | 0 | 0 |
| framed | 60 | 612 | 0.95 | 0.94 | 0.94 | 0.96 | 0.65 | 43 | 0 | 0 |

## 項目別（recall / precision / 不明）

| 項目 | bare R / P / 不明 | hinted R / P / 不明 | framed R / P / 不明 | 採点数 |
|---|---|---|---|---|
| scaffolding（足場） | 1.00 / 1.00 / 2 | 1.00 / 1.00 / 1 | 1.00 / 1.00 / 1 | 57 |
| heavy_machinery（建設機械） | 0.91 / 1.00 / 2 | 0.88 / 1.00 / 2 | 0.91 / 1.00 / 2 | 51 |
| workers（作業員） | 1.00 / 1.00 / 10 | 1.00 / 1.00 / 11 | 1.00 / 1.00 / 6 | 60 |
| worker_no_helmet（ヘルメット未着用の作業員） | 1.00 / 0.75 / 11 | 1.00 / 0.75 / 11 | 1.00 / 0.75 / 4 | 57 |
| perimeter_barrier（仮囲い・バリケード） | 0.89 / 0.96 / 8 | 0.89 / 0.92 / 8 | 0.89 / 0.92 / 1 | 54 |
| excavation（掘削・土留め） | 0.67 / 1.00 / 9 | 0.33 / 1.00 / 4 | 0.78 / 1.00 / 3 | 48 |
| stacked_materials（資材の仮置き） | 1.00 / 0.86 / 10 | 1.00 / 0.86 / 8 | 1.00 / 0.82 / 11 | 45 |
| adjacent_structures（隣接する既存構造物） | 0.96 / 0.82 / 6 | 0.92 / 0.88 / 7 | 1.00 / 0.83 / 2 | 48 |
| public_road_or_traffic（公道・交通） | 1.00 / 1.00 / 5 | 1.00 / 1.00 / 4 | 1.00 / 1.00 / 3 | 42 |
| signage（看板・標識） | 0.89 / 1.00 / 1 | 0.96 / 1.00 / 2 | 0.81 / 1.00 / 4 | 45 |
| water_or_mud（水・泥） | 1.00 / 1.00 / 4 | 1.00 / 1.00 / 3 | 0.89 / 1.00 / 2 | 54 |
| overhead_lines（架空線） | 1.00 / 1.00 / 6 | 1.00 / 1.00 / 8 | 1.00 / 1.00 / 4 | 51 |

## 失敗の型

| 条件 | 見落とし(miss) | 誤検出(false_alarm) | 判定可能なのに不明 | 形式不正 | 呼び出し失敗 |
|---|---|---|---|---|---|
| bare | 5 | 10 | 74 | 0 | 0 |
| hinted | 7 | 9 | 69 | 0 | 0 |
| framed | 8 | 12 | 43 | 0 | 0 |

### bare: 型ごとに多い項目
- miss: heavy_machinery 2, signage 2, perimeter_barrier 1
- false_alarm: adjacent_structures 5, stacked_materials 3, perimeter_barrier 1, worker_no_helmet 1
- abstain_on_clear: worker_no_helmet 11, stacked_materials 10, workers 10, excavation 9

### hinted: 型ごとに多い項目
- miss: excavation 3, heavy_machinery 2, adjacent_structures 1, perimeter_barrier 1
- false_alarm: adjacent_structures 3, stacked_materials 3, perimeter_barrier 2, worker_no_helmet 1
- abstain_on_clear: workers 11, worker_no_helmet 11, stacked_materials 8, perimeter_barrier 8

### framed: 型ごとに多い項目
- miss: perimeter_barrier 3, signage 3, heavy_machinery 1, excavation 1
- false_alarm: adjacent_structures 5, stacked_materials 4, perimeter_barrier 2, worker_no_helmet 1
- abstain_on_clear: stacked_materials 11, workers 6, signage 4, overhead_lines 4
