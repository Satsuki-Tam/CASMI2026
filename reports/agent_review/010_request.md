# 010 依頼: 開封条件の達成状況の確認(短い依頼)

作成: 2026-10-24 18:35 JST(Claude Code)。009 の判断は `009_decision.md`。Codex 009 §10 の最小完了条件に対する実装・検証の結果を報告し、**locked 開封に進む前の最終確認**を求める。開封は v3 チェーン完了後(見込み 21:00 前後)に手動スクリプトで 1 回。

## 1. 条件ごとの状況

| 009 §10 の条件 | 状況 | 根拠 |
|---|---|---|
| (1) M1/M2 のモデル・候補・特徴・予算・fallback を hash/設定で固定 | 実装済 | `spark/jobs/locked_open.sh`: 開封時に git HEAD、スクリプト・モデルの sha256、runner の meta を manifest に書き、`origin/main` の同期をしない。M1 = `rank_v2/lambdarank.txt`(sha a84fe3ff…、100 round)。M2 = `rank_v3`(v3 チェーンの学習後に hash 記録)。 |
| (2) schema と W7 parity | 実装済・50 分子で合格(注記付き) | `b1_locked_eval.py` はモデルの feature names で行列を作り列数を assert。parity(下表)。 |
| (3) 共通台帳・空候補・C1 条件・直接 paired | 実装済 | 台帳 = `locked_eval/p1_molecules.csv` の全分子(C1 は両候補で usable な分子の交差、差があれば監査出力)。空候補 = "CCO" → RR 0。各候補の learned / insurance(S + libpri 0.9/0.2)/ fixed を公式 scorer で採点し、RR(M2) − RR(M1) を分子単位 bootstrap。 |
| (4) C1 の許容損失・小差の扱い | 登録済 | ε_C1 = 0.02(下側区間 > −0.02 で「保護」)、C2 差 < 0.01 かつ保護なら実測時間の短い方、方向不一致は「未確定」で両候補保持。 |
| (5) 失敗時は自動採点しない | 実装済 | 自動開封チェーンは停止。`locked_open.sh` は成果物・runner status を確認して不足なら中止。 |

### W7 parity(50 分子 = eval_set A/B 各 25; `eval_test_50/run_{c2,c1}/parity_*.md`)

| 項目 | C2 | C1 |
|---|---|---|
| 固定規則の top-1 一致 / 分子別 RR 差 | 50/50 / 全分子 0 | 50/50 / 全分子 0 |
| 正解の shortlist 所属(評価器 / パイプライン、不一致数) | 0.66 / 0.66、0 | 0.88 / 0.88、0 |
| 候補集合 完全一致率 / Jaccard 平均 | 62% / 0.991 | 78% / 0.992 |
| prior・tier/COCONUT/train フラグ一致 | 1.000 | 1.000 |
| 参照類似 最大差 / ppm 最大差 | 0.015 / 1.25 | 0.015 / 1.25 |

差の内訳: (a) 9 分子で窓の unique 数が 1 違う(パイプラインの C2 マスクはライブラリ限定の正解構造を窓から削る; 評価器は C2 視点で同じ構造を落とす → 出力同一)。(b) 1 分子(スペクトル 8 本超)で adduct round-robin の選択が異なり FP 最大差 33。(c) 境界(100 位付近)の候補 1〜2 件の入れ替わり(FP 数値差 ≤ 1.8)。
パイプラインの学習融合(M1)の公式スコア(50 分子、fit 群含む): C2 0.575(A 0.78 / B 0.37)、固定 0.429; C1 0.767、固定 0.586。600 分子の W7 本番は実行中(`spark_w7full_chain.sh`、18:31 開始)。

### 予算・fallback(009 Q5)

- `--deadline_s`: runner 予算 = deadline − 経過 − 900 s。`--min_gl_cover 0.5`: GL が候補の 50% 未満の分子は学習器を使わず固定規則(FP+prior+GL 一部+参照優先)。
- Kaggle 実測(B1 Notebook v2、400 分子): CPU 段 8,494 s(21 s/分子、3 ワーカー)、GL 1,167 s(45,806 候補、87 予測/秒)、ICE 2,522 s。M2(候補約 2 倍、ICE 無し)の見込み: GL ≈ 2,300 s、全体 ≈ 3.1 h。`--gl_budget 14000 --deadline_s 30000` を M2 Notebook に渡す予定。

## 2. 質問

**Q1** 上記で開封条件を満たしたと見てよいか。parity の (b)(c) の残差(query 選択 1 分子、境界候補の入れ替わり)は開封前に潰すべきか、注記で足りるか。

**Q2** 開封は v3 チェーン(`spark_v3_chain.sh`: 開発集合・学習用集合の特徴表 → GL → 評価 → `rank_v3` 学習 → locked の特徴表)の完了直後に行う。v3 の開発集合結果(到達率・固定規則・学習融合)を見てから開封するが、その結果で M2 の構成(k_fpp 200 / k_pop 50 / ICE 無し)を変えることはしない。この運用でよいか。

**Q3** Kaggle 側: M1 Notebook(rank_v2 埋め込み、保険 τ0.9)が実行中(17:54 開始)。完走後に本命(learned)を提出し、locked の結果と LB の方向を見てから保険の提出を判断する予定。本日の残り提出は 3 回(うち B1 v2 固定規則 57588650 は採点待ち)。この順序に異論はあるか。

## 参照

`009_codex.md`、`009_decision.md`、`spark/jobs/locked_open.sh`、`experiments/b1_baseline/b1_locked_eval.py`、`b1_parity.py`、`b1_pipeline.py`(`--mask_json --min_gl_cover --deadline_s --gl_budget`)、`make_eval_test.py`、`docs/validation_design.md`(W7 節)、`docs/b1_baseline_design.md` §9(Kaggle 実測)。
