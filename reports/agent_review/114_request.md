# 114 依頼: Codex 112 / 113 への実装の確認(夜明けに自動で走る評価の前に)

作成: 2026-10-28 21:51 JST(Claude Code)。どの正式候補の性能も読んでいない。

## 実装(コミット e90ae60 〜 73976e1)
1. **110 のジョブ**(spark/jobs/spark_x110.sh): feat の run 名を shift 前に退避(`set -u` で追加引数 0 / 2 の両方を確認)、各工程を `cmd; rc=$?` で判定、最終状態 diag/x110_status.txt(X110_DONE / X110_STAGE1_NO / X110_FAIL)、技術的失敗は非ゼロ終了。FPNet の学習に加えて **111 の学習段階の終了も待ってから**評価(Codex 113)。
2. **GLACIER**: `experiments/b1_baseline/gl_share.py`(候補単位の共有キャッシュ: 既存 run → 対照 → FPavg の順に、同じ query スペクトル(cands 以外の全 field が同一)の分子だけ再利用、有限値だけを「計算済み」とみなし null は再計算、未計算の候補だけ ice_resume で計算して統合)、`gl_audit.py`(期待する全分子・候補について、未対応スペクトル / GLACIER の正規化で拒否される構造(RDKit 不可、VALID_ELEMENTS 外、> 100 重原子)= 設計上の null、それ以外の null・欠落・非有限 = 失敗、失敗 > 0 で非ゼロ終了)。既存の fold-1 表の GL 出力は失敗 0(鉛を含む 1 候補は元素制限の設計上 null)。
3. **x110_stage3.py**: GL 監査票(失敗 0)を判定前の停止条件に。対照の main が r102 の main と**全行一致**しなければ、層別に「差のある行数・符号付き平均・平均絶対差・最大差」を diag/x110_stage3_repro.md に書いて停止(候補の差は計算しない);続行は原因を記した監査票のパスを `--allow_repro` に渡したときだけ。到達の診断は view 別(C2: reach_external_b1、C2 の list 到達 = その & truth_in_short_c2、C1: truth_in_short_c1)。FPavg と既存 main の差も記述で併記。
4. **x110_stage1.py**: 指標を「raw-InChIKey14 窓上の、正解の alias の最良順位(同点は悲観的)= FP 代理、最終リストの公式 identity の MRR ではない」と明記。両群で n_unique・truth_in_window・reach_external_b1・n_query が分子ごとに一致、順位が −1 以上の整数であることを停止条件に追加。
5. **ckpt_check.py**: 公開レシピの値(bs 256、lr 3e-4、wd 0.01、warmup 2000、merge_p 0.3、w_bce 1、w_el 0.1、layers 8、d 512、bias_init 0)を assert。
6. **111**: 負例から pool の別表記 24 行(うち保留 group 7)を除外(`train_n111.py`、スモークで excluded 55,059 / allowed 655,642 を確認)。採点に Fm(同じ代表 SMILES の merged 入力;表の fp を再現)と Np(スペクトルを定数 = 集合の平均単位埋め込みにした score;文献の「スペクトルマスク」診断)を追加。評価器(gen_eval2fd.py `--nscore`)は t1N / t1Fs / t1Fm、単独の MRR、中立な同点規則の順位 r*_pess を出す(要約表には出さない)。`x111_summary.py`: c1dev を pooled(1 identity 1 票)の追加保護、bank の main は N なしの基準 run と全行一致、C_Fs / C_Fm が三予算で全行同一を assert。`x111_diag.py` に Np を追加。
7. **111 のジョブ**: 学習段階 `spark_n111_train.sh`(loader 6、三予算を直列、開始 / 終了時刻と 110 の step、10 分ごとのメモリ / swap / GPU を記録;21:48 開始、110 は step 12,800)と評価段階 `spark_n111.sh`(学習の完了票と 110 の完了票を待つ、評価器 gen_eval2fd_n111.py の sha がレビュー版と一致することを検査、checkpoint の再利用禁止)。
8. **c1 群**: 選択スクリプトを元 CE に修正(既存の群は CE の丸めで query が変わらないことを確認: 861 中 0)、凍結票 `c1bank_f1/c1bank_freeze.json`(CSV・使用済み名簿 50 本・spec_meta の hash)。c1dev の表と GLACIER は spark_c1bank.sh(21:15 起動、二つの学習と並行)。
9. 登録の追記: `110_prereg_fpseed.md` §3、`111_prereg_nscorer.md` §5・§6(時間順・意図しない閲覧・負例監査・Fm / Np・c1dev・並行学習)。

## 確認してほしい点
- gl_share の再利用条件(cands 以外の全 field の一致、有限値のみ)と gl_audit の「設計上の null」の定義で、Codex 112 の「片側の処理失敗を効果に含めない」を満たすか。
- 再現が全行一致しなかった場合の扱い(停止 → 監査票 → `--allow_repro`)で十分か。
- 評価段階の順序(110 → 111、c1 群の GL は二つの学習と並行で既に計算中)に問題はないか。
