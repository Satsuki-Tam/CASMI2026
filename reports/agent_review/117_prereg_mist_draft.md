# 117 事前登録の草稿: MIST(MSG aug / noaug)を第二の独立な証拠として P に 1 位固定で接続

作成: 2026-10-29 00:59 JST(Claude Code、草稿;**利用者の導入許可の前で、MIST のコード・重みは未取得・未実行**)。Codex 116 の分岐「110 / 111 が両方不通過で MIST の許可・前処理が揃えば、MSG aug / noaug の小規模推論比較を先に」に対応。110 / 111 のどちらかが正式に通れば、その fold 2 の再現が先(Codex 116 Q1)。技術的な要件は reports/research/mist_inference_requirements_2026-10-28.md(以下「調査」)。

## 0. 位置付け
- 問い: 構造の異なる FP 予測器(式条件付き・部分式割当の transformer、MSG で学習)は、FPNet 系(P)と**違う誤り方**をし、固定の接続で P の 1 位以外の並びを改善するか。111(FPNet 初期化の自前採点器)と同じ枠組みで、証拠の源だけを替える。
- 115 との関係: **aug − noaug は「GLACIER の模擬スペクトルで学習を補う」効果を、著者が大規模(7,845 万行)に行った版**の測定になる。aug > noaug なら 115 の方向を支持、差が無ければ 115 の優先度を下げる(115 は自前の FPNet・固定カタログでの別の比較で、この結果で 115 の登録を変えない)。

## 1. 候補(一つ)と対照
- **C_M** = 凍結した主リスト P(v8w7a、gen_eval2fd --v7f --parents 0、既存 fold-1 表と保存済み GLACIER)の **1 位を固定**し、残りの全 shortlist 候補を `s = 1/(10 + r_P) + 0.5/(10 + r_M)` の降順(同点は P 順)、25 件で切る(111 の接続と同一)。r_M = MIST-aug のスコアによる全 shortlist での順位(欠測は最下位)。
- 対照・診断(判定に使わない): **C_M0** = 同じ接続で noaug(aug − noaug の差を記述)、MIST 単独・FPNet 単独の識別(r*_pess)、P との正解順位の順位相関。
- 選択はしない(aug だけが候補)。noaug を後から候補へ繰り上げない。

## 2. MIST の採点(導入後の技術確認を通ってから、性能の前に固定)
- 入力: 各分子の query は b1_features と同じ選択(最大 8、電子補正)のうち **[M+H]+ / [M+Na]+ のスペクトルだけ**(MIST の学習付加体)。他の付加体・負イオンは MIST 欠測(代理は使わない;代理は別登録)。対応スペクトルが無い分子は C_M = P(全行不変を assert)。
- 式の条件付け: 候補ごとに**その候補自身の中性分子式**(RDKit CalcMolFormula、公式 key の代表表記)で 1 回推論し、同じ式の候補は予測を共有。|m(式) + 付加体 − 前駆体 m/z| が窓の許容(±10 ppm + 電子補正の扱いは b1_features と同じ)を外れる式は欠測。語彙外元素・254 超の元素数は欠測。
- 前処理: repo の `merge_ms_spectrum` → `assign_subformulae(tree, 20.0)` → 上位 10 本 + CLS(調査 1.3、repo の関数をそのまま import)。前駆体 m/z = 測定値。
- スコア: 予測確率 p(4,096)と候補の Morgan r2 4,096 bit(MIST の `morgan4096` 関数)の **cos**、分子単位は対応スペクトルの**平均**。対数尤度・閾値 Tanimoto は記述のみ。
- 実装: experiments/mist/(mist_rows.py → mist_infer.py → mist_score.py)。出力は 111 の n111_score.py と同じ列形式(N 列 = MIST-aug、別列に noaug)で、評価器 gen_eval2fd `--nscore` をそのまま使う(main の不変・RR = 1 の行の不変・先頭 key 不変を assert)。checkpoint は weights_only=True で読めることを確認(読めなければ config を別途検査し、理由を記録)。

## 3. 事前の技術確認(どれかが不合格なら CASMI には進まない;性能は読まない)
- 調査 Step 2 の A0(静的確認)・A(公表値 aug 閾値 0.18791 ±1e-3、MSG test 平均 Tanimoto 0.433 ±0.01)・B(batch・並び順・CPU/GPU の不変)・C(自前の行作成が msg_compact と 99.5% 以上一致)・E(自前ラッパーと CLI の一致)。D(MSG での小規模検索)は記述(MSG test は MIST の評価集合で、我々の判定に使わない)。
- CASMI 側: 対応スペクトルのある分子数・式の欠測率・割当ピーク数の分布を cell ごとに記録(性能列は出さない)。

## 4. 評価(fold 1、111 と同じ読み取りの枠組み)
- 集合: f1dev(C〜G)、np053f1dev(NP_H / NP_X / NP_N)— **どちらも選択時に MSG(raw / 公式 key)を除外済み**(p2_select_v2 / p3np の not_msg)なので、MIST の学習分子と重ならない。aug の 4M 合成構造との重なりは列で記録して層別(判定は全体)。c1dev(c1bank_f1、MSG any 除外)も同じ。
- 主指標 = 1/4 d(np053f1dev NP_H C2) + 1/4 d(np053f1dev NP_N C2) + 1/2 d(f1dev D C2)、d = C_M − P。関門: 主指標 ≥ +0.005 かつ 95% 下限 > 0;A・D 各ブロックの下限 ≥ −0.01;保護の下限 ≥ −0.01: 旧 B(f1dev C/D/E/F C2 等重み)、G C1、NP C1(NP_H / NP_N 等重み)、c1dev pooled。bootstrap 4,000 回、seed 固定。
- 注意(結果の前に記す): NP_N・E は負イオン中心で MIST の対応が少ない → それらの cell は C_M ≈ P になりやすく、主指標の A ブロックの半分(NP_N)は構造上ほぼ 0 の寄与になる見込み。これは不利な条件として受け入れ、重みを変えない。
- 通った場合: fold 2(f2dev / np053f2dev、fold-2 c1 群)で同じ関門を単独で一回。MIST は fold に依存しないので再学習は不要(fold 2 は P 側の表だけが変わる)。両 fold 通過で、本番の実装照合(Kaggle での導入・T4 の速度・parity)を別登録。

## 5. 未確定(導入後に確認して、性能の前に追記)
- Morgan の設定(chirality・count の有無)、ckpt の config が weights_only で読めるか、push 先の Kaggle 環境の torch。
- 推論の量(式の数 × 対応スペクトル数)と時間。
