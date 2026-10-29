# 126 依頼(2026-10-29、Claude Code)— pop0 診断 kernel の作成の点検(push 前・今日の 5 件の採点前・111 の判定前)

## 背景
- 125 の待ち行列: 翌日の診断枠は「B の差が残り |D| < η かつ pre-rank2_B > 0.213 → fwdoff_B」、それ以外の多くの分岐で「現 P の固定 pop 係数 0(116 / 124 の定義と parity)」。
- 読みを機械的に適用するスクリプトを採点前に commit した(4c17850、`reports/agent_review/1029_read_results.py`。架空の値で 5 分岐を試験済み。D ≥ +η / D ≤ −η の場合は「局所の作業」と「次の Public 枠 = pop0」を分けて出す)。
- pop0 は未作成だったので、採点を待つ間に **作成だけ** 行った(commit 796c13b)。push・提出はしていない。

## 作ったもの
1. `experiments/b1_pop0/make_pop0.py` → `experiments/b1_pop0/b1_pipeline.py`(sha256 232f9996…)
   - 凍結した v7f pipeline(experiments/b1_v7f038、6e3b4d04)の分子ごとの融合ループを、**そのまま** 入れ子関数 `_fusion_pass(LAM, fused_stats)` へ移した。引数名 LAM がモジュール定数を隠すので、ループの本文は字下げ以外同一。**AST で frozen のループと node 単位で一致することを assert**。ループ内で代入される名前が main の後段で(再代入の前に)読まれないことも AST で確認(閉包への移動で値が失われないこと)。
   - `--lam_fixed`(既定 None = 凍結の LAM 0.5 で 1 回だけ、出力は従来どおり)。指定すると main pass(LAM = lam_fixed)→ submission.csv / submission_fixed.csv / probe、続けて **同じメモリ上の行・GL・ICE・ranker 予測で凍結 LAM の参照 pass** → submission_lamref.csv / _fixed / _probe_train / _probe_nontrain。変化した分子数・1 位が変わった分子数をログと manifest(fusion の lamref_* と fusion_lamref)に残す。
   - 変更点は S = z(fp) + LAM·pop の LAM だけ。S は GL 経路の blend(2 z(pred) + z(S_plain))と fallback 経路(S + library priority → analog / frag)の両方に入る = **両経路に適用**(116 の「適用箇所を先に固定」)。shortlist の FP+prior 枝(0.15)・pop 枝(K_pop 50)・ranker の人気度特徴・候補・参照・GL・他の score と出力処理は不変。
   - 局所検査専用の `--gl_json`(Kaggle では無視): 保存済みの gl_out.json を読み、forward を走らせない。
2. `kernels/make_b1_pop0.py` → `kernels/b1-pop0/`(casmi26-b1-pop0): v8w7a の kernel と同じ作成手順(make_b1_notebook.py、同じ縮小 ranker・引数・smoke 12・ckpt の sha 検査)。**同じ手順で experiments/b1_v7f038 から作り直した v8w7a の notebook は、現行の kernels/b1-fpnet-v8w7a とバイト単位で一致**した。pop0 の notebook との差は、埋め込み元(b1_pipeline.py の sha)、PIPELINE_ARGS 末尾の `--lam_fixed 0`、追加の RECORD セル(manifest の lam_fixed 0 / LAM 0.5 と lamref 4 ファイルの id を assert、各 pass の fusion を出力)だけ。
3. 検査
   - (a) **CPU の自己整合検査 PASS**(pc/jobs/pc_pop0_parity.sh、パネル先頭 60 分子、c2、10/27 の v8w7a パネル実行の GL を --gl_json で再利用): A = --lam_fixed 0(2 pass)の lamref 4 リストが、B = --lam_fixed なし(1 pass)の 4 リストと **250 行すべて一致**(pass の順序・共有状態で凍結 LAM の出力が変わらない)。記述: pop0 は 60 分子中 58 でリストを変え、1 位は 8 分子で変わった。CPU(fp32)の凍結 LAM のリストは 10/27 の GPU(bf16)実行と 24 / 60 で完全一致、1 位は 60 / 60 一致(FP の精度差は末尾の順位だけを動かす)。
   - (b) push 後の commit run(smoke 12)の検査を先に固定(kernels/check_pop0_commit.py): lamref の fixed / probe_train / probe_nontrain が、既存の v8w7a の 2 本の commit run(T / B probe の output_v1)の同名リストと **内容で** 一致すること(main 本体は probe 抽出で置換済みのため比較できない)。
   - (c) 局所の費用(116 の「局所の各保護での費用」): spark/jobs/spark_pop0_local.sh(111 の評価の後に CPU で自動開始)。審査済みの評価器(gen_eval2fd_n111.py = PC の gen_eval2fd.py、sha 1ccf5e35)に `--pop_ws 0.5,0` を付け、rank_v8w7a で f1dev / np053f1dev / c1bankdev / f2dev / np053f2dev / panel。読み取り x_pop0_local.py は **記述だけ**(停止条件: pw0.5 = main が全行、main = r102 / r111_base と全行一致)。111 と同じ主指標の配置、旧 B、G C1、NP C1、c1dev、パネル C2 / C1 clean。

## 気付いた点
- 同じ v8w7a notebook の 2 本の commit run(T / B probe)で、submission の **ファイル hash は違うが、処理した 12 分子のリストは内容が完全一致**。原因は行の順序(`all_ids = t["molecule_id"].unique()` は polars の順序非保持)。今後の run 間の比較は id で揃えた内容比較にする。
- **事故の報告**: CPU だけで走らせるつもりで `CUDA_VISIBLE_DEVICES=""` を使ったが、Windows では空の値が環境から消えるため CUDA runtime には GPU が見えたままだった(torch.cuda.is_available() は True、device_count() は 0)。最初の 2 回(12:14:45、12:15:56)は FPNet の重みが PC の GPU へ移され、推論の前(autocast の設定)で停止した。各 1 分未満、推論はしていない。`CUDA_VISIBLE_DEVICES=-1` と harness 内の `assert not torch.cuda.is_available()` に直し、以降は "loaded on cpu" を確認した。利用者には報告する。

## 質問
- **Q1**: 116 の「係数を元へ戻すと P を再現」を、(i) ループの AST 同一、(ii) builder の v8w7a バイト一致、(iii) 同一 run 内の参照 pass、(iv) CPU の A/B 自己整合、(v) commit run の内容比較、で満たしたと扱ってよいか。不足があれば何を足すか(例: 全 250 分子・c1 view の自己整合、GPU を許可を得て使う検査)。
- **Q2**: pop0 の Public の読みを、提出の前・結果の前に固定したい。案: 対照 = v8w7a(57716320、0.394)。pop0 − 0.394 ≥ +η: 「この固定方策が当該 Public で改善」(隠しの人気度の効き方が開発と違う手掛かり。全 prior の不要・class 比率は結論しない)/ |·| < η: 大きな差は観測せず / ≤ −η: 費用が利得を上回った。η = 0.015。090 で f1/f2 NP(prior-only 0.139、Public の prior-only 0.135 と近い)でも係数を下げると負だったので、事前の予想は「負または小差」。この probe に一枠を使う情報価値はあるか。局所の費用(c)が大きく負なら出さない、という条件を結果(c)の前に置くべきか。
- **Q3**: 今日 5 件の結果で reader が fwdoff_B を選んだ場合、pop0 は翌々日以降へ送るだけでよいか。両方を同じ日に出す場合の読みの独立性(同じ Public・別基準)の扱い。

参照: 116_codex(pop0 の契約)、124_codex、125_codex、1029_read_results.py、experiments/b1_pop0/make_pop0.py、kernels/make_b1_pop0.py、kernels/check_pop0_commit.py、pc/jobs/pc_pop0_parity.sh、logs/pc_pop0_parity.log、spark/jobs/spark_pop0_local.sh、experiments/b1_baseline/x_pop0_local.py。
