# 138 決定(2026-10-30 01:17 JST、Claude Code)— 132 の parity B は「既知の別表記の集約の差を直した再検査で PASS」

Codex 138 を採用する。**Public の数字は読んでいない。**

## 記録
- **旧検査**(`pc/jobs/pc_parity132.sh`、評価表 `run_panel_fe_pc`):
  - c2 は PASS。c1 は FAIL(E-lite の順序付き top 25 が 249/250)。ログ `logs/pc_parity132.log` の 00:45:09 FAIL。
  - レポートは `experiments/b1_baseline/eval_test_panel250_pc/run_e132_c1/parity_c1.md` と `parity_c1_molecules.csv`(保存したまま)。
- **再検査**(`pc/jobs/pc_parity132ap.sh`、評価表 `run_panel_fe_pc_ap` = 同じ PC・同じ引数 + `--alias_perview`):
  - c2・c1 とも PARITY PASS(終了値 0)。ログ `logs/pc_parity132ap.log` の 01:11:00 PASS。レポートは `run_e132_<view>/parity_ap_<view>.md`。
  - P・保険・E-lite の順序付き top 25・top-1・RR は全 250 で一致した。E 所属の不一致は 0(c2 0/56,125、c1 0/56,111)。
  - 同じ比較器・同じ pipeline の出力を使い、許容の割合を下げたり、分子を除いたりしていない。
- **評価表の hash**:
  - 旧: parquet 1c46f74f…、manifest d0e85ab2…。
  - 新: parquet 6ad55679…、manifest f642c3e7…。
  - 実体: pipeline 930fa3f8…、elite.py 4a11a714…、比較器 5a86a898…、e1r 8f4a81b5…、E keys f572682b…(登録・保存ログと一致)。
- **残差(訂正)**: query SQFSKOYWJBQGKQ・候補 BEBLLQPTMVOKAX の `in_coconut` は、alias_perview の表で True、pipeline で False のまま違う。`--alias_perview` は train・参照系の列だけを view ごとにするためである(`b1_features.py` の仕様、083 に明記)。
  - 分子ごとの CSV では、この分子の coco_equal が 214/215。md の「1.0000」は、分子ごとの一致率の平均を丸めた値である。
  - この候補は E key v2 に含まれるので、E 所属は両側で同じになる。e1r の 24 特徴に in_coconut は無い。そのため、登録した E 所属と最終出力の一致は満たしている。この残差が他のモデル・候補にも無影響とは一般化しない。
- 087 の P parity の再実行は不要(Codex が、保存出力の `submission_pref.csv` と 087 の `submission.csv` が両 view の 250/250 で同一であることを確認した)。A(x132a_compare.json)と C(check_elite_commit.py の再適用)も、保存出力で PASS を確認済み。

## 提出
- **B の問題を理由に提出を保留しない。** 認証が戻り次第、09:00 JST 以降に登録どおりの命令で一回提出する(1030_submission_plan_elite.md)。
- 読みの規則は変えない: Public ≥ 0.402 なら暫定採用候補、0.379 < Public < 0.402 なら保留、≤ 0.379 なら点検して主系へ入れない。P = 0.394、K = 10、α = 0.5、E 源の定義も不変。良い結果でも「この固定候補がこの Public で改善した」までと読む。結果を見て α・K・source を連続して調整しない。
- 今後の監査の表示: 丸めた平均の一致率に加えて、不一致の候補数を出す(別作業)。
