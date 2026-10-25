# 021 依頼: 記憶の利得を最終出力へ通すための ranker 学習表 — 二本目の FPNet 学習(full_rk)の設計確認(15:35 に開始可否を決めたい)

作成: 2026-10-25 14:00 JST(Claude Code)。前回 `020_decision.md`。手元 GPU は 20:50 まで使用可。full_eval の学習は 15:35 頃完了予定(その後 Spark で現行 M2x + full_eval を自動評価)。

## 1. 新しい事実(`docs/validation_design.md` 末尾「同一窓での FPNet 比較」)
同じ候補窓で、学習済み FPNet は FP 単独の MRR@25 を大きく上げる: W7 B 0.367 → 0.570(fold1)/ 0.636(full1)、dev2 E 0.248 → 0.570 / 0.583、F 0.156 → 0.431 / 0.386、D 0.428 → 0.568 / 0.665、パネル 0.226 → 0.806(full1、query 取得も学習済み)。R@200 も +0.06〜+0.17(NP)。**ところが登録出力(rank_v4b + blend21)の利得は +0.03〜+0.04 だけ**。現行 ranker は未見 FP の特徴(fold-0 モデルで fold-0 分子)で学習しており、FP が強く信頼できる状況を学んでいない。

## 2. 提案: 二本目の学習 `full_rk`(15:40〜19:40、手元 GPU、同じ公開レシピ・82,855 更新)
目的: ranker の学習表に「identity は学習済み・query 取得は未見」の C1 行と「完全に未見」の C2 行を、同じ FPNet で作る。
除外(学習から外す):
1. パネルの query 取得 + 重複(full_eval と同じ;パネル C1 は評価専用のまま)。
2. dev2 / locked2 の identity group 全体(評価用、full_eval と同じ)。
3. **p1_run1(現行 ranker の fit 集合、600 分子)の identity group 全体** → この FPNet で完全に未見 = C2 行を本物のクラス 2 に近い条件で作れる。
4. **W7(eval_set)と eval_c1 の query 取得**(選択ライブラリの行 + 他ライブラリの重複)→ identity は他ライブラリの独立スペクトルで学習済み、query は未見 = C1 行(他ライブラリ参照が無い分子は事実上未見になり、C2 行として扱える)。
ranker 学習表(この FPNet の特徴で作り直し): p1_run1 の C2・C1 行(未見)、W7 と eval_c1 の C1 行(学習済み identity・未見 query)。W7 の C2 行は「参照を隠した学習済み identity」= 記憶の残存なので学習から外す。
評価: dev2(未見、C2/C1)、パネル C1(学習済み identity・未見 query)、locked2 は最終 1 回。提出時の FPNet は full_rk(または full_eval)— 学習表と推論の FPNet を一致させるなら full_rk。

## 3. 質問
**Q1** この除外設計で「C1 行 = 学習済み identity・未見 query」「C2 行 = 未見」が成り立つか。W7 の query 取得の除外基準(選択ライブラリの全行 + 他ライブラリの同 adduct・|Δprec| < 5 mDa・類似 ≥ 0.95)で足りるか。
**Q2** 提出時に full_rk を使うと、p1_run1 の 600 identity(と dev2/locked2 の 1,000)が FPNet に未学習のまま残る(全 train の約 0.6%)。隠しクラス 1 にそれらが含まれる確率は小さいが、損失はある。許容か、最後に全量で学習し直すべきか。
**Q3** 今日は時間的に「full_rk の学習(15:40〜19:40)」と「full_eval の評価・提出」を並行できる。full_rk を始める価値があるか、それとも full_eval の評価結果を見てから(=今日は始めない)にすべきか。
