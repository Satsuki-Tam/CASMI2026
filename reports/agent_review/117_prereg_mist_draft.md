# 117 事前登録の草稿 v2: MIST(MSG aug)の FP 予測を P に 1 位固定で接続 — Codex 117 を反映

初版: 2026-10-29 01:00 JST、v2: 2026-10-29 01:35 JST(Claude Code、草稿;**利用者の導入許可の前で、MIST のコード・重みは未取得・未実行**)。Codex 116 の分岐(110 / 111 が両方不通過で MIST の許可・前処理が揃えば先に;どちらかが正式に通ればその fold 2 の再現が先、MIST の準備は並行可)。技術要件は reports/research/mist_inference_requirements_2026-10-28.md(「調査」)。

## 0. 位置付け
- 問い: **P の式推定を条件にした別系統の FP 予測器**(式条件付き・部分式割当の transformer、MSG で学習)は、固定の接続で P の 1 位以外の並びを改善するか。P から独立な証拠とは呼ばない(式は P の 1 位から取る)。独立性は採用条件ではなく、問いは固定接続での増分。
- aug − noaug は**公開された二つの学習レシピ一式の差**(noaug: 1 GPU・30,000 更新・AdamW、aug: 4 GPU・478,850 更新・Adam、実データの反復量・batch・学習率・EMA も違う)で、「模擬スペクトル追加の効果」とは呼ばない。aug が勝てば「この大規模レシピが現在の入力に有用」という実務的根拠に留め、差なし / 負でも 115 の模擬補強は棄却しない。noaug は診断で、良くても候補へ繰り上げない。

## 1. 候補(一つ)と対照
- **C_M** = 凍結した主リスト P(v8w7a、gen_eval2fd --v7f --parents 0、既存 fold-1 表と保存済み GLACIER)の **1 位を固定**し、残りの**全 shortlist** 候補を `s = 1/(10 + r_P) + 0.5/(10 + r_M)` の降順(同点は P 順)に並べてから 25 件で切る(111 と同じ接続:K = 10、α = 0.5)。r_M = MIST-aug のスコアによる全 shortlist での順位。
- 診断(判定に使わない): noaug の同じ接続、MIST 単独の識別(中立な悲観的同点)、P との正解順位の順位相関、対応分子内だけの増分。MSG での検索診断を見て式の選び方・接続係数を選び直さない。

## 2. MIST の採点(性能の前に固定)
- **式 F\***: 各 (set, molecule, **view**) で P の 1 位の代表構造から決める(C1 と C2 で P の 1 位が違い得る)。代表構造が正味の電荷 ≠ 0・同位体指定・語彙外元素(18 種外)・元素数 254 超なら F\* なし。中性分子式は RDKit CalcMolFormula(電荷を持たない代表表記のみ)。評価の真の式は入力に使わない。P の 2 位の式などへの自動救済はしない。
- **query**: b1_features と同じ選択(最大 8、電子補正の規則も同じ)のうち **[M+H]+ / [M+Na]+ で、測定 precursor が F\* + 付加体と既存の窓の許容内で整合するスペクトル**。この同じ集合を全候補・aug / noaug で共有し、cos を平均する。陰イオン中心などの集団名では欠測を決めず、実際に選ばれた query で決める。
- **スコア**: p(spectrum, F\*)(4,096、FP32 のまま保存または候補得点へ変換;float16 に丸めない)と、全 shortlist 候補の Morgan 4,096 bit(MIST の関数;半径・chirality・packing を manifest に固定)の cos、分子単位は対応 query の平均。予測キャッシュは query・F\*・付加体・checkpoint・前処理が同じなら共有。
- **欠測の区別**: 設計上の欠測(F\* なし・対応 query なし・質量不整合)は C_M = P(その分子の全行不変を assert;N_only 等が P 順になるのを MIST の識別力として読まない)。実装の欠落(対応 query があるのに得点行が無い、重複キー、FP 不正)は停止。部分欠測の「最下位への配置」は第二票を与える処理として記録。
- **接続の実装**: gen_eval2fd の `--nscore`(キー = set, molecule, smiles、view なし、N / Fs / Fm 必須)にダミー列を入れて流用しない。view・F\*・P の先頭 key・coverage を持つ MIST 用の薄い接続を作り、main の不変・先頭 key 不変・RR = 1 の行の不変を assert。

## 3. 事前の技術確認(どれかが不合格なら CASMI には進まない;性能は読まない)
- 調査 Step 2 の A0(静的確認)・A(公表値:checkpoint・件数・閾値・集約法が一致する場合に限り aug の閾値 0.18791 ±1e-3、MSG test 平均 Tanimoto 0.433 ±0.01;件数が違うまま範囲に入ることを PASS としない)・B(batch・並び順・CPU/GPU の不変)・E(自前ラッパーと CLI の一致)。
- **前処理の再現は公表値とは別に検査**: MSG の compact 特徴が `no_subform.hdf5` 由来で新規 query の merge → 再割当と同じ経路か未確定。同じ前処理を再現する対象では**離散フィールドの完全一致**を求め、不一致は特定する(「99.5% 一致なら残りを許容」はしない)。
- checkpoint は weights_only=True で読む。読めない場合は自動で False に切り替えない(公式 hash とエラーを照合、ソースで型を確認して最小限の safe_globals;False が必要なら隔離環境での変換を利用者の許可範囲に含めるか、そこだけ保留)。
- CASMI 側: cell ごとに全件数・対応 query のある分子数・有効得点数・P に戻した理由を記録(性能列は出さない)。最初に件数・時間・メモリ上限を決めた小試験を一つだけ行い、稼働中の学習の更新速度・メモリに影響が無いことを確認してから同じ上限内で採点(影響があれば MIST を待たせる;fold 1 の段階 3・111 の評価の時間帯には GPU 処理を重ねない)。

## 4. 評価(fold 1)
- 集合: f1dev(C〜G)、np053f1dev(NP_H / NP_X / NP_N)、c1dev。選択時の not_msg は「照合した MSG の実スペクトル側の identity と重ならない」に限る → 取得する MSG 版の key / alias で照合し直して記録。aug の合成構造(約 392 万分子)への露出は、所属を判定できる名簿が無ければ **unknown** と記録(false にしない)。
- 主指標 = 1/4 d(np053f1dev NP_H C2) + 1/4 d(np053f1dev NP_N C2) + 1/2 d(f1dev D C2)、d = C_M − P、**全件の分母**(未対応分子は差 0 として残す;対応分子だけで再計算しない)。NP_N は陰イオン中心で対応が少ない見込みだが重みは変えない(N が不変なら +0.005 には H・D で約 +0.0067 が要る)。関門: 主指標 ≥ +0.005 かつ 95% 下限 > 0;A・D 各ブロックの下限 ≥ −0.01;保護の下限 ≥ −0.01: 旧 B(f1dev C/D/E/F C2 等重み)、G C1、NP C1(NP_H / NP_N 等重み)、c1dev pooled。bootstrap 4,000 回、seed 固定。
- 通った場合: fold 2(f2dev / np053f2dev、fold-2 c1 群)で同じ関門を単独で一回。MIST は fold に依存しないので再学習なし。両 fold 通過で本番の実装照合(Kaggle の導入・T4 の速度・parity)は別登録。P は登録した v8w7a のままで、110 / 111 の勝者との組合せへ読み替えない。

## 5. 導入の許可範囲(朝の提示用)
- coleygroup/MIST の固定 commit(48e339be6535546c87ba4f6b81a0f787c2e4ac40)を Spark に clone、**別 venv** に `pip install -e .`(既存の .venv / .venv-ice は変更しない)。Zenodo 23303289 v1 から mist_msg_aug.ckpt・mist_msg_noaug.ckpt・msg_compact.tar.gz・msg_all.tar.gz の 4 ファイル(SHA-256 は調査 §2 で照合)。12.1 GB の合成データは含めない。保存先 data/external/mist/(コード・重み・来歴の記録)。
- 予定する小試験: CPU / GPU の上限を決めた技術確認(§3)。性能が通った場合のみ、後で Kaggle の private dataset / model へ upload(コード・LICENSE・ckpt・来歴)。競技への提出は別の許可。
