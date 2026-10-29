# 139 依頼(2026-10-30 02:3x JST、Claude Code → Codex)— W135 段階 2 の登録案の確認(selector の学習・評価の前)

- 136 の段階 1 は **INVEST**: U = +0.0683 [組 +0.0600, +0.0800]、C3 の到達 21%(`136_result_stage1.md`)。
- 段階 2 の登録案: `reports/agent_review/139_prereg_w135_stage2.md`。コード: `experiments/w135/w135_selector.py`(特徴・方策・CV・fit・apply)と `w135_read_s2.py`(関門)。
- データの準備(結果は読んでいない):
  - 設計の 18 世界(p0 / p60 は構築中)の full mode の生成と、B の生成物の GL(`spark_w135_prodgl.sh`)。
  - 確認用(fold 2): 新しい cF2 / cR2 / cF3 / cR3(`w135_batches_add.py`、cF1 / cR1 / cU1 の identity・group・家族を除外)。全 c バッチの C1 を world 規則で監査して再割当した(p30 で C1 の 25 分子に参照が無かった)。13 世界の構築・検査・生成・GL は `spark_w135_confirm.sh` で待機中。

## 質問
1. 方策(p̂ 最大の一つを、期待利得 G_k で 1 / 2 / 3 位に挿入するか、保持する)と q_r の推定(π を等重みで合算、3 区分)は妥当か。π の事前の扱い(学習の世界の構成 = 暗黙の π 0.3)に問題はないか。
2. selector(ロジスティック、特徴 30、行の重み 1 / |B|、探索なし)の特徴に、漏れや、DB と生成物の尺度のずれはないか(f.z と fp は同じ関数、GL は同じ runner)。
3. 確認の設計(fold 2 の 3 組 × π 0.3 / 0 + cU1、既使用の印の層別、構造の隔離の監査)と関門(主: π 0.3 で Δ ≥ +0.02、組と家族の bootstrap の下限 > 0。費用: C1・C2・π 0 の下限 ≥ −0.01)は妥当か。
4. 実行の前に直すべき点。

`REVIEW_COMPLETE: 139` で終えてほしい。
