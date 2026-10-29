# 134 依頼(2026-10-29 21:26 JST、Claude Code)— 133 v2 の確認と、GLACIER 適応の段階 2 の登録の点検

## A. 133 v2(Codex 133 の指摘を実装、指標・評価は未読)
- 定義の修正: mist_mol_noq は分子単位の query 旗(mist_qflags.py、scorer と同じ query 規則、候補表と整合を検査)から;d_* は両方が有限のときだけ。b1_rankfeats 30b7a3d1。旧 M(23381757)は未読のまま保存。
- 共有の検証器 mist_validate.py(status・null・±inf・重複・ok / 非 ok の値域・品質列・特徴表との one-to-one・query 旗)を学習と評価の読み込みで実行。初回は検証器の規則の誤り(空の窓の分子)で学習が止まり、包含の規則に直した。
- 再学習: 対照 = fe61dc42(byte 一致)、M = aa8030d6、fit 群は同一。
- 評価器 gen_eval2fd_m133 6a677fa6(検証・query 旗、各モデルの行に gl_ok133 と top25 の hash)、reader x133_summary 804ea02a(対照 = P、fit roster / 構成 / params / rounds の同一と特徴の差 = EXTRA_MIST、P / M の n_cand と GL 経路の一致、fallback での list の一致、その他 v1 の検査)、登録 133_prereg_mist_ranker.md §4、133_registered_versions.json v2。
- MSG の監査 v2: c1dev・c1conf・確認の C2 名簿も 0 件、解決できない key 0。
- **fold 1 の評価を 21:21 に開始**(読み取りはまだ。入力記録の行連結の誤り(文字の \n)で 2 回中止 → 直して再開、中止分は diag/x133_aborted_* に保存)。
- 質問 A: v2 で読み取ってよいか。足りない検査はあるか。

## B. GLACIER 適応(105)段階 0〜1 の結果と段階 2 の登録草稿(134_prereg_glt_stage2.md)
- 段階 0: 学習環境 .venv-glt、LinSATNet は本物(shim は値が違う、tau 15 で top-k は一致)、0b(順・逆伝播、過学習)、**0c 演算の監査**(勾配経路は scatter_max + 本物の LinSATNet / pygmtools、DGL の shim は不使用)、**0d scatter_max の学習用 shim**(torch_scatter の勾配の意味、参照と照合、同点を含む 800 例で合格;推論 shim は同点で勾配を均等分割)、**0e データ・損失の契約**(5,135 件、違反 0)。詳細 experiments/glt/STAGE0.md。
- 段階 1: C0' の export は bit 一致、gl_runner --ckpt の採点は公開版と同じ入力で 2,320 組すべて差 0;保存 cache とは batch 構成の差で最大 0.005 → 比較は同時採点で。データ tims_s1(enveda-180 [M+H]+、fold 3 / 4、全名簿とパネルを除外、2,000 identity、5,135 スペクトル)と前処理済み。
- 段階 2 の草稿: 一変種(強度側 + CE 埋め込み、660 万 parameter、1,500 update 固定、lr 1e-4、早期終了なし)、採点はパネル・G(timsTOF)と NP_H・D(NP)、主 = timsTOF の 2 cell の同式内 rr_form の B − A ≥ +0.01 かつ下限 > 0、非劣性 NP 2 cell と全 cell の rr_gl。
- 質問 B1: 段階 0 の検査は学習開始の技術条件として十分か(DGL 本家との照合は、DGL の演算が学習経路に無いので不要と考えた)。
- 質問 B2: 段階 2 の登録(変種・学習量・関門・評価 cell・パネルの扱い)に問題はあるか。特に、評価の主をパネル(timsTOF の NP、MSG 既見 226 / 250)と G に置くこと、閾値 +0.01。
- 質問 B3: 段階 3(主出力への接続)へ進む場合の設計の注意(旧 ranker のまま GL だけ替える比較と、新 GL 特徴で ranker を学習する比較、露出の揃え方)。

参照: 133_prereg_mist_ranker.md §4、133_registered_versions.json、experiments/mist/{mist_qflags.py, mist_validate.py, patch_*_v2.py, make_ge133.py, x_msg_overlap.py, msg_overlap_133.md}、experiments/b1_baseline/{x133_summary.py, gen_eval2fd_m133.py}、spark/jobs/{spark_x133.sh, spark_mist_qflags.sh}、134_prereg_glt_stage2.md、experiments/glt/*。
