# Enveda CASMI 2026 – Molecule ID From Mass Spectra: コンペ概要メモ

最終更新: 2026-10-24。公式ページ(Overview / Data / Rules など 11 ページ)とディスカッション全 119 スレッドは Kaggle 公式 API(competitions API の `list_competition_pages` / `list_competition_topics`、discussions API の `get_topic` / `list_comments`)で取得し、`docs/official/` に保存した。ディスカッションは投稿者名付きで保存し、運営側の発言にフラグを付けた: [HOST] = ピン留めスレッドの投稿者(David Healey = Enveda、Ashley Oldacre = Kaggle)、[Kaggle] = inversion(Kaggle 運営、告知とチュートリアル担当)、[Organizer] = Marie Killian(ルール・ライセンス質問に運営として回答。所属は投稿からは未確認)。取得スクリプト: `src/fetch_kaggle_info.py`(`--staff Name=Label` で追加のフラグ指定)。

- コンペ URL: https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra (competition id 143318)
- 公式メトリック実装: https://www.kaggle.com/code/metric/casmi-mean-reciprocal-rank (ローカル複製: `src/metric.py`)
- 公式チュートリアル(de novo Transformer): https://www.kaggle.com/code/inversion/casmi-denovo-tutorial-notebook
- 主催: Enveda Therapeutics, Inc.(Boulder, CO の創薬企業)。CASMI = Critical Assessment of Small Molecule Identification(2012 年創設、2022 年まで学術チームが運営、許諾を得て名称を復活)
- 種別: Featured / Code Competition。賞金総額 $50,000(1位 $16,000、2位 $12,000、3位 $9,000、4位 $7,000、5位 $6,000)
- 参加チーム数: 3,877(2026-10-24 時点)。Public LB トップ 0.504、上位 20 位ラインが約 0.47
- 公式ページの保存先: `docs/official/pages/`(data-description, Evaluation, rules, Timeline, Prizes, Code Requirements, Background, Description, abstract, Acknowledgements, foundational-rules)

## 1. 日程(すべて UTC 23:59)

| 日付 | 内容 |
|---|---|
| 2026-09-14 | 開始 |
| 2026-12-07 | エントリー締切(ルール承諾が必要)・チームマージ締切 |
| 2026-12-14 | 最終提出締切 |

## 2. タスク(公式 Data ページより)

LC-MS/MS(タンデム質量分析)のスペクトルから、低分子の **2D 構造(SMILES)** を予測する。

- 対象分子: 「植物・哺乳類・微生物由来の天然試料に見られるような分子」= 確認済み天然物、推定天然物、天然物アナログ、自然界に存在しうる合成分子
- 入力: 分子ごとに 1〜複数本の MS/MS スペクトル(フラグメント m/z と相対強度の配列)+ プリカーサ m/z、アダクト、極性、装置種、衝突エネルギー
- 出力: `molecule_id` ごとに **最大 25 個** の候補 SMILES を確信度順に `;` 区切りで並べる
- **予測単位は分子(molecule_id)** であり、スペクトル単位ではない。同一分子の複数スペクトル(異なる衝突エネルギー・アダクト)の証拠を 1 本のランキングに統合する

### 難易度クラス(公式)

| クラス | 定義 | 主な解法 |
|---|---|---|
| 1 — 公開スペクトルライブラリにあり | 参照 MS/MS スペクトルが公開されており、学習スペクトルとの類似度で見つかる | スペクトルライブラリ検索 |
| 2 — 構造は既知、スペクトルなし | 公開スペクトルはないが、PubChem または天然物 DB COCONUT に構造がある | 構造 DB からの候補取得 + 再ランキング |
| 3 — 新規構造 | PubChem に存在しない。de novo 予測が必要 | de novo 構造生成 |

「実際の複雑混合物を模すため、クラス分布とどの分子がどのクラスかはコンペ期間中は非公開」(公式)。コミュニティ推定はばらつきが大きく、クラス 1 が 10〜28%、クラス 2 が 20〜55%、クラス 3 が 30〜74%。ライブラリ検索のみの提出が Public LB 0.15 前後であることから、**クラス 2/3 をどれだけ取れるかが勝負**。

## 3. データ

`data/raw/` に展開済み(zip 3.03 GB、Kaggle 上のファイル作成日時 2026-09-15 14:33 UTC)。9/15 に「水損失アダクトを追加した小規模更新があるので再ダウンロードを」というホスト告知があり、手元のファイルはその日時以降の版。

| ファイル | サイズ | 内容 |
|---|---|---|
| train.parquet | 3.03 GB | 2,539,608 スペクトル × 18 列。275,810 ユニーク inchikey14、277,566 ユニーク SMILES、51,291 分子式 |
| test.parquet | 4.8 MB | 1,213 スペクトル / 400 分子 × 12 列(**ダミー**。再実行時に隠しテストへ差し替え、サイズはほぼ同じ) |
| sample_submission.csv | 44 KB | 400 行、`molecule_id,smiles` |

### 隠しテストセット(公式)

- 約 1,500 スペクトル / 約 400 分子、分子あたり 1〜16 スペクトル(中央値 3)、すべて Bruker timsTOF で測定
- 単一同位体質量 157〜1,159 Da(中央値 348)
- 最小限のクリーニングのみ: (a) 実測プリカーサ質量が構造+アダクトと矛盾するスペクトルを除外、(b) ベースピークが生カウント 1,000 未満のスペクトルをノイズとして除外、(c) プリカーサ + 2 Da を超えるピークを除去
- アダクトは 10 種: `[M+H]+`, `[M+NH4]+`, `[M-H2O+H]+`, `[M-2H2O+H]+`, `[M+Na]+`, `[M+K]+`, `[M-H]-`, `[M-H2O-H]-`, `[M+CH2O2-H]-`, `[M+Cl]-`(train にはもっと多い)
- Kaggle 運営(inversion)の回答: train と test、ダミー test と隠しテストの間で ID の重複はない(10/7)。隠しテストは 10/7 に「一部ピーク質量の電子質量分の誤差」を修正して差し替え、全提出が再採点された(運営告知)
- Public LB は隠しテストの一部(参加者推定で約 130 分子 ≒ 1/3)。1 分子で約 0.008 動くので 0.005 程度の差はノイズ

### 列定義(公式 + 実データ確認)

| 列 | 型 | 意味 | test |
|---|---|---|---|
| molecule_id / spectrum_id | str | 匿名の分子 ID / スペクトル ID(**train には存在しない**。公式 Data ページの「18 列」と整合。train は inchikey14 で分子をまとめる) | ✓ |
| ms2_mzs / ms2_normalized_intensities | list[f64] | フラグメント m/z と強度(ベースピーク = 1.0 に正規化、i 番目同士が対応) | ✓ |
| base_peak_intensity | f64 | 正規化前のベースピーク生強度(強いほどノイズが少ない傾向)。train では事前正規化済みライブラリで欠損(46%) | ✓ |
| adduct | str | プリカーサのアダクト(train は 121 種) | ✓ |
| ionization_mode | str | positive / negative | ✓ |
| instrument_type | str | test は常に `timsTOF`。train は出典ごとの自由記述(83 種、欠損あり)。`enveda-180` と `enveda-np-examples` のみ timsTOF | ✓ |
| precursor_mz | f64 | 実測プリカーサ m/z | ✓ |
| collision_energy_ev | list[f64] | eV 換算の衝突エネルギー。`[20]` は単発、`[20, 40, 60]` は複数エネルギーをマージしたスペクトル。**モデル入力にはこの列を使う**(公式推奨) | ✓ |
| collision_energy_orig / _units | str | 元の記録値と単位(eV / NCE / V / unknown)。NCE→eV は Thermo の公称式による近似 | ✓ |
| normalized_smiles | str | **正解ラベル**。RDKit 標準化済み SMILES | ✗ |
| inchikey / inchikey14 | str | InChIKey と先頭 14 文字(**スコアラーの鍵とは一致しないことがある**、§4) | ✗ |
| molecular_formula | str | 中性分子の分子式 | ✗ |
| ingest_lib | str | 出典ライブラリ(11 種) | ✗ |
| adduct_orig | str | 標準化前のアダクト表記 | ✗ |
| precursor_error_ppm | f64 | 実測プリカーサ m/z とラベル構造+アダクトから導かれる値の ppm 誤差。未クリーニングで **ラベル品質指標** を兼ねる | ✗ |
| num_peaks | i64 | ピーク数 | ✗ |

### 出典ライブラリ(公式説明 + 実データ統計)

| ingest_lib | スペクトル | 分子 | 装置 | ピーク数中央値 | 公式説明 |
|---|---:|---:|---|---:|---|
| enveda-180 | 1,153,785 | 182,941 | timsTOF | 138 | Enveda 公開データ。テストと同じ timsTOF で一貫した処理だが、化学は合成ドラッグライク化合物でテストとは別領域 |
| pluskal_ms2 | 527,581 | 46,821 | Orbitrap | 21 | Pluskal lab の MSnLib。商用スクリーニング化合物を複数 CE で一貫測定(単位 NCE) |
| riken | 347,171 | 15,892 | 多様 | 9 | RIKEN 公開ライブラリ。植物二次代謝物が中心。m/z 精度が小数 2 桁で ppm 誤差が見かけ上大きい |
| gnps | 220,849 | 45,750 | 多様 | 46 | GNPS コミュニティライブラリ。最大の天然物参照集だが最も不均質。CE 欠損 |
| massbank | 101,727 | 9,180 | 多様 | 11 | MassBank コンソーシアム(キュレーション済み) |
| mona | 92,416 | 11,681 | 多様 | 57 | MassBank of North America(Fiehn Lab) |
| spectraverse | 50,933 | 9,631 | 多様 | 47 | 公開ライブラリの調和集約(他にない小規模ライブラリを含む)。高質量側、CE ほぼ欠損 |
| msdial | 40,765 | 9,127 | 多様 | 11 | MS-DIAL 付属の公開コレクション |
| drug_plus | 2,545 | 2,539 | 不明 | 108 | 医薬品 LC-MS/MS DB。約 2,500 薬物、1 スペクトルずつ、CE 情報なし |
| enveda-np-examples | 1,184 | 250 | timsTOF | 141 | **テストに最も近いライブラリ**。テストと同じ装置・同じパイプラインで処理した 250 の一般的な天然物。他ライブラリにも存在するよう意図的に選ばれている |
| masaryk | 652 | 416 | Orbitrap | 9 | RECETOX(Masaryk 大学)の標準品ライブラリ |

その他の分布(実データ):

- 極性: positive 1,899,640 / negative 639,968
- 主要アダクト: [M+H]+ 1.32M、[M-H]- 466k、[2M+Na]+ 190k、[M+Na]+ 178k、[2M+H]+ 92k、[M+CH2O2-H]- 83k、[2M-H]- 56k、[M+NH4]+ 53k、[M+Cl]- 28k、[M-H2O+H]+ 22k、[M+K]+ 19k。**二量体アダクト(13%)はテストに存在しない**
- CE 単位: eV 1.37M / NCE 789k / unknown 325k / V 57k。CE リスト長 3 以上(マージ)が約 48 万行、CE 欠損 13%
- 分子あたりスペクトル数: 中央値 6、90% 点 14、最大 1,468。複数ライブラリに登場する分子 28,113(約 10%)
- precursor_error_ppm: 中央値 1.5 ppm、95% 点 17 ppm、99% 点 2,884 ppm、|ppm|>20 が 4.7%(riken の大半は精度起因で誤ラベルではない)
- 同一構造のバイト一致重複スペクトル 57,642 行(ライブラリ間コピー)。公式は「完全重複は除去済み、同一化合物の独立測定は残る」としているが、実データでは残っている

### ローカル test.parquet の正体

1,213 スペクトルは **すべて enveda-180 の行とビット一致**(当方でも全件一致を確認、400 分子それぞれが train の 1 構造に対応)。合成ドラッグライク化合物で precursor m/z 245〜460、7 アダクト、CE は 20/40/60 eV 単発(75%)または 20,40,60 マージ(25%)、負モードは "-40" のように符号付き。ローカル test での自己評価は無意味(MRR 1.0)。隠しテストに含まれる条件(1,159 Da、10 アダクト、16 スペクトル/分子、水損失アダクト)はローカルに無いので、提出前に模擬データで動作確認する。

## 4. 評価指標: MRR@25(公式)

```
MRR@25 = (1/U) Σ_u 1/rank_u   (rank_u = 分子 u のリストで最初に正解した候補の順位。25 位以内に正解がなければ 0)
```

- 1 位 = 1.0、2 位 = 0.5、25 位 = 0.04。各分子に正解は 1 つなので最初の正解だけが数えられる
- 正解判定(公式コード): `MolFromSmiles` → **`RemoveStereochemistry`(10/7 に追加、遡及適用)** → `rdMolStandardize.TautomerEnumerator().Canonicalize`(**RDKit 2026.03.3 固定**) → `MolToInchiKey()[:14]` を比較。提出側と正解側に同じ関数を適用
- 立体中心・互変異性体の違いは不問。例: グルコースの立体あり/なし SMILES はどちらも `WQZGKKKJIJFFOK` で一致
- 重元素組成が異なる候補は即不一致(高速ゲート)。パースできない SMILES は不一致扱い
- 提出ファイルの拒否条件: `molecule_id` / `smiles` 列欠落、空ファイル、どちらかの列に null、molecule_id の重複、26 個以上の候補。25 個未満は可、外れ候補のペナルティは順位を消費することのみ
- **train の `inchikey14` 列はスコアラーの鍵と一致しない**(tautomer 正準化前)。全学習 SMILES 277,566 件で再計算すると 4,467 件(1.61%)で鍵が変わり、1,541 の鍵に複数の inchikey14 が併合される。候補の重複排除・正解照合・検証分割はすべて **スコアラー鍵(`src/metric.canonicalize_smiles_to_ik14`)で行う**。事前計算結果: `data/processed/train_scorer_keys.parquet`

## 5. ルール(公式 Rules + ホスト回答)

| 項目 | 内容 |
|---|---|
| 提出形式 | Kaggle Notebook のみ。CPU / GPU とも実行時間 **9 時間以内**、**インターネット無効**、出力は `submission.csv` |
| 提出回数 | 1 日 5 回。最終評価用に 2 件まで選択 |
| チーム | 最大 5 人。マージは 12/7 まで、合計提出数が上限以内であること |
| データライセンス | CC BY-NC 4.0(非商用・学術利用)。ホスト: train.parquet は公開ライブラリの集約なので実質オープンソース扱い、NC 条項はテストデータを想定したもの |
| 外部データ | 公開・無償・全参加者が平等にアクセスできるものは可(事前学習モデル含む)。**10/17 ホスト告知: CC BY-NC など非商用条項付きのオープンデータも可**。非公開・有償・プロプライエタリは不可。**NIST ライブラリおよびその派生(学習済み重み含む)は禁止、使用した解は失格** |
| 入賞者の義務 | 解法コード(学習・推論・環境説明)を **MIT 等 OSI 承認ライセンス** で公開、再現可能な詳細説明を提出。ライセンス非互換な入力データ・事前学習モデル自体の公開義務は免除(Rules 2.5.a.3) |
| コード共有 | チーム外との私的共有は禁止。公開共有は Kaggle フォーラム/Notebook 上のみ(OSI ライセンス扱い) |
| その他 | 1 人 1 アカウント。テスト/検証データの手作業ラベル付けは禁止。学習データを私有クラウドで処理することは可(ホスト回答) |

ホストが利用可と明言したもの(ディスカッション 748270 の集約表): train.parquet とそれで学習したモデル・派生データセット、MassSpecGym とその学習モデル、GLACIER / ICEBERG(MassSpecGym 版重み)、DreaMS 重み、ChEBI / LIPID MAPS、CFM-ID 4、GNPS / MassBank / MoNA の新版、GNPS-NIST14-MATCHES、Enveda-180 の Zenodo 版、PubChem(サブセット提出可)、COCONUT。FRIGID の公式チェックポイント(CC BY-NC)も可だが、元の学習コードと許可データへのアクセスを提示して再現可能にすること。

## 6. 公開ソリューションの到達点(2026-10-24 時点)

LB 上位(0.46〜0.50)はほぼすべて **候補取得 → 多証拠スコアリング → 学習ランカー → 融合** パイプラインの派生。

| 構成要素 | 内容 |
|---|---|
| 候補プール | 学習構造 275k + COCONUT 2.0(約 46 万)= 約 71 万構造。中性質量 ±10 ppm 窓(空なら 30 ppm)。アダクト式でプリカーサ m/z → 中性質量(分子内の複数スペクトルの中央値) |
| 追加候補源 | PubChem 全体(約 1.06 億構造、質量ソート済み)、ChEBI + LIPID MAPS(約 10 万)、PubChemLite(約 39 万) |
| ライブラリ検索 | スペクトルエントロピー類似度(Li et al. 2021)/ 修正コサイン。同極性・同アダクトで train 2.54M と照合 |
| アナログ伝播 | 質量シフト ±200 Da のアナログ検索 → Tanimoto で候補へ伝播(クラス 2 用) |
| 指紋予測(FPNet) | 最大 16 スペクトル + メタデータ → 数千ビット部分構造指紋。`fpnet_full1`、fold-safe 版、A+B 版などが公開 |
| 順方向モデル | ICEBERG / GLACIER(Coley lab ms-pred、MassSpecGym 学習版)で候補からスペクトルを予測し実測と比較。同一分子式内の並べ替えに使用。GLACIER は [M+H]+ のみ |
| MetFrag-lite | 1〜2 結合切断でフラグメント列挙、説明強度割合をスコア化(順方向モデルが使えない場合の代替) |
| 事前分布 | PubChem popularity prior(substance 記録数・PubMed 文献数の対数)、天然物 DB 所属、LOTUS 文献数 |
| ランカー | LightGBM / HistGradientBoosting の複数シード・複数クラス重み平均、LambdaRank |
| 融合 | 複数エンジンを Reciprocal Rank Fusion、スコアラー鍵で重複排除、空き枠は質量適合候補で埋める |

公開最高は約 0.464。Public LB トップ 0.504 との差は小さいが、ディスカッション「公開ノートブックの 0.43+ は一度も CV で検証されていない」(748068)が指摘するとおり、公開系譜の改善は約 130 分子の Public LB だけで採否が決まっており、Private で剥落するリスクがある。de novo 生成単体(公式チュートリアル Transformer)は 0.1〜0.28 程度。クラス 3 の改善は「ローカルでは改善するが LB に反映されない」という報告が複数(751300)。

主要な公開データセット: `prvsiyan/coconut-casmi26-candidates`, `ahmedberatozer/casmi26-v4b-models`, `ahmedberatozer/casmi26-fpnet-full1`, `ahmedberatozer/casmi26-iceberg`, `ahmedberatozer/casmi26-glacier`, `ahmedberatozer/casmi26-pubchem-tier`, `dmitriigluzdov/casmi26-pubchem-popularity-prior`, `dmitriigluzdov/casmi26-fold-safe-fpnet`, `dmitriigluzdov/casmi26-identity-disjoint-validation-folds`, `dmitriigluzdov/casmi26-natural-product-panel-benchmark`, `sergiomalv/casmi-chebi-lmsd-structures`, `franciscoangulo/casmi26-pubchemlite-cc0-candidate-fingerprints`, `hengck23/hengck23-dreams-enveda-casmi26`, `metric/rdkit-2026-3-3-wheel`。

公式 Data ページが挙げる外部リソース: MIST-CF / SIRIUS(分子式推定)、matchms(スペクトル処理)、MassIVE(ラベルなし生データ、自己教師あり事前学習向け)、GeMS / DreaMS(大規模ラベルなしコーパスと事前学習埋め込み)、FragHub(公開ライブラリの調和集約)。

## 7. 検証設計と落とし穴(公式 + ディスカッションの知見)

1. ローカル test.parquet は train の部分集合。評価には使えない(動作確認・時間計測のみ)
2. ランダムなスペクトル分割では 97.7% の検証分子が train 側にもスペクトルを持つ。**スコアラー鍵で分子単位に分割**し、必要なら Bemis–Murcko 骨格単位でも分割する
3. `enveda-np-examples`(250 分子)は全 250 分子が他ライブラリに 55,599 スペクトル存在する。構造単位で除外し、除外後に完全一致検索が 0 件であることをアサートする
4. クラス別シナリオで検証する: クラス 1 相当(他ライブラリにスペクトルあり)、クラス 2 相当(自分のスペクトルを全て除く)、クラス 3 相当(候補プールからも除く、または Tanimoto ≥ 0.7 の類似構造も除く)。ライブラリ検索のみで c1 ≈ 0.92、c2 ≈ 0.01、c3 = 0。ある参加者の構成例: ホールドアウト 1,250 構造(np-examples 250 + COCONUT 内の天然物 600 + COCONUT 外 400)、テストのスペクトル数分布・10 アダクトに合わせて 5 回サンプリング、ブートストラップで差の有意性を確認、再学習を伴う変更は複数シード平均で比較
5. DB 経路の誤りは 98% が「同一分子式の異性体」。質量窓の幅(8.5 vs 10 ppm)はほぼ無関係で、**構造異性体の識別**が本質。同一分子式の異性体パネルが感度の高い開発指標になる
6. 「新規分子」シミュレーション(正解を DB から削除して回復できるか)は実際の未登録分子に対して約 3 倍楽観的。真に DB に無い分子で検証する
7. キュレーション天然物 DB(ChEBI、LIPID MAPS、NPAtlas)は PubChem ∪ COCONUT 以上のカバレッジを与えず、所属フラグは公開ホールドアウトでは効くが LB では悪化した例あり
8. `precursor_error_ppm` の一律 10 ppm フィルタは riken(テストに近い化学)を半分失い性能が落ちる。桁違いの異常値のみ除外するかライブラリ別に扱う
9. 装置差: timsTOF のピーク数中央値 ~140〜230 だが、その 82% は相対強度 1% 未満。1% 床を適用すると train(14)と test(18)は同程度。前処理を揃え、ピーク数に左右されない類似度を使う
10. 正モード m/z に約 +0.5 mDa の系統誤差(enveda-180 のキャリブレーションが Na 原子質量を使用、電子質量分)。許容 0.01 Da 以上なら影響なし。隠しテストは 10/7 に修正済み
11. CE 単位は eV / NCE / V 混在。`collision_energy_ev` は近似換算。負モードの元表記はマイナス符号付き
12. アダクト式を正確に(例: [2M+Na]+ は Na を引いて 2 で割る)。隠しテストの 10 アダクトのうち `[M-H2O+H]+`, `[M-2H2O+H]+`, `[M-H2O-H]-` はローカル test に無い
13. 1 分子でも候補が空だと提出エラー。必ずフォールバック候補を入れる。公開パイプラインの GPU 段は再現性がなく同一コードで 0.437〜0.440 と揺れる

## 8. ローカル環境

| 項目 | 内容 |
|---|---|
| マシン | Windows 11、RTX 5070 Ti 16 GB(sm_120)、RAM 61.6 GB、ディスク空き 1.4 TB、16 論理コア |
| Python | uv 管理の 3.11.16 仮想環境 `.venv`(Windows 側の `python` コマンドは Store エイリアスで動かないため `.venv\Scripts\python.exe` を使う) |
| 主要パッケージ | rdkit 2026.03.3(スコアラーと同一)、torch 2.11.0+cu128(CUDA 動作確認済)、polars 2.0、pandas、pyarrow、lightgbm 4.7、numba、scikit-learn、matchms、pyteomics、jupyterlab。全リスト: `requirements-lock.txt` |
| Kaggle CLI | 2.2.5(`.venv\Scripts\kaggle.exe`、`~/.kaggle/credentials.json` で認証済み) |
| 文字コード | Windows コンソールが cp932 のため `python -X utf8` で実行する(`-I` を付けると環境変数 PYTHONUTF8 は無視される) |

### ディレクトリ構成

```
C:\kaggle\CASMI
├── .venv/                     Python 3.11 仮想環境
├── data/
│   ├── raw/                   train.parquet / test.parquet / sample_submission.csv(+ zip)
│   ├── processed/             train_meta.parquet(ピーク配列を除いた 2.54M 行, 88 MB)
│   │                          train_molecules.parquet(275,810 分子の集約)
│   │                          test_meta.parquet, train_scorer_keys.parquet(277,566 SMILES のスコアラー鍵)
│   └── external/              COCONUT 等の外部データ置き場
├── src/
│   ├── metric.py              公式 MRR@25 スコアラーのローカル複製 + 鍵正規化関数
│   ├── make_meta.py           メタデータ parquet 作成
│   ├── compute_scorer_keys.py 全学習 SMILES のスコアラー鍵を並列計算
│   └── fetch_kaggle_info.py   公式ページ・メタデータ・ディスカッションを Kaggle API で取得
├── docs/
│   ├── competition_overview.md  このメモ
│   └── official/              competition_meta.json, pages/*.md(公式 11 ページ), discussion_topics.json, discussion/*.md
├── reference/kernels/         公開ノートブック 11 本(ipynb + 変換済み .md)
├── notebooks/ models/ submissions/
└── requirements-lock.txt
```

### よく使うコマンド

```powershell
# スクリプト実行(リポジトリルートで)
.venv\Scripts\python.exe -I -X utf8 src\make_meta.py data\raw data\processed
.venv\Scripts\python.exe -I -X utf8 src\metric.py                       # メトリックの自己テスト
.venv\Scripts\python.exe -I -X utf8 src\fetch_kaggle_info.py enveda-CASMI26-molecule-id-mass-spectra docs\official --top 10
# Kaggle 操作
.venv\Scripts\kaggle.exe competitions leaderboard enveda-CASMI26-molecule-id-mass-spectra -s
.venv\Scripts\kaggle.exe kernels pull <user>/<slug> -p reference\kernels\<dir> -m
```

## 9. 次のステップ案

1. **検証基盤**: スコアラー鍵による分子単位分割、クラス 1/2/3 を模した 3 シナリオ評価、`enveda-np-examples` 250 分子パネル、ブートストラップによる差の有意性判定
2. **ベースライン再現**: ライブラリ検索(エントロピー類似度)+ 中性質量窓候補(train + COCONUT)で c1 を確保しつつ、公開パイプライン(FPNet + ランカー + RRF)をローカルで動かして LB 0.46 付近を再現。ただし公開系譜は CV 未検証なので、各構成要素を自前の検証で採否判断する
3. **独自改善の候補**: timsTOF 特化の指紋予測モデルの自前学習(enveda-180 で事前学習 → 天然物ライブラリで微調整)、DreaMS / MIST 系埋め込み、同一分子式異性体の識別に特化したランカー、順方向モデルの適用範囲拡大、クラス 3 向けの制約付き生成(分子式制約 + アナログ編集、FRIGID 等)
4. **提出運用**: 9 時間・オフライン制約下で動く Notebook を早期に 1 本作り、隠しテスト条件(1,159 Da、10 アダクト、16 スペクトル/分子)を模したスモークテストを通す。最終提出 2 件の選び方(Public LB 依存を避ける)を事前に決める
