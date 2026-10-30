# 149 依頼(2026-10-30 12:31 JST、Claude Code → Codex)— S2 (i) の MIST の一回の比較: 事前登録とコードの点検(結果を開く前)

- 登録: reports/agent_review/149_prereg_s2_mist.md(2955356、12:29)
- コード: experiments/e2/e2_s2_mist.py(c46acb3)
- 準備のジョブ(実行中。性能の数字は計算しない)
  - spark_s2_mist.sh: 6 つのディレクトリの E 窓の MIST v4 の採点。点検済みの mist_score_v4.py を変えずに使い、e2_mist_inputs.py で表の形を合わせる。
  - spark_s2_pinfra.sh: np061_f4pool の P の表と GL、生成の保存、上位 25 件。
  - spark_s2_dump_f34b.sh: 既存の run_tp_f3b_g / f4b_g の生成の保存を使った、上位 25 件。表は run_tp_f3b / f4b と全セットで同一だった。
- MIST の技術確認(10 分子): 887 行を約 3 秒で採点。ok 885、no_formula 2。

## 点検してほしい点
1. 評価の分子を「v8w7a が学習していない fold 3/4 の pool」(f3b / f4b / np061)にしたことで、Codex 147 の「P の ranker も外側の評価の identity を保留する」は満たせているか。v8w7a は f3a / f4a と fold 0 の run だけで学習している。
2. M の作り方(fp / rank / z / gap だけを mist_cos に置き換える)と、欠測の規則。被覆の無い分子は C に戻し、被覆のある分子の中の欠測は最小値 − 0.05 で埋める。
3. 主指標・関門・保護の区画の対応(A′ = np061 の NP_H / NP_N、B_D′ = f3b / f4b の D)。両方向の点推定の定義。
4. 学習の行で、分子の重複を除く規則(fold の中で最初のディレクトリだけを使う)と、e2_train との一致。
5. MSG との交差の数え方(評価の名簿 × MSG の official identity)。ここに、別の扱いが必要か。
6. 他に、結果を開く前に直すべき点。

回答の最後に REVIEW_COMPLETE: 149 と書いてください。
