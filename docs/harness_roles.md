# ハーネスの役割の分担(Claude Code / Codex / 利用者)— 2026-10-30 15:11 JST、Claude Code 作成

kaggle-harness(v0.1.0)は Claude Code だけで回す前提で作られている。CASMI では Codex も議論・レビューに加わっているので、ハーネスの 6 役と人間の承認 G0〜G4 を次のように割り当てる。根拠はハーネスの規則(Judge は提案者と別のモデル ID、Critic は独立、発想役は互いに独立でパケットだけを読む)と、これまでの Codex の実績(登録・コードの点検、文献の数字の訂正、設計の欠陥の指摘)。

| 役割(ハーネス) | 担当 | 起動の仕方 | 補足 |
|---|---|---|---|
| Orchestrator | Claude Code(主セッション) | — | 状態の変更は全て `tools/state_cli.py` など固定のツール経由。生ログは読まない。 |
| Executor | Claude Code(実験ごとの新しいサブエージェント) | Agent | 実装・事前登録・実行。修正は新しい実験 ID。 |
| Analyst | Claude Code(新しいサブエージェント) | Agent | OOF の誤差の表から、発見ごとに 2 つ以上の機構・予測・検証法。説明できない発見は違和感へ。 |
| **Critic(正式)** | **Codex の新しい文脈**(`codex exec -s read-only`、CASMI リポジトリの外の新しい作業場所に、登録した source の snapshot と成果物だけを置く) | 実験 ID と source snapshot が決まった後 | `changes_features: true` の実験のリーク・再現性・規約の点検。JSON(reviewer, verdict, source_hash = 登録済み source_hashes の正規 JSON の digest, checks, findings)を `reports/critic/<exp_id>.json` へ。source が変わったら旧レビューは使わない。古い番号つき Markdown を pass の JSON に変換しない。 |
| 設計レビュー(文脈あり) | **Codex(既存の CASMI 会話)** | `codex queue`(reports/agent_review/NNN) | G0 の前の CV・指標の点検、過去の結果との照合、文献の重要な主張の照合。正式な Critic / Judge の代わりにはしない。 |
| **Judge** | **提案者と別のモデル**: Claude(claude-opus-5-5)の案 → **Codex(gpt-6-astra)の新しい文脈**、Codex の案 → Claude の新しい文脈 | 毎回新しい文脈。入力は提案・過去の要約・公開差分マップ・近傍 8 件だけ | 新規性 P / H の採点 JSON(proposer_model / judge_model を実際の ID で記録)。同じモデル ID なら採点しない。代替の Claude が書いた案を Gemini / Codex の案として記録しない。 |
| Ideator(3 役) | Claude(新しい文脈)× 2〜3。**Codex は、パケットだけを読めることを OS で保証する起動経路(models.sandbox_launcher)ができるまで使わない** | `tools/ideate_external.py`(Codex・Gemini は隔離が無いので標準どおり Claude で代替され、その事実が記録される) | 手動の codex exec でこの条件を迂回し、その出力を標準の隔離済みの役と同じように数えることはしない。 |
| Librarian | Claude Code(サブエージェント、Web 調査) | Agent | 重要な数字・主張は Codex が一次資料で照合する(148 の文献の数字の訂正と同じ役)。 |
| 人間の承認 G0〜G4 | **利用者** | 利用者の端末で `python tools/human.py ...` | エージェントは承認トークンを発行しない。提出は G3 のトークンつきの `tools/submit.py` だけ。 |

## これまでとの違い(運用)
- 提出: 10/29 の「候補を優先、診断は相談」、10/30 夜の「今日の分は裁量で提出」は、ハーネスの G3(人間が成果物ごとに承認)に置き換わる。
- Public LB: 最適化の目的ではなく、違和感の検出の観測値として記録する(`tools/submit.py lb`)。
- 実験: 全て仮説・ブランチ・定量の予測(全体とスライスの metric_delta)を事前登録してから実行する。CV・指標・fold は G0 で固定し、変えるときは新しいワークスペース。
- 外部のデータ・モデル: G4 で承認した資源 ID だけを使う。
- Codex への依頼の番号(reports/agent_review/NNN)は、ハーネスの外の議論・設計レビューに引き続き使う。Critic の JSON と Judge の JSON は、ハーネスのワークスペースの規定の場所に保存する。

## 逸脱・代替の記録(Codex 154 Q5)
対象と期待する保証 / 実際の保証 / 適用範囲 / 理由 / 対策 / 実装・設定・packet の hash / 確認した検査 / 実際の provider・model・文脈 ID / fallback の理由 / 費用の予約と実額の区別 / 解消または再点検の条件 — の 11 項目を、ワークスペースの reports/deviations/ に一件ずつ記録する。
- D1: sandbox local(Windows)。学習プロセスの OS 隔離なし。フック・読み取り専用属性・hash の検査は OS 境界ではない。
- D2: CPU だけの運用で、ハーネスの GPU 時間による lane の配分・予算・再構成の時間条件が働かない。Orchestrator が lane ごとの job 数の上限を守る。ハーネスへの CPU 予算の追加を利用者に提案。
- D3: Codex / Gemini の発想役は隔離の起動経路が無いため実行しない(Claude で代替)。
- D4: holdout のラベルはワークスペースの外(CASMI リポジトリ)にあるが、同じ OS ユーザーなら読める(運用上の分離)。
- D5: 正式な Critic はハーネスの既定(Claude のサブエージェント)ではなく、Codex の新しい文脈で行う(独立したモデルによる点検のため。読む範囲は作業場所に置いた snapshot と成果物だけだが、OS による制限ではない)。利用者が既定どおりを望めば Claude のサブエージェントに戻す。
