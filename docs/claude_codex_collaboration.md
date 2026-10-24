# CASMI の Claude Code と Codex の共同作業

Claude Code が調査・実装・実験を進め、Codex が仮説・検証設計・結果の解釈をレビューする。レビューはこの CASMI 作業を理解済みの Codex 会話に依頼する。依頼と回答は `reports/agent_review/` に保存する。

## 担当

- Claude Code：実験の主担当。実装、学習、計算資源の管理、結果の記録と変更の採否を担う。
- Codex：独立したレビュー担当。根拠の確認、対案、必要な比較実験を提示する。作業ファイルの編集や GPU を使う検証を担当する場合は、その範囲を Claude Code と先に分担する。
- 方針が一致しない場合：一致した事実、異なる仮説、両者を判別できる最小の実験を記録し、実験で判断する。通常は一つの論点につき一往復、重要な未解決点があるときに追加で議論する。

初回の競技調査の結果は `reports/agent_review/000_codex_initial_review.md` にある。

## この会話への依頼

作業場所：`C:\kaggle\CASMI`

Codex の会話 ID：`01a1693e-4ae2-7e13-b547-8baf61b5281b`

Codex 実行ファイル：`C:\Users\satsu\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe`

Claude Code は、次の順序で依頼する。

1. 未使用の依頼番号で `reports/agent_review/001_request.md` などを作る。最初に次の質問、仮説、根拠、基準版・実験 ID、参照するコードや結果ファイル、まだ分からない点を書く。重要な実験の前と結果が出た後を主な依頼時点とする。
2. ファイルを保存してから、下のコマンドを PowerShell で実行する。番号は依頼ごとに変える。
3. `001_codex.md` ができ、末尾に `REVIEW_COMPLETE: 001` があることを確認して読む。キューへの登録成功とレビュー完了は別である。待つ間は依存しない調査を進められる。確認は 20〜30 秒程度の間隔とし、数分たっても回答がなければ通知結果と Codex 側の状態を確認する。同じ依頼を連続送信しない。
4. 採用する点、採用しない点と理由、次の実験を `001_decision.md` に記録する。追加の質問には新しい番号を使い、元の依頼と回答を参照する。

```powershell
& 'C:\Users\satsu\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe' queue --thread '01a1693e-4ae2-7e13-b547-8baf61b5281b' --message 'CASMI の Claude Code からレビュー依頼 001。C:\kaggle\CASMI\docs\claude_codex_collaboration.md と C:\kaggle\CASMI\reports\agent_review\001_request.md を読み、関連資料を確認してください。回答は C:\kaggle\CASMI\reports\agent_review\001_codex.md に保存し、完成後に末尾へ REVIEW_COMPLETE: 001 を付けてください。'
```

`codex queue` は既存の会話へメッセージを送る機能である。モデルや承認設定の上書きは不要。別のレビュー会話を作る場合はこの手順の会話 ID を更新する。コマンド仕様は [OpenAI 公式 CLI リファレンス](https://learn.chatgpt.com/docs/cli/reference#codex-queue) と、インストール済み CLI の `queue --help` で確認済み。

2026-10-24 の接続テストでは、ローカル CLI からのキュー登録後、この会話の次のターンで通知を受信し、`reports/agent_review/transport_receipt.txt` に指定トークンを書き込めた。確認済みの範囲は CLI 送信 → この会話の受信 → 共有ファイルへの回答である。Claude Code 側からの初回レビュー依頼と回答の読み取りは、実際の依頼時に確認する。

## レビューの内容

Codex は依頼に応じて、結論、根拠、重要な異論、次に比較する実験を簡潔に答える。観測事実と推測を分け、未実行の案を実験結果として扱わない。既存の実験形式やファイルがあれば、それを参照して重複資料を増やさない。

CASMI では特に、公式スコアラーとの同一性、分子と学習済みモデルの学習データの重複、Class 1／2／3 の検証条件、候補のカバレッジと順位、装置・化学構造の分布差、公開スコアとローカル検証の区別を確認する。

送信済みの依頼と完了済みの回答は保存し、新しい議論には新しい番号を使う。実験中のコード・入力・設定を途中で変更しない。レビューの依頼は、Kaggle 提出や公開、外部サービスの利用範囲を広げるものではない。
