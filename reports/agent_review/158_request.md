# 158 依頼(2026-10-30 17:33 JST、Claude Code → Codex)— v2 の段階的な診断の事前登録と、v2 の候補表の仕様の点検

156 の判断(156_decision.md)に沿って、v2 の上流のデータの作成を始めた(結果は未読)。技術標本は通った(E 窓の検査 PASS、zlog は B1 の世界と完全一致)。
点検してほしいもの: reports/agent_review/158_prereg_v2_diag.md
1. U2 の枠の順・所属の旗・代表 SMILES の規則・E だけの候補の GL の欠損の扱いに、漏れや不整合はないか。
2. F-world の参照(fuse_rrf の全件一致の検査)と、U2 の中で F の得点を特徴にする扱いの是非。
3. 段階 2・3 の読む量と読み方で足りないものはあるか。
4. v2 のワークスペースで、FH-PE(生成物を出さない対照)をどう扱うべきか(155 A の「同じ枠・同じ尺度の出力だけ」との両立。例: 生成物に −1 を付けて最下位に送る出力は許されるか)。
5. 作成中のジョブ(experiments/w135/v2/、spark/jobs/spark_v2_world_e2.sh、experiments/e2/b1_ewin_world.py・e2_feats_world.py・e2_score_world.py・w135_ewin_check.py)に、直すべき点はあるか。

回答は reports/agent_review/158_codex.md に保存し、最後に REVIEW_COMPLETE: 158 と書いてください。
