# ハーネスの役割の分担(Claude Code / Codex / 利用者)— 2026-10-30 15:11 JST、Claude Code 作成

kaggle-harness(v0.1.0)は Claude Code だけで回す前提で作られている。CASMI では Codex も議論・レビューに加わっているので、ハーネスの 6 役と人間の承認 G0〜G4 を次のように割り当てる。根拠はハーネスの規則(Judge は提案者と別のモデル ID、Critic は独立、発想役は互いに独立でパケットだけを読む)と、これまでの Codex の実績(登録・コードの点検、文献の数字の訂正、設計の欠陥の指摘)。

| 役割(ハーネス) | 担当 | 起動の仕方 | 補足 |
|---|---|---|---|
| Orchestrator | Claude Code(主セッション) | — | 状態の変更は全て `tools/state_cli.py` など固定のツール経由。生ログは読まない。 |
| Executor | Claude Code(実験ごとの新しいサブエージェント) | Agent | 実装・事前登録・実行。修正は新しい実験 ID。 |
| Analyst | Claude Code(新しいサブエージェント) | Agent | OOF の誤差の表から、発見ごとに 2 つ以上の機構・予測・検証法。説明できない発見は違和感へ。 |
| **Critic** | **Codex** | 既存の CASMI レビュー会話へ `codex queue`(番号つきの依頼) | 特徴・前処理を変える実験(`changes_features: true`)のリーク・再現性・規約の点検。回答は `reports/critic/<exp_id>.json`(reviewer, verdict, source_hash, checks, findings)。G0 前の CV・指標・fold の点検も担当。 |
| **Judge** | **Codex**(提案者 Claude と別のモデル) | 毎回新しい文脈の `codex exec`(読み取り専用)。入力は提案・過去の要約・公開差分マップ・近傍 8 件だけ | 新規性 P / H の採点 JSON。モデル ID が未確定・同じなら採点しない。Windows ではパケット限定の OS 隔離が無いので、「指示による読み取り範囲の制限」を逸脱として記録する。 |
| Ideator(3 役) | Claude(新しい文脈)+ **Codex**(新しい文脈の `codex exec`、パケットだけを渡す)+ Gemini の代わりの 2 つ目の Claude | `tools/ideate_external.py` は Codex の隔離ランチャーが無いと Codex を実行しない。手動で Codex を呼んだ場合は、その事実と隔離が無いことを記録する | 代替(Gemini → Claude)も記録する。 |
| Librarian | Claude Code(サブエージェント、Web 調査) | Agent | 重要な数字・主張は Codex が一次資料で照合する(148 の文献の数字の訂正と同じ役)。 |
| 人間の承認 G0〜G4 | **利用者** | 利用者の端末で `python tools/human.py ...` | エージェントは承認トークンを発行しない。提出は G3 のトークンつきの `tools/submit.py` だけ。 |

## これまでとの違い(運用)
- 提出: 10/29 の「候補を優先、診断は相談」、10/30 夜の「今日の分は裁量で提出」は、ハーネスの G3(人間が成果物ごとに承認)に置き換わる。
- Public LB: 最適化の目的ではなく、違和感の検出の観測値として記録する(`tools/submit.py lb`)。
- 実験: 全て仮説・ブランチ・定量の予測(全体とスライスの metric_delta)を事前登録してから実行する。CV・指標・fold は G0 で固定し、変えるときは新しいワークスペース。
- 外部のデータ・モデル: G4 で承認した資源 ID だけを使う。
- Codex への依頼の番号(reports/agent_review/NNN)は、ハーネスの外の議論・設計レビューに引き続き使う。Critic の JSON と Judge の JSON は、ハーネスのワークスペースの規定の場所に保存する。
