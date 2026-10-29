# 133 事前登録(草稿、Codex の点検の前):MIST 特徴を加えた ranker の一対比較(Codex 131 Q2 の優先 2)

作成: 2026-10-29 20:20 JST(Claude Code、date)。結果(学習・評価)の前。Codex 133 の点検で確定版にする。

## 0. 目的と根拠
- 127: ranker は今の特徴では学習データの量に対してほぼ飽和(P(0.25) 0.4228 / P(0.5) 0.4215 / P(1) 0.4262)→ 伸ばすには**新しい情報**が要る。
- 128: MIST 単独(同じ式の中)の真の順位の中央値は 4〜8 位(P は 1 位)、P の誤りを MIST が 1 位で救うのは 6〜17%。単独の差し替えでは負けるが、**学習で他の証拠と組み合わせる**価値は否定されていない(Codex 131:単一 cos 列でなく、欠損理由・有効 query 数・式内順位 / 差・割当の質・既存証拠との不一致を観測可能な特徴に)。
- MSG の露出(experiments/mist/msg_overlap_133.md、公式 identity): **v8w7a の学習 run(fit 2,900 identity)と開発表(f1 / f2 / np053 / c1bank)は MSG の train / val / test のどれとも重ならない**(0 件)。パネルは 226 / 250 が MSG train / val(既見側の補助の保護に留める)。→ MSG 除外で学習行は減らず、「MIST あり − 対照」と「MIST あり − 元の P」は同じ行・同じレシピの比較になる。

## 1. 比較(一対、一候補)
- **対照 P**: v8w7a のレシピ(b1_rank_train.py --runs RUNS0 v3 + pool f3a / f4a --feats v2_noice_ana --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 --params_from rank_params_v7a --analog_parquet analog_tr_v8w)。同じ環境で再学習し fe61dc42 と byte 一致を確認(一致しなければ原因を記録し、再学習した対照で比較)。
- **M**: 同じ行・同じレシピ + --feats v2_noice_ana_mist(= v2_noice_ana + EXTRA_MIST 19 列;lib_nref / in_train は同じく除く)+ --mist_dir experiments/mist/scores_v4 --mist_tags(run → tag)。params・rounds は固定(探索なし)。
- **EXTRA_MIST**(b1_rankfeats、patch_rankfeats_m133.py に定義): mist(cos、欠損 −1)、z_mist、mist_missing、rank_mist、gap_mist、margin_mist_mol、mist_nq、mist_mol_noq(分子に MIST の使える query が無い = 陰イオンのみ等)、mist_mol_ok、式内の rank_mist_form / gap_mist_form(同じ式 = 同じ条件の cos だけを比べる)、n_form、rank_form_mist(式群の最良 cos の式間順位)、割当の質 mist_fint / mist_npk / mist_ppm(候補式ごとの MIST の部分式割当)、不一致 d_rank_mist_fp / d_z_mist_fp / d_z_mist_gl(MIST 値が無ければ NaN)。異なる式の cos を同じ尺度と仮定しない設計(式内の量と式間の量を分ける)。
- **MIST の得点**: mist_score_v4.py(v3 + 割当の質の 3 列;v3 の 4 列は 5 つの開発 tag で v3 と行ごとに完全一致を確認してから使う)。陽イオン([M+H]+ / [M+Na]+)のみ。
- 評価器: gen_eval2fd_m133.py(登録済み 3c51a35b の複製に MIST 入力だけを追加;MIST block を持たないモデルは従来どおり)。P と M を同じ run で評価(--model rank_v8w7a,rank_m133)。M は GL 経路の分子だけで P と異なり得る(fallback 経路は ranker を使わない)。

## 2. 読み(128 と同じ段階・関門)
1. **fold 1**(f1dev / np053f1dev / c1bankdev): 主指標 = 1/4 NP_H C2 + 1/4 NP_N C2 + 1/2 D C2(全件の分母)の M − P ≥ +0.005 かつ 95% 下限 > 0;block A(NP_H / NP_N C2)・block D の下限 ≥ −0.01;保護(下限 ≥ −0.01): 旧 B(f1 NP C2 C〜F)、G C1、053 NP C1、c1dev C1、c1dev の陽イオン C1 層(MIST が動く層だけで薄めない)。
2. **fold 2**(f2dev / np053f2dev、既使用なので安定性の記録): 主指標 > 0 かつ block A / D・旧 B・G C1・NP C1 の下限 ≥ −0.01。
3. **確認(一回)**: np096_conf093(H / N)+ np102_d0conf(D)を 1/2 ずつ(平均 ≥ +0.005 かつ下限 > 0、各ブロックの下限 ≥ −0.01)、C1 の費用は c1bank_f1/c1conf の陽イオン群の usable(下限 ≥ −0.01)。
4. **Public**(確認を通った場合のみ): MIST の推論を Kaggle の pipeline に移植(MIST の code と checkpoint の private 化、parity、時間)してから一回。読みは v8w7a(0.394)比の従来の規則。
- 記述(採否に使わない): 極性・GL 経路 / fallback・MIST の status 層・正解の式内順位の変化・特徴の重要度・パネル(MSG 既見)の差。

## 3. 未定(Codex に確認したい点)
- 対照の再学習の環境(PC / Spark)。fe61dc42 は PC の 127 で byte 再現済み。
- 学習(約 91 万行・3,931 群、v8w7a の記録)に MIST 列 19 個を足すことでの過学習の懸念と、特徴の数を減らす事前の版(例: cos / z / missing / 式内 rank / 割当の質だけ)を同時に登録するか(複数登録すると選択の問題が出るので一つに絞りたい)。

## 4. 確定版 v2(2026-10-29 21:19、Codex 133 を受けて、学習指標・評価は未読)
- **定義の修正(結果未読の意味の修正、候補は一つのまま)**: (1) mist_mol_noq = 分子に MIST の使える query(select_queries 後の [M+H]+ / [M+Na]+)が無い。候補式の有無と独立(mist_qflags.py が scorer と同じ query 規則で分子単位に出す;候補表と整合を検査)。(2) d_rank_mist_fp / d_z_mist_fp は MIST と FP がともに有限、d_z_mist_gl は MIST と GL がともに有限のときだけ(他は NaN)。b1_rankfeats **30b7a3d1**。v1 の M(23381757、旧定義)は未読のまま rank_m133_v1_unread に保存。
- **言い換え**: 式間の cos(raw / global z・rank・gap / rank_form_mist)も入力し、その信頼性の校正は学習に委ねる(「異なる式の cos を同じ尺度と仮定しない設計」とは言わない)。式群の最大 cos は群の候補数にも影響されるので、式の正しさの確率とは呼ばない。名称・読みは「**MIST + 候補式の特徴を加えた ranker の差**」(n_form のように MIST 値が欠損でも残る構造情報を含む;全増分を MIST の FP 予測に帰さない)。
- **割当の質の定義**: mist_fint = MIST の merge 後の強度のうち候補式の部分式に割り当てられた割合(生ピークの化学的説明率ではない);mist_npk = 割当済みの全ピーク数(top 10 ではない)の query 平均(非整数になり得る);mist_ppm = MIST の mass_diff(abs_error / max(m/z, 200) × 10^6)の query 内の強度加重平均を query 間で平均(割当 0 の query は NaN として除く;割当なしを誤差 0 にしない)。
- **入力の検査(全入口)**: mist_validate.py(status・null・未知 status・±inf・重複・ok / 非 ok の値域・品質列の値域・特徴表との公式 identity / SMILES の one-to-one)と query 旗の検査を、学習(b1_rank_train 77458713)と評価(gen_eval2fd_m133 **6a677fa6**)の読み込みで実行。最初の再学習は検証器の誤り(空の窓の分子を持つ query 旗を不一致と判定)で M が停止 → 包含の規則に直して再学習(記録 rank_m133_v2_validatorbug.log)。
- **再学習の結果(指標未読)**: 対照 = fe61dc42(再び byte 一致)、**M = aa8030d6**、学習 15 表すべて検査を通過、fit 群 3,931 / C1 比 0.457 は対照と同じ。
- **P0 は v8w7a(0.394)に固定**。132 の E-lite が作業基準になっても M − P0 を M − E-lite に読み替えない(組合せは別登録)。
- **露出の監査 v2**(msg_overlap_133.md): c1dev・c1conf・確認の C2 名簿(np096_conf093、np102_d0conf)も MSG と 0 件、解決できない key 0。
- **reader v2**(x133_summary.py **804ea02a**): 登録版の照合(評価器・特徴・trainer・検証器・query 旗・P・M・MIST の scorer / adapter / checkpoint / commit)、対照 = P の byte 一致、**対照と M の fit roster・構成・params・rounds が同一で特徴の差が EXTRA_MIST だけ**、全名簿の期待行・usable C1・重複・値域、P の main = 凍結 P、**P と M で各行の n_cand と GL 経路が一致し、GL fallback の行では最終リスト(top 25 の公式 key の hash)が一致**、入力の開始・終了の不変。STOP は非 0 終了。
- **読みの補足**: 再学習した ranker は MIST 値の無い分子でも変わり得る(構造上不変なのは GL fallback 経路だけ)。記述として GL 経路 × MIST の query 有無の件数と差、陰イオン側も出す。確認の C2 の重みは H/4 + N/4 + D/2、MIST が使える行へ分母を縮めない。C1 の usable は凍結した台帳の定義。確認集合(np096_conf093、np102_d0conf、c1conf の陽イオン usable)は他の依頼でも未開封・未使用であることを台帳で確かめて 133 に予約する。
- **Kaggle 移植の条件(確認を開く前に決める、Codex 133 Q3)**: MIST のコードは MIT(LICENSE と著作権表示を同梱)、checkpoint は Zenodo 23303289 の mist_msg_aug.ckpt(sha 9f251d77…、EMA 重み)に固定。(1) 入力・特徴の一致(query 選択・H / Na・候補式・電子補正・質量許容・20 ppm 割当・top 10 + CLS・直接 float16 丸め・FP bit・query 集約、CPU / GPU の許容は小試験で先に決める)、(2) 出力経路の一致(公式 key の順序付き top 25、GL fallback・MIST 全欠損・一部の式だけ有効・割当 0・強い参照・陰イオンを含む)、(3) 時間と資源を小さな代表集合で先に測る、(4) 未対応(no_mist_adduct 等 = 欠損特徴)と故障(読込・採点・照合・値域の失敗 = kernel 失敗)を区別。環境と実行時間の小試験は確認を開く前に済ませる。
