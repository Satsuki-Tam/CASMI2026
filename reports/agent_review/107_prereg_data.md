# 107 事前登録: ranker の学習データの拡充(使用済みの fold-safe 開発表をクロスフィッティングで追加)

作成: 2026-10-28 18:36 JST(Claude Code、結果の前)。根拠: これまでの改善は学習データの追加から来た(v8w = v4b + fold 3/4 の pool、v8w7a = v7a + pool:開発 053 NP_H C2 +0.03、Public +0.004)。今日の監査・予備試験で、既存の証拠の組み合わせ方や前方モデルの要約・ICE では上積みが無かった。登録の目的は「同じレシピで学習行を増やすと、隠しに近い層を含めて改善するか」。

## 1. 候補(一つ)
- **CF** = v8w7a と同じレシピ(features v2_noice_ana − lib_nref − in_train、params rank_params_v7a、C1 × 3 は RUNS0 だけ、他は × 1、analog 特徴あり)で、学習 run = RUNS0 v3 + pool f3a / f4a + **使用済みの fold-safe 開発表 4 つ**(run_f1dev・run_f2dev・run_np053_f1dev・run_np053_f2dev、計 1,640 分子;FP は各 fold を保留したモデル = 未見の同一性)。full_eval の表(p2dev・パネル)は学習に入れない(FP の露出条件が違う)。
- **クロスフィッティング**: 4 表の分子を identity group 単位で 2 分割(seed 1070、表ごと)。cfA = RUNS0 + pool + 4 表の A 側、cfB = 同じく B 側。各開発分子は**自分を学習していない方**のモデルで採点(A 側の分子は cfB、B 側は cfA)。p2dev とパネルは cfall(4 表すべてを足したモデル = 最終候補)で採点。
- 4 表の analog 特徴は analog_probe.py で Spark 上で計算(RUNS0 / pool の既存 analog_tr_v8w は PC で計算済み — 計算環境の差は記録)。

## 2. 開発の読み(102 / 104 と同じ集計)
- 主指標 = 1/2 A(053 NP C2 の 4 cell、各 1/8)+ 1/2 B_D(f1/f2 D C2 の 2 cell、各 1/4)、d = CF(クロスフィット)− v8w7a、strict。
- **関門**: 主指標 ≥ +0.005 かつ下限 > 0;A・B_D の各下限 ≥ −0.01;保護(下限 ≥ −0.01): 旧 B(f1/f2 NP C2 の C〜F、クロスフィット)、G C1(f1/f2、クロスフィット)、**パネル C1 clean(cfall)**、053 NP C1(クロスフィット)。dev2(p2dev、cfall)は stress として記録。
- 検査: 完全性・値域、v8w7a の main = 102 の main(全行一致)、各分子が自分を学習していないモデルで採点されていること(分割表との照合)。
- 注意: 開発表は過去に何度も読んだ集合なので、この比較は「データ追加の効果」の開発での推定であり、選択の楽観は確認で吸収する。

## 3. 確認(関門を通った場合だけ、一回)
- cfall を np096_conf093(H200 / N200)+ np102_d0conf(D 286)で読む(H/4 + N/4 + D/2)。C1: c1cost098(E、usable の実数)。条件は 104 §4・§6 と同じ(平均 ≥ +0.005 かつ下限 > 0、各ブロックと C1 の下限 ≥ −0.01、usable 0 や未判定は不合格)。
- これらの集合は 102 / 104 では開いていない。

## 4. 確定版(Codex 107 を受けて、19:03、性能結果は未読)
- v1(18:41〜19:00 の学習・評価)の出力は未読のまま隔離(diag/cf107_v1_unread、rank_cfA / cfB / cfall_v1unread)。**検査だけ実施: cf0(同じ run・同じレシピ・--filter_to_csv・統合 analog)は v8w7a を 6 表の全行で再現(差 0)** → 主比較は登録どおり CF − v8w7a(同時に CF − cf0 とも同じ)。
1. **保護集合の identity group を全ての追加 fit から除外**(Codex が見つけたパネル C1 clean との重複 3 group:188 / 235 / 57 を含む)。保護集合 = パネル、dev2 / locked2(eval_set2 / locked_eval2 v2)、未開封の確認集合(np096_conf093、np102_d0conf、c1cost098)。評価の分母(4 表 1,640 分子)はそのまま。分割表に cf(A / B)と fit_ok を持たせ、cfall も除外済みの全件 CSV で学習。
2. **実 fit 名簿の照合**: trainer が正例あり群への限定・C1 反復の後の (run, set, molecule, view, identity_group) を rank_<M>/fit_roster.csv に保存;読みで「各評価行の group が、その行を採点したモデルの名簿に無い」「パネル・dev2 の group が cfall の名簿に無い」を assert。group の欠測禁止、group が一つの表・一つの fold にだけ属することを分割で assert。
3. **--filter_to_csv は分子台帳(M / LEDGER)も CSV に揃え**、CSV の分子に台帳行が無ければ停止。**analog cache の被覆**を run × set ごとに記録し、開発 4 表は欠損 0 を必須(--analog_strict)。
4. A 側 / B 側の主指標と実 fit の group 数を別に記録。開発表での cfall の値(自分を学習)は判定用の表に出さない。行 bootstrap の区間は固定した一つの分割・学習結果に条件付いた記述区間。**不通過後に seed や分割を替えて合格を探さない**。
5. これは ranker 層の交差 fit であり、特徴生成(FP・GL 等)の全段を含む外側 holdout ではない(別 fold の学習行の FP モデルは評価側の同一性を学習済みの場合がある)。得られるのは「この追加レシピ一式の効果」(C1 / C2・COCO・G・GL 経路の比率も動く)。
6. ジョブ: 失敗時は非ゼロ終了、全出力の新規生成を確認、manifest に分割表・fit 用 CSV・実 fit 名簿・コードの hash。確認(§3)の読みに使う集合の不重複も分割で assert 済み。

## 5. 開封前の検査で見つかった名簿の不整合(19:21、性能結果は未読)
- 読みの検査「パネルの行の identity group が cfall の実 fit 名簿に無い」で停止(パネル 2 行)。調査: **パネルの選択 CSV(panel_np250/p1_molecules.csv)の identity_group 列は 0〜249 のパネル内の通し番号で、全体共通の identity group ではない**(全 250 行で identity_folds の group と不一致)。他の選択 CSV(開発 4 表、dev2、locked2、np096_conf093、np102_d0conf、c1cost098)は全行が全体共通の group。
- 全体共通の group で照合し直すと、**開発 4 表とパネルの重複は 0、cf0 / cfall の実 fit 名簿とパネルの重複も 0**。Codex 107 が挙げた 3 件(188 / 235 / 57)と今回の停止は、通し番号と全体 ID の数値の偶然の一致だった。
- v2 はこの 3 分子を追加 fit から余分に除いている(保守側の誤りで、評価を楽観にしない)ため、再学習はしない。読みのパネル(と dev2)の照合は、scorer_key → identity_folds の全体共通 group で行うように修正(x107_summary.py)。分割の保護集合の読み込みでもパネルは全体 group を使うべきだったことを記録(次からは修正)。
