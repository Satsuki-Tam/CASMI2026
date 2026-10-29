# 132 事前登録: 固定した E-lite RRF(rrf_rank_e1r_0.5)の Public 一回比較 — 102 の NO を保存した例外

作成: 2026-10-29 19:42 JST(Claude Code、時刻は date)。Codex 131 Q1 の条件をそのまま固定する。Public の結果を見る前。

## 0. 位置づけ
- **102 の判定(開発の関門で選択なし)は変えない。** 本件は 10/29 の Public 診断(B 群で E0 の後段が rank-2 前で両単体より +0.026、1029_results_reading)を受けて**方法を選び直した**一回の比較であり、方法の選択に Public を使っている。定数(E、E 窓、K、α)は 10/28 の 102 で固定済みだが、これは「Public を使っていない確認」ではない。
- **従来の全保護層の非劣性を通った候補ではない。** 102 の関門を形式上残して提出後だけ無視する運用はしない。採否はこの登録の §3 の Public の読みだけで決める。
- 受け入れる既知の費用(102、開発、strict、variant − main): B_D(f1/f2 D C2)−0.0348、旧 B(C〜F)−0.0467、正解が E 源の外の C2 行 −0.1160、パネル C1 clean −0.0348。利益: A(053 NP C2)+0.0390、G C1 +0.0480、053 NP C1 +0.0267。開発の主指標 +0.0021 [−0.0142, +0.0176]。
- 構成への感度(推定ではない): A / D の単純混合で Δ(w) = 0.0390 w − 0.0348 (1 − w)、w ≈ 0.472 で符号が変わる。E 所属が同じでも極性・人気度・参照条件で差は違う。

## 1. 候補(一つ、固定)
- **P** = v8w7a の提出済み実体: kernel casmi26-b1-fpnet-v8w7a と同じ引数・ranker(rank_v8w7a、sha256 fe61dc42…;kernel は予測同一の stripped 版 41413657…)。sources は experiments/b1_pop0(b1_v7f038 の分子ごとの融合を _fusion_pass へ verbatim に移したもの;既定の引数で v8w7a と同一 — AST 同一性、パネル 250 の CPU A/B、pop0 の commit run での参照 run との内容一致で確認済み)に E-lite を足した experiments/b1_elite。
- **E** = rank_e1r(102、LightGBM lambdarank、sha256 8f4a81b5…、e1 の 24 特徴)、**E key v2**(diag/e_window_keys_v2.parquet、sha256 f572682b…)。
- **E 部分集合** = P の全 shortlist(公式 identity で重複除去済みの候補行)のうち `in_coconut | in_train | 公式 key ∈ E key v2`(102 と同じ「P の全 shortlist の E 部分集合」)。full E 窓への拡張・別 FPNet・先頭固定は入れない。
- E の特徴は **E 部分集合の中で再計算**(feature_matrix に部分配列を渡す = 学習・102 評価と同じ定義)。GL 経路・fallback 経路の両方の分子に適用。
- **r_E**: E の予測の降順、同点は P の順。**RRF(i) = 1/(K + r_P(i)) + α/(K + r_E(i))**(r_P = P の最終順序の 1 始まりの順位;E 外の候補は第二項 0)、**K = 10、α = 0.5**、同点は P の順。最終 top 25(行 = 公式 identity)。
- E が空なら P と同一。**E の予測が非有限なら停止**(kernel は失敗し、その版は提出しない;p_e の票や P へ置き換えない)。
- 同じ run の中で α = 0 の経路が全分子で P の全順序を再現することを assert し、P のリスト(submission_pref.csv)も同じ run で書く。

## 2. 実装と parity(Public の前に全て通す。どれかが通らなければ提出しない)
- **(A) 関数の同一性(Spark、CPU)**: 共有関数(experiments/b1_elite/elite.py)を、102 の評価器の複製(gen_eval2fd の複製に検査だけを足す;本体は不変)の中で同じ入力に適用し、102 の 6 表(np053f1dev / np053f2dev / f1dev / f2dev / panel / p2dev)・c1 / c2 の全分子で (i) E の順序と RRF の全順序が評価器の inline 実装と完全一致、(ii) α = 0 で main の全順序と一致、(iii) 出力の RR(main、rrf_rank_e1r_0.5)が保存済みの diag/r102_<表>.csv と全行一致(キーの重複なし・集合の一致・one-to-one)。
- **(B) pipeline と評価器の経路(PC、GPU は 0〜9 時)**: パネル 250、c2 / c1 の評価モード、087 の parity と同じ設定で、GLACIER は 087 の run(run_v8w7a_<view>)の出力を再利用(--gl_json;forward は走らせない)。b1_parity の拡張版で (i) P の順序付き top 25 の公式 identity が全分子一致(087 と同じ基準)、(ii) 共通候補の E 所属が全行一致、(iii) E-lite の順序付き top 25 の公式 identity が全分子一致、(iv) RR 一致。層の件数(E 空、正解が E 外、陰イオンのみ、lib ≥ 0.9 の強い参照、GL fallback)を記録する。パネルで 0 件の層は (A) の全 dev 表(全層を含む)で補う。
- **(C) Kaggle**: private dataset(e1r の lambdarank.txt と E key v2;notebook で sha256 を照合)。kernel は v8w7a の作り方(make_b1_notebook.py、smoke 12)+ E-lite の引数。commit run で (i) submission_pref.csv の内容が v8w7a の参照 run の submission.csv と一致、(ii) E-lite のリストが妥当(全分子・非空・25 以下)、(iii) manifest に E の件数・P との 1 位の変化・E の失敗 0 を記録。

## 3. 読み(Public、通常出力 vs P = 0.394)
- d = Public(E-lite) − 0.394。**d ≥ +0.008 → 暫定採用候補;−0.015 < d < +0.008 → 保留;d ≤ −0.015 → 点検して主系へ入れない**(境界は重複させない)。
- 技術的な不一致がなく Public ≥ 0.402 なら、次の開発の作業基準(P の代わり)に使う判断は可能。ただし 102 の NO と特定層の費用は残す。0.500 達成とは別の中間成果。
- 一回の結果を見て α・K・源の定義を連続して動かさない。正なら「この固定候補がこの Public で改善」、負なら「この候補の便益が費用を上回らなかった」と読む。いずれも隠しの E 率や、改善の全てが源の加重によることは決まらない。Private への移行は未確認。
- 参考: Public は約 130 分子で、1 分子の RR が 1 変わると約 0.0077。

## 4. 並行(この比較の結果で変えない)
Codex 131 の Q2 / Q3(131_decision.md): 全名簿の源の確定と源の感度表、MIST 特徴の ranker 再学習の一対比較、GLACIER の timsTOF 適応、class 3 の実現性。

## 5. Codex 132 を受けた技術修正(20:31、Public の前;候補・定数・読みは不変)
- 書き方の訂正: §0 の「採否はこの登録の §3 の Public の読みだけで決める」は「**§2 の技術的成立(A・B・C の合格)を確認した上で、性能上の判断を §3 で行う**」と読む。elite.py の冒頭の「r_E … 0 for rows outside E」は「E 外は第二項 0(実装上 r_E = ∞)」の意味(実装と登録の式は一致;(A) で使った elite.py 4a11a714 の実体を変えないため、ファイルは書き換えない)。
- **(A) の結果(20:22)**: 6 表・両 view の候補のある全分子で、評価器の inline 実装と elite.py が E の行・E の特徴行列・E の順序・α 0.5 / 1.0 の RRF の全順序・α 0 の main 順を完全再現(assert 件数 = 候補のある行数)。保存済み r102 の全 RR 列とも全行一致(x132a_compare.md、**PARITY_A PASS**)。最初の比較器は pandas 3 で NaN 同士の比較を不一致と数える誤り(候補 0 の行の e_reach)があり、NaN を考慮する版に直して保存出力を再比較した(v1 の出力は x132a_compare_v1_nanbug.md に保存)。親ジョブは FAIL を非 0 の終了にするよう修正(spark_e132a.sh)。
- **(C) v1 の結果(20:21)**: commit run の P(submission_pref.csv)は v8w7a の参照 run 2 本と byte 一致、fixed / probe 一致、E-lite の list は妥当(check_elite_commit.py PASS)。ただし下の修正で pipeline と notebook が変わるため、**提出する版で C を取り直す**。
- pipeline(b1_pipeline.py **930fa3f8**、make_elite.py): E 有効時に K = 10・α = 0.5・pcl_boost off・twin_tau None・主 ranker の読込を要求;E 入力は同名が複数あれば期待 sha のものだけ(曖昧なら停止)、解決した絶対パスと「期待 sha を渡したか」を manifest に記録;E 空なら E-lite = P、候補の公式 key は非 null・一意を分子ごとに assert;elite_stats は空でも列名を固定。elite.py は不変(4a11a714)。CPU の smoke で旧版と全出力の内容が一致(行の順だけ違う)。
- notebook v2(make_b1_elite.py): pipeline の前に **公式 identity の RDKit = 2026.03.3** と互変異性・立体の fixture 12 件の公式 key を、pipeline と同じ新しいインタープリタで検査し、版・パス・wheel の hash を ELITE_RDKIT として記録(違えば停止)。RECORD: 期待 sha を渡したこと、入力が /kaggle/input 下に解決されたこと、elite_stats の分子 = n_shortlist > 0 の処理済み分子(一意)、n_cand = n_shortlist、0 ≤ n_e ≤ n_cand、E 空の分子で list 不変。
- (B) v2(b1_parity_e132.py、make_parity132.py): E-lite モードでは全入力の存在、名簿(solution)・P / fixed / E-lite・stage stats の ID の一意と集合一致を先に要求し、**比較した ID = 評価器の表で view の list が空でない名簿の分子**を要求、list が空の名簿の分子は P と E-lite が同じ placeholder であることを要求(分母から落とさない)。ジョブは各 pipeline を 08:00 前にだけ開始し 08:55 で打ち切る(未完了 = FAIL、範囲を縮めない)、FAIL は非 0 で終了。
- 提出の条件: A の JSON が PASS、B の c1 / c2 の parity がともに PASS(終了コード 0 と md の PARITY PASS)、提出する notebook の版の C が PASS、各記録の hash が提出する notebook・e1r・E keys と対応すること。読みは登録どおり(Public ≥ 0.402 暫定採用候補 / 0.379 < Public < 0.402 保留 / ≤ 0.379 点検)。
