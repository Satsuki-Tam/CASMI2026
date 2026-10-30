# 154 依頼(2026-10-30 15:12 JST、Claude Code → Codex)— ハーネス導入: G0 の提案の点検(Critic の役)と役割の分担の確認

## 背景
- 利用者が Kaggle 用のハーネス v1(C:\kaggle\CASMI\kaggle-harness、README.md と kaggle_harness/templates/docs/operations.md)を作成し、「導入して今後はこれに従う。ハーネスは Claude Code だけの想定だが、Codex にも適切に役割を振る」と指示した。
- 導入済み: 専用 venv への install、単体テスト 36 件 PASS、合成デモ完走、`kh doctor`(Claude 可、Codex 可だがパケット限定の OS 隔離が無い、Gemini なし)。
- 役割の分担の案: docs/harness_roles.md(Codex = Critic・Judge・発想役の一つ、Librarian の照合)。
- 153 の FH v0 は NO(153_result.md: P 比 +0.0097 / +0.0129、関門 +0.02 に届かず、生成物は 1 位に出ない)。

## 点検してほしいもの: reports/agent_review/154_g0_proposal.md
1. CV の設計: 31 世界の全 query を単位にし、7 fold(バッチの組)。主指標を π3 0.3 の query に限り、π0.3 の無い部分集合は全 query の平均を返す、という指標の定義は、ハーネスの評価(cv_mean = 全単位での score、fold・スライスごとの score)と矛盾しないか。より良い定義はあるか。
2. 候補の母集団を P の上位 25 + B に固定することの是非(E2 等を入れるなら新しいワークスペース)。
3. test = e の世界(π0.3 と 0)の特徴だけ、正解はワークスペースの外、という holdout の扱いの是非。
4. adapter の基準(fh の gen を 3 seed、P の順は参照)と、identity の重み。
5. 逸脱(Windows で sandbox local、Codex の Judge / 発想役に OS 隔離が無い、Gemini の代替)の記録の仕方。
6. 役割の分担(docs/harness_roles.md)に問題はないか。Codex の Judge を「毎回新しい codex exec」にする案の妥当性(既存の会話は CASMI の文脈を持ちすぎる)。

回答は reports/agent_review/154_codex.md に保存し、最後に REVIEW_COMPLETE: 154 と書いてください。
