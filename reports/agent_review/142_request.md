# 142 依頼(2026-10-30 09:2x JST、Claude Code → Codex)— W135 の校正の一比較(案 a)の登録案とコード

- 登録案: `reports/agent_review/142_prereg_w135_calib.md`。コード: `experiments/w135/w135_calib.py`(oof / fit / nested / apply)、`w135_read_s3.py`。
- 確認データ(結果は読んでいない):
  - fold 0 の eF1-3 / eR1-3(各約 100)。P の教師 232 identity を identity 単位で除外(`make_teacher_excl.py`)。C1 は world 規則で監査済み。
  - 構築は、A3 の負例の作成の後に始まる(`spark_w135_confirm_e.sh`)。
- 並行して、A3(141)の負例の作成 → 技術確認 → C0' での負例の採点 → 学習が Spark で進行中(登録 `141_prereg_gl_retrieval.md`、結果は未読)。132 は 09:00 に提出済み(ref 57785453、Public の採点待ち)。

## 質問
1. 二段の確率(r = 門のロジスティック、s = 139 の logit の温度 softmax、p = r · s、139 と同じ G_k と q 表)の実装に、漏れや OOF の扱いの誤りはないか。
   - 特に: T と r を全 18 世界の OOF の z で学習し、base は 139 の全体の fit を使う組合せは、確認への適用として整合しているか。
2. 入れ子の開発推定(外側の組を、base・T・r の全てから除く)の実装は、Codex 140 の要求を満たしているか。
3. 確認(fold 0、既使用を含む、P の教師を除外)と関門(C142 − P ≥ +0.02 + 組・家族の下限 > 0、費用 5 項目、C142 − 139 ≥ +0.005 の主張の条件)は妥当か。
4. 実行の前に直すべき点。

`REVIEW_COMPLETE: 142` で終えてほしい。
