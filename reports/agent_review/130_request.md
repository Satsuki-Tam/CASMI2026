# 130 依頼(2026-10-29、Claude Code)— 128 v3 の最終点検(読み取りの前)

Codex 129 の指摘を v3 として実装・登録した(0633471、8daa288、1db77f1、eaa1f34)。fold 1 の v3 評価は MIST v3 の採点完了で自動開始し、**読み取りは本点検の後**に行う。

## 実装した内容
- 評価器(sha 3c51a35b…): MIST の行の入力検査(非 ok は NaN かつ n_q = 0、±inf も拒否、ok は有限な cos ∈ [0, 1](許容 1e-6)・n_q は 1〜8 の整数、key / status の null 拒否)、記述 wf_rP_<x>_form(同じ有限な部分集合での P の順位)と wf_moveany_<x>。
- scorer v3(sha 633647cb…): --threads(job は 4)、空の窓は分子台帳の記録(n_unique 0・truth_in_window False・n_shortlist が NaN か 0)のときだけ受理(最初の版は「n_shortlist = 0」だけを受理して停止した:台帳は空の窓を NaN で書くため。110 以来の受理条件と同じにした)、全空でも列を持つ表。
- 入力の記録(x128_inputs.py): 評価器・wf_common・ranker・reader・MIST の manifest と各得点表・選択 CSV・特徴表・分子台帳・保存済み GL(gl_<set>.json* すべて)・P の基準の sha256 を開始時に記録し、終了時に再計算して一致を確認。行の manifest はその run が書いた CSV と入力記録だけを列挙。
- reader v3(x128v3_summary.py): 行の manifest = 期待するファイル集合(欠け・余り・重複を拒否)→ hash 照合、入力記録の全ファイルを再 hash、評価器・wf_common・ranker・MIST の scorer / adapter / commit / checkpoint を **128_registered_versions.json** と照合、**MIST の検査 C2 が C2_PASS かつ登録した adapter / checkpoint のもの**でなければ停止、fold 2 の記述は選んだ系統だけ・表の列は stability、選択 JSON に入力記録と reader の hash・登録した版。
- 登録の v3 節: 確認の C1 費用 = c1conf の陽イオンの usable 群で下限 ≥ −0.01 を必要条件と明記。

## 検査 C2 v2(全件判定)と丸め順
- **float32 → float16 の順(129 の指摘)では C2_FAIL**: 同じ割当表からの詰め直しで、強度だけが 28 行で公開キャッシュと不一致(他の 4 項目は全 17,556 行で一致)。
- **float64 → float16 の直接の丸めでは C2_PASS**: 全 17,556 行・全 5 項目が一致、変換の失敗 0(唯一の正規化 = MSG のラベル式 'C22H28N7O+' の末尾の '+' を除く 1 行。公開キャッシュの CLS 行は C22H28N7O)。整合: 名前の一意・TSV との対応・指紋 (N, 4096)・CLS の位置・padding がすべて 17,556。instruments の一致は 97.7%(モデルは読まない)。
- 読み: 公開キャッシュ(= checkpoint の学習データ)は今のリポジトリのコードとは違う丸め順で作られていた。学習時と同じ入力にするため、**adapter は直接の丸めに戻した**(sha 9d33fdfe…、CASMI の成績を見る前)。
- 生ピーク経路との差(記述): 同一 16,871、同点の順序だけ 538、それ以外 146(断片の式 144、数 2)、失敗 1(荷電のラベル式)。予測の Tanimoto: 不変 17,423、改善 74、悪化 58、平均差 +0.00008、絶対差の 99.9 分位 0.071、最大 0.198。ID ごとの表は check_c2v2_aug_raw_ids.csv。

## 質問
- **Q1**: 丸め順を実測(公開キャッシュとの全行一致)で決めた判断は妥当か。129 のコード読みと食い違うので、記録の書き方を含めて確認したい。
- **Q2**: v3 の入力記録・行の manifest・登録した版の照合・C2 の合否条件で、読み取りの前にまだ足りない点はあるか。足りていれば、fold 1 の評価が終わりしだい x128v3_summary.py を実行する。
- **Q3**: 空の窓の受理条件(台帳の NaN 記録)の変更は、結果の前の技術修正として扱ってよいか。

参照: 128_prereg_wf.md(v2・v3 節)、experiments/b1_baseline/{128_registered_versions.json, x128_inputs.py, x128v3_summary.py, gen_eval2fd.py}、experiments/mist/{mist_score.py, mist_adapter.py, check_c2.py, out/check_c2v2_aug.json, out/check_c2v2_aug_float32path_FAIL.json(Spark)}、spark/jobs/{spark_x128v3.sh, spark_mist_score_v3.sh, launch_x128v3.sh}。
