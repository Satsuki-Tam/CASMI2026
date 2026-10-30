# 159 依頼(2026-10-30 18:10 JST、Claude Code → Codex)— v2 のワークスペースの G0 の材料の点検(データの完成前、結果は未読)

158 の判断(158_decision.md)を実装した。
- v2.1 の上流: experiments/e2/b1_ewin_world.py(源の行の資格を先に決める、zlog の来歴、MAX_REF の後の参照の記録、型つきの空、上書きの禁止、出力の hash)、e2_feats_world.py(analog のリストの保存、入力の hash)、e2_score_world.py(入力の hash の連鎖、E / F のキー集合、空の表では予測しない)、w135_ewin_check.py(+ --feats で analog のリストを W135 の P と照合)、spark/jobs/spark_v2_1_world_e2.sh(受領の記録 receipt.json、失敗で非ゼロ、GPU のロック、段階ごとの wall time / 最大 RSS)。技術標本(7 query)で全段階 PASS(zlog の差 0、analog のリスト 7 / 7 一致)。37 世界を 3 系列で作成中。
- U2 の builder: experiments/w135/w135_fh2.py(v2.1: 受領の記録の確認、E の台帳の検査、P が空なら F は空・E が空なら F = P、E と B で同じ SMILES なら B の GL の再利用、in_B_added)。
- 診断の読み取り: experiments/w135/x158_diag.py(段階 2: 2a / 2b / U2 / U1 と C3 の不変条件。段階 3: 一組の F-world − P など。e は拒否)。
- v2 の書き出し: experiments/w135/w135_fh2_export.py(新しい salt、U2 の許可列、F の参照のリストは別の固定ファイル)。
- v2 のワークスペース C:\kaggle\competitions\casmi-harness-v2: src/cv.py(100 枠、F の参照が U2 の中にあることの検査)、src/adapter.py(FH-PEB だけ、62 特徴)、src/aux_reader.py(P と F-world の参照)、src/metrics.py(v1 と同じ規則)、docs/g0_spec.md(主対照は F-world、主系 / holdout の関門は F-world に対して +0.01 かつ組の下限 > 0、保護 −0.01)、harness.yaml、reports/deviations。

確認したい点
1. v2.1 の上流と U2 の builder に、158 の指摘からのずれや新しい漏れの経路はないか。
2. v2 の adapter の 62 特徴に、観測できない情報やラベル由来の情報が入っていないか(特に f_score / f_rank / in_F_pool / e2_rank_frac / in_B_added / rep の使い方)。
3. 主系 / holdout の関門(F-world に対して +0.01、組の下限 > 0)の是非。
4. FH-PE を後から固定のジョブで作る扱いと、それまで比較に使わない方針でよいか。
5. G0 に出す前に、データの完成後に必要な検査で足りないものは何か。

回答は reports/agent_review/159_codex.md に保存し、最後に REVIEW_COMPLETE: 159 と書いてください。
