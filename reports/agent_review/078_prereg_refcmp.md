# 078 事前登録: 参照の比較可能性の特徴ブロック(Codex 072 Q3 / 075 (a))— v8w のデータ・パラメータ固定の一対比較

作成: 2026-10-27 12:09 JST(学習・評価の前、Claude Code)。
- **定義(厳密、学習・評価・本番で同じ)**: b1_features の参照選択(query 選択、清浄化、完全重複・近重複の除外、MAX_REF 24 の上限と同 adduct 優先、C1 = 真の query ライブラリの参照を除く / C2 = 真の参照を全て除く)の後に残った参照について、n_cmp_pol = query の極性と同じ極性の参照数(類似度を実際に計算した参照)、n_cmp_add = query の adduct と同じ adduct の参照数。`refcmp_exact.py` で保存済みの表に再現(類似度・参照数が表と完全一致することを各 run で検査)。本番の pipeline には同じ計算を後で入れる(採用の前に parity で一致を確認)。
- **特徴(4 つ)**: lib_has_cmp = 1[n_cmp_pol > 0]、lib_ncmp = log1p(n_cmp_pol)、lib_has_add = 1[n_cmp_add > 0]、lib_sim_cmp = lib_sim(比較あり)/ NaN(比較なし = 欠測)。既存の lib_sim・fallback の 0 は変えない。lib_nref / in_train は従来どおり外したまま。
- **条件**: v8w_cmp = v8w と同じ fit 群(run_v3_p1/eval/c1、tp_f3a/f4a)・C1 複製・パラメータ(rank_v4b 由来、300 rounds)・feats v2_noice_cmp。**対照 = v8w_pc**(同じ環境で再学習した v8w)。EA は off(EA との交互作用は別に)。
- **評価**(gen_eval2m、同じ一回の評価で v4b・v8w_pc・v8w_cmp、071 と同じ 6 表): 主指標 = 053 dev NP_H C2(COCONUT 収載正解、f1/f2 block 等重み)、τ = +0.005(v8w_pc 比)。主保護(ε = 0.01、三状態): パネル C1 clean、f1/f2 の G C1(block 等重み)、f1/f2 NP C2(C/D/E/F)。副次: 非収載正解の C2(正解 key を COCONUT 所属表に結合)、dev2、053 NP C1、shortlist 到達条件付き。
- **選択(開発)**: 主保護で U < −ε が無く、かつ確認の関門と同じ非劣性(パネル C1 clean と G C1 の下限 > −0.01)を満たし、主指標 ≥ τ のときだけ候補。候補になった場合の確認は 053 NP_H/NP_N conf(未開封、075 で再割当て可)— 確認の条件は候補が出た時点で、結果を読む前に別途登録する。

## 追記(12:16、学習後・評価前)
- 厳密な再計算の一致(`diag/refcmpx_run_*.log`): 参照数(= 比較可能性の数の母集合)は新しい表で 99.98〜100%、10/24〜25 の旧版 b1_features で作った v3 系の学習表(run_v3_p1/eval/c1)で 99.56〜99.96%(C1 view の参照除外と上限の順序の修正前のため)。類似度の不一致は 0.1〜1% で、差はほぼ ARM / x86 の浮動小数の微小差(新しい表で最大 0.01)。v3 系の不一致行はそのまま学習に入る(除外すると v8w のデータではなくなるため)ことを記録する。
- v8w_cmp(sha eb531464)は v8w と同じ 3,931 群・c1 share 0.457。新しい特徴の分割回数: lib_ncmp 444、lib_sim_cmp 318、lib_has_add 7、lib_has_cmp 3。
- 評価は 077 と同じ一回の gen_eval2m(--refcmp)で v4b・v8w_pc・v9a・v9b・v9b_w・v8w_cmp を採点(`pc/jobs/pc_eval077078.sh`)。
