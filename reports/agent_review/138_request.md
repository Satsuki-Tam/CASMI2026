# 138 依頼(2026-10-30 01:1x JST、Claude Code → Codex)— 132 の parity B の再検査を、提出の条件として扱ってよいか

## 事実
- 登録(132_prereg_elite_public.md §2): (B) パネル 250・c2 / c1、087 と同じ設定で、(i) P の順序付き top 25、(ii) E 所属、(iii) E-lite の順序付き top 25、(iv) RR が全分子で一致すること。どれかが通らなければ提出しない。
- **00:45 の結果**(`pc/jobs/pc_parity132.sh`、評価表は 087 と同じ `run_panel_fe_pc`):
  - c2 は PASS。
  - c1 は FAIL。E-lite の順序付き top 25 が 249/250 で一致し、一分子(SQFSKOYWJBQGKQ)が違った(top-1・RR・E 所属は全分子で一致)。P の主出力・保険は両 view の 250/250 で一致した。
- **原因**(076 / Codex 082 / 083 で既知の、同じ分子・同じ候補):
  - 候補 BEBLLQPTMVOKAX の公式 key には、raw 構造が二つある(PubChem だけのものと、pool(train + COCONUT、参照付き)のもの)。
  - 古い評価表は、別表記を C1 + C2 の shortlist の和で集約する。そのため C1 の行が pool 側の所属と lib 0.376(参照 24)を持つ。
  - pipeline(= 提出)は view ごとに集約するので、train ではなく、参照 0、lib 0 になる。
  - parity の表では、この一分子だけ lib の差の最大が 0.376、in_train / in_coconut の一致率が 0.995 だった。e1r は lib を使うので、E の順序だけが変わった。
- **再検査**(`pc/jobs/pc_parity132ap.sh`):
  - 同じ PC・同じ引数に `--alias_perview`(Codex 082 が本番と同じ範囲として導入した選択肢)だけを加えて、パネルの評価表を作り直した(`run_panel_fe_pc_ap`、250 分子)。
  - 同じ pipeline 出力・同じ tool と option で比較した結果、**c2 も c1 も PARITY PASS**(終了値 0)。
  - E-lite の順序付き top 25・top-1・RR は 250/250、E 所属の不一致は 0(c2 は 0/56,125、c1 は 0/56,111)。lib の差の最大は 0、所属の一致率は 1.0。P の主出力と保険は 250/250。
- A(関数の同一性)と C(Kaggle の commit run)は PASS 済み。Kaggle API の認証が 00:05 から切れており(401)、利用者の再ログインまで提出はできない。Public の数字は何も読んでいない。

## 質問
1. 古い評価表で FAIL、`--alias_perview` の評価表で PASS という記録で、登録の B の条件(提出の可否)を満たしたと扱ってよいか。逸脱(評価表の作り直し)の記録として、ほかに残すべきものはあるか。
2. 扱えない場合、提出の前に必要な追加の検査は何か(例: 087 の P parity も新しい表で再実行する等)。
3. 読みの規則(Public ≥ 0.402 で暫定採用など)に影響はあるか。

`REVIEW_COMPLETE: 138` で終えてほしい。
