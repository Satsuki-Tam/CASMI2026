# 064 事前登録(診断): dev2 での FPNet × ranker の 4 セル交差比較(Codex 062 Q2)

作成: 2026-10-27 05:29 JST(結果の前)。目的: 「f1/f2(公開 fold の表)では v8w が正、dev2(full_eval の表)では 0〜負」が、FPNet の違い(checkpoint)によるのか、分子・化学・参照条件の違いによるのかを、同じ dev2 の query で切り分ける。
- セル: {公開 fpnet_fold0(dev2 = fold 0 なので未見), 自前 full_eval(dev2 = hold で未見)} × {rank_v4b, rank_v8w}。full_eval 列は既存の `r047_rank_v4b_p2dev` / `r056_rank_v8w_p2dev`(gen_eval2 67d113ec、run_p2dev_fe)。fold0 列は現行の b1_features で dev2 の表を作り直し(--dump_gen、run_p2dev_f0x)、GLACIER を掛けて同じ gen_eval2 で評価する(端から端 = 各 FPNet が自分の shortlist を作る)。
- 量: 各列で Δ = v8w − v4b(分子ごと)、交互作用 I = Δ(full_eval) − Δ(fold0)、層ごと(C/D の C1/C2、G)と NP C2 マクロ、identity bootstrap。
- 読み: I が NP C2 で負に大きく(例えば −0.01 未満で区間も負側)、fold0 列の Δ が f1/f2 と同程度に正なら「checkpoint の違いが v8w の利得を消す」→ v8w の本番化には full_eval の特徴での ranker の再学習(または FP の尺度・露出を揃える)が必要。I ≈ 0 で両列とも小さいなら、f1/f2 との差は分子・化学の違い(dev2 の層の構成)によると読む。いずれも v8w の採否そのものではない(確認は 3b/4b、parity は別)。
- dev2 は何度も使った集合なので、独立の確認とは呼ばない。
