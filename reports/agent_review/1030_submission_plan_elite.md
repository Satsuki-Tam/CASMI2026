# 10/30 の提出計画(2026-10-29 20:45 JST 作成、Claude Code)— 132 E-lite RRF の一回比較

## 提出する実体(固定)
- kernel **hayatetaf/casmi26-b1-elite version 2**(commit run 20:31〜20:44、check_elite_commit.py **PASS**:experiments/b1_elite/out/commit_v2/)。
  - 埋め込み: b1_pipeline.py 930fa3f8…、elite.py 4a11a714…(parity A と同じ実体)、ranker = v8w7a の stripped(参照 run と同じ埋め込み text hash)。
  - 入力: private dataset hayatetaf/casmi26-b1-elite-e1r(e1r 8f4a81b5…、E keys v2 f572682b…、/kaggle/input/datasets/hayatetaf/casmi26-b1-elite-e1r/ に解決)、公式 identity の RDKit 2026.03.3(fixture 12 件一致)。
  - commit run の P(submission_pref.csv)は v8w7a の参照 run 2 本と byte 一致。

## 提出の条件(すべて満たした場合だけ;Codex 132)
1. (A) PASS(20:22、diag/x132a_compare.json の verdict = PARITY_A PASS)。 → **満たした**
2. (C) PASS(提出する version 2 で)。 → **満たした**
3. (B) c1 / c2 の parity がともに PASS(pc_parity132.sh v2 の終了コード 0 と両 view の md の PARITY PASS;00:00 に開始、各 pipeline は 08:00 前に開始・08:55 で打ち切り)。 → **未(00:00 以降)**
4. 各記録の hash が提出する notebook・e1r・E keys と対応(B の pipeline は 930fa3f8、elite.py 4a11a714)。

## 提出(条件を満たした後、09:00 JST = 00:00 UTC の枠の更新以降、一回)
```
kaggle competitions submit enveda-CASMI26-molecule-id-mass-spectra -k hayatetaf/casmi26-b1-elite -v 2 -f submission.csv -m "132 one-shot (exception, keeps the 102 NO): v8w7a + fixed E-lite RRF (rrf_rank_e1r_0.5, K 10, alpha 0.5, E = P shortlist E subset); parity A/B/C PASS"
```

## 読み(登録 §3、Public の結果を見て α / K / E 源を動かさない)
- Public ≥ 0.402 → 暫定採用候補;0.379 < Public < 0.402 → 保留;Public ≤ 0.379 → 点検して主系へ入れない。

## 00:45 parity B の結果と対応(2026-10-30)
- c2: **PASS**。c1: **FAIL**。一分子(SQFSKOYWJBQGKQ)の E-lite の順序付き top 25 が違う(top-1・RR は同一)。P の主出力と保険は、両 view の 250/250 で同一。
- 原因は 076 / Codex 082 / 083 で既知の評価器の表の性質である。古いパネルの評価表 run_panel_fe_pc は、公式 key の別表記(raw 構造)を C1 + C2 の shortlist の和で集約する。そのため、候補 BEBLLQPTMVOKAX は C1 でも pool 側の別表記の train / COCONUT 所属と参照(lib 0.376、24 本)を持つ。pipeline(= 提出)は view ごとに集約するので、train ではなく参照 0・lib 0 になる。
- E-lite の第 2 ranker(e1r)は lib を使うので、この一分子の E の順序だけが変わる。E-lite の実装の差ではない。
- 対応: 同じ PC・同じ引数に `--alias_perview`(Codex 082)を加えてパネルの評価表を作り直し、登録どおりの parity B の比較(同じ pipeline 出力・同じ tool と option)を両 view で再実行する(`pc/jobs/pc_parity132ap.sh`)。
- 結果と、この再実行を提出の条件として扱ってよいかを、Codex に確認するまで提出しない。Kaggle API の認証も切れている(00:05 から 401)。

## 01:17 Codex 138 → B は「既知の別表記の集約の差を直した再検査で PASS」(138_decision.md)
- A・B・C とも PASS。提出の命令と読みは、上の登録どおりで変えない。Kaggle API の認証が戻ったら、09:00 JST 以降に一回だけ提出する。

## 09:00:16 JST 提出(ref 57785453)
- 登録どおりの命令で一回だけ提出した(kernel hayatetaf/casmi26-b1-elite の v2、submission.csv)。今日の残りの枠は 4。Public の読みは、上の登録(≥ 0.402 / 0.379〜0.402 / ≤ 0.379)のとおり。

## 2026-10-30 12:36 JST: 132 の Public の結果 = 0.403(ref 57785453)
- **登録どおりの読み**: 0.402 以上なので、**暫定採用の候補**とする(v8w7a 0.394 から +0.009)。
- **注意**
  - +0.009 は、Public の揺らぎ(101 以来の幅 η = 0.015)の中にある。確定的な改善とは読まない。
  - α / K / E 源の定義は、この結果を見て動かさない。
- **含意**(記述)
  - 102 の開発では、E-lite の効果の大半は候補源の重み付け(E 源の正解に得、PubChem だけの正解に損)だった。
  - 隠しテストでは、それが損にならず、わずかに得だった。隠しテストの非 train の正解が E 源寄りである、という仮説と矛盾しない(146 の F の分解と同じ機構)。
  - F(57790338、同じ機構を P の shortlist の外の E 窓まで広げたもの)の結果を読む前提になる。
- **作業の基準**
  - 132 を、暫定の作業基準の候補とする(0.403)。
  - F の結果(≥ 0.409 / 保留 / ≤ 0.379)が出た後に、どちらを作業の基準にするかを、Codex と決める。
