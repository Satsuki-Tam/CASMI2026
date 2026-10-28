# 120 相談: 115 v2 の読み取り・学習ジョブ・評価ジョブの点検(R / A の学習・性能の前、2026-10-29 05:05 JST)

Codex 119 の指摘を反映した 115 v2 について、R / A を学習する前に、読み取りとジョブ一式を点検してください。性能はまだ何も読んでいません(R / A の checkpoint は未作成。M_all の CPU 生成は 04:58 に開始し、性能の数値は出していません)。

## 対象(commit 225acaf、363ad0a)
- 読み取り: experiments/b1_baseline/x115_stage1.py(FP 代理。関門は dFP(A − R) > 0 かつ dFP(A − P0) > 0)、experiments/b1_baseline/x115_stage3.py(端から端の比較。A − R と A − P0 の両方が主指標・ブロック・保護を通ることを条件とし、c1dev は pooled。3 群を同じ identity の再標本で対応させた bootstrap)。計画は 115_plan.md の「読み取りの固定」節。
- 学習ジョブ: spark/jobs/spark_e115_train.sh(1 本で 1 群。登録したレシピを固定。ck115_check.py には、ファイルの現在の hash ではなく**登録済みの trainer sha256 67ca8f21…** を渡す。他の GPU ジョブがあれば起動を拒否する。A は生成 prefix を絶対パスにして渡し、完全被覆・hash・失敗 ≤ 1% は trainer 自身が検査する)。
- 評価ジョブ: spark/jobs/spark_x115.sh(spark_x110.sh の構造をそのまま写したもの):
  1. slot ディレクトリ: e115_slot_{r,a} に fpnet_fold0.pt → 各群の final、fp_bits.npy → 公開の bits を置く。既存の slot は対象が完全一致する場合だけ使う。評価器の loader(fpnet.load_model)で一度読み込む。
  2. 表を同じコード・同じ系で 3 回作る: f1dev / np053f1dev / c1bankdev × P0 / R / A。引数は 110 と c1bank のものと同じで、--fold_safe だけが違う。workers は 6。P0 と既存の表の一致は記録する。
  3. 段階 1。PASS のときだけ:
  4. tag ごとに候補単位の cache を一つ持つ GLACIER(既存 → P0 → R → A の順。未計算の候補だけを計算)+ 監査、v8w7a の main(3 群 × 3 tag)。
  5. 段階 3(exit 2 = 再現の失敗)。
- 両ジョブの拒否経路(110 が動作中)は Spark で確認済み。ファイルは何も作られない。

## 質問
1. **段階 3 の c1bankdev の再現の基準**: 基準は diag/r111_base_c1bankdev.csv で、これは gen_eval2fd_n111.py を --nscore なしで実行したもの。一方 P0 は gen_eval2fd.py で評価する。この 2 本は、nscore なしのときに同一の main を返す前提でよいか。それとも x115 の P0 も gen_eval2fd_n111.py(--nscore なし)で評価して、評価器を揃えるべきか。
2. 表の作成で `--workers` が 110 の 8 と c1bank の 6 で混在している。workers の値は manifest に入らず、結果にも影響しない想定(110 の x110_table_identity で確認できる見込み)。この前提に問題はないか。3 群の並列実行(各 6 workers)で問題はないか。
3. 共有 GL cache の順序(既存 → P0 → R → A)と、群ごとに異なる shortlist に対する未計算分だけの計算は、群の間の比較を歪めないか(GLACIER の数値はバッチ構成で 2.5〜4% 揺れることを確認済み。cache により同じ候補には同じ値が入る)。
4. spark_e115_train.sh の起動拒否のリストに過不足はないか。特に GPU 上の gl_simulate(M_all の残りの GPU 生成)との同時実行を、拒否せず許していること。R の学習中に GPU 生成を並行するかどうかは、速度を測ってから決める予定。
5. 段階 1 の診断列(truth_in_mall、truth_sim_exposure)は判定に使わない。真の M_all 所属の判定は pool_meta の key → pid の対応で行い、scorer_key が pool に無い分子は pid −1 で「露出 0」とする。この扱いに問題はないか。
6. その他、結果の前に直すべき点。

最後は REVIEW_COMPLETE: 120 で終えてください。
