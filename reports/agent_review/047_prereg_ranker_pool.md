# 047 事前登録(学習・評価の前に固定、23:16 JST): ranker の学習行を fold-3/4 の pool で拡張(固定パラメータ)

- 候補 **rank_v8a**: rank_v4b のレシピ(`--feats v2_noice --drop lib_nref in_train --c1_repeat 3 --params_from rank_v4b/rank_results.json`、学習 runs = run_v3_p1:fit + run_v3_eval + run_v3_c1)に、**fold-3a・fold-4a の pool を fit として追加**(`run_tp_f3a:train_pool_f3a/p2_molecules.csv:fit`、`run_tp_f4a:train_pool_f4a/p2_molecules.csv:fit`;特徴は各 fold の fold-safe FPNet = 未見)。パラメータ・round 数は rank_v4b と同じ(データ拡張の効果だけを見る)。
- 対照: **rank_v4b**(登録済み)と、同じレシピを pool 無しで再学習した **rank_v4b_r**(再学習の雑音の確認、rank_v4b と同一になるはず)。
- 主出力 = anaw0.5(blend21 = 2 z(ranker) + z(fixed)、GL 不足は保険、+ 0.5 z(ap))。ranker だけを入れ替える。
- 学習に入る query group 数(層 × view × fold、正解到達・GL 被覆・C1 usable)を学習ログから性能を見る前に記録。
- **開発(採否)**: fold-1 dev(fpnet_fold1)と fold-2 dev(fpnet_fold2)の C2 NP マクロ(C/D/E/F 等重み、二ブロック各 1/2)の Δ(rank_v8a − rank_v4b)> 0。保護: fold-1/2 dev の C1(C/E/F/G)・C2 G、dev2 v2(full_eval)の C1/C2 全層、パネル full_eval の C1 clean 202 と C2 で Δ ≥ −0.01(点推定)。
- **確認(一回)**: fold-3b・fold-4b(新 ranker の学習に入れない;FPNet は各 fold 未見)で、C2 NP マクロ Δ > 0 かつ C1/C2 全層 Δ ≥ −0.01。fold-1/2 locked は生成の確認で開封済みなので使わない。
- 限界(Codex 045): fpnet_fold3/4 は fold-0/1/2 の identity を学習済み → fold-1/2 での評価は「ranker の fit 行と評価 group が重ならない開発比較」。C1 ×3 は「identity 既見・query 未見」の学習条件ではない(パネル C1 clean を保護層に置く)。
