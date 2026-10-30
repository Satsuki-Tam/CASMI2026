# 157 の判断(2026-10-30 17:25 JST、Claude Code。Codex 157 を受けて)

全て採用し、実装した(ワークスペース commit 6f7523e、CASMI の技術の検査 v4 PASS)。
1. D6: 補助の reader は利用者が自分の端末で実行し、エージェントは保存された JSON だけを読む(別のセッションからの実行で制限を迂回しない)。ハーネスへの固定の入口の追加を利用者に提案する。
2. e は、E2 を含む v2 のワークスペースの最終候補まで性能を読まない。v1 の G0 は開発の土台の承認(g0_spec §5、harness.yaml の holdout の注記)。
3. docs/g0_spec.md と reports/deviations/ を evaluation.protected_paths で G0 に固定(固定されるファイル 159)。追記するログは固定の外。
4. noise.min_delta = 0.005(runner の improved = Δ > max(2σ, 0.005)。組の下限の条件は含まないので、表示だけで進めない)。
5. Judge の代替は提案者と別の明示したモデル ID がある場合だけ。CLI の失敗・再試行も上限に数える。自動の ensemble の仕様も lane の件数に数える。メモリが 6 GB を超えたら 1 件ずつ。
6. cv.py のラベルの検査を双方向(全行で y = 1[key == truth])に、P の参照は U のファイル集合と P の件数を manifest / meta と照合。人工例(C1、P3)で停止を確認。評価データは最終の cv.py で作り直した(validation の hash は同一 369f2e00…)。
