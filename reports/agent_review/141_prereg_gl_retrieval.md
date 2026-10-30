# 141 事前登録(2026-10-30 09:0x JST、Claude Code)— A3: 同じ式の hard negative による GLACIER の識別学習

141_decision.md(Codex 141 を採用)の具体化である。**A3 の学習・採点の数字は、この登録より前には一つも無い**。

## 1. 候補 A3(固定)
- 開始点は C0'(released)。学習するのは inten_encoder / inten_decoder / output_map だけ(A2 と同じ)。tims_s1 の train 4,614 スペクトル(val は不使用)。1,500 update、positive batch 16、lr 1e-4、warmup 100、seed 0。
- 損失は `L = L_A2_positive + 0.1 · L_ret`(τ = 0.1)。`s_j = −cos_loss_sparse(pred_e2e(j), observed)`。負例は model の decoy 経路で通す。padding は mask する。負例の無い query は L_A2 だけ。
- **負例**(学習の前に固定し、学習の途中で選び直さない):
  - 候補: `make_glt_decoys.py` v2。train の identity ごとに、同じ中性式の構造(PubChem tier / v2 pool / COCONUT、±0.2 mDa)を集め、公式 key で重複を除く。真の別名・identity group、fold 0 / 1 / 2 と panel の構造は除く。Tanimoto の上位 200 で事前選別する。
  - 選択: `make_glt_hardneg.py`。train の各スペクトルについて、そのスペクトルでの C0' の GL の上位 7(同値は key。採点できた候補だけ)。
- コード: `finetune_glt_v3.py`(A2 の v2 は不変)。

## 2. 技術確認(性能の前、GPU)
- `--precheck`: 一 batch で、L_A2 と L_ret をそれぞれ逆伝播し、勾配が有限かつ非 0 であること。inten3 以外の parameter と buffer は bit 一致。時間と最大メモリを記録する。
- 負例の対応(同じ式、真と別の公式 key)は、選択表の検査で確かめる。
- export と strict reload の後、10 分子の確認で得点が C0' と異なること(134 と同じ検査)。

## 3. 開発の比較(凍結した A3 vs A2 vs C0'、同じ runner の入力・設定)
- cell(GL-only、view c2、全 roster、134 v2 の評価器 `gl_only_eval.py` v2.1):
  - f1G・f2G(timsTOF、base・A2・A3 のいずれにも未見)。
  - NP_H(np053 f1dev)、D(f1dev)、panel(P_np250。base GL が既見の多い C1 側の保護)。
- **主**(実用の増分): f1G + f2G を合わせた 200 分子で、rr_form の **A3 − C0' ≥ +0.01 かつ 95% 下限 > 0**(identity の bootstrap、4,000、seed 141)。
- **目的の効果**(A3 を通すための必要条件): 同じ 200 分子で、rr_form の **A3 − A2 の点推定 > 0**。区間は記述とする。目的の変更が効いたと主張するのは、下限 > 0 の場合だけである。
- **費用**(下限 ≥ −0.01): NP_H と D の rr_form。f1G・f2G・NP_H・D・panel の rr_gl。
- 記述: 各 cell の top1_form・margin_form・同式候補の数・被覆、A2 − C0'(A2 の NO を救済するためには使わない)、NP の rr_form。
- **PASS**(主 + 目的 + 費用)なら、§4 の確認へ進む。**NO** なら A3 を止め、λ・τ・K・step の選び直しはしない。技術的な不成立(入力の不一致、非 null の組の違い、学習の失敗)は NO と分ける。

## 4. 一回の確認(§3 が PASS の場合だけ。開封の前に別に固定する)
- 新しい timsTOF の集合を作る。fold 1 / 2 の G 適格(enveda-180 の query、他の library の参照)のうち、未使用の identity から作り、負例・教師・開発の identity を公式 key と共通の group で除く。名前のある locked G は全て開封済み(045 / 067)である。
- 凍結した A3 の重み・負例の一覧・評価器・対照・欠損の扱いを固定してから一回だけ読む。主の関門は §3 と同じ形で、確認の集合だけで読む。

## 5. 限界
- 改善できるのは、GL が使える分子(陽イオンの [M+H]+ / [M+Na]+)の同じ式の識別だけである。台帳で GL の比較が無い isomer の誤りの大半(GL の対象外の層)には直接は効かない。
- G は timsTOF の能力の診断であり、未見の NP での純増の代用ではない。ranker への接続(段階 3)では、未見の NP の全件の主出力を主指標にする(別に登録する)。
