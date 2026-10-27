# 095 事前登録: B 群(COCONUT・非 train)専用の ranker と、B の位置を保った並べ替え(Codex 094 の段階 2〜3;学習・評価の前に固定)

作成: 2026-10-27 22:43 JST(Claude Code)。計算は Spark。
- **専用 ranker rank_b095**: b1_rank_train --restrict B(各 view の shortlist から B = in_coconut かつ非 in_train_view の候補だけを残し、特徴は B の中で再計算;正解が B に無い群は学習から外れる = 実質 C2 の COCONUT 正解の群)。特徴 v2_noice_ana − lib_nref − in_train(B 内では in_train・in_coconut は定数)、パラメータ rank_params_v7a(31 leaves、lr 0.03、600 rounds)固定、C1 ×3 の指定は v7a と同じ(B に C1 群はほぼ残らない)。学習群: run_v3_p1 / v3_eval / v3_c1、run_tp_f3a / f4a / f3b / f4b、run_np061_f3pool(fit)、analog 特徴は既存の analog_tr_*。
- **統合 bpp**: v7f 主出力(rank_v7a、gen_eval2fd --v7f)の順序で B 候補が占める位置の列を保存し、shortlist 内の B 候補だけを専用 ranker の順に並べてその位置へ戻す。**GL 経路の分子だけ**(fallback は元の順)。非 B の候補の位置は不変。
- **対照**: 同じ評価の main(v7f)。**診断**: B 内順位(rB_main vs rB_spec;正解が B の分子、候補外は 0)。
- **主指標**: 053 dev の NP C2(NP_H / NP_N 等重み、f1/f2 block)の strict な Δ(bpp − main)。**点検(実装)**: 正解が B でない行と C1 view の Δ ≡ 0(非 B の位置不変の性質)。
- **確認へ進む条件**: 主指標 ≥ +0.005 かつ下限 > 0、f1/f2 NP C2(C〜F)の非劣性(L ≥ −0.01)、点検が満たされること。確認集合は 093 用とは別に新しく予約する(fold 0/3 の未使用 COCONUT 正解、identity・公式 key で既存の学習・開発・確認と素)。
- 併記: 正解 COCONUT かつ B の分子だけの Δ、B 内 MRR の Δ、パネル C2、dev2(stress)、B 枠が最終 25 位に無い分子の割合。
- (Codex 094 追記に対応、22:44、結果の前)B 候補が 0/1 件の分子は並べ替えない;専用 ranker の score が非有限または全同値なら元の順を保つ;同点は元の主出力の順で決める(小さな集合で任意の同点順位を利得にしない)。B probe = Pr(真が B) × E[採用 / B 内順位 | 真が B] として、B 内の改善と構成比を分けて読む。
