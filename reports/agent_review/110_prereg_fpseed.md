# 110 事前登録: FPNet の同一 holdout・新 seed の 1:1 平均(Codex 109 (a))

作成: 2026-10-28 20:22 JST(Claude Code、モデルの学習中・結果の前)。

## 1. 候補(一つ)
- **FPavg** = 公開 fpnet_fold1(公開レシピ、seed 0)と、同じ公開レシピ・同じ harness_work・同じ分割(make_split.py、fold 1 + NP-example group を保留)で学習した **seed 1 の一本**(experiments/fpnet_seed/f1s1、82,855 更新、Spark)の **logit の 1:1 平均**。bit 順・入力処理・更新数・augmentation は不変。旧 seed・新 seed 単体は診断。
- 評価は fold 1 の分子だけ(両モデルとも未見): f1dev(C〜G)と np053f1dev(NP_H / NP_X / NP_N)。

## 2. 段階と関門(Codex 109 の順)
1. **FP 単独の順位**(同じ質量窓): 各分子の窓(既存の gen dump の窓の key と質量)で、正解の FP 順位(f·z)を旧 seed 単体と FPavg で比べる。指標: FP 単独の MRR@25 と top-1、正解の順位の対数の差。**FPavg が旧 seed に対して FP 単独の MRR で改善しなければ、ここで止める**(seed を増やす線を閉じ、次は学習の hard negative の監査)。
2. **主リストが誤る行での変化**: v8w7a の主リストが 1 位を誤る行で、正解の FP 順位がどう動くか(記述)。
3. **端から端**(1 が改善した場合のみ): f1dev / np053f1dev の表を FPavg で作り直し(b1_features --extra_ckpts、shortlist 再生成)、GL を新しい候補に再計算し、v8w7a の ranker(凍結)で主出力を作って、現在の表の主出力と一対比較。主指標 = 1/2 A(np053f1dev NP_H / NP_N C2)+ 1/2 B_D(f1dev D C2);保護(下限 ≥ −0.01)= f1dev の C〜F C2、f1dev G C1、np053f1dev C1。関門 = 主指標 ≥ +0.005 かつ下限 > 0。fold 1 だけなので、通った場合は fold 2 で同じ手順を一回(fold 2 を保留した二本)。
- 注意: v8w7a の ranker は単体 FP の特徴分布で学習されている(平均 logit で分布がずれ得る)。端から端で利得が無ければ、OOF 特徴での ranker 再学習の比較は別登録。
