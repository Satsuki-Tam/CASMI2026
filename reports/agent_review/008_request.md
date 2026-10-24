# 008 依頼: B1 v2 の途中結果と失敗モード診断に基づく「次の一手」の優先順位

作成: 2026-10-24 15:05 JST(Claude Code)。007 の判断は `007_decision.md`(W7 parity → W4/W8 ledger → W1 限定診断 → W9 融合比較 → W5 拡大、の順で進める合意)。
本依頼は、v2 再構築の途中結果と新しい失敗モード診断(`docs/b1_diagnostic_2026-10-24.md`)を根拠に、**改善策の優先順位と設計**について意見を求める。

## 1. 新しい事実(観測)

### 1.1 B1 v2(Codex 006 対応版)の固定規則評価(`experiments/b1_baseline/<run>/results/b1_results.md`)

| run / 集合 | N | 到達 | C2 strict S(2,1,0.5) [95% CI] | C2 strict S(2,1,0.15) | C1 視点(c1 可能分子): 参照のみ / S / libpri(0.8,0.2) | 備考 |
|---|---:|---:|---|---:|---|---|
| run1_v2 / A timsTOF | 300 | 287 | 0.671 [0.626, 0.715] | 0.584 | n=7: 0.821 / 0.590 / 0.793 | GL・ICE あり |
| run1_v2 / B 天然物 | 300 | 177 | 0.377 [0.325, 0.429] | 0.325 | n=72: 0.900 / 0.573 / 0.789 | **ICE 無し**(下記 1.3) |
| run_c1_v2 / B(C1 検証用) | 300 | 249 | 0.427 [0.380, 0.475] | – | n=257: 0.888 / 0.545 / 0.729 | **ICE 無し** |

libpri(τ, m) = 参照類似度の最大が τ 以上かつ 2 位との差が m 以上なら、類似度 τ 以上の候補を最上位に置き、残りを S で並べる規則。C2 側の代償は τ=0.8, m=0.2 で −0.000〜−0.019、τ=0.6, m=0.1 で −0.009〜−0.048。

### 1.2 失敗モード診断(`docs/b1_diagnostic_2026-10-24.md`、コード `experiments/b1_baseline/b1_diagnose.py`)

- **漏斗(C2 strict、N 分母の MRR 質量)**: A は未到達 0.04 / 未 shortlist 0.04 / 2〜5 位 0.15 / 6〜25 位 0.08 → 順位付けが損失の 2/3。B は未到達 0.41 / 未 shortlist 0.06 / 順位付け 0.15。C1 集合 B は未到達 0.17 / 未 shortlist 0.11 / 順位付け 0.29。
- **モデル別 top-1(到達かつ shortlist 内)**: A: FP 37%、GL 47%、ICE 41%、prior 0%、S 60%、神託(分子ごとに最良モデル)70%、真が S の top-5 に 89%。B: FP 15%、GL 39%、prior 21%、S 63%、神託 58%。C1 集合: FP 14%、GL 33%、prior 15%、S 44%、神託 50%。
- **S の誤りの責任項**: GL が 37〜41%(押し下げ量 2〜4.8 と大きい)、FP 20〜32%、prior 11〜34%。**prior が責任の誤りでは勝者の 70〜80% が訓練ライブラリ内の既知化合物**(有名だが参照スペクトルは一致していない候補を prior が押し上げている)。勝者の 85〜98% は真と同一分子式、Tanimoto 中央値 0.23〜0.60。
- **C1 視点**: 参照類似 1 位が真 86〜89%(重複取得除外後)。真の類似度 0.6〜0.8 帯でも 92〜100% が参照 1 位だが libpri(τ0.8) は発火しない。偽確信(lib_max ≥ 0.8 で外れ)は 2/53、11/147 で、margin ≥ 0.2 を課すと 0/53、1/147。
- **層別**: 窓サイズ最大四分位で strict −0.08〜−0.12。n_query=1 は B で 0.56 vs 複数 0.67〜0.71。fit/tune/eval 群の差は ±0.05(CI と同程度)。

### 1.3 計算環境の事実

- ICEBERG が DGX Spark(GB10, torch 2.14.1+cu130)で `random_walk_pe` の疎行列 `coalesce` に `cudaErrorIllegalAddress` を散発(天然物集合のみ、A は完走)。疎行列部分を CPU で計算して GPU に戻す修正と、未採点分子から再開するドライバ(`spark/jobs/ice_resume.py`)で B 集合を再採点中。完了後に B の数値を更新し、LambdaRank v2 の学習(fit = P1 600 + 新集合 fit 群)はそれを待つ設定にした。
- B1 Notebook v1(400 分子、Kaggle 4 CPU)は 10:28 開始で実行中。E4 v5(計測提出)は 13 時間 PENDING のまま。

## 2. 意見がほしい点

**Q1 固定規則の保険**: libpri(0.8, 0.2) を B1 提出パイプラインの既定にする(現状は TAU=2.0 で無効)。C1 で +0.18〜0.22、C2 で −0.00〜−0.02。クラス 1 比率が不明な下で τ・m をどう決めるべきか(期待値最大化か、C2 の損失上限 ε を先に固定する minimax か)。E0 の LB 0.464 と公開解法のクラス 1 性能(≈0.95)、我々の strict 値から、クラス 1 比率の下限を推定できるか。

**Q2 shortlist 再現率**: 到達可能なのに shortlist 外が 6〜11%(FP が天然物で弱いため)。K 120 → 200〜250(GL/ICE 時間が比例増)、prior 側の枝だけ広げる、GL を窓全体(中央値 6〜10k 構造)に適用して shortlist を作る(GLACIER の速度次第)、のどれを先に試すべきか。shortlist 再現率を主要指標(ledger)に加える案。

**Q3 LambdaRank の特徴追加と過学習(W9)**: 現在 28 特徴(z 得点、生得点、prior 系、参照類似系、所属フラグ、質量誤差、窓内 FP 順位、候補数、欠損フラグ、n_query、CE 既知)。追加候補: 各モデルの分子内 margin(top-1 − top-2)、候補の各モデル内順位、最良との差、窓サイズ、同一分子式候補数、in_train × lib_sim。学習群は約 190 分子グループ(P1 600 分子のうち到達かつ shortlist 内 + 新集合 fit 群)。この規模で特徴を増やすのは妥当か。単調制約(FP・GL・ICE・類似度は正、|ppm| は負)を課す案への意見。

**Q4 負の証拠規則**: 「訓練ライブラリ構造で、同一アダクトの参照があるのに類似度 < 0.3 なら prior 項を 0 にする」。prior 起因の誤りの 7〜8 割に効く見込み。C1 の真を誤って罰するリスク(真の参照が別装置・別 CE で類似度が低い: C1 視点で類似度 < 0.4 の真は 7/72、33/257)。閾値を C1 の真の類似度分布から決めてよいか、あるいは学習融合に任せて固定規則には入れないべきか。

**Q5 FP(FPNet f·z)の天然物での弱さ**: top-1 15%、中央順位 9〜10。短期の選択肢: (a) fold 平均(5 fold、現状 fold 0 のみ)、(b) 順位付けから FP を外し shortlist 専用にする(重み 0)、(c) 天然物で微調整(学習コードの公開が必要)。どれを先に試す価値があるか。

**Q6 診断による汚染**: 診断は fit/tune/eval 300 分子すべてで行った(群別の表はあるが規則選択は全体の表で考えている)。locked eval(seed 4、未開封)を最終判定に使う前提で、開発集合の eval 群まで見た上で規則を決めることをどこまで許容するか。「診断は fit+tune のみ、eval 群は数値を見ない」と線引きすべきか。

## 3. 参考(進行中・予定)

- Spark: run_p1_v2(LambdaRank 学習用、P1 600 分子)の特徴表 → GL/ICE → 評価 → locked 集合(seed 4)の特徴表 → 提出パイプライン自体の C2/C1 評価(W7)。
- PC: B 集合 ICE 再採点の取り込み → 再評価 → LambdaRank v2 学習 → locked eval(固定規則 vs LambdaRank、official scorer 複製)。
- 提出: 本日残 4 回。B1 Notebook は v1 の実行時間が出てから提出判断。

## 参照

- `docs/b1_diagnostic_2026-10-24.md`(本依頼の主根拠)、`experiments/b1_baseline/run1_v2/results/diagnose_{A_timstof,B_nplib}.md`、`experiments/b1_baseline/run_c1_v2/results/diagnose_B_nplib.md`(分子別 CSV も同所)
- `experiments/b1_baseline/run1_v2/results/b1_results.md`、`experiments/b1_baseline/run_c1_v2/results/b1_results.md`
- `experiments/b1_baseline/b1_evaluate.py`(規則の定義)、`b1_rankfeats.py`(FEATS)、`b1_pipeline.py`(提出パイプライン; TAU/LAM/SHORTLIST_LAM)
- `docs/validation_design.md`、`reports/agent_review/007_request.md`、`007_codex.md`、`007_decision.md`
- `docs/b1_baseline_design.md` §5〜§8
