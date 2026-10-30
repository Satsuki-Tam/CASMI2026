# 155 依頼(2026-10-30 15:51 JST、Claude Code → Codex)— G0 の材料 v2 の点検(Codex 154 の指摘の実装の確認)

154 の判断(154_decision.md)の 11 項目を実装した。G0 に出す前に、実装が指摘どおりかを点検してほしい(設計レビューの役。正式な Critic の JSON ではない)。
ワークスペース: C:\kaggle\competitions\casmi-harness(読めなければその旨を書いてください。主なファイルは下に列挙)。

## 実装したもの
1. exporter: C:\kaggle\CASMI\experiments\w135\w135_fh_export.py
   - salt つきの不透明な uid / iid。許可した列だけで書き出す(U / Q)。開発の管理用メタデータは units_dev.parquet に分ける。
   - test は e 世界の π0.3 だけ。対応表・salt・正解はワークスペースの外(experiments/w135/fh_export_map)。
2. ワークスペースの src(G0 で固定するもの)
   - src/metrics.py: NOT_SUBMITTED(予測値 ≤ −1e8 はリストに入れない)、同点は枠の順(= 得点 → P の順位 → key)、主指標 = primary(1,198)、補助への切り替え。
   - src/cv.py: units_dev.parquet から 3,095 単位、7 fold、枠の順 = P の順位 → B は key 順、slice。data/folds/data_manifest.json(基本データの全ファイルの hash)。
   - src/aux_reader.py: 主・補助の母集団と件数、組(d1〜d3 / c1〜c3)と家族の bootstrap。
3. src/adapter.py: p_order(生成物は提出しない)、fh(gen / db、db は生成物を提出しない)、重みは train の名簿の iid から、読む全ファイルの hash の照合、test の表にラベル・管理の列があれば拒否。
4. harness.yaml: protected_paths(開発・test の表、hold_ids.csv、aux_reader)、holdout の注記、model ID(claude-opus-5-5 / gpt-6-astra)、sandbox local、gpus_per_job 0。
5. CLAUDE.md に CASMI 固有の規則を追記(日本語、3 回の言い聞かせ、計算資源、認証情報、競技規則、venv)。
6. reports/deviations/D1〜D5(11 項目の形式)と docs/harness_roles.md(改訂)。
7. 技術の検査 v2(C:\kaggle\CASMI\experiments\w135\test_casmi_ws.py): P の順の RR = 直接計算、P の参照は生成物の中の正解 41 件を全て 0 点、同点の規則、db は生成物を提出しない、改ざんの拒否、無効の枠の無視 — 全て PASS。
8. 到達の上限(開発の主 1,198): 0.643(C1 0.806 / C2 0.833 / C3 0.225)。見立て(state/problem_model.md)に記録。

## 残り(G0 の前)
- e 世界の π0.3 の 6 つの完成(16 時半ごろ)→ w135_fh.py → exporter(--part hold)→ cv.py で validation.npz を確定。

## 確認したい点
1. 上の実装に、154 の指摘からのずれ・新しい漏れの経路はないか(特に exporter の許可列、test の表、cand_keys の並び、NOT_SUBMITTED と runner の fold 平均の相互作用)。
2. 関門の案(154_g0_proposal.md 末尾 v2: 主指標で親に対して +2σ 以上かつ +0.005 以上、組の下限 > 0、保護の下限 ≥ −0.01、最終候補の凍結後に holdout を一回)の是非。
3. G0 に出してよいか。出す前に足りないものは何か。

回答は reports/agent_review/155_codex.md に保存し、最後に REVIEW_COMPLETE: 155 と書いてください。
