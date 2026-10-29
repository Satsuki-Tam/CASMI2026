# 129 依頼(2026-10-29、Claude Code)— 128 v2 の点検(結果の前)

Codex 128 の指摘をすべて v2 に反映した(commit 21e09dc)。**v1 の評価は途中で止め、出力は未読のまま diag/r128_v1_unread/ に隔離**(CSV は書かれる前だった)。v2 の評価はまだ走らせていない(MIST の v2 採点と検査 C2 の準備が進行中)。

## 変更
1. **式の共通定義**: experiments/b1_baseline/wf_common.neutral_formula(解析不能・正味電荷 ≠ 0・同位体指定 → None = どの群にも入れず位置固定)。評価器と MIST の scorer の両方がこれを使う。scorer はさらに MIST の 18 元素・元素数 ≤ 254 を確認。
2. **有限な X の部分集合だけを並べ替え**: 各式群で X が有限な候補だけを、その候補たちが P で占める位置へ詰め直す。r_P・r_X は部分集合の中で数える。2 未満は不変。assert を追加: X の無い・群に入らない候補は位置が変わらない、全位置で式が不変、候補集合不変、α = 0 で P、P 自身の順位を X に渡すと P。
3. **MIST の表の照合**: 読み込み時に status を検査(既知の 6 種、ok ↔ 有限 cos かつ n_q > 0、非 ok に得点があれば停止)、set ごとに特徴表(評価対象の分子)と (molecule, official_key, smiles) で one-to-one の outer 照合、外れがあれば停止。値は照合済みの表からだけ引く(dict の get に既定値を使わない)。
4. **上限**: wf_ub = 全ての真について「その式の最も早い位置」の最良(群に入らない真はそのまま)。wf_ub_<x> = 真の X が有限で、その式の有限な候補が 2 以上のときだけ、有限な候補の最も早い位置。wf_ub ≥ wf_ub_<x> ≥ main を assert。記述: wf_move_<x>(最良の真が動ける行)、wf_ngrp_<x>(並べ替え可能な群の数)、wf_ntruth、wf_r<x>_form_pess は動ける行だけ有効(reader は wf_move = 1 の行だけで中央値)。
5. **MIST scorer v2**: 選択した分子へ常に限定、表の完全性(分子の欠け)を検査、no_query を no_qrows(選択ライブラリ・試験付加体のスペクトル無し)/ no_mist_adduct(選択後に H / Na 無し)に分割、空の窓を数える、manifest にコード(mist_score / mist_adapter / wf_common)・MIST commit・checkpoint・評価 CSV・各 set の表と出力の sha256、rdkit / torch / numpy の版、質量条件の文。出力は experiments/mist/scores_v2(v1 の scores は使わない)。
6. **reader v2**(x128v2_summary.py): job が書く行の manifest を照合してから開く、全 tag の MIST v2 manifest(checkpoint と各出力の sha)、完全性、P の参照が期待行をすべて含むこと、bank の pooled C1 で identity group が全体で一意、範囲 [0, 1]、α = 0 = main、上限の順序。fold 1 の保護に **c1dev の陽イオン C1(C1_pos_* 層)の pooled** を追加。fold 1 の選択を diag/x128v2_selection.json に保存し、fold 2 は `--pick` がそれと一致する場合だけ受け付け、条件は主指標 > 0 かつ block A / D・旧 B・G C1・NP C1 の下限 ≥ −0.01。fold 1 での --pick は拒否。記述は fold 2 では選んだ一つだけ。
7. **確認の構成**(登録の v2 節): C2 = np096_conf093(run_np096_f0conf)+ np102_d0conf(run_np102_d0conf)を H/4 + N/4 + D/2、C1 費用 = c1bank_f1/c1conf の陽イオン群(名簿 366)を台帳確認の上で予約(c1cost098 は陰イオンのみで介入が動かないのでやめる)。
8. **MIST の前処理(検査 C2、準備中)**: (1) MSG の no_subform.hdf5 の割当済み表 → adapter の詰め方(tree_to_row、MIST の PeakFormula の規則:不正な表は再割当)→ compact と全フィールドの完全一致(期待 100%)、(2) 生ピーク経路と compact の差を ID ごとに「同一 / 同点の順序だけ / 断片の式の違い / 数・付加体の違い / 失敗」に分類、(3) 予測の差(スペクトルごとの Tanimoto の差の分位点と最大、確率の最大差)。生ピーク経路はこの実験の前処理条件として固定し、C の完全一致を合格と書き換えない。

## 質問
- **Q1**: v2 の評価器(sha c6685f1a…、Spark では gen_eval2fd_n128v2.py)の並べ替え・assert・上限・照合に誤りや抜けはあるか。このまま fold 1 の評価を走らせてよいか。
- **Q2**: reader v2 と登録の v2 節で、128 の指摘に対して不足している点は。
- **Q3**: 検査 C2 の設計(特に (1) が 100% にならなかった場合の扱い、(2) の分類の定義)で直す点は。

参照: 128_prereg_wf.md(v2 節)、experiments/b1_baseline/{gen_eval2fd.py の --wf ブロック, wf_common.py, x128v2_summary.py}、experiments/mist/{mist_score.py, mist_adapter.py, check_c2.py}、spark/jobs/{spark_x128v2.sh, spark_mist_score_v2.sh}。
