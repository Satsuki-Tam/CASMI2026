# 068 依頼: 本番 FPNet の選択(EXT の発見と 067 の設計)、v8w の扱い

作成: 2026-10-27 07:17 JST(Claude Code)。前提: `065_ext_result.md`(EXT と 066)、`067_prereg_fpnet_mix.md`、`064_result.md`、`056_conf_results.md`、`062_decision.md`。

## 1. 新しい観察
- **EXT ベンチ**(knowledge table の外部スペクトルのうち train に無く MassSpecGym にも無い構造 60 = FPNet・ranker・ライブラリ・GLACIER の全てに未見): 0.379 構成 0.5054。rank_v4b を固定して FPNet だけ替えると、**公開 fold0 0.5436(+0.038 [+0.003, +0.081]、8 改善 / 5 悪化)**、公開 5 本平均 0.5250(+0.020 [−0.023, +0.067])。
- 一方 dev2(full_eval と fold0 の両方に未見)では full_eval が C C2 +0.026、G C2 +0.020、D C2 −0.011(064 の基準列)。dev2 は full_eval の採用判断に使った集合。
- Public では fold0(M2x 0.354)→ full_eval(0.370)で +0.016(全体)。
- 仮説: full_eval の利得は既見のクラス 1 の記憶で、未見のクラス 2 では公開 fold0 の方が良い(rank_v4b の学習表も fold0 の特徴)。

## 2. 067(実行中、結果の前)
- 未開封の locked2 v2(fold 0、500 分子、full_eval の lock = 未見、fold0 にも未見)で A = full_eval / B = fold0 / C = 両者の logit 等重み平均を rank_v4b 固定で比較、主指標 NP C2 の C − A、主保護はパネル C1 clean(F 既見・fold0 はパネルを除外 = 未見)で C − A の非劣性。合格なら「0.5F + 0.5fold0」を pipeline(`experiments/b1_mix067`、--mix_folds)で本番候補に → panel parity → 一変更の Public 比較。
- 設計に見落としはないか(特に、locked2 をここで使うことの是非、パネル C1 を既見の regime として主保護にする妥当性、P = 5 本平均を候補に入れなかった点 — locked2 では P の 4 本が既見)。

## 3. v8w
- 3b/4b の確認は合格(+0.0067 [+0.0023, +0.0112])、064 の交差比較で checkpoint の交互作用なし、model だけ替えた pipeline の panel parity は c2 PASS(c1 実行中)、EXT では −0.004(n 60)。総合すると真の効果は小さい正(+0.005 前後)と見る。Public の一変更比較に使う価値はあるか、それとも 067 の結果(FPNet の選択)を先に決めてから v8w を重ねるべきか。
