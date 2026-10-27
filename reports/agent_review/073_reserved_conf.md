# 073 予約: 新しい確認集合(COCONUT 収載正解・fold 3/4 の未使用分)— 作成のみ、未開封

作成: 2026-10-27 09:30 JST(Claude Code、Codex 070「学習を増やす前に、未使用 identity から確認群を予約」を受けて)。
- 中身: `np061_f3unused` / `np061_f4unused`(061 の p3_select_np で pool に入らなかった残り = 既存のどの集合とも identity group が素、MSG に無い、正解は COCONUT 収載)。
  fold 3: NP_H 214 / NP_N 139 / NP_X 13、fold 4: NP_H 268 / NP_N 110 / NP_X 3。
- 表: 手元の PC で b1_features(fpnet_fold3/4 = その fold の identity に未見、hash は表の manifest に記録)+ GL(NP_H)、`run_np073_f{3,4}conf`、gen dump 付き。
- 用途: **一つに固定した候補の確認に一回だけ使う**。どの候補に使うかは、その候補の開発結果を読む前に別の登録で割り当てる。表が出来ても主出力・差分は計算しない。
- 注意: ranker の学習 pool(tp_f3a/f3b/f4a/f4b、np061_f3pool)と同じ fold の別 identity。学習表と同じ fold の FPNet で特徴を作るので「下流 ranker の fit と評価 group が非重複、評価 query 用 FPNet は未見」という比較(Codex 070 の表現)になる。上流モデルまで通した厳密な holdout ではない。
- 053 X・056 の 3b/4b・067 の locked2 は数え直さない。053 の NP_H/NP_N conf は 071 の確認用に残す(未開封)。
