# 022 判断: pool60 は不採用で確定。「M2x + full_eval のみ」の今夜の比較提出の基準を結果を見る前に固定

作成: 2026-10-25 16:00 JST(Claude Code)。依頼 `022_request.md`、回答 `022_codex.md`。full_eval の評価結果(`fe_eval_*`)はこの時点で未生成。

## 1. 判定基準(結果を見る前に固定)
- **主比較**: パネル C1 の **clean 202 分子**(残存学習スペクトルとの最大類似 < 0.90 = 「高類似の残存例を検出していない群」;取得の独立性の証明ではない)の登録主出力 paired ΔMRR。uncertain 48(高類似の残存例がある群;重複確定ではない)と全 250 を併記。区分は固定 CSV(sha256 961ceb94…)のまま動かさない。候補不在は 0 で分母に残す。clean の区間が 0 を含めば「利得は未確定」と付記。
- **保護**: dev2 の C2(C/D/E/F/G)、C1(C/E/F/G;D/C1 は NA)。各層で点推定と 95% 下限が ≥ −0.02。W7(学習済み)とパネル C2(identity 学習済み)は保護に使わない。locked2 は開けない。

| 結果 | 今夜の扱い |
|---|---|
| clean C1 の点推定が正、dev2 全保護層で点推定・下限とも ≥ −0.02 | 実装・監査条件も満たせば比較提出 |
| clean C1 の点推定が正、全保護層の点推定は ≥ −0.02 だが一部の下限 < −0.02 | **非劣性未確定の一回の比較提出として可**(未確定の層を提出前に固定記録、本命 0.354 は保持) |
| 保護層の点推定 < −0.02、または clean C1 の利得なし(uncertain だけ改善) | 見送り |
| 参照・学習除外、checkpoint、候補生成、出力に未解決の不一致 | 比較提出も保留 |

- Public の読みは 020 のまま(基準 0.354 / 57610156、一変更のみ、±0.02 は運用閾値;Public で未確認のローカル保護を合格に変えない)。

## 2. 実装確認(実施中)
- `spark_parity_fe.sh`: パネル 16 分子(GL 被覆の多 adduct 5、GL 不足 4、参照優先が発火しうる 4、最大の窓 3;候補ゼロの例はパネルに無い — 未網羅として記録)で、提出パイプライン(`--fpnet_ckpt` = 同じ checkpoint)と評価器の表(run_panel_fe)を両 view・共有 forward・閾値 1.0 で比較。モデル・予測・stage stats を渡して出力比較が実際に走ることを確認する。
- Kaggle 実行では dataset version と checkpoint sha256 をログと manifest で確認する。

## 3. dataset(private)の記録
- `kernels/fpnet-fulleval-dataset/`: checkpoint + `TRAINING_MANIFEST.json`(checkpoint 内の全学習引数、コード・入力・記録の sha256、環境、最終評価、commit e0fb59c)、`code/`(使った trainer・生成スクリプト・前処理・casmi パッケージ・監査コード)、`records/`(gate、実測の hold-out 交差 0、split、dropped rows 1,196、パネル監査群、dev2/locked2 一覧)。README は pool 由来の負例(train 構造 + COCONUT)を明記。作成後に可視性(private)を確認する。
