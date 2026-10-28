# 102 事前登録: 第二エンジン E-lite(人気度・候補源を使わない別リスト)と v8w7a の identity RRF

作成: 2026-10-28 14:2x JST(Claude Code)。結果を見る前に固定する。Codex 101 の 3〜5 日目の「小規模な第二エンジン」の第一段。

## 0. 動機(101 までの事実)
- E0 の B probe: BASE(engine 1)0.213 → 最終 0.259。後段(engine 2 のリストとの RRF、式群内の GL、rank-2 挿入、候補の追加)で +0.046。
- E0 の engine 2(cell 08 を読んだ):窓 = COCONUT + BIO + PubChemLite + train、特徴 = ライブラリ類似度・analog(Tanimoto × sim³ / sim⁶)・FP・MetFrag-lite・質量誤差・窓の大きさ。**人気度・候補源の特徴は一つも無い**。点ごとの HistGB(depth 6、500 iter、lr 0.03、min leaf 80)。
- 090: 単一 ranker から人気度を除くと開発の全集合で悪化(f1/f2 NP C2 −0.008、G C1 −0.041)。一方、prior 順位 11 位以下の正解では +0.024〜+0.032。→「同じ証拠を第二のリストとして混ぜる」ことは、単一 ranker の特徴削除とは別の仮説(Codex 101 Q4)。
- 101 の候補窓の監査: pool + BIO + PubChemLite の窓(中央値 60〜100)は COCONUT 正解について B1 の窓と同じ到達、B1 の shortlist(0.850 / 0.878)より僅かに高い(0.866 / 0.884)。

## 1. 第一段の範囲(E-lite)— 既存の表を使い、新しい候補・新しい証拠は入れない
- 候補: 既存の B1 の表(shortlist の和集合)の行のうち **E 窓** = `in_coconut | in_train_<view> | official key ∈ PubChemLite ∪ BIO`(`diag/e_window_keys.parquet`、e_keys.py:PubChemLite は同梱の公式 key、BIO は SMILES から公式 key を再計算)。C2 view では正解の train 所属を隠すので、train にしか無い正解は E 窓に入らない(Codex 101 の規則)。B1 の shortlist 外の pool 候補(COCONUT 正解で 1.6〜0.6%)は入らない = 限界として記録。
- 特徴 `e1`(24、b1_rankfeats.py):z_fp, fp, rank_fp, gap_fp, margin_fp_mol, z_gl, gl, rank_gl, gap_gl, margin_gl_mol, gl_missing, lib_sim, lib_same, lib_margin, lib_max_mol, lib_rank, ppm_err, n_cands, n_query, ce_known, ana_ap, z_ana_ap, ana_mt, ana_gap。**人気度 7 特徴・in_tier / in_train / in_coconut・lib_nref・fp_rank_window・ICE は無し**。相対特徴は E 窓の中で再計算(学習・評価とも)。
- モデル(学習行 = v8w7a と同じ:RUNS0 v3 + pool f3a/f4a、C1 ×3(pool は ×1)、analog 特徴 analog_tr_v8w):
  - **e1b**(主): LightGBM binary(点ごと)、群ごとの総重みを揃えた行重み(行平均 1 に再尺度)、固定 params(rank_params_e1b:31 leaves、depth 6、lr 0.03、min leaf 80、500 rounds;探索なし)。
  - **e1r**(対照): LightGBM lambdarank、同じ行・特徴、params = rank_params_v7a(31 leaves、lr 0.03、600 rounds)。
- 主リスト P = v8w7a の v7f 出力規則(gen_eval2fd --v7f、GL 経路 = 2z(learned)+z(fixed)、fallback = 保険 + z(ap) + z(MetFrag-lite))。

## 2. 融合(固定)
- 行 = 公式 identity(表は公式 key で重複除去済み)。RRF(i) = 1/(K + r_P(i)) + α · 1/(K + r_2(i))、第二リストに無い候補は第二項 0。**K = 10 固定**(E0 の K=3 は LB 合わせなので移植しない;標準の 60 との中間を事前に固定、調整しない)。同点は P の順。
- 第二リスト: E(e1b / e1r)と **p_e = P の順位を E 窓に制限したもの**(候補源の加重だけの対照:新しい順位を含まない)。
- 候補 6 つ: rrf_e1b_{0.5, 1}、rrf_e1r_{0.5, 1}、rrf_pe_{0.5, 1}。α は E の重み(P は 1)。rank-2 挿入は同時に入れない。

## 3. 開発での読み(既に使った開発表のみ;確認集合は開かない)
表: np053f1dev / np053f2dev(NP_H / NP_X / NP_N、COCONUT 正解)、f1dev / f2dev(C〜G)、panel(run_panel_fe、full_eval)、p2dev(stress)。評価器 = gen_eval2fd --v7f --parents 0 --views c1,c2 --emodel rank_e1b,rank_e1r(P の main は gen_eval2m と一致することを 099 で確認済み)。
- **主指標 = 2 ブロックの平均**(どちらも C2、strict、variant − main、identity bootstrap 4,000):
  - A = 053 NP C2(H / N 等重み、fold 等重み):COCONUT 正解(B 群の代表)
  - B = f1/f2 dev NP C2(C / D / E / F 等重み、fold 等重み):正解の人気度が隠しに近い、PubChem のみの正解を多く含む
- **関門(候補ごと)**: 主指標 ≥ +0.005 かつ下限 > 0;ブロック A・B それぞれ非劣性(下限 ≥ −0.01);保護(下限 ≥ −0.01): **G C1(f1/f2)、パネル C1 clean、053 NP C1(H/N)**。
- **選択**: 関門を通った候補のうち主指標の点推定が最大のもの一つ。無ければ「なし」。
- **E の順位の価値の読み(候補源の加重との区別)**: 同じ α で rrf_e − rrf_pe(主指標)。下限 > 0 なら E の新しい順位に価値;|差| が小さく rrf_pe も関門を通るなら、利得は候補源の加重(P が E 窓の候補を過小評価)と読む。選ばれたのが rrf_pe なら「E は不要、候補源の再加重」として記録し、次の段の設計を変える。
- 診断(採否に使わない): e_only・p_e・orc(max(main, E 単体))の MRR、救済 / 損失の件数(variant の RR > / < main)、正解の COCONUT 所属で分けた差(非 COCO C2 の費用)、GL 経路 / fallback、H / N、C1 の 2 位以下への後退、p2dev。

## 4. 確認(関門を通った一候補だけ、1 回)
- C2: **np096_conf093(NP_H 200 + NP_N 200、fold 0、未開封)** を 102 の確認へ用途変更(093 は開発の関門を通らず、確認は開いていない)+ **新しい fold 0 の D 型(NP 単一ライブラリ)集合**(既存の全選択 CSV とパネルを除外して選ぶ;件数・seed は開く前に記録)= ブロック A / B の構成を保つ。
- C1 費用: c1cost098(E 100、fold 0、作成済み・未開封)。timsTOF の C1 費用(G 型)は新集合が作れないため独立に確認できない(096 の記録どおり、限界として明記)。
- 確認の条件: 2 ブロックの平均 ≥ +0.005 かつ下限 > 0;各ブロックと c1cost098 の下限 ≥ −0.01。

## 5. 実装(結果の前に固定)
- e_keys.py(新規)、b1_rankfeats.py(`e1`)、b1_rank_train.py(`--restrict E`、`--ekeys`、`--pointwise`)、gen_eval2fd.py(`--emodel`、`--ekeys`、`--rrf_k`;main と他の変種は不変)、rank_params_e1b/rank_results.json。
- 学習・評価は Spark。結果の読みは x102_summary.py(この登録の規則のみ)。
