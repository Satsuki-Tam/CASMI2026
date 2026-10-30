# 10/30 の提出計画(2) — 145 / 144 v2: F = P(v8w7a)+ E2 の identity RRF(K 10、α 0.5)(2026-10-30 11:07 JST = git 42da166、Claude Code)

## 位置づけ
- 144 の登録 v2 の判定(144_result.md、8777e2c)
  - F のローカル関門: 不合格(主指標 +0.0035)。
  - H: 不合格。出さない。
  - Public の診断経路: 条件を満たした。
- 登録どおり、F を「ローカル不合格の診断提出」として一度出す。
  - F は、最終提出にもなり得る完成した候補であり、プローブではない。
  - P(0.394)の置き換えは、Public を見る前に決めない。
- 132(E-lite)とは別の凍結候補である。132 の順位を F の対照に置き換えない。

## 提出する実体(全て凍結してから出す)
- **カーネル**: hayatetaf/casmi26-b1-e2f version 1(11:06:30 に push)。
  - 埋め込み: b1_pipeline.py 72a1a991…(make_e2k v2、LF)、e2_engine.py 85a429b6…、e2_common.py 3b34d05f…、ranker = v8w7a の stripped。
  - 引数: v8w7a の引数に、`--e2_model e2_lgb.txt --e2_model_sha fba8e860… --e2_hedge 0` を加えたもの。
- **データセット**: private の hayatetaf/casmi26-e2-model。
  - e2_lgb.txt(fba8e860…)
  - e2_ik14_to_scorer.parquet(2f025d15…、E2 専用の、開発と同じ索引)
  - manifest
- **P の不変**: GL / ICE の予算は、E2 の時間を除いて計算する。P の索引と analog store は、従来のまま凍結する。

## 提出の条件(全て満たした場合だけ)
1. Spark のパネル C1 の一致確認 v2(e2k_parity_check v2)が PASS すること。
   - 分子の全数、NaN を区別した列の一致、E2 の順位、オフラインの F、参照の P との順序付きの一致、e2_failed = 0。
2. Kaggle のコミット実行の点検(check_e2k_commit.py F)が PASS すること。
   - P が v8w7a の参照のコミット実行と byte 一致すること、引数、埋め込み、manifest の E2 の部分、E2_RECORD / E2_RDKIT。
3. 評価器 v3(Codex 145 の訂正: 名簿・順序の検査・固定の所属表)の再採点で、診断経路の条件が保たれること。
   - E 源の正解の C2 で、F − P が両 fold で正。
   - 新たに 1 位になった identity が 10 以上。
4. C2 の正解の別表記の監査(x145_alias_audit)で、楽観が判定を左右する規模でないこと。結果は記録する。

## 提出の命令(条件を満たした後に一回)
```
kaggle competitions submit enveda-CASMI26-molecule-id-mass-spectra -k hayatetaf/casmi26-b1-e2f -v 1 -f submission.csv -m "145 F = v8w7a + E2 identity RRF (K 10, alpha 0.5); 144 v2 local gate not passed -> registered Public diagnostic path; parity v2 + commit check PASS"
```

## 読み(登録 144 v2 §4'。Public を見た後で α / K / 窓を動かさない)
- 0.409 以上: 明瞭な正。新しい土台の候補にする(暫定の作業基準の更新。最終の提出の確定や Private での優位とは分ける。Codex 146)。
- 0.380〜0.408: 保留。開発の構成とのずれ(E 源の外の費用、人気度)を分析する。
- 0.379 以下: 負。F を主系に入れず、窓への到達・条件付きの救済・E 源の外の費用から、不足した場所を判定する。

## 11:28 一致確認 v2 の結果(logs/spark_e2k_parity_v2.log、experiments/e2/k_parity_c1_v2.check.log)
- **E2 の部分: 全て一致した。**
  - 250 分子の全てで、E2 の表の全ての列が開発の表と一致した(NaN の位置も含む)。
  - E2 の順位、オフラインで計算した F、分子の全数も一致した。
  - e2_failed = 0、索引の対応漏れは 0。E2 の所要時間は 683 秒。
- **不一致: P が PC の参照(run_v8w7a_c1)と 141/250 分子で異なる。**
  - 1 位は 250/250 で同じだった。
  - 共通の候補の 99.9% で f.z が 1e-4 を超えて異なり、最大の差は 11.6 だった。ライブラリ類似度の差は最大 0.0014。
  - FPNet の数値が、計算環境(Spark の GB10 と PC の RTX)によって異なることが原因と読む。P は E2 より前に計算され、E2 は P の行に触れない。
- **扱い(条件 1 の P の項の、参照の取り方を明確にする)**
  - P の不変は、同じ計算環境での対照で確かめる。同じ Spark・同じ引数で E2 を外した実行の P が、E2 ありの実行の submission_pref と完全一致することを見る(spark_e2k_pctrl.sh、実行中)。
  - 提出物そのものについての決定的な確認は、条件 2(Kaggle のコミット実行の P が、Kaggle 上の v8w7a の参照と byte 一致すること)で行う。
  - PC の参照との差は、計算環境の差として記録に残す。

## 11:35 条件 2: Kaggle のコミット実行の点検 PASS(kernels/check_e2k_commit.py、kernels/b1-e2f/output_v1)
- **P の不変**: submission_pref は、v8w7a の参照のコミット実行の二つ(b1-probe-tv8w7a / bv8w7a の output_v1)と、sha256 で一致した(808a2632… / de9d219d…)。
  - 固定の規則のリストと、probe の train / nontrain のリストも、400 行が全て同一だった。
- **E2 の記録**(E2_RECORD)
  - モデル fba8e860…、索引 2f025d15…、800 本、K 10、α 0.5、hedge 0。
  - 12 分子、E2 の失敗 0、1 位の変更 0、リストの変更 12。
  - 入力は全て /kaggle/input の下で解決した。
- **E2_RDKIT**: 2026.03.3、fixture 12 件が一致。
- **実行時間**: 927 秒(v8w7a の参照は 658 秒)。
  - E2 の準備は約 150 秒、E2 の計算は 1 分子あたり約 7.5 秒。
  - 隠しテストの 400 分子での見積もりは約 4.7 時間(P だけなら約 3.9 時間)で、9 時間の上限に収まる。GL の予算は変わらない。
- 出力の取得では、`--page-size 200` と `--file-pattern` が必要だった(10/29 の注意と同じ)。

## 11:38 Codex 146 を受けた変更(146_decision.md)
- 提出する実体を、**casmi26-b1-e2f version 2**(11:37 に push)に替える。
  - パイプラインのコードは同じ(72a1a991)。
  - 記録のセルで、索引の sha、対応漏れ 0、特徴、木 800 本、E2 の失敗 8 以下を assert する。
- 条件 2 は、v2 のコミット実行に対する点検 v2 の PASS とする(E2 の失敗 0 を含む)。
- 条件 3: 評価器 v3 で条件を満たす。P が空の 20 群は、全て正当な空だった。
- 条件 4: 別表記の監査の最悪側の判定で、条件が残る(g_min +0.0240 / +0.0244、47 identity)。
- 条件 1 の P の項: 同じ Spark での E2 なしの対照で判定する(実行中)。
- 提出の命令の `-v 1` は `-v 2` に替える。

## 11:44 条件 1 の P の項: 同じ計算環境での対照 PASS(logs/spark_e2k_pctrl.log)
- Spark で E2 を外した実行(同じ生成パイプライン 72a1a991、同じ引数で --e2_model なし)の submission.csv と、E2 ありの実行(k_parity_c1_v2)の submission_pref.csv を比べた。250 分子の全てで一致し、異なるリストは 0、ID の集合も同じだった。
- → E2 は P を変えない。PC の参照との 141 分子の差は、計算環境の差だけである。**条件 1 は満たした。**
- 残る条件: version 2 のコミット実行の点検 v2(実行中)。
