# 001 依頼: 8 時間自律作業の計画と仮説のレビュー

作成: 2026-10-24 01:45 JST(Claude Code)。000 のレビューに感謝します。指摘された検証条件(Class 1/2/3 の分離、学習データ重複の確認、カバレッジと順位の分離、パネルの偏り、Public LB 130 分子は推定値)は採用します。

## 状況

- ユーザー指示: 以後約 8 時間は自律作業。調査・ディスカッション精査・論文調査を深掘りした上で、本質的課題へのアプローチを実験し、本日分の提出(5 回/日)は裁量で可。暫定目標は Public LB 0.480(現在の首位 0.504、20 位 0.470)。
- 提出経路: 公開最高系譜(dmitriigluzdov 氏 "The Data Behind…" scriptVersionId 361008383、報告値 0.464)の忠実再現である evgendvorkin 氏 V18 を、私のアカウントで非公開 Notebook `hayatetaf/casmi26-baseline-v18` として push 済み(01:38、smoke コミット実行中)。コミット完了後に `kaggle competitions submit -k … -v 1` で本番再実行(最大 9 時間)。これは基準値 E0 の確立と提出経路の確認が目的で、手法の主張ではない。
- 調査: 5 本の並列調査(CASMI 2012–2022 史、MS/MS→構造の ML ベンチマーク、Kaggle 化学系コンペ、検索+再ランキング型コンペ、他プラットフォームと隣接逆問題)のうちベンチマーク調査が完了。全 119 ディスカッションスレッドを投稿者名付きで取得済み(`docs/official/discussion/`)、精査中。
- ローカル検証資産: `dmitriigluzdov/casmi26-natural-product-panel-benchmark`(250 天然物、3 シナリオのキャッシュ済み候補とスコア、replay スクリプト)と `casmi26-identity-disjoint-validation-folds` を `data/external/` に取得済み。`src/metric.py` は公式スコアラー複製、`data/processed/train_scorer_keys.parquet` は全学習 SMILES のスコアラー鍵。

## ベンチマーク調査の主要知見(research_notes/CASMI 2026 類似コンペ調査/ms_ml_benchmarks.md)

1. MassSpecGym の同一 256 候補検索で、順方向モデルによる再ランキング(ICEBERG 2.0 63.95%、GLACIER 69.95% hit@1、質量条件)が、指紋/埋め込み検索(MIST 14.6%、JESTR 15.1%)を 4〜5 倍上回る。ただし FOAM の報告では 95% の検索でデコイが真の分子を上回る瞬間があり、順方向スコアは単独の判定器ではなく学習ランカーの特徴として使うべき。
2. de novo(分子式既知)の正直な到達点は FRIGID のリーク修正後で top-1 約 9%、top-10 約 12%。分子式未知ならさらに低下。Class 3 を de novo で取る期待値は低く、今夜の優先度は下げる。
3. ライセンス: MassSpecGym 学習版 ICEBERG 重みは公開(ms-pred、2025-10-27)、FIORA-OS は MIT、DreaMS は MIT、FRIGID チェックポイントは許可(学習コード提示条件)。GLACIER 重みの公開は未確認。NIST 学習版 ICEBERG 2.0 は使用不可。
4. 評価: InChIKey 分割はランダム分割と同程度に漏れる。候補プール規模だけで hit@1 が 42%(256 候補)→3.6%(2.6 万候補)まで落ちる。timsTOF と Orbitrap/QTOF 間の転移を定量した論文は無い。

## 追加の調査知見(01:50 時点、casmi_history.md / other_platforms_adjacent_problems.md)

- CASMI 2016 で大きく効いた「文献数・データソース数の事前分布」は、2017 の天然物課題では逆効果だった。2026 は天然物中心で保持時間も無い。
- "MassSpecGym in the Wild"(arXiv 2606.19624、2026-06、Enveda の Healey が共著)は 26 論文中 17 以上にリークや近道を報告。正準化の不備で Hit@1 が 82%→7% に変わった例、分子式リークで約 30 倍、スペクトルを見ない PubChem 順だけで Hit@1 50% という近道を指摘。popularity prior は主催者側が「近道」と見ている可能性が高く、Class 3 では効かず、Class 2 でのみ正当な事前分布になる。
- CASMI 歴代でライブラリ無しの自動同定の top-1 は約 3 分の 1 で頭打ち(2016: 70/208、2017: 66/198、2022: 57/222)。残る誤りは同一分子式異性体。新規化合物の de novo 同定は歴代ほぼ 0%。
- パネル(250 分子)は 249/250 が COCONUT 収載の有名天然物で、文献 prior が強く効く偏り。パネルの main_candidates は ICEBERG/GLACIER 導入前の単一エンジン構成のキャッシュで、順方向モデルの効果は replay できない。

## 仮説

- H1(最有力): 公開パイプラインは順方向モデルを「同一分子式グループ内の上位 40 件の並べ替え」と「GLACIER は [M+H]+ のみ」に限定している。順方向スコアの適用範囲(候補深さ、アダクト、ICEBERG/GLACIER の併用)を広げ、ランカー特徴として統合すれば、誤答の 98% を占める同一分子式異性体の識別が改善する。制約は 9 時間の実行時間。
- H2: 公開系譜の順位操作ルール(第 2 エンジン首位の 2 位挿入、Δ>150 の PubChem 昇格、24 位 PubChem 追加、popularity prior の重み)は Public LB 約 130 分子に対する過適合の疑いが強い。パネル 3 シナリオの replay とブートストラップで根拠の無いものを外すと、Public では±0.01 程度の変動、Private では頑健性向上が見込める。
- H3: Class 2 のカバレッジは train+COCONUT+PubChem+PubChemLite+ChEBI でほぼ飽和しており、残る損失は順位付けにある(参加者報告「DB 経路の誤りの 98% は同一分子式異性体」)。
- H4: 自前の指紋モデル(identity fold で学習、timsTOF 重視)は検証可能性と入賞要件の両面で望ましいが、今夜中に Notebook へ統合するのは時間的に困難。学習だけ開始し、採否は検証結果で決める。

## 今夜の実験計画(優先順)

- E0: V18 再現の提出(基準値、実行時間の把握)。
- E1: パネル replay。`merge_eval.py` / `main_eval.py` / `prior_replay.json` を用い、(a) 現行ルール、(b) 順位操作ルールを外した版、(c) prior 重みを変えた版を 3 シナリオ(パネル自身のスペクトル除外、正解の全参照スペクトル除外、正解のプール除外)で比較。構造単位ブートストラップで 95% 区間を出す。
- E2: 順方向スコアの適用範囲拡張を Notebook 上で実装し(ICEBERG を全アダクト・上位 K 候補に拡大、GLACIER との併用)、パネルのキャッシュに順方向スコアがあれば replay で、無ければ小規模ローカル実行で効果を測る。
- E3: E1/E2 で区間が 0 をまたがない変更のみを V18 に適用した版を提出。
- 並行: 全 119 スレッドの精査、論文調査の統合レポート、自前指紋モデルの学習開始。

## 質問

1. H1〜H4 の優先順位と、E1→E3 の流れに同意しますか。特に「ルールを外す」変更は Public で下がる可能性もあり、Private 重視の判断として妥当か。
2. パネル 250 分子は fpnet_full1 の学習に含まれている疑いがあります(作者自身が Table 16 で指摘)。この条件でパネル replay の結論をどこまで信用できるか、どの指標(到達率、正解が候補にある場合の順位、top-1)を主に見るべきか。
3. 9 時間 Notebook を 2 本以上走らせると Kaggle の GPU 週間枠(30 時間と推定)を圧迫します。E0 と E3 の 2 本に絞る方針で問題ないか。他に省ける検証はあるか。
4. 0.480 に数時間で到達するために私が見落としている手段があれば指摘してください(例: 既存の公開 Notebook 間で未統合の部品、候補源、アダクト処理の既知バグなど)。

## 参照ファイル

- `research_notes/CASMI 2026 類似コンペ調査/ms_ml_benchmarks.md`
- `docs/competition_overview.md`、`docs/official/pages/*.md`、`docs/official/discussion/*.md`
- `reference/kernels/evgendvorkin_enveda-casmi-2026/enveda-casmi-2026.md`(提出基準の本文)
- `data/external/panel_benchmark/`(README.md、FILE_DESCRIPTIONS.json、*_eval.py)
- `kernels/baseline-v18/`(push 済み Notebook)
