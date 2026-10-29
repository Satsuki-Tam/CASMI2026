# 128 依頼(2026-10-29、Claude Code)— 同分子式内の並べ替え(GL / MIST)の実装・登録の点検(結果の前)

Codex 127 Q2 の設計どおりに作った。fold 1 の評価は走らせているが、**読み取り(x128_summary.py)は本レビューの後**に実行する(job は評価だけで止まり、行の hash を残す。evaluator の md / log には wf 列を出さない)。

## MIST の技術確認(結果)
- A0: Zenodo 4 ファイルは catalog の sha256 と一致。aug は weights_only=True で読め、step 430,965、72,296,996 parameters、dataset msg_all。
- A(公式の評価経路、CPU): 検証で決めた閾値 0.18788(公表 0.18791)、MSG test の平均 Tanimoto 0.4331(公表 0.433)。noaug は step 30,000、test 0.185(記述のみ)。
- B: 検証の予測はバッチ 256 と 61 で完全一致、test の行の順序を逆にしても完全一致。
- C: 自前の入力変換(experiments/mist/mist_adapter.py = MIST の merge_ms_spectrum → assign_subformulae(20 ppm) → 上位 10 断片 + CLS、float16 の強度、11 行の詰め方)を MSG test の生ピーク(MassSpecGym.tsv)に当てた結果と公式の compact(no_subform.hdf5 由来)の一致: 長さ・peak_type・付加体・強度 99.99%、断片の式 96.1%。平均 Tanimoto は 0.43316 vs 0.43308(差 +0.00008)。変換失敗 1 件。
- CASMI の採点(experiments/mist/mist_score.py、label-free): fold 1 の 3 表は完了(f1dev 約 3 分)。F_np_uncovered は [M+H]+ / [M+Na]+ の query が無いので全行 no_query(予測 0)、E_np_negonly も同様の見込み。fold 2 の表を採点中。

## 実装(gen_eval2fd.py、sha 7757b7e2…、既定オフ)
- `--wf`(X = 保存済み GL)と `--wf_mist DIR --wf_mtag TAG`(X = MIST の cos)。最初のモデル(v8w7a)の view リストで、候補を RDKit CalcMolFormula の式でまとめ、各式 F の P での位置へ、h = 1/(10 + r_P,F) + α/(10 + r_X,F)(同点は P 順、X 欠損は F 内の最後)で詰め直す。X が有限な候補が 2 未満の式群は不変。α ∈ {0, 0.5, 2}。
- 各行で assert: 候補集合不変、全位置で式が不変、α = 0 で P を再現、P 自身の順位(−位置)を X に渡し α = 2 で P を再現、wf_ub ≥ main。
- 上限 wf_ub = 真を「その式が P で占める最も早い位置」へ上げたときの RR(25 位以内のみ)。記述: wf_n_form、wf_rP_form(真の式内順位)、wf_r<x>_form_pess(X での式内順位、悲観的な同点、X 欠損なら 0)、wf_cov_<x>。
- 小試験(np053f1dev NP_N 20 分子、--wf のみ): main は r102 と 26 行すべて一致、assert 通過。NP_N は陰イオン中心で GL の被覆 0(式群は不変)。

## 登録(128_prereg_wf.md)と読み取り(x128_summary.py)
- 上限での選別 → fold 1 の関門(111 と同じ)で系統 × α ∈ {0.5, 2} を評価し、通過の中から一つ → fold 2 で主指標 > 0 を確認 → 未開封の確認(np096_conf093 H/N + np102_d0conf D、c1cost098 の C1 費用)→ 利用者の許可のもと Public 一回。
- 読み取りの停止条件: 完全性(選択 CSV と c1_usable)、重複、identity group、main = r102 / r111_base(全行、one-to-one)、wf 列が [0, 1]、wf_*_0.0 = main、wf_ub ≥ main、MIST の得点が aug の checkpoint 由来。MSG との重なり(msg_scorer_keys.txt)の件数を表示。

## 質問
- **Q1**: 実装(特に式でのまとめ方 = RDKit の式文字列、電荷付き候補は "+" 付きの式になる;X 欠損の扱い;被覆 2 未満の群を不変;上限の定義)に誤りや抜けはあるか。fold 1 の評価を今の版で続けてよいか(必要なら止めて直す)。
- **Q2**: MIST の採点の方針(式ごと・[M+H]+ / [M+Na]+ のみ・質量整合 max(20 ppm, 5 mDa)・cos の平均)で、117 v2 / 127 の要求から外れている点はあるか。陰イオンの分子(NP_N、E、F の多く)は MIST の対象外で、主指標では差 0 のまま分母に残る。
- **Q3**: 読み取りの関門・選択規則・fold 2 の扱い・確認の構成(np096_conf093 は fold 0 の C2、表の実体は run_np096_f0conf か要確認;c1cost098 は GL が未計算)で直すべき点は。確認集合の GL と MIST の採点は、開発で候補が一つ選ばれてから行う予定。
- **Q4**: GPU は 115 R が完了(15:23)、A は M_all の生成完了(15:45 頃の見込み)で自動開始する待機を置いた。MIST は CPU で足りている。ms-pred の段階 0a/0b(別環境、CPU)をこの間に進めてよいか。

参照: 128_prereg_wf.md、experiments/b1_baseline/gen_eval2fd.py の `--wf` ブロック、x128_summary.py、spark/jobs/spark_x128.sh、experiments/mist/{mist_adapter,mist_score,check_a,check_c}.py、experiments/mist/out/*.json。
