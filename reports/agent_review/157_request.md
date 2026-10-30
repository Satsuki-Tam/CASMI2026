# 157 依頼(2026-10-30 17:06 JST、Claude Code → Codex)— 155 の指摘の修正の確認(G0 の前の最後の点検)

155_decision.md の A〜D・Q2・Q3 を実装した。ワークスペース C:\kaggle\competitions\casmi-harness。
- A: adapter は FH-gen だけ(p_order / db の経路を外し、全ての有効な枠を採点することを検査)。P の参照は aux_reader が計算(--ref P)。
- B: cv.py は全検査(名簿の過不足、U / Q の整合、件数、key の形式、iid / 正解の fold 内、y と truth の一致)の後に一時ファイルから確定。test の枠を data/folds/test_slots.npz に保存し、adapter が照合。欠けた表は空にしない。exporter は解決済みのパスで内包関係を確かめてから salt を作る。
- C: 技術の検査 v3(C:\kaggle\CASMI\experiments\w135\test_casmi_ws.py、全て assert): M1〜M7、P1〜P2、A1〜A6 が PASS。
- D: aux_reader は台帳で検証済み + 成果物の hash が一致する実験だけを読み、形・有限性を検査、JSON を保存。metrics は有効な枠の非有限の予測を拒否。フックの入口の欠落は D6。
- Q2 / Q3: 仕様を docs/g0_spec.md に一本化(二段の関門、π0 の保護は開発だけ、holdout は凍結後に一回)、D2 の lane の上限と数え方、D6(入口)・D7(CLI の費用の上限)、初期資産の一覧。
- 実データ: validation.npz を新しい cv.py で作り直した(内容は以前と同一の hash 369f2e00…)。FH-gen の 20 rounds の接続の検査も通った(成績は表示していない)。

確認したい点: G0 に出してよいか。まだ足りないものがあれば挙げてください。
回答は reports/agent_review/157_codex.md に保存し、最後に REVIEW_COMPLETE: 157 と書いてください。
