# 087 事前登録: v7f 型 ranker に v8w の学習構成を移す一対比較(Codex 082 / 084 の手順 3)

作成: 2026-10-27 18:07 JST(学習・評価の前、Claude Code)。
- **対照 rank_v7a_pc**: rank_v7a のレシピ(run_v3_p1 fit + run_v3_eval + run_v3_c1、feats v2_noice_ana − lib_nref − in_train、C1 ×3、パラメータ = rank_v4b と同じで 600 rounds = rank_v7a のモデルファイルの parameters 節と一致)を PC で再学習。analog 特徴は PC の analog_probe(`diag/analog_tr_v3*.parquet`)。元の rank_v7a(Spark)とは木の構造が違い、053 dev fold-1 で v7a_pc − v7a = C2 −0.0023(320 中 27 行が変化)、C1 −0.0027 → **再現差として記録し、比較はすべて PC の v7a_pc を対照にする**。
- **候補 rank_v8w7a**: 対照と同じ特徴・パラメータ・出力規則で、学習群に v8w の pool(run_tp_f3a / f4a、fit、C1 ×1、analog 特徴 = analog_tr_tpf3a/f4a)を足す(= v8w と同じデータ構成;C1 比率は v8w と同様 0.457 前後を記録)。EA は off。
- **評価**: gen_eval2m --v7f(v7f の主出力 = GL 経路で 2 z(ranker) + z(固定則)、外側の analog 項なし、GL 不足は保険 + z(ap) + z(MetFrag-lite);gen_eval2pv と 372/372 行一致を確認済み)で rank_v7a・rank_v7a_pc・rank_v8w7a を同じ一回で 053 dev f1/f2、f1dev、f2dev、パネル、dev2 に掛ける。
- **主指標**: 053 dev の NP_H C2(COCONUT 収載正解、GL 経路)、f1/f2 block 等重み、**v8w7a − v7a_pc**、τ = +0.005。併記: B 群に絞った順位(B 内 1 位率、B probe 相当)の差、非収載正解の C2(正解 key を COCONUT 所属表に結合)、GL 経路と fallback の分け(fallback は ranker を通らないので Δ ≡ 0 の点検)。
- **主保護**(ε = 0.01): パネル C1 clean、f1/f2 の G C1、f1/f2 NP C2(C/D/E/F)— 確認へ進む条件は三つとも下限 > −0.01(非劣性)。
- **確認**(関門を通った場合だけ): 予約 **083**(fold 4 の COCONUT 正解、NP_H を主対象)を一回 — 条件は関門を通った時点で、結果を読む前に追記する。
