# 025 依頼: 診断 probe 2 本の提出確認と、full_eval 直接比較の提出(重みは private Kaggle Model で解決)、commit 実行の smoke 切替

作成: 2026-10-25 21:52 JST(Claude Code)。前回 `024_decision.md`(w=0.5 は既見領域で利得 ≈ 0 → 今日の提出優先度は低い)、`023b_decision.md`(probe は pool / Pc の二本、三本目は「容量が解決した場合の full_eval 直接比較」に保留)。

## 1. 報告: probe 2 本を提出(Public は 01:00〜01:30 頃)
| probe | 提出 ID | kernel | 提出前の確認 |
|---|---|---|---|
| pool(train か COCONUT のみ) | 57630176(21:39) | `casmi26-b1-probe-pool` v2(旧 wrapper) | commit run の出力から: 埋め込み sha(b1_pipeline 1bc93dda / common 9585a88d / rankfeats 6e4d6e1d / model 237710b6)を実ファイルで確認、`b1_pipeline.log` の最終行 `submission written: (400, 2)`、manifest 完全。pipeline は submission.csv → probe 5 本 → fixed → manifest → 最終ログの順に書き、Kaggle では最終ログの後に処理が無い(`--solution` なし)。旧 wrapper の assert(行数 = sample、ID 集合一致、≤ 25)は通過(kernel COMPLETE)。**旧 wrapper は rc を記録しない**。notebook のログは API の 429 で未取得。 |
| Pc(PubChem tier のみ) | 57630335(21:44) | `casmi26-b1-probe-p` v1(新 wrapper) | `submission_meta.json`: emit probe_pubchem、pipeline_rc 0、埋め込み sha は pool と同一、submission.csv の sha256 b327ac99… = submission_probe_pubchem.csv、400 行、CCO 0 行(ダミー test 上)。 |
- 読みは 023b §2 の表のまま(P_pool ≥ 0.374 / ≤ 0.334、P_Pc ≤ 0.02)。

## 2. 報告: checkpoint を Kaggle に置く手段 — private Model(dataset とは別枠)
- Kaggle 公式(product-feedback 512322、2024-06-14、Kaggle staff): "Users now have a limit of 200GB for private models and 200GB for private datasets." → private dataset の残量(29 MB)とは別枠。
- private model `hayatetaf/casmi26-b1-fpnet-fulleval`(instance PyTorch/full-eval v1)を作成: `full_eval_final.pt`(198,792,173 bytes、アップロード前に sha256 5b8d1c31… を照合)+ TRAINING_MANIFEST・README・code/・records/(用意済みの dataset フォルダと同じ内容)。isPrivate true を API で確認。他の dataset の削除・公開はしていない。

## 3. full_eval の直接比較を提出へ(今日の 5 本目 = 023b で保留した枠)
- kernel `casmi26-b1-fpnet` v1(21:50 push): 埋め込み pipeline **4dc9e7b3**(= parity 合格版 f88c49a + コンペ置き場所の探索 + 診断 probe ファイル train/nontrain の書き出し;主出力のコードは不変 — `git diff f88c49a HEAD`)、common fa9bb9eb(select_queries 一本化、旧実装と 600/600 一致を確認済み)、rankfeats 6e4d6e1d、rank_v4b 237710b6。引数 = 0.354(v4)と同一 + `--fpnet_ckpt full_eval_final.pt`。dataset は v4 と同一、model source に上の private model。
- 0.354 との差: (a) FPNet checkpoint(意図した一変更)、(b) 主出力不変を確認済みのコード整理、(c) wrapper(新しい検査 + 下の smoke 切替)。
- **commit 実行の smoke 切替(新規)**: E0 の方式どおり TEST_SIG = test の spectrum_id を整列した md5、`IS_RERUN = env KAGGLE_IS_COMPETITION_RERUN または TEST_SIG ≠ 654e030e…`(可視ダミーで手元計算し E0 の定数と一致)、`SMOKE = SMOKE_N(12) > 0 かつ not IS_RERUN` のときだけ pipeline に `--limit 12`(pipeline 既存の引数: 先頭 12 分子だけ処理、他の ID は CCO)。目的: kernel 1 版あたり約 3 h の GPU 週枠(30 h、土曜 09:00 以降に約 20 h 使用と推定)と提出までの 3 h を節約。代償: commit 実行が 400 分子の時間リハーサルにならない(1 分子あたりの時間は同じ構造なので不変、v4・probe の 400 分子の隠し再実行は完走済み)。万一隠し再実行で smoke になれば 12 分子だけ → Public ≈ 0.01〜0.03 で判別可能(実装失敗として読み、手法の結果として扱わない)。
- Public の読み(020/022 で固定済み、変えない): 基準 0.354(57610156)、一変更。Δ ≥ +0.02 → 暫定基準候補(dev2 の下限未確定 7 層は記録のまま)、±0.02 → 未確定(本命 0.354 を保持)、≤ −0.02 → 見送り。

## 4. 質問
**Q1** pool probe の rc の根拠(上の §1)は十分か。notebook ログを取得できるまで pool の Public 値を「条件付き」と扱うべきか。
**Q2** smoke 切替のリスク評価は妥当か。追加すべき防護はあるか(例: smoke でない run では manifest の molecules = test の分子数を assert、`--limit` が引数に無いことを assert、を次版から入れる)。今回の v1 は防護なしで提出してよいか。
**Q3** 3 つの Public 値(pool / Pc / full_eval)が揃ったときの読みの順序と相互作用。full_eval は別 run の一変更比較で、probe とは独立に読む想定。
**Q4** full_rk の chain(23:00 頃完了見込み)で RK_new が 023 §4 に合格した場合、full_rk checkpoint も private model の別 instance で置ける。GPU 週枠を考えると、明日(09:00 以降の 5 枠)の提出順はどうするべきか(候補: full_rk + RK_new、full_rk + RK_old(FPNet だけの比較)、pool/Pc の結果に応じた Pc 弱め案)。
