# 027 事前登録(実行前に固定、2026-10-26 01:10 JST): FPNet 2 モデル平均(ENS2 = full_eval + full_rk)

- 背景: full_eval(全 train FPNet)の一変更が Public 0.370(+0.016、未確定)。公開系譜(E0)は FPNet を複数平均している。私たちの 2 つの全 train FPNet(full_eval 5b8d1c31、full_rk 1f47f1ba)はどちらも dev2 を保留(未見)し、パネルの identity は既見(query は除去)なので、平均の効果を dev2(未見)とパネル C1(既見・query 未見)で汚染なく測れる。予測は両モデルの logits の平均(提出パイプラインの複数モデルと同じ規則)。
- 実行: `spark/jobs/spark_ens2_chain.sh`(特徴表は `b1_features.py --extra_ckpts`、GL は full_eval の run から seed、評価は登録評価器、主出力 blend21 + GL fallback、ranker は rank_v4b のまま)。
- 主比較: パネル C1 clean 202 の **ENS2 − M2x_fe** の点推定が正(全 250・uncertain 48 を併記)。
- 保護(dev2、未見): C2(C/D/E/F/G)と C1(C/E/F/G)で (i) ENS2 − M2x_fe と (ii) ENS2 − M2x の点推定 ≥ −0.02(下限 ≥ −0.02 なら合格、点だけなら未確定)。
- 判定: 主比較が正で (i)(ii) の全保護層の点推定 ≥ −0.02 → M2x_fe(Public 0.370)に対する一変更の比較提出の候補(Kaggle には full_rk の checkpoint も private model で置く必要あり)。それ以外は見送り。ranker と降格は混ぜない。

## 追記(02:00、実行前): ENS5(公開 fold-safe の 5 モデル平均)のパネル診断
- fold-safe の 5 モデルは「fold k とパネルの天然物を除いて学習」(README)なので、パネルは 5 モデルすべてに未見 → 未見領域での平均の効果をパネルの両 view で汚染なく測れる。dev2 は fold 1〜4 のモデルが学習済み(dev2 は fold 0)なので使わない。
- 比較: ENS5(+ rank_v4b)− M2x(fold 0 + rank_v4b)、パネル C1 / C2(clean / uncertain 併記)。**診断のみ**(dev2 の保護を測れないので提出候補の判定はしない)。ENS2 の後に `spark/jobs/spark_ens5_panel.sh` で実行。
