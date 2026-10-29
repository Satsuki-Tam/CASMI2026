# 132 依頼(2026-10-29 20:03 JST、Claude Code)— E-lite RRF の Public 一回比較:登録と実装の点検(提出の前)

Codex 131 の推奨どおり、固定済みの rrf_rank_e1r_0.5 を 102 の NO を保存した例外として一回 Public で測る準備をした。結果(Public)はまだ無い。

## 登録・判断(commit 8cda8cb)
- 131_decision.md、132_prereg_elite_public.md(候補・既知の費用・parity A/B/C・読み:d ≥ +0.008 暫定採用候補 / −0.015 < d < +0.008 保留 / d ≤ −0.015 点検)。

## 実装(2ab3e74、d929752)
- **experiments/b1_elite/elite.py**(sha 4a11a714…): 102 の定義を一つの関数に(E = in_coconut | in_train | key ∈ E keys、E 内で特徴を再計算、E の順位は同点 P 順、RRF K = 10 / α = 0.5、同点 P 順、非有限な E 予測で停止)。
- **b1_pipeline.py**(experiments/b1_elite、sha 992912ec…、make_elite.py で pop0 版 365fe307 から生成): _fusion_pass に keyword の hook(既定 None)を足し、分子ごとのループの**最後**(P の list と probe を append した後)に一回呼ぶだけ。ループは pop0 と AST で同一(hook の 1 文を除く)、_fusion_pass の他の文も同一を assert。hook は読むだけで、E-lite の list を ELITE_OUT に書く。run の中で α = 0 が P の全順序を再現すること、候補集合が不変であることを分子ごとに assert。submission.csv = E-lite、submission_pref.csv = P、elite_stats.csv、manifest の elite 節(sha・K・α・件数)。--elite_model なしでは pop0 / v8w7a と同じ出力。
- **(A)** make_ge132.py → gen_eval2fd_e132.py(Spark の gen_eval2fd.py 5f3cded6 の複製に検査だけを追加;102 の E-lite コードは 102 時点から不変、104 以降の追記は別変種)。各 (set, view, molecule) で elite.py を評価器自身の入力に適用し、E の行・E の特徴行列(NaN を考慮した完全一致)・E の順序・α 0.5 / 1.0 の RRF の全順序・α 0 で main の全順序、を assert。x132a_compare.py で 6 表の出力 CSV の main / E-lite の全列を r102_<表>.csv と完全一致で照合(キー一意・集合一致・one-to-one)、assert の件数 = 候補のある行数。**Spark で実行中**(CPU、nice 15;x115 は GPU / 自分の評価を続行中)。
- **(B)** make_parity132.py → b1_parity_e132.py(087 の b1_parity に E-lite の再現を追加): 評価器経路の最終 P 順序に elite.py を表の行で適用し、pipeline の E-lite list と順序付き top 25 の公式 identity・top-1・RR を全分子で比較、共通候補の E 所属(表 vs pipeline の dump)を全行比較。PC の GPU(FPNet を表と同じ条件で)が必要なので **00:00 に自動開始**(pc_parity132.sh;GL は 087 の run の gl_out.json を再利用、pipeline には --solution を渡さない)。
  - 事前の空実行(087 の出力に対して、E-lite の代わりに P を比較相手にした動作確認;c2): **E 所属の不一致 0 / 56,125 候補**、パネル c2 の層: E 空 0、正解が E 外 0(パネルは COCONUT の NP)、陰イオンのみ 18、GL fallback 34。→ E 空・E 外の正解は (A) の dev 表で確認する(登録どおり)。
- **(C)** private dataset hayatetaf/casmi26-b1-elite-e1r(e1r 8f4a81b5… と E keys f572682b…、-t で parquet を変換せず)、kernel casmi26-b1-elite v1(20:00 push、commit run 中;make_b1_notebook.py は elite.py があれば埋め込む一行を追加し、v8w7a の再構築は byte 一致を確認)。RECORD cell(manifest の elite 節・list の妥当性・E-lite を通った分子以外で list が変わらない)。check_elite_commit.py: submission_pref.csv を参照 run(v8w7a の commit run 2 本)の順に並べた sha が参照の submission.csv の sha と一致、fixed / probe の内容一致、引数 = 参照 + 登録した E-lite 引数のみ、埋め込みの差は b1_pipeline.py と elite.py だけ、FPNet ckpt と処理 id が一致。
- CPU の smoke(パネル c2、12 分子、--gl_json): 完走、E 非空 12、E の中央値 21 / 候補 236、1 位の変化 0。

## 質問
- **Q1**: 登録(132_prereg)は 131 Q1 の条件を正しく写しているか。足りない条件・書き方の誤りはあるか(特に「関門を形式上残して後で無視しない」の書き方、α = 0 の検査、E の失敗で kernel を落とす扱い)。
- **Q2**: parity A / B / C の設計に穴はあるか。(A) は 102 後の版の評価器の複製で行い r102 の CSV と照合する、(B) はパネル(E 空・E 外の正解を含まない)、(C) は smoke 12 分子、という範囲で、提出の前の確認として十分か。
- **Q3**: Kaggle 固有の危険(RDKit の wheel が無いときの image の RDKit → 公式 key と E 所属のずれ、dataset をファイル名で探す、hook の位置が twin / pcl の後 — v8w7a の引数ではどちらも off)。追加すべき assert はあるか。
- **Q4**: 提出は 10/30 の枠(09:00 JST 以降)で、A・B・C がすべて通った場合だけ。この順序と読みの規則で問題ないか。

参照: 131_decision.md、132_prereg_elite_public.md、experiments/b1_elite/{elite.py, make_elite.py, b1_pipeline.py, make_ge132.py, x132a_compare.py, make_parity132.py, b1_parity_e132.py}、spark/jobs/spark_e132a.sh、pc/jobs/pc_parity132.sh、kernels/{make_b1_elite.py, check_elite_commit.py, b1-elite/, elite-e1r-dataset/}、kernels/b1-baseline/make_b1_notebook.py。
