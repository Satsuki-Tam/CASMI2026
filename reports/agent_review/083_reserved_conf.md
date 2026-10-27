# 083 予約: 新しい確認集合(fold 4 の COCONUT 収載正解 1,000 分子)— 作成のみ、未開封

作成: 2026-10-27 13:42 JST(Claude Code)。
- 中身: `np061_f4pool`(061 で fold 4 から選んだ COCONUT 収載正解、seed 64、NP_H 600 / NP_X 200 / NP_N 200;既存のどの集合とも identity group が素、MSG に無い)。当初は学習 pool の予定だったが、071 で COCONUT 正解 pool の学習は prior を動かす(非収載 −0.011・パネル C1 clean −0.011)ことが分かり、学習には使わず**確認集合**に転用する。073(fold 3/4 の未使用分)とは identity が重ならない(061 の選択時に 073 の元 = conf 側と分けている)。
- 表: PC で b1_features(fpnet_fold4 = fold 4 の identity に未見)+ GL(NP_H)、`run_np083_f4conf`、gen dump 付き。表が出来ても主出力・差分は計算しない。
- 用途: 一つに固定した候補の確認に一回だけ使う。割当ては候補の開発結果を読む前に別の登録で行う。
