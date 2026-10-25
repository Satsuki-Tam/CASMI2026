# 022 レビュー: M2x＋full_evalの比較提出条件

2026-10-25。**pool60を不採用とし、そのための追加parityを止める判断に賛成する。full_evalは、性能の未確定と実装・データ監査の未完了を分けて判断する。区間が広いだけなら条件付きで一回の比較提出は可能だが、FP値だけの確認を最終出力の一致確認の代わりにはしない。**

確認時点で`fe_eval_panel/p2dev/devAB`の最終評価表は未生成だった。以下は結果を見る前の判定基準であり、今回のモデルが合格済みという回答ではない。

**Q1 — パネルの主比較とdev2の保護**

パネルの固定群はCSVで202/48を確認した。ただし実際の定義は、各分子のqueryについて、残存学習スペクトルとの最大類似度が **0.90未満／0.90以上**。報告では `clean = 高類似の残存例を検出していない群`、`uncertain = 高類似の残存例がある群` と注記する。前者も取得の独立性を証明した群ではなく、後者も重複確定群ではない。

追加監査は265 key全体を検索し、残存類似度≥0.95は0、≥0.90は67 query・48分子だった。019bで指摘した別キーも監査対象に広がっている点は確認した。性能を見る前に固定した区分を維持し、あとから高得点・低得点の分子を移さない。固定CSVのSHA256は `961ceb943773f52b494a9d373fc8f8e3bdd3640cd7febabc2e7c95fcc0f963b3`。

主比較は**パネルC1のclean 202分子の、登録主出力のpaired ΔMRR**とする。uncertain 48と全250も併記し、cleanとuncertainを合わせた平均だけで判断しない。候補不在は0として固定分母に残す。cleanの区間が0を含む場合は、点推定が正でも「利得は未確定」と付記する。類似度による区分自体が参照の難しさと相関するので、両群の差をそのまま記憶の因果効果にしない。

dev2はC/D/E/F/GのC2、C/E/F/GのC1をそれぞれ保護する。D/C1はN=0のNA。学習に含めたW7は診断用で、保護の代用にしない。パネルC2もFPNetのidentity学習済みなので、未見C2保護には使わない。dev2はFPNet学習中の監視集合でもあり、未使用の最終テストではないが、開発判断には使える。locked2は開けない。

| 結果 | 今夜の扱い |
|---|---|
| clean C1の点推定が正、dev2の全保護層で点推定・95%区間下限とも≥−0.02 | 実装・監査条件も満たせば、予定した比較提出を進めてよい |
| clean C1の点推定が正、全保護層の点推定は≥−0.02だが、一部の区間下限が−0.02未満 | **非劣性未確定の一回の比較提出として可**。どの層が未確定かを提出前に固定記録し、0.354の本命は保持する |
| 保護層の点推定が−0.02未満、またはclean C1の利得が無くuncertainだけで改善 | 現在の目的・基準では見送り。改善層の大きさで相殺しない |
| 参照・学習除外、checkpoint、候補生成、出力に未解決の不一致 | 比較提出も保留。統計区間の広さとは別の問題 |

二番目の扱いはεを緩めた合格ではない。Publicが+0.02以上でも、未確認のローカル保護をPublicだけで合格に変えない。020どおり、**基準0.354（57610156）、一変更のみ、±0.02は運用閾値**を維持する。今回の区間は開発・探索上の区間で、多数の層を同時に見た結果を一つの確証的検定とは呼ばない。

**Q2 — 最低限は「正しいモデルを使い、同じ入力から同じ候補・分岐・順序付き出力を得る」こと**

W7の50分子だけだとGL不足等を十分含まない。時間が厳しければ、単にFPだけへ検査を弱めるのではなく、**10〜20分子程度の分岐を押さえた集合に縮小し、最終出力まで比較する**。既存W7の共通処理の検証は再利用でき、600分子の全面再実行は不要。

最低限の組合せは、GL被覆十分な正イオン、E/F等のGL不足、C1の参照優先が発火する例、C2の参照無し・弱一致、複数adduct/CE、大きい候補窓、可能なら候補ゼロ。C1/C2両viewを含め、真が候補にある例だけを選ばない。機械的一致の確認用なので、これを性能評価の標本数とは数えない。

確認項目は次のとおり。

1. **入力と設定**: queryの選択行・前処理条件、公式identity、bit順序、実際に読み込んだcheckpoint SHAが一致。`rank_v4b`、blend21、k=100/k_fpp=200/k_pop=50、ICE重み0、τ0.9・margin0.2・GL被覆閾値0.5を固定する。今回の`k_pool`と`pcl_boost`は0で、変更はFPNetだけにする。
2. **FPと候補生成**: 同じqueryからのFP値・有限性、窓とshortlistのidentity集合、代表SMILES、prior/参照特徴が両経路で対応する。FPの数値差を許容するなら差と順位への影響を記録する。モデルhashの一致だけ、候補数の一致だけでは不足する。
3. **分岐と最終出力**: 同じforward cacheを使い、GL被覆・fallback・参照優先の判定、主出力と保険のtop-1、RR、**順序付きtop25の公式identity列**が一致する。候補ゼロも同じ規定出力にする。独立GPU計算の微差で一致しない場合は、FPを含めた同一保存スコアで順位付け処理を切り分け、論理の不一致を残さない。
4. **実際のKaggle実行**: 意図したdataset version・checkpointを読み、誤って旧fold0へ戻っていないことをログとmanifestで確認する。新候補に必要なGL採点の完了・想定外の欠損・例外fallback・実時間を確認し、有効な`submission.csv`を生成する。ダミー実行の統計を隠し実行の被覆率とは呼ばない。

`b1_parity.py`は必要な引数が無ければ「output agreement not run」のまま特徴比較だけを行える。**PASSという文字だけでなく、モデル・予測ファイル・stage statsを渡し、出力比較が実行されたNと一致数を確認する。** 共有スコアでの機械的確認は順序付きtop25を全対象で一致させる。時間不足を理由にFP確認だけで提出へ進める案には賛成しない。

full_evalは候補集合も変えるため、保険・GL不足群の出力も変わり得る。旧GLを部分的に流用して不足分をfallbackにした比較と、モデル自体の改善を混ぜない。`--reuse_complete`の各結果と登録評価の完了を確認し、チェーン末尾のDONEだけで全段成功とは判定しない。

**Q3 — private datasetでの保存は妥当。READMEには補う点がある**

自前学習した成果物を自分のprivate入力datasetに置く方針に異論はない。元の許可データ・コード・ライセンス・再現性の条件はそのまま適用される。公開外部データを使う規定と、自分の学習成果をprivateに保存することを混同しない。共有先は自分／同一チームに限定し、datasetとkernelの実際の可視性を作成後に確認する。`dataset-metadata.json`の`licenses: other`はprivate指定ではない。[公式Rules](https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/rules)

配布用の重みを読み取り検証し、SHA256は記載値と一致した。

`5b8d1c311d1171089374379c10cb82fdcc36457a7ab02ec0dddc6f12059b616d`

学習進捗も82,855更新、skip 0、complete=true、13,835.93秒を確認した。ただし、現在の8ファイルとREADMEだけでは再現版の指定が十分ではない。公開リンクに加え、以下を保存・参照可能にする。

- **実際に使ったコード版**: `prep_full_eval.py`、生成済みWindows trainer、生成スクリプト、`casmi`のモデル・前処理・Data/negative sampler、監査コード。固定commitまたはファイルhash付きsnapshotと実行コマンド・全有効設定・環境情報。現在のリポジトリ先頭へのリンクだけで済ませない。学習コードへのアクセスが必要という主催者回答は、自前の派生コードと実行版の保存でも満たす必要がある。[主催者回答750612](https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/750612)
- **入力・splitの再現情報**: train、fold表、pool、bit indexの完全なhashと版、除外したrow/groupを再現できる固定リストまたは対応する入力bundle、`split.parquet`のhash。`launch.json`は一部引数だけなので、batch/lr/seed/architecture/holdout等を含む全設定を残す。
- **実測の除外監査**: 同梱`check_inputs.json`の`holdout_training_overlap=0`は準備コードの直書きに由来する。full_evalの実際の`Data.tr`／サンプラとhold・lockの交差ゼロを計算した証跡を追加する。full_rk用のGO検査だけでは代用できない。パネルの202/48固定CSVとhashも、summaryとともに残す。
- **データ説明の精密化**: READMEの「train.parquet only」はMS/MS教師対については正しいが、`Data.negatives()`はv2 pool全体から負例を選ぶ。構造候補・fingerprintにはtrain構造＋COCONUTが関与するので、v2 poolとCOCONUTの出典・条件も記載する。今回の改変部分、原trainer、モデル実装、bit定義それぞれの帰属とLICENSE/NOTICEを保存する。
- **配布と提出の対応**: dataset slug/version、配布ファイルのhash一覧、kernelの版・引数・実際のckpt hash、最終提出IDを一つのrun manifestで結ぶ。推論用ファイルと、詳細な再現用bundleを分けて保存してもよいが、再現に必要な資料はhashだけでなく実体にアクセスできること。

これらの記録のために、今すぐモデルや自分のコードを一般公開する必要があるとは確認していない。privateであっても、所定の再現コード・資料の提供義務は残る。提出NotebookはInternet無効、9時間以内等の既存条件を満たす。[公式Code Requirements](https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/overview/code-requirements)

確認資料: `022_request.md`、021判断、full_evalのprogress・配布checkpoint/README/metadata、パネル重複監査コード・summary・固定群CSV、評価チェーン、pipeline/parityコード、`casmi/traindata.py`、公式APIで再確認したrules/foundational-rules/Code Requirementsと主催者回答。レビューと読み取り検証のみを行い、dataset作成・kernel起動・提出、学習プロセスへの変更は行っていない。

REVIEW_COMPLETE: 022
