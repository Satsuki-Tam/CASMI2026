# 051 事前登録: ICEBERG を主出力の固定規則の成分に戻す(未見 NP クラス 2 と既見クラス 1 での測定)

作成: 2026-10-27 02:13 JST(結果を見る前)。背景: B1 は 10/24 に初期の開発集合(A 合成 timsTOF / B NP、Spark の ICE が一部で異常終了した時期)で ICE を外した(w_ice 0、ranker も v2_noice)。公開系譜は ICE+GL を併用(ICE_LAM = GL_LAM = 1 で +0.007 の報告、GL 不在時の ICE fallback)。P1 set A では ICE の上乗せ +0.038 を観測している。未見の NP クラス 2(fold-1/2 dev)では未測定。

## 変更(一つ、重みは二点)
- 主出力(rank_v4b blend21 + GL-cover fallback + anaw0.5)の固定規則成分 S = z(FP) + 2 z(GL) + 0.5 pop に **w · z(ICE)** を足す(GL 経路では blend の z(S) の中、fallback 経路では insurance の S の中)。w ∈ {0.5, 1}。learned ranker の入力は不変(v2_noice)。ICE の被覆が list の 50% 未満の分子は不変。
- 評価器 `gen_eval2i.py`(登録の gen_eval2 67d113ec の複製 + ice<w> 列、main は gen_eval2 と一致することを確認)、ICE は run の複製(`run_*_ice/work/ice_<set>.json`)に保存し原本は不変。

## 測定(`spark/jobs/spark_ice051_dev.sh`)
- fold-1 / fold-2 dev(fpnet_fold1/2、identity 未見)の C / D / G、パネル 250(既見 = 隠しのクラス 1 の regime)。

## 判定(開発)
- 主指標: **NP マクロ = 0.5 × (C C2 と D C2 をプールした Δ) + 0.5 × (パネル C1 clean の Δ)**。w は主指標の大きい方を開発で選ぶ(同点なら 0.5)。
- 保護の規則は `049b_request.md` の提案(プールした層ごとに有意な害が無いこと、多重性補正つき + NP マクロの点推定 ≥ 0)を **Codex が結果の読み出し前に同意した場合**に使い、同意が無ければ従来の規則(各層 ≥ −0.01)を使う。どちらを使ったかを結果に明記する。両方の判定を併記する。
- 開発で選ぶ条件: 主指標 > +0.005 かつ保護合格。確認は新しい集合(fold-0/1/2 の未使用 identity から、結果の前に固定)で一回。
