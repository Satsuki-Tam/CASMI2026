# 149 事前登録(2026-10-30 12:29 JST、Claude Code)— S2 (i): MIST を FP の源にした第二エンジン M と、現 E2 のレシピ C の一回の比較

147 の決定(147_decision.md)の S2 の最初の一手。MIST の採点値・M の学習結果・比較の数字は、まだ一つも見ていない時点で登録する。

## 問い
全 E 窓を、自前の C1 / C2 の模擬の行で学習した点ごとの順位器で並べるとき、FP の源を FPNet(f.z)から MIST に替えたエンジンは、P との融合の完成系で救済を増やすか。
- 128(同じ分子式の中での MIST の直接の並べ替え)の NO と、133(P の ranker への MIST 特徴の追加)の NO は残す。
- 135 で主軸から外した MIST を、この一回だけ再開する。checkpoint・特徴の追加の探索はしない。

## 比べるもの(候補・mask・その他の特徴・群の重み・容量は揃える)
- **C**: 現 E2 のレシピ(e2_common.FEATS の 21 特徴、LightGBM binary、144 のパラメタ、木 800 本で固定)。
- **M**: 同じ 21 特徴のうち、fp / fp_rank / fp_z / fp_gap だけを、MIST の mist_cos から同じ式で作ったものに置き換える。
  - mist_cos は mist_score_v4.py の値で、query は P と同じ方針、[M+H]+ / [M+Na]+ だけを使う。分子式は評価器と同じ定義で、真の分子式は使わない。
  - 異なる分子式の候補も、同じ cos の尺度で比べる。
- **欠測の規則**(先に固定)
  - 分子の中に mist_cos が有限の候補が一つも無い分子(負イオンだけ、全て mass_mismatch など)は、「MIST 被覆なし」とする。M の学習行から除き、評価では M の順位 = C の順位とする(fallback)。
  - 被覆のある分子の中で、mist_cos が欠ける候補(no_formula など)は、その分子の有限値の最小値 − 0.05 で埋める。行は除かない。
- **融合**: F_C = fuse_rrf(P, E2_C, α 0.5, K 10)、F_M = fuse_rrf(P, E2_M, α 0.5, K 10)。144 と同じ関数を使う。

## 学習と評価(fold 3/4 の交差。使用済みの fold 1/2 と、予約した fold 0 は使わない)
- **学習**: fold 3 の 3 ディレクトリ(train_pool_f3a / f3b / np061_f3pool)で学習し、fold 4 に当てる。その逆も行う。C と M で同じ。
  - 学習の群の規則は e2_common.train_groups(C2 = 窓に正解、C1 = 参照あり)。
- **評価の分子**: v8w7a が学習に使っていない identity(train_pool_f3b / np061_f3pool / train_pool_f4b / np061_f4pool)。
  - P = v8w7a の上位 25 件(diag/top149_<tag>.parquet。gen_eval2fd --dump_top、parents 0、views c1 / c2)。
  - FPNet は、各分子の fold の fold-safe 版(P と E2 で同じ)。
- **上流の露出の台帳**
  - FPNet: fold-safe(評価の fold は未見)。
  - v8w7a: 評価の identity は未見(f3a / f4a と fold 0 だけで学習)。
  - E2 C / M: 反対の fold だけで学習。
  - MIST: MassSpecGym で学習。評価の名簿と MSG の official identity の交差を数えて報告し、交差がある場合は、それを除いた感度も記述する。

## 主指標と関門(F_M − F_C、C2、分子を区画の中で再標本、4000 回)
- **主指標**: 1/2 A′ + 1/2 B_D′。
  - A′ = np061_f3pool と np061_f4pool の NP_H / NP_N の C2(4 区画を等しく重み付け)。
  - B_D′ = train_pool_f3b と f4b の D_np_single の C2(2 区画を等しく重み付け)。
- **関門**(Codex 147 の案)
  - 主指標 ≥ +0.01、かつ 95% の下限 > 0。
  - 両方向の点推定が正: fold 3 の評価(4→3 のモデル)と fold 4 の評価(3→4 のモデル)の、それぞれの A′ / B_D′ の主指標。
  - 保護の下限 ≥ −0.01:
    - 旧 B′(f3b / f4b の C〜F の C2、8 区画)
    - E 源の外の正解の C2(A′ + 旧 B′ をプール。所属は評価器 v3 と同じ固定の表)
    - G C1(f3b / f4b)
    - NP C1(np061 の C1 と、f3b / f4b の C〜F の C1)
- **記述**(判定には使わない)
  - E2_M − E2_C の単独の差。
  - 救済と損失の総量(正の差の和と負の差の和を別に)。
  - P が外した行での変化。同じ分子式の中での真の順位の差。
  - MIST の被覆(分子・候補)。
  - oracle の mean(max(RR_C, RR_M) − RR_C)。
  - MSG と交差した分子を除いた感度。
- **判断**
  - 関門を通れば、M を S2 の候補エンジンとして、全 fold での学習・完成系・Public の候補へ進める(別の登録)。
  - 通らなければ、MIST の定数の探索はしないで、(ii)(自前の別系統の FP、148 を含む)へ進む。

## 計算の予算
- MIST の採点(CPU)、P の上位 25 件の書き出し、np061_f4pool の表と GL は、全て実行中(性能の数字は計算しない)。
- 学習(4 モデル)と評価は、数分で終わる。

## 記録(12:28)
spark_s2_pinfra.sh の f3b / f4b の流れは、既存の run_tp_f3b_g / run_tp_f4b_g(10/27 の生成の保存。表は run_tp_f3b / f4b と全セットで同一)を上書きしかけた。表と保存が書き換わる前に PID で止めた。失われたのは、二つの features.log だけである。既存の保存を使うジョブ(spark_s2_dump_f34b.sh)に置き換えた。
