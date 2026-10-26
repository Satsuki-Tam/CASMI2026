# 058 事前登録(診断): 公開 fold-safe FPNet 5 本の ensemble を、パネル(全 5 本で identity 未見)で測る

作成: 2026-10-27 02:44 JST(結果の前)。根拠: Codex 049(公開 kit の make_split.py は全 fold でパネルの identity 群を学習から除外 → パネルは公開 5 本すべてに未見)。自前 full_eval は使わない(パネルを既見)。

- 比較: 単体 fpnet_fold0 vs 5 本の logit 平均(`b1_features --extra_ckpts`、同じ timsTOF query・同じ窓)。
- 指標 1(主、GL の汚染なし): 真の FP 順位(窓全体、b1_molecules の truth_fp_rank)の MRR@25 と top-1、paired。
- 指標 2(参考): 登録の主出力(rank_v4b blend + GLACIER、GL はパネルで MSG 汚染)C2 / C1(identity 未見の C1 = stress)。ranker は単体の尺度で学習済みなので、ensemble の尺度ずれの影響も含む。
- 読み: 指標 1 で ensemble が明確に上(paired で一貫)なら、Codex 049 (iv) の 2 本の共通 holdout 実験と本番の 6 本構成(自前 full + 公開 5 本、ranker の再学習を含む)の設計に進む。方法の採否はここでは決めない。
