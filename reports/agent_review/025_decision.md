# 025 判断: full_eval の直接比較を提出(57630996)。pool の完成物を確認(rc 0 も notebook ログで直接確認)。smoke 切替は次版で防護を追加

作成: 2026-10-25 22:12 JST(Claude Code)。依頼 `025_request.md`、回答 `025_codex.md`。

## 1. 採否
| 論点 | 判断 |
|---|---|
| pool probe(57630176)の実行妥当性 | Codex の追加確認をすべて実施: 最終 `submission.csv` の sha256 254ca65a… = `submission_probe_pool.csv`(EMIT probe_pool;main は cb52e623…)、kernel の最新 = 提出した v2、`b1_stage_stats.csv` の処理済み一意 ID 400 = 全分子、CCO 0 行。429 解消後に notebook ログも取得でき、**`pipeline rc 0 11527s`・`EMIT probe_pool`・`OK (400, 2)` を直接確認**。→ 追加の保留条件なし。 |
| full_eval v1 の提出 | Codex の条件(smoke 完了、実際にマウントされた checkpoint の完全 SHA 一致、12 件処理、rc 0、main 出力、forward / fallback の記録)をすべて確認して 22:09 に提出(57630996、本日 5 本目)。確認値: checkpoint `/kaggle/input/models/hayatetaf/casmi26-b1-fpnet-fulleval/pytorch/full-eval/1/full_eval_final.pt` sha256 5b8d1c311d1171089374379c10cb82fdcc36457a7ab02ec0dddc6f12059b616d、test 署名 654e030e…・rerun False・smoke True・`--limit 12`、fusion {gl_used 11, learned 11, fallback 1, lib_priority 1, empty 388}、pipeline 4dc9e7b3・common fa9bb9eb・rankfeats 6e4d6e1d・rank_v4b 237710b6。**新 checkpoint での 400 分子の時間リハーサルは未実施**(候補・forward の所要時間は変わり得る)。 |
| 撤回 | 「smoke 誤作動なら Public ≈ 0.01〜0.03 で判別できる」は撤回(12 件だけ処理した場合の上限は 12/130 ≈ 0.092)。低い値を不具合として除外するには実行証拠が必要で、得点だけなら原因未確定とする。「一分子あたりの時間は不変」も保証しない。 |
| smoke 切替の次版の防護(順位付けは変えない) | (1) wrapper が判定に使った `COMP_TEST` を pipeline の `--test` に明示し、sample も同じコンペディレクトリから読む。(2) 全件モードでは `--limit` が無いこと、`b1_stage_stats.csv` の一意な処理済み ID 集合 = test の ID 集合、を assert(候補ゼロと未処理を区別)。(3) ロードした checkpoint の完全 SHA・ranker・EMIT・rc を検証し、入力署名・モード・処理件数・出力 hash を保存。(4) 既知ダミーの判定に内容も使う(手元 test.parquet のファイル sha256 2fa29c4a…;Kaggle で同じバイト列か確認してから allowlist に使い、不一致・不明は全件へ倒す)。 |

## 2. Public の読み(提出前に固定、Codex Q3)
- 順序: 実行妥当性 → full_eval − 0.354(020/022 の運用閾値:≥ +0.02 暫定候補、±0.02 未確定、≤ −0.02 見送り;7 保護層の下限未確定は記録のまま)→ pool / Pc(023b / 024 の表)。
- `max(0, 0.354 − P_pool) ≤ 元 baseline の Pc 寄与 ≤ min(0.354, P_Pc)`、`P_pool + P_Pc − 0.354` = 固定 baseline で真の所属群を完全に選べた場合の回収量(別 run 差を含む近似)。和が 0.354 を明瞭に下回る・1 を超える場合は所属・出力・実行差を点検し、構成比を解釈しない。
- **full_eval の値を probe の式の 0.354 に代入しない**(probe は旧 FPNet の順位列)。三つの値は同じ Public 分子の採点なので統計的に独立ではなく、FPNet × Pc 降格の相互作用も測れない(「両方改善したので加算できる」とは読まない)。

## 3. 明日(10/26 09:00 以降)の方針(Codex Q4)
- full_rk は「full_rk + RK_old → full_rk + RK_new」を一組で(両レシピを結果前に凍結;前者 = FPNet 変更、差 = 同じ FPNet 上の ranker 変更)。一本しか回せないなら full_rk + RK_new を完成システムの比較として(0.354 との差は checkpoint + ranker の複合と明記)。full_rk 側の監査・保護・実装が未達なら急がない。full_eval + RK_old を full_rk + RK_old の対照に代用しない。
- Pc 弱め案はその後。pool ≥ 0.374 でも、採用する full_rk + RK_new 上での w=0.5 の追加効果が局所比較で消えていれば提出しない。w ≥ 1・不合格ゲートを Public だけで候補に戻さない。
- GPU 週枠は推定でなく残量表示を確認して決める(五枠を使い切る必要はない)。
