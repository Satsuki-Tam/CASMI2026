# 070 依頼: E0 の棚卸し(069)を受けた移植計画 — 大規模な模擬学習(P1)の設計

作成: 2026-10-27 09:04 JST(Claude Code)。前提: `069_e0_inventory.md`(E0 の段階別の棚卸し、file:line つき)、`056_conf_results.md`、`065_ext_result.md`、`067_prereg_fpnet_mix.md`。
利用者の方針(08:20): 公開 notebook に継ぎ足す改善は禁止、E0 を分析して原理的な部分を B1 に取り入れるのは可(LB 合わせ・評価不備に注意)。計算場所(08:37〜): Spark は利用者が別件で使用中 → 実験は手元の PC(RTX 5070 Ti、CUDA は一度に一つ、Ryzen 9700X)。

## 1. 069 の要点(サブエージェントの棚卸し)
- E0 の本体の強みは「推論と同じ engine の候補生成・特徴計算で、真の情報を規則的に隠した query(class 1 = query ライブラリだけ隠す、class 2 = 全ライブラリ、class 3 = 真を pool から除き生成でのみ到達)を大量に作り、それで ranker を学習する」こと(engine.py:236-251、family 開発は 23,748 query)。B1 の rank_v4b は 1,304 群。v8w(約 3,900 群)は小規模版で確認 +0.0067 [+0.0023, +0.0112]。
- E0 の engine 1 は pool(train ∪ COCONUT)の窓全体(中央値 75)を 160 特徴で採点し、生成物も同じ ranker で採点する。系譜の各段の大半は Public で 0〜1 分子分、5-fold FPNet・NP/LOTUS prior・6 番目の PubChem 枠は ±0。
- 学習コードがあるのは公開 fold-safe FPNet だけ(他の重みは学習コード無し = 賞の資格の点で使えない)→ 考え方だけを移す。

## 2. 提案(P1 の B1 版)
- 学習表: 公開 fold-safe FPNet で **OOF の特徴**(fold k の分子には fold k のモデル)を作り、folds 0/3/4 の未使用 identity から数千分子(COCONUT 収載正解を厚く、query は全ライブラリ、timsTOF の G 型も一定数)を b1_features に通す。view は C1(query ライブラリの参照だけ除く)・C2(全参照を除く)・C3(真を DB から除き生成物で到達 — まずは C1/C2 のみで始め、C3 は P4 = 生成物の本体採点と一緒に)。GL は PC で全 shortlist に掛ける(1,000 分子あたり GPU で約 1 時間の見込み)。
- 学習: v8w のレシピ(rank_v4b のパラメータ固定、C1 比率を 0.46 前後に揃える)で群数だけ増やす版と、特徴を追加する版(analog の ap / mt、MetFrag-lite、source flag の明示)を分ける。
- 評価: 開発 = f1dev / f2dev / 053 dev(公開 fold1/2 の表)、確認 = 053 の NP_H / NP_N conf(未開封)、既見クラス 1 の保護 = パネル C1 clean(full_eval の表)、stress = EXT 60(全モデル未見)と dev2。本番 FPNet(full_eval、または 067 の結果次第で混合)との特徴分布のずれは 064 型の交差比較で確認。

## 質問
1. P1 の設計に見落としは(特に、OOF 特徴を公開 fold モデルで作り本番は full_eval / 混合で推論する点、学習表の class 比率が暗黙の prior になる点、G 型の扱い)。
2. PC の計算資源(GL を含め 1,000 分子あたり数時間)を考えると、最初の規模はどれくらいが妥当か。v8w(約 3,900 群)からの増分の効果を見るための最小の設計。
3. 069 の他の候補(P2 source 降格、P3 N1A の条件拡大、P4 生成物の本体採点、P5 第二の独立リスト)の中で、今日の probe の結果を待たずに着手すべきものはあるか。
