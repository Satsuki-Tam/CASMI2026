# 014 依頼: 開封前の登録確認(M2x = rank_v4b + blend21)と、朝の提出可否

作成: 2026-10-25 02:30 JST(Claude Code)。前回 `013_decision.md`(採否はすべて受け入れ)。本依頼は、013 の手順 1〜3 の結果を提示し、locked 開封(1 回)と朝の提出の可否を確認するもの。§3 は結果が出た時点で追記する。

## 1. 登録内容(開封前に固定)

| 項目 | M1(凍結対照) | M2x(比較用候補) |
|---|---|---|
| shortlist / forward | v2: FP100 ∪ FP+prior100 ∪ 参照20、GL + ICE | v3: FP100 ∪ FP+prior200 ∪ 参照20 ∪ prior50、GL のみ |
| 学習器 | `rank_v2/lambdarank.txt`(28 特徴、sha a84fe3ff…) | `rank_v4b/lambdarank.txt`(23 特徴 = v2_noice − lib_nref − in_train、C1 fit 群 ×3、sha 237710b6…) |
| 本命の出力 | learned(登録当時のまま) | **blend21 = 2·z(learned) + z(S_plain)**(GL 被覆 < 0.5 なら保険リスト) |
| 保険 | S(2,1,0.5) + libpri(0.9, 0.2) | S(2,0,0.5) + libpri(0.9, 0.2) |
| locked 特徴表 | `run_locked_v2b`(修正済み C1 参照選択、GL/ICE は旧 run から種) | `run_v3b_locked`(同) |
| 提出パイプライン引数 | — | `--k_fpp 200 --k_pop 50 --w_ice 0 --tau 0.9 --main blend21 --gl_budget 14000 --deadline_s 30000` |
| proxy | off | off |

採用規則(010 のまま): A/B 別の paired C2 差(M2x blend21 − M1 learned)、M2x の C1 損失 ≤ 0.02(下側 CI > −0.02 で保護)、保護下で C2 差 < 0.01 なら実測時間の短い方、方向不一致なら未確定で両候補保持。開封後に規則を変えない。開封スクリプト `spark/jobs/locked_open_v5.sh`(manifest に git HEAD・sha256・runner 状態を記録、再実行拒否)。

## 2. 013 の手順の結果

### 2.1 blend の欠損分岐の統一
`b1_locked_eval.py` / `b1_learned_probe.py` / `b1_pipeline.py --main blend21` で同一(GL 被覆不足 → 保険リストそのまま;被覆あり → 2·z(learned)+z(libpri 前の固定規則))。

### 2.2 W7 600 の原因と再実行
旧 `eval_test_full/test.parquet`(10-24 18:31)は builder 修正(float32 丸め・決定的 round-robin)前の生成物: >8 スペクトル分子 18 件の query 選択差、同一スペクトル 573 分子の FP 差(float64 ピーク vs float32 store)を説明。現行 builder は評価器と同じ選択を返す(TXFHOGSJIZXREA 等で確認)。再生成 `eval_test_full2`(2,819 スペクトル / 600 分子)で M2x(blend21)の 600 分子機械的一致を実行中(C2 → C1)。結果は §3。

### 2.3 proxy
パネルで利得なし(013 判断 §1)。off。

### 2.4 忠実な M1 パネル(K=100、GL+ICE、`run_panel_v2k`)
rank_v2 の C1 0.599 / C2 0.918(固定 0.856 / 0.852、参照単独 0.911)→ クラス 1 崩壊は候補構成に依存しない。公開 main list との差(250 分子): 固定 − 公開 = C2 −0.118 / C1 −0.099。

### 2.5 修正表・共通台帳での旧 M1 vs M2x(実行中 → §3)
M1 側の修正表 `run1b_v2`(eval_set、K=100、GL+ICE 種あり)/ `run_c1b_v2`(C1 集合)を計算中。完了後、dev tune+eval と C1 集合で learned / blend21 / fixed / insurance を公式 scorer で比較(`dev_pair_final`, `dev_pair_final_c1set`)。

## 3. 追記(結果)
(W7 600 M2x の一致表、dev_pair_final の paired 差を追記)

## 4. 意見がほしい点
**Q1** §3 の結果が「W7 機械的一致: 候補集合・真の所属・top-1・RR が全件一致(forward 雑音による順序差は別報告)」「dev C2 で M2x blend21 − M1 learned が −0.02 を下回らない」「C1 集合で M2x blend21 が M1 learned に対し下側 CI > −0.02 でないとしても固定・保険を上回る」を満たしたら、`locked_open_v5.sh` を実行してよいか。満たさない項目があった場合の扱い(開封せず M1 のみ提出 / 開封して記録のみ)。
**Q2** 朝の 2 枠: (i) M2x 本命(blend21)、(ii) 同じ Notebook 構成の `--emit insurance` version(submission.csv = 固定 + libpri τ0.9)で「2 つの最終出力ポリシーの差」を観測。locked の結果が M2x 不採用でも、(i) を「比較用」として提出する価値はあるか(E0 0.464 との差で読む)。
**Q3** 公開 LB の約 130 分子で 1 分子 ≈ 0.0077。本命 − 保険の差が ±0.02 以内なら「差なし」と読む運用でよいか。
