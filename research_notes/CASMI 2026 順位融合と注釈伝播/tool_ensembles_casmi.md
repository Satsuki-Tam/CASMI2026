# 独立 in-silico 同定ツールの組み合わせ（consensus / ensemble ranking）— CASMI 2016/2017/2022 と後続研究の定量ファクトベース（天然物重視）

凡例（全セクション共通）:
- 【ツール間】= 異なるツール・モデル系統の出力（スコア/順位）を結合したもの（誤りの独立性が期待できる）。【モデル内】= 1 つのツール内部で複数の証拠・特徴量・サブモデルを統合したもの（例: COSMIC, MS2Query, ESP）。【事前情報】= 参照数・DB 収載・ライブラリ一致・RT・分類学など MS/MS 断片化以外の情報との結合。
- 「oracle」= 各チャレンジで最も良い順位を出したツールを後知恵で選んだ場合の上限値（実際に到達できる融合性能ではない）。
- 「再計算」と書いた数値は、CASMI 公式サイトが公開している per-challenge 順位 CSV を本調査で集計したもの（論文の数値ではない）。各ツール単体の Top1/Top10 が論文・公式表と一致することを確認した上で、oracle・MRR@25・順位相関を算出した。MRR@25 は順位 >25 または正解欠落を 0 とし、同順位は CASMI 公式の平均順位（average rank）をそのまま使用した。

## 1. CASMI 2016 / 2017 / 2022 と事後解析: ツール結合の実測ゲインと結合ルール

### Takeaway
CASMI 2016 では 6 つの in-silico フラグメンタを等重みで結合した事後エントリ「Combined MS/MS」が全単体を上回った（208 問で Top1 82 vs 最良単体 70、Top10 166 vs 123）が、Top1 の伸びは oracle 上限（Top1 120）までの伸びしろの約 1/4 にとどまり、主な改善は Top10・平均順位側だった。訓練データで重みを決めた投票モデル（Blaženović 2017）は訓練セットで Top1 +33%（52→69）だったのに、チャレンジセットでは最良単体（MetFrag 53）を Top1 で超えられず（51）、Top10 のみ +18 件だった。参照数・ライブラリ一致などの強い事前情報が入ると、フラグメンタを足す上積みは 208 問中 +1〜2 件程度に縮む。

### Cited Findings

#### CASMI 2016: 設計と評価ルール
- 【設計】Category 2「In Silico Fragmentation Only」（ライブラリ検索・追加情報は禁止）と Category 3「Full Information」（RT、ライブラリ、特許、参照数など可）。同じ 208 チャレンジ（188 物質、positive 127 [M+H]+ / negative 81 [M−H]−）、訓練 312 スペクトル。Q Exactive Plus、stepped HCD 20/35/50。候補は ChemSpider から ±5 ppm で取得して参加者に配布 — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- 【分割】MassBank スペクトルとの類似度 >0.85 のものは訓練側に回し、チャレンジは「MassBank に近いスペクトルが無い」ものに限定（NP を Category 1 に残すための例外 2 件あり）— [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- 【評価】同点は平均順位で評価（以前の「最悪順位」から変更。ランダム微小値で同点を崩す抜け道への対策）。立体異性体は InChIKey 第 1 ブロックで統合し最高スコアのみ残す。各チャレンジで最良順位の参加者に gold — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)

#### CASMI 2016: 単体 vs 結合（Category 2, 208 問）
- 公式結果: CSI:IOKR_A（Team Brouard）が 86 勝（41%）で優勝、CSI:FID（Team Dührkop）82 勝（39%）、MS-FINDER（Team Vaniya）70 勝（34%）。Top1 は CSI:FID 70（34%; positive のみ提出）、CSI:IOKR_A 62、MS-FINDER 46。全手法が Top10 ≥49%、CFM_orig は Top10 123（59%）で最多 — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- 全エントリと結合エントリの比較（Table 3 と Table 5 から転記、* は事後/内部エントリ）— [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)

| エントリ（系統） | Top1 | Top3 | Top10 | 平均順位 | 中央順位 |
|---|---|---|---|---|---|
| CFM_orig（ML 生成モデル） | 39 | 77 | 123 | 47.98 | 6 |
| CFM_retrain | 40 | 73 | 116 | 44.53 | 7 |
| CSI:IOKR_A（指紋/カーネル回帰） | 62 | 93 | 118 | 127.3 | 5.25 |
| CSI:IOKR_AR*（学習データ追加） | 78 | 102 | 131 | 95.09 | 4 |
| CSI:FID（指紋予測; positive のみ） | 70 | 90 | 100 | 25.17 | 1 |
| CSI:FID_leaveout* | 36 | 70 | 88 | 52.02 | 3 |
| MetFrag*（組合せ的断片化） | 24 | 60 | 108 | 51.92 | 8.75 |
| MAGMa+（組合せ的断片化） | 24 | 59 | 105 | 70.79 | 9.8 |
| MS-FINDER（ルールベース） | 46 | 79 | 101 | 19.75 | 3 |
| MetFrag+CFM*（2 ツール加重和） | 41 | 84 | 127 | 33.97 | 6 |
| Combined MS/MS*（6 ツール等重み） | 82 | 126 | 166 | 13.4 | 2 |

- 【ツール間】Combined MS/MS の構成: CFM_orig、CSI:FID、CSI:IOKR_A、MAGMa+、MetFrag、MS-FINDER の 6 エントリを等重み（equal weighting）で結合。"The Combined MS/MS entry outperformed all of the individual Category 2 entries, showing the complementarity of the different approaches." ライブラリ検索エントリ（MoNA, Top1 70）も上回った — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- 著者自身が重み付けは単純だったと認めている: 結合は個々より良く "supporting the potential use of consensus fragmentation results ... using a more sophisticated weighting than that attempted here" — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- 【ツール間・結合ルール】MetFrag+CFM: MetFrag の候補リストを CFM-ID v2 に入力して追加スコアを得て加重和。重みは訓練データで 100 組をランダム抽出し訓練 Top1 最多の組を採用（w_MetFrag = 0.5793923, w_CFM-ID = 0.4206077）— [Schymanski 2017 SI](https://static-content.springer.com/esm/art%3A10.1186%2Fs13321-017-0207-1/MediaObjects/13321_2017_207_MOESM1_ESM.pdf)
- MetFrag+CFM の効果: 全体 Top1 は 41（MetFrag 24, CFM 39）で「CFM 単体比ではわずかな改善」だが、negative mode の Top1 は 9（MetFrag）・12（CFM）→ 20 に増加 — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- 再計算（CASMI 2016 公式 per-challenge CSV, 208 問）: 構成 6 ツールの MRR@25 は CSI:FID 0.395 / CSI:IOKR_A 0.392 / MS-FINDER 0.323 / CFM_orig 0.314 / MetFrag 0.251 / MAGMa+ 0.246。6 ツールの oracle は Top1 120 / Top10 192 / MRR@25 0.710。実際の等重み結合（Top1 82, Top10 166）は、最良単体から oracle までの伸びしろ（Top1: 70→120、Top10: 123→192）のうち Top1 で約 24%（+12）、Top10 で約 62%（+43）を回収した計算になる — [CASMI 2016 extra-category2.csv](http://casmi-contest.org/2016/extra-category2.csv)（結合値は [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1) Table 5）
- 再計算: MetFrag+CFM（加重和）の MRR@25 は 0.335（CFM_orig 0.314, MetFrag 0.251, 2 ツール oracle 0.384）→ 伸びしろの約 30%。Top1 41 vs oracle 46、Top10 127 vs oracle 144 — [CASMI 2016 extra-category2.csv](http://casmi-contest.org/2016/extra-category2.csv)
- 再計算: 2 ツール oracle の MRR@25（単体 CSI:IOKR_A 0.392）: 異系統ペアは IOKR_A+MS-FINDER 0.548、IOKR_A+CFM_orig 0.536、IOKR_A+MetFrag 0.517、CSI:FID+CFM_orig 0.547、CSI:FID+MS-FINDER 0.546。同系統ペアは CSI:FID+IOKR_A 0.499、MAGMa+ + MetFrag 0.296（単体 0.246/0.251）— [CASMI 2016 extra-category2.csv](http://casmi-contest.org/2016/extra-category2.csv)

#### CASMI 2016: 学習データと重ならない問題での結合
- 3 チームの訓練セットと重ならない 87 問（positive 44 / negative 43）で再評価すると、Top1 の最大シェアは 34% → 18% に低下。Top1: CSI:IOKR_AR 16、CFM_retrain 15、CSI:IOKR_A 15、CSI:FID_leaveout 13、MetFrag+CFM 13、CSI:IOKR_U 11、CFM_orig 10、MS-FINDER 10、CSI:FID 9、MAGMa+ 6、MetFrag 5、MAGMa 5。Top10 は MetFrag+CFM 47 が最多（CFM_orig 46、IOKR_AR 46、IOKR_A 45）。平均順位は MS-FINDER 28.7 が最良、MetFrag+CFM 37.16 が次点 — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- Team Dührkop の申告: 67 問で最上位候補が自チームの訓練セット中の化合物だった。"If we evaluate our method on spectra from compounds we have already trained on we usually reach a performance comparable to spectral library search." 訓練化合物を除いて再学習した CSI:FID_leaveout は positive の Top1 が 70 → 36 — [CASMI 2016 追加結果ページ](http://casmi-contest.org/2016/results-extra-cat2.shtml); [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)

#### CASMI 2016: メタデータとの結合（Category 3）
- 【事前情報】公式: Team Kind の MS-FINDER+MD（MS-FINDER + NIST MS Search による NIST/MoNA/ReSpect/MassBank 照合 + 構造 DB 照合）が 159 勝・Top1 146 で優勝。Team Allen（CFM-ID + DB スコア）は 156 勝・Top1 120 — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- 事後エントリ（Top1/Top10）: MetFrag+RT+Refs 162/191、MetFrag+CFM+RT+Refs 163/199（平均順位 5.39）、MetFrag+CFM+RT+Refs+MoNA 155/194。MoNA の悪化は、訓練/チャレンジ分割にスペクトル類似度を使ったため MoNA の重みがチャレンジに対して楽観的すぎたことによる — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- 単一メタデータの威力（Table 5）: Refs（ChemSpider 参照数）単独で Top1 143 / Top10 196 / 中央順位 1、Lowest CSID 113 / 177、MoNA（ライブラリ類似）70 / 104、RT 予測 1 / 20。Combined MS/MS（82 / 166）は参照数単独より Top1 で 61 件少ない。Combined MS/MS+RT+Refs は 164 / 194、+MoNA で 164 / 195。"The references outperformed all individual metadata categories and even the combined fragmenters clearly." — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- メタデータ込みで重みを最適化すると CFM-ID の重みは小さくなる: MetFrag+CFM+RT+Refs では w_CFM-ID = 0.129（positive）/ 0.090（negative）、w_Refs = 0.334 / 0.327 — [Schymanski 2017 SI](https://static-content.springer.com/esm/art%3A10.1186%2Fs13321-017-0207-1/MediaObjects/13321_2017_207_MOESM1_ESM.pdf)
- 著者の注意: CASMI 2016 はよく知られた人為起源物質が中心で参照数が効いたが、"This situation is also likely to be drastically different for natural products and metabolites, where many more closely-related substances or even isomers could be expected." — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)

#### Blaženović et al. 2017（CASMI 2016 データでの 4 ツール投票モデル）
- 対象: MetFragCL、CFM-ID、MAGMa+、MS-FINDER を訓練 312 / チャレンジ 208 で再実行（候補は CASMI 配布の ChemSpider リスト。訓練 432,511 候補、チャレンジ 258,808 候補）— [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)
- 【ツール間・結合ルール】voting/consensus: 一次スコア = その候補を順位付けできたツール数（4 ツールなら最大 4）。二次スコア S = Σ_A Rank_A / ω_A（ω_A = 訓練セットで測った各ツールの Top10 感度。Top1/5/10/20 版を試し、Top10 版が最良）。57 通りの組合せを訓練で評価してからチャレンジに適用 — [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)
- 訓練での Top10 感度 ω: MetFragCL 0.548、CFM-ID 0.545、MAGMa+ 0.484、MS-FINDER 0.375 — [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)
- in silico のみの結果（Top1/Top5/Top10/Top20、Table 1・Table 2 から転記）— [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)

| 組合せ | 訓練 312 問 | チャレンジ 208 問 |
|---|---|---|
| MetFrag 単体 | 52/134/171/210 | 53/92/111/137 |
| CFM-ID 単体 | 48/124/170/209 | 29/76/104/122 |
| MAGMa+ 単体 | 50/121/151/189 | 28/72/98/117 |
| MS-FINDER 単体 | 32/86/117/145 | 23/57/79/93 |
| MetFrag+CFM-ID | 69/155/194/230 | 47/102/129/153 |
| MetFrag+CFM-ID+MS-FINDER | 58/145/179/221 | 51/95/129/151 |
| 4 ツール全部 | 62/145/180/228 | 46/97/128/152 |
| MetFrag+MS-FINDER | 43/120/143/178 | 33/76/103/125 |
| MS-FINDER+CFM-ID | 50/111/141/188 | 30/76/110/139 |

- 本文: "The voting/consensus model built on MetFragCL, CFM-ID and MS-FINDER did not improve the top hit results of MetFrag, however there were 9% more correctly assigned structures noted in the top 10." — [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)
- 【事前情報・結合ルール】DB/MS/MS boosting: "Final score = in silico consensus rank + DB presence + 2×DB_STOFF-IDENT + 4×DB_MS/MS"（MS-FINDER 内部構造 DB への収載、環境物質 DB STOFF-IDENT への収載、MassBank/NIST14 との MS/MS 類似一致でブースト）— [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)
- boosting 込みのチャレンジ結果: CFM-ID+ID_sorted+DB+MS/MS consensus 181/194/201/204（Top1 87%）、CFM-ID+DB+MS/MS（in silico 1 ツール）180/193/199/201、ID_sorted+DB+MS/MS（in silico なし）174/195/198/204、Randomize+DB+MS/MS 123/184/189/197。訓練の最良は MetFrag+CFM-ID+DB+MS/MS 290（93%）で、boosting のみでも 286 — [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)
- 結論: "for the 'known-unknown' compounds the choice of in silico fragmentation software is negligible, when database and MS/MS boosting are aiding the annotation process." — [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)
- ライブラリ: チャレンジ 208 問中 125（60%）が MassBank+NIST と一致（dot product 441–999）。抄録: "Matching MS/MS spectra against the MS/MS libraries without using any in silico tool yielded 60% correct hits" — [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)
- 論文内の不整合: 抄録は 93%/87% を "a combination of MAGMa+, CFM-ID and compound importance information along with MS/MS matching" とするが、表の最上位は訓練 = MetFrag+CFM-ID+DB+MS/MS（290）、チャレンジ = CFM-ID+ID_sorted+DB+MS/MS（181）— [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)
- 同じツール・同じ 208 問でも実行者によって Top1 が大きく異なる: MetFrag 24（CASMI 主催者の MetFrag2.3）vs 53（Blaženović の MetFragCL）、CFM 39 vs 29、MS-FINDER 46 vs 23、MAGMa+ 24 vs 28 — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1); [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)
- 2018 年のレビューの要約: MS/MS 検索と bio-DB 照合によるブースト、および複数ツール出力の結合で「最大 93% の同定率」— [Blaženović 2018 review](https://doi.org/10.3390/metabo8020031)

#### MetFrag 2.2 論文（Ruttkies et al. 2016）: 2 フラグメンタ結合とメタデータ
- 【結合ルール】最終スコア = 各スコア項の加重和。各項は候補リスト内の最大値で正規化（最高 = 1）。重みは和 1 の制約で 100 組（メタデータ込みは 1000 組）をランダム抽出し、正解 Top1 数が最大の組を採用 — [Ruttkies 2016](https://doi.org/10.1186/s13321-016-0115-9)
- 【ツール間】473 本の Eawag Orbitrap HR-MS/MS（PubChem 分子式検索候補、pessimistic rank）: Top1 は MetFrag2.2 30（6%）、CFM-ID 43（9%）、MetFrag2.2+CFM-ID 62（13%）。Top10 226 / 232 / 276、中央順位 12 / 11 / 8、平均順位 141 / 127 / 85、期待順位での Top1 43 / 57 / 70。本文は最良重み ω_CFM-ID = 0.33 で "the number of Top 1 ranks improved from 30 to 61" としている（表と 1 件の差）— [Ruttkies 2016](https://doi.org/10.1186/s13321-016-0115-9)
- 動機の記述: "As CFM-ID and MetFrag2.2 use independent in silico fragmentation approaches, one can hypothesize that the combination of the approaches should improve the results further." — [Ruttkies 2016](https://doi.org/10.1186/s13321-016-0115-9)
- 【事前情報】メタデータ込み（PubChem）: 参照数のみで 311 件超が Top1（65%）、Frag+RT+Refs で 336（71%）、そこに CFM-ID を加えて 343（73%）。ChemSpider では 420（89%）— [Ruttkies 2016](https://doi.org/10.1186/s13321-016-0115-9)
- 計算コスト: 1 クエリ平均で MetFrag2.2 54 秒、CFM-ID 8,979 秒（150 分）— [Ruttkies 2016](https://doi.org/10.1186/s13321-016-0115-9)
- 追加 3 データセット（計 824 スペクトル）: 断片化のみで Top1 2–9%、全スコア項を等重みにすると 64–82%（データセット間の差が大きい）— [Ruttkies 2016](https://doi.org/10.1186/s13321-016-0115-9)

#### CASMI 2017（天然物中心）
- カテゴリ: Cat 1 = 天然物の構造同定（植物由来＋一部ヒト内因性、45 問、手動可）、Cat 2 = in silico 断片化のみ（243 問、2 ラボで測定、ライブラリはモデル学習にのみ使用可）、Cat 3 = 全情報可、Cat 4 = 候補リスト付きの自動順位付け（198 問）— [CASMI 2017 カテゴリ](http://casmi-contest.org/2017/rules-categories.shtml); [CASMI 2017 結果](http://casmi-contest.org/2017/results.shtml)
- "The CASMI 2017 challenge was focused on Natural Products." LC-MS チャレンジは 243 問 — [McEachran 2020](https://doi.org/10.3390/metabo10060260)
- 公式結果（Top1/Top3/Top10）— [CASMI 2017 結果](http://casmi-contest.org/2017/results.shtml)
  - Cat 2: kai_iso 77/110/147、kai112 38/55/74、yuanyuesimple 16/31/72、yuanyuesqrt 16/32/68、Rakesh 0/0/5
  - Cat 3: tkind1 91/148/193（238 問提出）、tkind2 29/63/107、TsugawaYamamoto 28/56/104
  - Cat 4（198 問）: kai_iso 66/91/119、kai112 55/85/116、IOKRtransferAvgScore 36/59/73、IOKR_TanimotoGaussian 33/50/61、IOKRtransfer 31/48/60、yuanyuesimple 10/23/58、metfrag_plus 6/21/51、metfrag 7/15/42
- CASMI 2017 の総括論文は見つからず、参加者アブストラクトもサイト上で確認できなかった。そのため、エントリ名と手法の対応（kai_* = SIRIUS/CSI:FingerID、IOKR* = Aalto の IOKR、metfrag* = MetFrag、tkind* = Kind ら、TsugawaYamamoto = MS-FINDER 系）は名前からの推定で、未検証 — [CASMI 2017 結果](http://casmi-contest.org/2017/results.shtml)
- 再計算（Cat 4, 198 問）: kai_iso 単体は Top1 66 / Top10 119 / MRR@25 0.422。他系統との 2 者 oracle は、+IOKRtransferAvgScore で Top1 76 / Top10 132 / MRR@25 0.475、+metfrag で 71 / 133 / 0.460、+yuanyuesimple で 72 / 135 / 0.468。4 系統全部の oracle は Top1 86 / Top10 151 / MRR@25 0.545 — [CASMI 2017 category4.csv](http://casmi-contest.org/2017/category4.csv)
- 再計算（同じチャレンジに対する Cat 2 の kai_iso と Cat 3 の tkind1）: 両者が正解を含む 203 問で Top1 は 67 と 91、両方 Top1 なのは 37 問のみ、oracle は 121。243 問での MRR@25 は kai_iso 0.411、tkind1 0.522、oracle 0.672 — [CASMI 2017 category2.csv](http://casmi-contest.org/2017/category2.csv); [CASMI 2017 category3.csv](http://casmi-contest.org/2017/category3.csv)
- 勝者の水準: 全情報の勝者は Top5 180 / Top1 91、in silico のみの勝者は Top5 52% — [McEachran 2020](https://doi.org/10.3390/metabo10060260)
- 2018 年のレビューは "The latest CASMI 2017 contest featured 300 small molecule challenges" と書いており、公式の 243 問と一致しない — [Blaženović 2018 review](https://doi.org/10.3390/metabo8020031); [CASMI 2017 結果](http://casmi-contest.org/2017/results.shtml)

#### McEachran et al. 2020（CFM-ID 予測スペクトル + データソース数で CASMI 2012–2017 を再評価）
- 【事前情報・結合ルール】CFM-ID の予測スペクトル（10/20/40 eV）とのコサインを 3 エネルギー分合計（最大 3.0）し、DSSTox の Data Source Count を結果セット内で 0–1 に正規化して加算。複数の参照カウントを組み合わせても DS 単独を上回らなかった — [McEachran 2020](https://doi.org/10.3390/metabo10060260)
- Top5 の割合（CFM-ID のみ / CFM-ID + DS / 各年の勝者）: 2012 36/64/36、2013 81/88/88、2014 57/76/71、2016 訓練 63/96/–、2016 チャレンジ 66/94/81、2017 59/53/74 — [McEachran 2020](https://doi.org/10.3390/metabo10060260)
- 2016 チャレンジでは Top1 152（73%）/ Top10 201 で、Blaženović の最良（Top1 181 / Top10 201）と Top10 は同等。著者の見解: "to achieve the highest confidence in top ranked hits, use of more than one in silico model appears to be optimal; i.e., consensus modeling appears to be the best approach." — [McEachran 2020](https://doi.org/10.3390/metabo10060260)

#### CASMI 2022
- Fiehn 研（UC Davis）主催。±ESI の生 LC-MS/MS と、500 化合物の RT・m/z リストを配布。"Compounds are not included in public libraries but comprise both metabolites and exposome chemicals." — [CASMI 2022 概要](http://casmi-contest.org/2022/index.shtml)
- 評価は付加イオン・分子式・化合物クラス・2D 構造の 4 カテゴリの「正解率」で、Top-k や順位ではない。目的は "to gauge which methods are used by the community ... and how close we are with respect to compound ID of unknowns" — [CASMI 2022 結果](https://fiehnlab.ucdavis.edu/casmi/casmi-2022-results)
- 2D 構造（priority リスト、正解数/試行数）: Duhrkop 57/222（26%）、Rutz 58/228（25%）、Nothias 58/228（25%）、Mehta 32/156（21%）、Xing 37/246（15%）、Tsugawa 30/241（12%）、Namini/Mosley 25/235（11%）、Wang 23/249（9%）、Nikolic_KUCA 21/55（38%; 試行数が少ない）、Frigerio/Andujar_patroon 1/22、Frigerio/Andujar_msdial 11/196。bonus リスト: Duhrkop 64/219（29%）、Rutz 62/219（28%）、Nothias 62/219（28%）、Xing 31/246（13%）— [CASMI 2022 結果](https://fiehnlab.ucdavis.edu/casmi/casmi-2022-results)
- 各チームの手法は Google Drive 上の抜粋にしか書かれておらず、本調査では確認していない。このため、どのエントリが複数ツールの結合だったかはこのページからは判定できない — [CASMI 2022 結果](https://fiehnlab.ucdavis.edu/casmi/casmi-2022-results)

### Inferences
- 実測された「結合 > 最良単体」の幅は、Top1 で相対 −4% 〜 +20%、Top10 で +3% 〜 +35% 程度。CASMI 2016 の等重み 6 ツールは Top1 +17%（70→82）・Top10 +35%（123→166）、MetFrag+CFM は Top1 +5%（39→41）・Top10 +3%（123→127）、Blaženović のチャレンジセットは Top1 −4%（53→51）・Top10 +16%（111→129）。MRR@25 は Top1 の寄与が大きいので、融合ゲインは控えめに見積もるべき。
- 実際の融合は、oracle までの伸びしろのうち Top1 で約 1/4〜1/3、Top10 で約 1/5〜2/3 しか回収していない（再計算）。oracle 自体は大きい（CASMI 2016 で MRR@25 0.39 → 0.71）ので、融合の鍵は「問題ごとにどのエンジンが正しいかを見分ける信号」（較正された信頼度・一致度）にあると考えられる。
- 訓練データで学習した重みは分布ずれで崩れる。Blaženović は訓練で Top1 +17 件（52→69）だったが、チャレンジでは最良単体比 −2〜−6 件だった。CASMI 2016 は「MassBank に近いもの = 訓練、遠いもの = チャレンジ」と分割しており、MoNA 重みの過大評価と同じ構造の分布ずれが起きていたと推定される。CASMI 2026 では、重み調整用の検証セットを hidden test（timsTOF、クラス 1/2/3 混在）に似せて作らない限り、訓練で見た融合ゲインは再現しないと考えるべき。
- 強い事前情報（参照数・ライブラリ一致・DB 収載）があると、断片化ツールを足してもほとんど効かない（CASMI 2016: +1〜2/208、MetFrag 論文: +7/473）。CASMI 2026 のクラス 1（ライブラリ収載）ではライブラリ/類似検索が支配し、第 2 の in-silico エンジンの寄与はクラス 2/3 に集中すると予想される。
- 同じツールでも実行設定やバージョンで Top1 が 2 倍以上変わる（MetFrag 24 vs 53 など）。融合の重みは「ツール名」ではなく、自分のパイプラインで実測した強さで決めるべき。
- Combined MS/MS の優位の一部は、CSI:FID が negative 81 問に提出していないのを他ツールが補った「カバレッジ補完」による。そのため、純粋な誤り独立性の効果は見かけより小さい可能性がある（CSI:FID を含むペアの oracle も同じ理由で膨らむ）。

### Gaps
- CASMI 2016 Combined MS/MS で各ツールのスコアをどう正規化したか（最大値正規化か順位ベースか、候補欠落の扱い）は、本文・SI で確認できなかった。MetFrag の枠組みは最大値正規化だが、Combined エントリへの適用は未確認。
- Combined MS/MS の per-challenge 順位は公開 CSV に含まれておらず、その MRR@25 は計算できなかった。
- CASMI 2017 の参加者アブストラクトと総括論文は見つからず、エントリと手法の対応は推定にとどまる。結合エントリの詳細（例: tkind1 が複数ツールの投票か）も不明。
- CASMI 2022 の手法記述（Google Drive）は確認しておらず、結合エントリと単体エントリを比較できない。
- 単純な順位平均（Borda 等）を MS/MS 同定ツール間で系統的に比較した査読論文は見つからなかった。最も近いのは Blaženović の感度重み付き順位和。

## 2. なぜ誤りが相補的になるのか — モデル系統・DB・学習データの違いと誤り相関の証拠

### Takeaway
相補性の主因は (1) 断片化モデルの系統差（組合せ的な結合切断、ルールベースの水素転位、生成的 ML、指紋予測）、(2) 学習データの範囲差（CSI 系は学習化合物に近い問題で強く、学習外や negative mode で弱い）、(3) 候補 DB と事前情報の差である。CASMI 2016/2017 の per-challenge 順位を再計算すると、同系統ペアの順位相関（対数順位の Pearson r）は 0.45–0.83 と高く、異系統ペアは 0.03–0.3 程度と低い。異系統ペアは Top1 正解集合の重なりも小さい。

### Cited Findings
- 系統の違い（Blaženović 2017 の記述）: MetFragCL は結合解離に基づく組合せ的断片化（m/z・強度・BDE で採点し、5 種の中性損失ルールで転位を補う）。CFM-ID は CID 断片化の生成モデルを学習。MAGMa+ は部分構造と結合切断ペナルティに基づき、パラメータを最適化した版。MS-FINDER は直鎖の α 開裂を 3 結合まで模擬して水素転位則を適用し、内部構造 DB への収載もスコアに含める — [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)
- CSI:FingerID は fragmentation tree と分子指紋予測を組み合わせる — [Ruttkies 2016](https://doi.org/10.1186/s13321-016-0115-9)。CSI:IOKR は複数カーネルを MKL で結合した Input Output Kernel Regression — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- CASMI 2016 の階層クラスタリング: MS-FINDER は単独で参加者クラスタを形成した（"MS-FINDER does indeed use a different approach to fragmentation than either the combinatorial fragmenters or the machine learning approaches"）。MAGMa/MAGMa+/MetFrag は CFM 系と別クラスタに分かれた。"red cluster" では組合せ的手法が CSI 系を明確に上回り、学習セットと異なる物質と推定されている。"dark blue cluster" では ML 系が良く、メタデータは組合せ的手法すら助けられなかった。green cluster（候補数が平均以下）では MS-FINDER が他を上回った — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- 事例: monobenzyl phthalate（Challenge 41）は主ピークがよく知られた転位で、組合せ的手法はこれを扱えず失敗した。CSI:IOKR と MS-FINDER は成功した — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- 学習データ量の非対称: IOKR の positive 学習データは 3,868（IOKR_A）/ 7,352（IOKR_AR）スペクトルだが、negative は 816 しかない。negative mode の Top1 は MS-FINDER 14、CFM_orig 12、IOKR_A 9。CSI:FID は negative を提出しなかった — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- 学習データの被覆と順位の関係: CFM は "a machine-learning approach with similar training set coverage to CSI, which allowed the complementary approach of MS-FINDER to claim third place ahead of CFM" — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
- molDiscovery 論文: "CSI:FingerID is biased towards the structures that are very similar to its training data, while molDiscovery’s performance does not depend on the similarity between training and testing data"。CSI:FingerID は学習データを除くと性能が大きく落ちる — [Cao 2021 molDiscovery](https://doi.org/10.1038/s41467-021-23986-0)
- 再計算: 対数順位の相関（両者が正解を含む問題に限定）と Top1 の重なり — [CASMI 2016 extra-category2.csv](http://casmi-contest.org/2016/extra-category2.csv); [CASMI 2017 category4.csv](http://casmi-contest.org/2017/category4.csv); [CASMI 2017 category2.csv](http://casmi-contest.org/2017/category2.csv); [CASMI 2017 category3.csv](http://casmi-contest.org/2017/category3.csv)

| データ | ペア | 系統 | n | r(log rank) | Top1（A, B, 両方） |
|---|---|---|---|---|---|
| 2016 Cat2 | MAGMa+ – MetFrag | 組合せ的同士 | 208 | 0.83 | 24, 24, 17 |
| 2016 Cat2 | CFM_orig – MAGMa+ | 生成 ML – 組合せ的 | 208 | 0.52 | 39, 24, 19 |
| 2016 Cat2 | CFM_orig – MetFrag | 生成 ML – 組合せ的 | 208 | 0.46 | 39, 24, 17 |
| 2016 Cat2 | CSI:FID – CSI:IOKR_A | 指紋/カーネル同士 | 126 | 0.48 | 70, 53, 46 |
| 2016 Cat2 | MetFrag – MS-FINDER | 組合せ的 – ルール | 150 | 0.41 | 17, 46, 13 |
| 2016 Cat2 | CSI:FID – MetFrag | 指紋 – 組合せ的 | 126 | 0.28 | 70, 15, 11 |
| 2016 Cat2 | CSI:FID – CFM_orig | 指紋 – 生成 ML | 126 | 0.14 | 70, 27, 19 |
| 2016 Cat2 | CSI:IOKR_A – MS-FINDER | 指紋 – ルール | 150 | 0.10 | 47, 46, 21 |
| 2016 Cat2 | CSI:IOKR_A – MetFrag | 指紋 – 組合せ的 | 208 | 0.07 | 62, 24, 9 |
| 2016 Cat2 | CSI:IOKR_A – MAGMa+ | 指紋 – 組合せ的 | 208 | 0.06 | 62, 24, 10 |
| 2017 Cat4 | IOKRtransferAvgScore – IOKR_TanimotoGaussian | 同一系統の変種 | 198 | 0.74 | 36, 33, 23 |
| 2017 Cat4 | kai_iso – kai112 | 同一チームの変種（推定 CSI） | 198 | 0.63 | 66, 55, 40 |
| 2017 Cat4 | metfrag – metfrag_plus | 同一系統 | 198 | 0.61 | 7, 6, 2 |
| 2017 Cat4 | kai_iso – IOKRtransferAvgScore | 指紋系同士（推定） | 198 | 0.45 | 66, 36, 26 |
| 2017 Cat4 | kai_iso – yuanyuesimple | 不明 | 198 | 0.24 | 66, 10, 4 |
| 2017 Cat4 | IOKRtransferAvgScore – metfrag | 指紋 – 組合せ的（推定） | 198 | 0.14 | 36, 7, 1 |
| 2017 Cat4 | kai_iso – metfrag | 指紋 – 組合せ的（推定） | 198 | 0.11 | 66, 7, 2 |
| 2017 Cat2/3 | tkind1 – TsugawaYamamoto | 全情報同士 | 165 | 0.42 | 72, 25, 21 |
| 2017 Cat2/3 | kai_iso（Cat2）– tkind1（Cat3） | in silico のみ – 全情報 | 203 | 0.03 | 67, 91, 37 |

- 【モデル内】ESP（同じ NIST20 で学習した MLP と GNN の 2 つのスペクトル予測器）: テストで GNN の方が正解を上位に置いたのは 24%、MLP の方が上位は 32%、同順位は 44%。スペクトル予測損失と順位にはほとんど相関がない（"there is little, if any, correlation between the spectral loss and the ranking"）— [Li 2024 ESP](https://doi.org/10.1093/bioinformatics/btae490)
- NP ベンチマーク（2,107 スペクトル）: ISDB-DNP・SIRIUS・MS-Finder の Top1 正解の和集合 1,110 件のうち、3 ツール共通は 29 件（データセットの <1.4%）だけ。"indicating the interest of considering various annotation tools" — [Rutz 2019](https://doi.org/10.3389/fpls.2019.01329)
- スコア尺度が揃っていない: CASMI 2016 で MetFrag・MAGMa+・CFM-ID・CSI:FingerID の生スコアで正誤を判別すると ROC AUC は 0.40–0.55（ほぼランダム）。"MetFrag normalizes scores, so the ordering of hits is exactly random." COSMIC は CSI スコア、次点とのスコア差、fragmentation tree で説明された強度などを、方向制約付き線形 SVM と Platt scaling で統合している — [Hoffmann 2022 COSMIC](https://doi.org/10.1038/s41587-021-01045-9)
- 同点の扱い: 平均順位評価は "can now disadvantage methods that report equal scores" — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)

### Inferences
- 「独立な第 2 エンジン」として価値が高いのは、主力（指紋予測/検索型と想定）と別系統のモデル（前向きスペクトル予測、組合せ的断片化、ルールベース）。同じライブラリで学習した別の指紋予測器は誤り相関が高く（r≈0.45–0.48、Top1 の重なりが大きい）、伸びしろも小さい（同系統 2 者 oracle の MRR@25 0.499 vs 異系統 0.536–0.548）。
- 学習データの被覆が誤り相関を作る。学習化合物に近い問題（クラス 1 相当）では ML 系がライブラリ検索並みに当たり、他系統の上積みは小さい。学習外（クラス 2/3 相当）では組合せ的・ルールベースの相対価値が上がる（CASMI 2016 の leave-out では MetFrag+CFM が Top10 最多、MS-FINDER が平均順位最良）。
- 生スコアは問題間で較正されていないので、融合は問題内の順位か問題内正規化スコアで行うのが安全。問題ごとに「どちらのエンジンを信じるか」を変えたいなら、COSMIC 型の較正特徴（次点とのギャップ等）が要る。
- 再計算の相関には「候補数」という共通の難易度因子も入っている（候補が多い問題は全員の順位が悪い）。そのため、真の誤り相関は表の値より低い可能性がある。

### Gaps
- ツール間の誤り相関（順位相関・正解集合の重なり）を体系的に定量した査読論文は見つからなかった。上の表は本調査の再計算であり、候補数で層別した偏相関などは未実施。
- 「ツール間で Top1 が一致したときの正答率」、つまり一致度を信頼度として使えるかを定量した研究は見つからなかった。

## 3. 2019–2026 の後続研究: 報告されたゲインと失敗条件

### Takeaway
2019 年以降の「統合」の多くは、異なるツールの順位融合ではない。単一モデル内の証拠統合（COSMIC の信頼度、MS2Query のランダムフォレスト、ESP の 2 予測器混合）や、MS/MS と RT 順序のような別モダリティの結合（LC-MS2Struct）が中心である。最新ツール同士（SIRIUS/CSI、ICEBERG、MIST など）の順位融合を定量評価した査読論文はほぼ見当たらない。ESP は「一方のメンバーが明確に弱いとアンサンブルが Top1 を下げる」実例を示している（NIST20/PubChem で Rank@1 0.205→0.169、NPLIB1 学習で 0.237→0.178）。

### Cited Findings
- 【モデル内】ESP（2024, Bioinformatics）: 同じデータで学習した MLP と GNN の前向きスペクトル予測を混ぜるモデル。順位結果に基づいて両者の重みを出す分類器を学習し、訓練例は順位差の SMAPE で重み付けする。抄録: NIST20 学習・PubChem 候補で平均順位を MLP 比 23.7%、GNN 比 37.2% 改善。ただし "MLP approaches remain strong contenders when considering top five ranks" — [Li 2024 ESP](https://doi.org/10.1093/bioinformatics/btae490)
- ESP の Table 1（Rank@1 / Rank@10 / 平均順位）— [ESP 全文 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11344591/)
  - (A) NIST20 学習・PubChem 全候補: MLP 0.197 / 0.453 / 279.96、MLP-PD 0.205 / 0.463 / 299.0、GNN 0.056 / 0.291 / 340.3、GNN-PD 0.075 / 0.333 / 320.7、ESP 0.169 / 0.488 / 213.6
  - (B) NIST20 学習・COCONUT 候補: MLP-PD 0.531 / 0.877 / 6.65、GNN-PD 0.488 / 0.859 / 6.34、ESP 0.551 / 0.900 / 5.66
  - (C) PubChem の類似候補 100 件: MLP-PD 0.283 / 0.646、GNN-PD 0.120 / 0.521、ESP 0.225 / 0.655
  - (D) NPLIB1 学習・PubChem 候補: MLP-PD 0.237 / 0.519 / 313.9、GNN-PD 0.121 / 0.459 / 225.9、ESP 0.178 / 0.479 / 291.1
- ESP の改善幅はプレプリント版（MLP 比 41%、GNN 比 30%）と出版版（23.7%、37.2%）で異なる — [ESP preprint](https://arxiv.org/abs/2203.13783); [Li 2024 ESP](https://doi.org/10.1093/bioinformatics/btae490)
- 【ツール出力＋別モダリティ】LC-MS2Struct（2022, Nat Mach Intell）: MS2 スコアラの出力と観測された保持時間順序を、構造化予測（structured SVM / max-margin Markov network 系）で統合する。MassBank の逆相 LC-MS2 公開データ全体（4,327 分子、18 LC 条件、16 提供者）で評価し、抄録では MS2 スコアラの注釈精度を "up to 106%" 改善。プレプリントでは最大 66.1%、立体異性体を予測する場合は 95.9%。これらは抄録の相対値で、本文は未確認 — [Bach 2022](https://doi.org/10.1038/s42256-022-00577-2); [Bach 2022 bioRxiv](https://www.biorxiv.org/content/10.1101/2022.02.11.480137v2)。実験リポジトリは MetFrag、CFM-ID、SIRIUS の候補スコアを扱う — [lcms2struct_exp README](https://github.com/aalto-ics-kepaco/lcms2struct_exp/blob/main/data/README.md)
- 【モデル内の信頼度】COSMIC（2022）: CASMI 2016 で、生物分子構造 DB 検索（123 クエリ）なら FDR 10% 未満で正しいヒット 57 件、ChemSpider 検索（127 クエリ）なら FDR 0% で 16 件。比較対象の MetFrag・MAGMa+・CFM-ID は ChemSpider で FDR 70% でも 0 件、CSI:FingerID の生スコアは FDR 40% で 0 件。COSMIC は "outperforms spectral library search for this purpose" — [Hoffmann 2022 COSMIC](https://doi.org/10.1038/s41587-021-01045-9)
- 【モデル内・ライブラリ検索】MS2Query（2023）: MS2Deepscore で 2,000 件を前選別し、ランダムフォレストで再順位付けする。RF は 5 特徴（Spec2Vec 類似度、query precursor m/z、precursor m/z 差、化学的に近いライブラリ 10 分子での重み付き平均 MS2Deepscore、それら 10 分子の平均 Tanimoto）から Tanimoto を予測する。アナログ検索では、35% のスペクトルに平均 Tanimoto 0.63 のアナログを返した（修正コサインは同じ再現率で 0.45）— [de Jonge 2023 MS2Query](https://doi.org/10.1038/s41467-023-37446-4)
- 【前向き予測の単体】ICEBERG（2025 プレプリント）: MassSpecGym で 46% top-1 / 86% top-10。NIST/GNPS に未収載の MSnLib 8,519 スペクトルでは、PubChem 全体を候補にして 38.0% top-1 / 80.3% top-10。"The top-10 identification accuracy of ICEBERG is almost doubled compared to SIRIUS"。SIRIUS との順位融合は報告されていない — [Wang 2025 ICEBERG preprint](https://doi.org/10.1101/2025.05.28.656653)
- 単一ツールの実試料精度: 9,000 超のシグナルに CSI:FingerID と NIST hybrid search を併用した研究で、MSI レベル 1 同定化合物に対する CSI:FingerID の 1 位正解率は 40%（抄録・要約ベース）— [Blaženović 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC11426395/)
- 【ツール間・クラスレベル】ConCISE（2022）: GNPS 分子ネットワーク内で CANOPUS のクラス予測を多数決し、superclass は 50%、class/subclass は 70% 以上一致したときだけ伝播する。真陽性率 >95% を保ちつつ、3 データセットで推定注釈を 465–1244% 増やしたと報告（要約ベース）— [Quinlan 2022 ConCISE](https://www.mdpi.com/2218-1989/12/12/1275)
- 失敗条件の実例（数値付き）:
  - 弱いメンバーとの結合: Blaženović のチャレンジで MetFrag 単体 53 → MetFrag+MS-FINDER 33（Top1）— [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)。ESP の (A) で Rank@1 0.205 → 0.169、(D) で 0.237 → 0.178 — [ESP 全文 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11344591/)
  - 学習した重みの分布ずれ: MetFrag+CFM-ID は訓練で 69（MetFrag 52）だったが、チャレンジで 47（MetFrag 53）— [Blaženović 2017](https://doi.org/10.1186/s13321-017-0219-x)。MoNA の重みが楽観的すぎて 163 → 155 — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)
  - 事前情報の支配による頭打ち: Combined MS/MS+RT+Refs 164 vs MetFrag+RT+Refs 162 — [Schymanski 2017](https://doi.org/10.1186/s13321-017-0207-1)。PubChem で 336 → 343（+CFM-ID）— [Ruttkies 2016](https://doi.org/10.1186/s13321-016-0115-9)
  - 事前情報がドメインに合わない: CASMI 2017（NP）で DS を加えると Top5 が 59% → 53% に低下 — [McEachran 2020](https://doi.org/10.3390/metabo10060260)

### Inferences
- MRR@25 を目的にするなら、平均順位や Top10 が良くなっても Top1 が下がる融合（ESP 型）は不利になりうる。第 2 エンジンの役割を「Top-k 内の並べ替え」や「同点・僅差のタイブレーク」に限定するなど、Top1 を守る設計を検証すべき（推論）。
- 2 メンバーの強さが近い場合（ESP の COCONUT: 0.531 vs 0.488）は、融合で Top1 も改善した。第 2 エンジンを主力と同程度まで強くすることが、Top1 での融合ゲインの前提条件と考えられる。
- 最新 ML ツール同士（CSI/MIST/ICEBERG/MassFormer 等）の融合は文献上未検証で、CASMI 2026 では自前の検証が必要。

### Gaps
- SIRIUS 5/6 と CANOPUS の組合せ（クラス予測による候補絞り込み・再順位付け）が構造 Top1 にどれだけ効くかを定量した査読論文は見つからなかった。
- CFM-ID 4 / ICEBERG / MassFormer / MIST と CSI:FingerID の順位融合を定量評価した研究は見つからなかった（ICEBERG 2025 は単体比較のみ）。MassSpecGym などのベンチマークで異系統アンサンブルを報告した結果も見つからなかった。
- LC-MS2Struct のツール別 Top1 の絶対値は本文未確認（抄録の相対改善率のみ）。
- MS2DECIDE（GNPS・SIRIUS・ISDB-LOTUS の出力を意思決定理論で集約し、新規性で優先付けするツール）の集約式と定量性能は、一次資料で確認できなかった。存在と目的は [MS2DECIDE 章 (bibbase)](https://bibbase.org/network/publication/mejri-cailloux-lepogam-ztrkescoffier-beniddir-ms2decideharnessingthecomplementarityofmassspectrometryannotationtoolsforprioritizingnovelnaturalproducts-2026) と [MS2DECIDE ChemRxiv](https://chemrxiv.org/engage/chemrxiv/article-details/674496997be152b1d0b876a0) で確認。「約 100 化合物の人工混合物に入れた新規 6 化合物をすべて上位 10 に入れた」という評価はニュース記事にしか見当たらない — [Techno-Science 記事](https://www.techno-science.net/en/news/when-artificial-intelligence-learns-to-sniff-out-novel-molecules-27916)

## 4. 天然物（NP）・植物抽出物での組み合わせ: 何が効いたか

### Takeaway
NP では次の 3 点が確認された。(i) ツール間の Top1 正解集合の重なりが非常に小さく（ISDB-DNP・SIRIUS・MS-Finder の 3 者共通は 29 件）、和集合（oracle）は最良単体を上回る（Top1 46.3% → 52.7%）。(ii) 参照数・データソース数のような「有名さ」の事前分布は効かないか逆効果（CASMI 2017 で Top5 59% → 53%）。(iii) 分類学的事前情報は全ツールで Top1 を大幅に押し上げた（2,107 件中 SIRIUS 975 → 1,508、ISDB-DNP 214 → 1,510）。一方、NP で「複数ツールの順位融合そのもの」の Top1 を報告した査読研究は見つからず、実測値は oracle（和集合）と事前情報結合に限られる。

### Cited Findings
- ベンチマーク: Dictionary of Natural Products（生物起源情報）と GNPS ライブラリを組み合わせた実測 MS/MS 2,107 本 — [Rutz 2019](https://doi.org/10.3389/fpls.2019.01329)
- 初期スコアでの Top1: ISDB-DNP 214（10.2%）、SIRIUS 975（46.3%）、MS-Finder 180（8.5%）。3 ツールの Top1 正解の和集合は 1,110（52.7%）、3 者共通は 29。全順位まで含めた正解数は ISDB-DNP 1,750、SIRIUS 1,589、MS-Finder 574 — [Rutz 2019](https://doi.org/10.3389/fpls.2019.01329)
- 【事前情報】分類学的スコア（taxonomically informed scoring）適用後の Top1: ISDB-DNP 1,510、SIRIUS 1,508、MS-Finder 546。和集合 1,786（84.8%）、3 者共通 376（17%）。F1 スコアは 1.5–7 倍 — [Rutz 2019](https://doi.org/10.3389/fpls.2019.01329)
- 結合ルール: 正規化スペクトルスコア（0–1）に、候補の生物起源と試料の分類学的一致度（科・属・種）に応じた加点の最大値を足して再順位付けする。ISDB-DNP 用の最適加点は科 0.81 / 属 1.62 / 種 2.55（ベイズ最適化）— [Rutz 2019](https://doi.org/10.3389/fpls.2019.01329)
- 著者の注意: 全化合物が DNP に含まれるため、同じ DB に基づく ISDB-DNP が有利。また GNPS ライブラリは SIRIUS の学習セットにも含まれる。"It was not meant to compare the performances of the tools." — [Rutz 2019](https://doi.org/10.3389/fpls.2019.01329)
- NP の異性体問題: DNP で分子式が一意な化合物は 10% 未満、分子式あたり平均 8.6 化合物、最大は C15H20O4 の 1,274 異性体 — [Rutz 2019](https://doi.org/10.3389/fpls.2019.01329)
- CASMI 2017（NP 中心）で「有名さ」事前分布が逆効果: CFM-ID のみの Top5 59% に対し、DSSTox データソース数を加えると 53%。"This is the only dataset where the addition of metadata decreased performance." 登録前の DSSTox には 54 化合物しかなく、その状態での Top5 は 38。2017 データの 71% は登録前の DSSTox に未収載だった。"if the compounds only have one data source then it is likely that other candidates returned from a monoisotopic mass search had a greater number of data sources." 全年合計で Top20 外になった 75 件のうち 65 件が 2017 データ — [McEachran 2020](https://doi.org/10.3390/metabo10060260)
- CASMI 2017 の oracle（再計算）: Cat 4 で kai_iso 単体 MRR@25 0.422 → 4 系統 oracle 0.545。Cat 2 kai_iso と Cat 3 tkind1 では 0.411 / 0.522 → oracle 0.672 で、両方 Top1 は 203 問中 37 問のみ — [CASMI 2017 category4.csv](http://casmi-contest.org/2017/category4.csv); [CASMI 2017 category2.csv](http://casmi-contest.org/2017/category2.csv); [CASMI 2017 category3.csv](http://casmi-contest.org/2017/category3.csv)
- 【モデル内】ESP を NP 候補空間で評価: NIST20 学習・COCONUT 候補では 2 予測器の強さが近く（MLP-PD Rank@1 0.531、GNN-PD 0.488）、ESP は 0.551 に改善。NPLIB1（NP ライブラリ）学習・PubChem 候補では GNN-PD が 0.121 と弱く、ESP（0.178）は MLP-PD（0.237）を下回った — [ESP 全文 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11344591/)
- ライブラリ被覆: GNPS の公開スペクトルライブラリは既知 NP の約 2.5% しか含まない — [de Jonge 2023 MS2Query](https://doi.org/10.1038/s41467-023-37446-4)
- MS-FINDER の内部構造 DB は 13 DB から構成され、UNPD・KNApSAcK・PlantCyc などの NP/植物 DB を含む（CASMI 2016 Category 2 では無効化して実行）— [Schymanski 2017 SI](https://static-content.springer.com/esm/art%3A10.1186%2Fs13321-017-0207-1/MediaObjects/13321_2017_207_MOESM1_ESM.pdf)
- 【ツール間・クラスレベル】ConCISE は分子ネットワーク上で CANOPUS 予測の多数決をとり、クラス注釈を伝播する（真陽性率 >95%、要約ベース）— [Quinlan 2022 ConCISE](https://www.mdpi.com/2218-1989/12/12/1275)
- 【ツール間】MS2DECIDE は GNPS・SIRIUS・ISDB-LOTUS の出力を意思決定理論と専門知識で集約し、NP の新規性で優先付けする。植物 Pleiocarpa mutica の実試料に適用された（定量値は一次資料で未確認）— [MS2DECIDE ChemRxiv](https://chemrxiv.org/engage/chemrxiv/article-details/674496997be152b1d0b876a0); [BioCIS 紹介](https://www.biocis.universite-paris-saclay.fr/?p=4910)
- 査読外: 食品中フェノール化合物の学位論文では、MS-Finder と SIRIUS の組合せで 90% 超を注釈し、3 ツールで初期スクリーニング → 手動精査の流れが効率的と結論している（検索要約ベースで信頼度は低い）— [UFRGS 学位論文](https://lume.ufrgs.br/handle/10183/273922)

### Inferences
- NP（特に COCONUT 由来のクラス 2）では、ツール間で Top1 正解集合がほとんど重ならない。融合の伸びしろは大きいが、どのツールを信じるかの判定は難しい。
- 参照数・データソース数・PubChem での知名度のような事前分布は、NP の候補間では差が出にくいか逆効果になりうる（CASMI 2017）。CASMI 2026 のクラス 2（PubChem/COCONUT 由来）では、知名度事前分布は検証セットで効果を確かめてから使うべき。
- 分類学的事前情報は強力だが、試料の生物種情報が入力に無ければ使えない。CASMI 2026 の入力仕様にこれが含まれるかは、本ノートの範囲外で未確認。
- ESP の COCONUT 結果は、候補集合が NP 空間（構造が類似している）でも、強さが同程度の 2 予測器の融合なら Top1 まで改善しうることを示唆する。逆に、NP 学習データ（NPLIB1）が小さいと弱いメンバーが足を引っ張る。

### Gaps
- 「MS-FINDER + CSI:FingerID + ライブラリ検索」の順位融合を NP/植物抽出物で評価し、融合後の Top1 を単体と比べた査読研究は見つからなかった。
- CASMI 2017 Cat 1（植物 NP 45 問）で複数ツールの結合を使ったエントリの手法と成績は、アブストラクトが見つからず不明。
- CASMI 2016 Category 1（NP 19 問）で MS-FINDER と SIRIUS の分子式コンセンサスを用いたとされる報告は、全文を取得できず未確認。
- MS2DECIDE と ConCISE の詳細な数値は、一次資料の全文では確認していない。
