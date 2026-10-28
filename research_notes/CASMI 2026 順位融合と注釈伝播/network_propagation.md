# バッチ内トランスダクティブ／ネットワーク型注釈伝播（MS/MS 天然物構造注釈）：定量ファクトベース

凡例: 「[筆者計算]」は原典の数値から算術的に導いた値。「（課題前提）」は依頼文で与えられた CASMI 2026 の前提で、外部ソースはない。数値は原典の表記どおり（相対か絶対か曖昧なものはその旨を明記）。

## KQ1. NAP / ChemWalker / MolNetEnhancer / ConCISE / ZODIAC / SNAP-MS / MS2LDA / FBMN / MolNotator / MetGem / グラフ型コンセンサス再ランキング：何を伝播し、Top-1/Top-k はどれだけ改善したか

### Takeaway
構造レベルで Top-1 を押し上げた数値を出しているのは主に NAP（MetFrag 候補の再ランキング）である。ライブラリ一致の隣接ノードをアンカーに使う Fusion は NIST17 で平均順位 14.7→4.7（中央値 5→1）だが、アンカー無しの Consensus は中央値 5→2 に留まる。ZODIAC はデータセット内の結合推論（Gibbs sampling）で「分子式」の誤り率を最大 16.5 倍下げた。MolNetEnhancer・ConCISE・SNAP-MS が伝播するのは化学クラスや化合物ファミリーで、クラス精度は高い（ConCISE TPR >95%、SNAP-MS 約 89%）。ただし、これらが構造の Top-1 をどれだけ上げるかは報告されていない。

### Cited Findings

#### NAP（Network Annotation Propagation; da Silva et al. 2018, PLoS Comput Biol, doi:10.1371/journal.pcbi.1006089）
- 入力は GNPS 分子ネットワーク（ノードは consensus MS/MS、エッジはスペクトル類似）と、各ノードの MetFrag in silico 候補リスト — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- **Fusion**：直接隣接ノードにライブラリ一致がある場合だけ適用できる。MetFusion 型のスコアで、MetFrag スコア f_c と、「隣接の cosine m_j × 候補と隣接注釈の Tanimoto t_cj」に sigmoid をかけた要約項を組み合わせる。既定値 α=0.3、β=−9、γ=0.6 は MetFusion の最適化値を流用 — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- **Consensus**：ライブラリ一致は不要。各直接隣接の上位 n-first 候補（既定 10）との最大 Tanimoto を同じ関数に入れる。Fusion の後に Consensus を重ねると、アンカーから遠いノードにも伝播する。構造類似度は CDK の "extended" fingerprint による Tanimoto — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- **NIST17 [M+H]+ ベンチマークの規模**：11,331 スペクトルのうち、ネットワーク内に類縁体を 1 つ以上持つ 5,467 件で評価（=約 48.2% [筆者計算]）。候補 DB は GNPS, HMDB, SUPER NATURAL II, ChEBI, DNP を合わせた 367,204 分子 — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- **NIST17 の平均/中央値順位**
  - MetFrag 単独 14.7/5（ランダム 23/12）
  - Consensus 単独 n-first=5: 10.9/2、10: 10.2/2、15: 9.8/2、20: 9.6/2
  - Fusion 4.7/1、Fusion 後の Consensus 6.3/2
  - — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- **「1 位の増加」**：Fusion +29.0%、Fusion 後の Consensus +19.8%。上位 20 内で MetFrag より順位が良くなった割合は +18.4% / +13.0%。相対値か絶対値かは本文から判別できない。Discussion ではこれらの数字をクラス割当に結び付けており、Results と食い違う — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- **1 位候補の ClassyFire Class が正解構造と一致した率**：Fusion 84%、Consensus 78%（Fusion 無しでは 66%）、MetFrag 44% — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- **序論の主張**：1 位候補に正しい部分構造が含まれる率は、ライブラリ有りで最大 81%、無しで最大 63%。これはクラスタリングに基づく部分構造レベルの値で、構造一致率ではない — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- **CASMI 2016 のデータ条件**：公開ライブラリ（CASMI 由来は除外）と一緒にネットワーク化し、類縁ノードと連結した 186/227 チャレンジ（pos 136、neg 50）で評価 — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- **CASMI 2016 の 1 位件数**
  - Fusion 113(pos)+44(neg)=157、Consensus 70+31=101
  - 比較：MS-Finder 159、CFM-ID 157（著者は「同等」と表現）
  - MetFrag 単独より改善した件数：Fusion 54+19、Consensus 36+8
  - MetFrag 単独の 1 位件数は本文に記載なし
  - — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- **実データ例**
  - *Euphorbia dendroides* のフォルボイド系ファミリー（14 ノード）：Fusion で 11/14 をフォルボイド誘導体と注釈（MetFrag の上位候補にはフォルボイドが無かった）。ライブラリ無しの Consensus では 8/14
  - 菌園のステロール系（37 ノード）：Consensus 32 ノード対 MetFrag 18 ノード
  - — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)

#### ChemWalker（Borelli et al. 2023, Bioinformatics）
- NAP は伝播が 1-hop（ライブラリ一致の直接隣接）に限られる。ChemWalker はシード（ライブラリ一致）から再出発する random walk でこれを解消し、シードに直接つながらないノードにも伝播する。エッジ重みは MetFusion 型（両ノードの MetFrag スコア、cosine、候補間の化学類似度）。収束判定は L1 < 1e-6 — [ChemWalker (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9991053/)
- 評価は NIST 555 スペクトルのネットワークで行い、RDKit の 27 種 fingerprint を比較した。本文の結論は「NAP と統計的に区別できない」。シードは最大 10% に制限した（NAP は注釈済みノードの全直接隣接の情報を使う）。数値の詳細は補遺のみ — [ChemWalker (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9991053/)

#### MolNetEnhancer（Ernst et al. 2019, Metabolites, doi:10.3390/metabo9070144）
- 伝播対象は構造ではなく、ClassyFire の化学クラス（kingdom〜direct parent の 5 階層）と MS2LDA の Mass2Motif。ライブラリ一致と in silico ツール（NAP, DEREPLICATOR, VarQuest, SIRIUS+CSI:FingerID）の候補構造を ClassyFire で分類し、分子ファミリー（MF）ごとに最頻クラスを割り当てる — [MolNetEnhancer (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6680503/)
- 「Chemical Classification score」は、MF 内でそのクラスに該当するノードの割合（例 2.25/6=0.375）。構造一致が 1 件だけのシングルトンはスコア 1 になる — [MolNetEnhancer (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6680503/)
- 既知構造に対するクラス正解率のベンチマークは無い。報告はケーススタディのみ — [MolNetEnhancer (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6680503/)
  - Euphorbia 43 抽出物：2 MF・73 feature をレベル 3 で注釈
  - Salinispora/Streptomyces：5,930 ノード、Mass2Motif 300 個のうち 40 個を注釈
- 著者自身の注意：高いクラススコアは同定の確度を意味しない（シングルトンは一致 1 件で高スコアになる）。多くの MF でクラス注釈が不整合（Supp. Fig. S2/S4） — [MolNetEnhancer (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6680503/)

#### ConCISE（Quinlan et al. 2022, Metabolites, doi:10.3390/metabo12121275）
- **方法**：GNPS ライブラリ一致（構造情報付き、優先）と CANOPUS の ClassyFire 予測（superclass/class/subclass）を、サブネットワーク内の多数決で統合する — [ConCISE (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9786801/)
  - 一致率の閾値は superclass ≥50%、class と subclass は ≥70%。通過した最も細かい階層を採用する
  - superclass が不成立なら "No Consensus Reached"
  - シングルトンにはライブラリ注釈しか付けない（偽陽性を抑えるため）
- **TPR**：ライブラリ一致 1,789 件を正解として、ライブラリ由来のコンセンサスで 98.88±1.62%、in silico だけのコンセンサスで 96.1±4.96% — [ConCISE (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9786801/)
- **規模と注釈率**：3 データセット（9,904〜21,991 features、3,112〜7,293 subnetworks）で、注釈数は 465%〜1244% 増加。feature の注釈率は 58.6%/56.3%/76.5%、平均サブネットワーク一致度は 87% 超 — [ConCISE (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9786801/)
- MolNetEnhancer や NAP との定量比較は無い — [ConCISE (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9786801/)

#### ZODIAC（Ludwig et al. 2020, Nat Mach Intell, doi:10.1038/s42256-020-00234-6）
- **何を伝播するか**：分子式候補。各化合物に SIRIUS の上位 50 分子式と「その他」を表すダミーノード（他と接続しない）を置き、同じデータセット内の化合物間で fragmentation tree を比較する — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)
  - エッジスコアは共通フラグメント＋共通 root loss の数を s/n1+s/n2 で正規化したもの
  - スコア分布は log-normal でモデル化し、「非ゼロスコアの 95% は偽エッジ」とみなす閾値を置く
  - さらに化合物ごとに個別閾値を設け、少なくとも 10 候補が 10 本以上のエッジを持つようにする
  - 事後分布は Gibbs sampling で推定する（MAP は NP 困難）
- **誤り率（SIRIUS→ZODIAC）** — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)
  - *E. dendroides*（75% が m/z ≥605）：正解 98/197→191/197、誤り 50.25%→3.05%（16.5 倍減）
  - NIST1950 血漿：9.57→6.38%
  - トマト：4.81→1.48%
  - 珪藻：12.90→6.45%
  - マウス糞便（低品質）：32.56→18.60%
- **adduct の取り違え**：dendroides での ZODIAC の誤り 6 件は、すべて [M+H]+ と [M+Na]+ の取り違えだった（質量差 21.984 vs 21.982 Da）。正しい adduct を与えると SIRIUS 66.17%→ZODIAC 99.50%（誤り 68 倍減） — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)
- **アンカー**：ライブラリ一致をアンカーとして入れても誤り率は改善しなかった（構造非重複の 10-fold CV）。結論でも「anchors have only a small effect」 — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)
- **確信度とカバー率**：ZODIAC score ≥0.9 で正解率 >93.94% を保ちつつ、各データセットの 52.26〜88.51% を保持する。ライブラリ検索で注釈できたのは 3.78〜16.55% — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)
- **実行時間と入力**：ZODIAC は 1〜19 分/データセット（SIRIUS は 3〜53 分）。MZmine、OpenMS、FBMN の出力を取り込める — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)

#### SNAP-MS（Morehouse et al. 2023, Nat Commun, doi:10.1038/s41467-022-35734-z）
- **方法**：MS2 ライブラリを使わない。GNPS サブネットワーク内の MS1 m/z を、adduct（[M+H]+, [M+Na]+, [M−H2O+H]+ 等）を仮定して Natural Products Atlas（または COCONUT）と照合する — [SNAP-MS (Europe PMC full text)](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9852437/fullTextXML)
  - ヒット化合物を Morgan(r=2)/Dice 0.71 でファミリーにまとめる
  - ファミリーの順位は「サブネットワークの質量を何個説明するか」で決める。ファミリーの大きさで決めると、異性体の多いファミリーが水増しされるため
- **精度**：序論では 35 サブネットワーク中 31 で正しい化合物クラス（89%）。Discussion には 194/219 という別の数値があり、不整合 — [SNAP-MS (Europe PMC full text)](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9852437/fullTextXML)
  - NIH 純品ライブラリ 22 サブネットワーク：正解ファミリーが 1 位 17 回・2 位 1 回。組立ミスのある 2 件を除くと 18/20（90%）
  - 公表済み 6 サブネットワーク：すべて一致
  - COCONUT への拡張：184 中 164 が正解（89%）
- **NAP（COCONUT 候補）との比較** — [SNAP-MS (Europe PMC full text)](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9852437/fullTextXML)
  - ノード単位：正解構造が top-10 に 66%、top-5 に 57%、top-1 に 30%
  - サブネットワーク単位：最も厳しい基準で 183 TP / 109 FP（63%）

#### MS2LDA / Mass2Motifs
- MS2LDA は LDA（トピックモデル）を MS/MS の fragment と neutral loss に適用し、共起パターン（Mass2Motif、しばしば部分構造に対応）を教師なしで抽出する手法 — [van der Hooft et al. 2016 PNAS](https://doi.org/10.1073/pnas.1608041113)
- MolNetEnhancer は Mass2Motif をネットワークに重ねて表示する（ノード上の円グラフ、motif を共有するノード間のエッジ） — [MolNetEnhancer (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6680503/)
- MS2LDA 2.0（bioRxiv 2025）は Spec2Vec ベースの自動注釈 MAG と再構築した MotifDB を導入した。検証には尿の MotifSet で手動注釈された Mass2Motif 101 個を使った — [MS2LDA 2.0 bioRxiv](https://www.biorxiv.org/content/10.1101/2025.06.19.659491.full.pdf)
- Glasgow eprints には Nat Commun 2026 の受理版 PDF が掲載されている — [eprints.gla.ac.uk/391728](https://eprints.gla.ac.uk/391728/)
- 「14 倍高速」は業界誌による二次情報 — [The Analytical Scientist](https://theanalyticalscientist.com/issues/2026/articles/july/mass-spec-roundup-signals-recovered/)

#### FBMN・MetGem・MolNotator（ネットワークの構築・表示系。伝播そのものではない）
- FBMN は LC-MS の feature 検出・アライメント結果からネットワークを作る GNPS のワークフロー — [Nothias et al. 2020 Nat Methods](https://doi.org/10.1038/s41592-020-0933-6)
- ZODIAC 等の伝播系ツールは FBMN の出力を入力に取れる — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)
- MetGem は t-SNE で分子ネットワークを生成・可視化するソフトで、伝播精度の評価は対象外 — [Olivon et al. 2018 Anal Chem](https://doi.org/10.1021/acs.analchem.8b03099)
- MolNotator は ion 種（adduct、complex、in-source fragment）を組合せで突き合わせて中性分子を予測し、ネットワーク上に「分子ノード」を置いて質量/分子式ベースの注釈を伝播する — [MolNotator bioRxiv](https://www.biorxiv.org/content/10.1101/2021.12.21.473622.full.pdf)
- MolNotator は地衣類由来の精製二次代謝物 156 種で 92.3% を正しく予測した（平均誤差 <2 ppm） — [WUR dataset page](https://research.wur.nl/en/datasets/from-mass-spectral-features-to-molecules-in-molecular-networks-mo/)

#### グラフ全体最適化・リポジトリ規模の伝播
- **NetID（Chen et al. 2021 Nat Methods）**：ノードはピーク、エッジは adduct・同位体・フラグメント・生化学変換に対応する質量差（MS2 類似度や共溶出でスコア化）。整数線形計画（ILP）で全ピークの分子式を同時に決める — [NetID (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8733904/)
  - 酵母 negative mode：5,588 ピーク中 約 4,800 にユニーク注釈
  - 手動で作った正解 314 ピークでの誤注釈は、最適化しないノード単位の方法より「概ね一桁少ない」（正確な値は図のみ）
- **KGMN/MetDNA2（Zhou et al. 2022 Nat Commun）**：判定基準は top-3 に正解の InChIKey 第 1 ブロックがあるか — [KGMN (Europe PMC full text)](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9636193/fullTextXML)
  - 既知代謝物の同定精度は 98.5%（正 3,325 / 誤 49）。MetDNA1 は 72.2%（正 1,767 / 誤 682）
  - 注釈カバー率は 71.0%→97.8%
- **リポジトリ規模の近傍 suspect ライブラリ（Bittremieux et al. 2023 Nat Commun）**：1,335 データセット・5.21 億スペクトルを molecular networking で結び、注釈済みスペクトルの隣接から 87,916 件の suspect を作った — [Bittremieux 2023 (Europe PMC full text)](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10733301/fullTextXML)
  - 一致率は平均 5.5%→9.3%（中央値 3.6%→6.4%）
  - 後から登録された 72 データセットでは 5.7%→8.9%
  - 試料種別ごとの増加倍率は 1.7±0.3（食品）〜3.0±0.7（環境）

### Inferences
- **アンカーの有無で改善幅が大きく違う。** NAP では Fusion（アンカー有り）が Consensus（アンカー無し）を一貫して上回る（NIST の中央値 1 対 2、CASMI 2016 の 1 位 157 対 101）。CASMI 2026 で使えるのがテストスペクトル同士の label-free 類似だけなら、NAP の Consensus に相当する「アンカー無しのコンセンサス再ランキング」になり、期待できる改善は Fusion より小さい。
- **学習・例示スペクトルをアンカーにできるかは要確認。** ラベル付きの学習スペクトルを同じネットワークに入れてアンカーにすることがルール上許されれば、Fusion 型に近い効果が見込める。ルールは未確認。
- **論文の改善幅はデータセット全体の改善幅ではない。** NAP の NIST 評価は類縁体を持つ 48% だけを対象にしている。CASMI テストで 1〜2 編集で結ばれる分子は約 30%（課題前提）なので、全体の改善は「近縁ありサブセットでの改善 × 近縁ありの割合 − 孤立ノードへの悪影響」で薄まる。これは粗い推定。
- **ZODIAC からの示唆。** データセット内の結合推論はアンカー無しでも効き、改善は大きな化合物（>600 Da、植物の二次代謝物）で特に大きい。最大の失敗要因は adduct の誤りなので、timsTOF データでも adduct・ion 種の扱いが伝播の前提条件になる。
- **クラス単位のコンセンサスを事前分布に使う。** ConCISE（50/70% 閾値で TPR >95%）や SNAP-MS（約 89%）のようなクラス・ファミリー単位のコンセンサスは精度が高い。そのため、構造候補を直接上書きするより、候補の化学クラスに軽い事前重みを与える使い方が安全と考えられる（TIMA の chemical consistency が実装例。KQ2 参照）。

### Gaps
- NAP について、CASMI 2016 での MetFrag 単独の 1 位件数、「+29.0%」が相対か絶対か、伝播で順位が悪化した件数は本文に無い。
- ChemWalker の top-k 数値は補遺にあり、未取得。
- MolNetEnhancer にはクラス正解率の定量評価が無い。
- MS2LDA 2.0 の MAG 注釈正解率は未取得。
- SNAP-MS の 31/35 と 194/219 の不整合は解消できなかった。
- 検索要約で見かけた「SNAP-MS の評価ライブラリが NP Atlas と重なる」という読者コメント型の批判は、出典を確認できていない（未検証）。
- BUDDY（Xing et al. 2023 Nat Methods）の experiment-specific global peak annotation による改善幅は、取得できた範囲に数値が無かった — [UBC thesis record](https://open.library.ubc.ca/cIRcle/collections/24/items/1.0431329)
- APEX（C. elegans、複数ネットワークにまたがる伝播）は未精査 — [APEX (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10701709/)

## KQ2. Taxonomically informed scoring（Rutz et al. 2019 → TIMA-R / LOTUS）：改善幅、生物起源を知っていることへの依存、起源が不明・混合のときの挙動

### Takeaway
種レベルの生物起源が既知という条件では、分類学的な再重み付けで Top-1 は劇的に上がる（2,107 スペクトルで ISDB-DNP 10.2%→約 71.7%、SIRIUS 46.3%→約 71.6%）。ただしこのベンチマークは候補 DB と起源情報が同じ DNP に由来しており、循環的で楽観的である。起源が不明・誤り・混合の場合の性能は評価されていない。現行の TIMA（R 版）では起源が不明だと全候補の生物スコアが 0 になり、順位は spectral（0.4）と、ネットワーク近傍に基づく chemical consistency（0.2）だけで決まる。

### Cited Findings
- **2019 版のスコア**：各ツールのスコアを 0–1 に正規化し、候補の報告生物が試料の生物と family/genus/species で一致すれば加点する（ベンチマークでは 1/2/3）。積ではなく和で結合する。網羅的なネットワーク近傍の再重み付けは含まない — [Rutz et al. 2019](https://www.frontiersin.org/articles/10.3389/fpls.2019.01329/full)
- **ベンチマークの構成**：GNPS ライブラリのスペクトルを DNP の構造と生物起源に対応付け、起源が種レベルで 1 つだけの 2,107 件を使った — [Rutz et al. 2019](https://www.frontiersin.org/articles/10.3389/fpls.2019.01329/full)
- **Top-1 正解数（再ランキング前→後）** — [Rutz et al. 2019](https://www.frontiersin.org/articles/10.3389/fpls.2019.01329/full)

| ツール | 前 | 後 | F1 の変化 |
|---|---|---|---|
| ISDB-DNP | 214（10.2%） | 1,510（≈71.7% [筆者計算]） | 7 倍 |
| SIRIUS | 975（46.3%） | 1,508（≈71.6% [筆者計算]） | 1.5 倍 |
| MS-Finder | 180（8.5%） | 546（≈25.9% [筆者計算]） | 3 倍 |
| 3 ツールの和集合 | 1,110（52.7%） | 1,786（84.8%） | — |
| 3 ツール共通の Top-1 | 29（<1.4%） | 376（17%） | — |

- **どの順位でもよいときの正解数**：ISDB-DNP 1,750、SIRIUS 1,589、MS-Finder 574 — [Rutz et al. 2019](https://www.frontiersin.org/articles/10.3389/fpls.2019.01329/full)
  - つまり再ランキング後には、回収可能な正解のうち ISDB-DNP で約 86%、SIRIUS と MS-Finder で約 95% が Top-1 に来ている [筆者計算]
- **起源情報を劣化させた実験**：エントリーを 4 等分し、3 ブロック（75%）で起源情報を消した（種のみ／属＋種／科＋属＋種）。その上で Bayesian optimization により加点値を最適化し、family 0.81、genus 1.62、species 2.55 を得た（最大 1,126 hits） — [Rutz et al. 2019](https://www.frontiersin.org/articles/10.3389/fpls.2019.01329/full)
  - 劣化なしと同じ尺度での比較は無く、劣化条件の性能低下は定量化されていない
- **実抽出物（Glaucium）**：predicentrine が 9 位→1 位、glaucine が 7 位→1 位。いずれも NMR で確認 — [Rutz et al. 2019](https://www.frontiersin.org/articles/10.3389/fpls.2019.01329/full)
- **著者が挙げた限界** — [Rutz et al. 2019](https://www.frontiersin.org/articles/10.3389/fpls.2019.01329/full)
  - 一致判定は名称の同一性だけで、系統距離は使っていない
  - ISDB-DNP はベンチマークと同じ DNP を使うため有利
  - GNPS ライブラリは SIRIUS の学習データにも含まれる
  - 短縮 InChIKey を使うので立体異性体は区別しない
  - 恩恵を受けるのは主に特化代謝物で、普遍的な分子には効きにくい（liriodenine は 50 以上の起源から報告されている）
  - 起源が不明・誤り・複数の場合の性能は報告していない
- **学会抄録**：SIRIUS、MSFinder、CFM+Tremolo のいずれでも「rank 1 の正解 >50%」 — [Thieme abstract](https://www.thieme-connect.com/products/ejournals/abstract/10.1055/s-0039-3399846)
- **現行 TIMA（R パッケージ）の既定ライブラリ**：LOTUS の structure–organism pairs（README では ">650k pairs"）を使い、SIRIUS v5/v6 と GNPS-FBMN の結果を取り込める — [TIMA GitHub](https://github.com/taxonomicallyinformedannotation/tima)
- LOTUS 本体は参照付きの structure–organism pairs を 75 万件以上収録している — [LOTUS eLife 2022](https://elifesciences.org/articles/70780)
- **現行 TIMA のスコア結合（ソースコード）**：最終スコアは spectral・biological・chemical の重み付き平均。欠損した証拠は NA→0 として扱い、重みの総和で割る（重みの再正規化はしない） — [weights_utils.R](https://github.com/taxonomicallyinformedannotation/tima/blob/main/R/weights_utils.R)
  - 既定の重みは biological 0.400、chemical 0.200、spectral 0.400 — [prepare_params_advanced.yaml](https://github.com/taxonomicallyinformedannotation/tima/blob/main/inst/params/prepare_params_advanced.yaml)
- **biological スコア** — [prepare_params_advanced.yaml](https://github.com/taxonomicallyinformedannotation/tima/blob/main/inst/params/prepare_params_advanced.yaml)
  - 分類階層ごとの点数は domain 0.10 から variety 1.00 まで
  - 試料の生物は単一 taxon なら名前を指定し（既定は null）、複数 taxon ならメタデータファイルで与える
  - 特徴量 1 つにつき保持する試料数の既定は 1
  - ライブラリを特定の分類群に絞る filter は既定で off（例として phylum Streptophyta が書かれている）
- **Biota ドメインの扱い**：「Biota」ドメインの候補（一次代謝など全生物共通）は、試料の分類に関係なく常に最大の biological スコアを受ける — [weight_bio.R](https://github.com/taxonomicallyinformedannotation/tima/blob/main/R/weight_bio.R)
- **chemical consistency（ネットワーク近傍によるコンセンサス再ランキング）の計算手順** — [clean_bio.R](https://github.com/taxonomicallyinformedannotation/tima/blob/main/R/clean_bio.R)
  1. 類似度上位 16 近傍のうち、近傍を 2 つ以上持つ feature だけを対象にする（16 は既定値）
  2. ClassyFire（kingdom/superclass/class/direct parent）と NPClassifier（pathway/superclass/class）の各階層で、consistency = 「候補にクラス X を含む注釈済み近傍の数」÷「注釈済み近傍の数」を求める
  3. consistency に、その feature 自身のクラス X についての最良 bio 重み付けスコアを掛け、最上位のクラスを feature の予測クラスとする
  4. このスコアが minimal_consistency（既定 0.0）未満なら "notConsistent" とする
- **候補への chemical スコアの付与**：予測クラスと一致する階層の点数のうち最大値を与える。点数は ClassyFire が 0.25/0.50/0.75/1.00、NPClassifier が 0.333/0.666/1.000 — [weight_chemo.R](https://github.com/taxonomicallyinformedannotation/tima/blob/main/R/weight_chemo.R), [prepare_params_advanced.yaml](https://github.com/taxonomicallyinformedannotation/tima/blob/main/inst/params/prepare_params_advanced.yaml)
- **応用例（逸話レベル）**
  - 苔類 *Bazzania*：SIRIUS の注釈は信頼できなかったが、TIMA は塩素化大環状 bis-bibenzyl（bazzanin 類）を良好な最終スコアで提示した — [Frontiers Plant Sci 2024](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2024.1470307/full)
  - phyllobilin 類：DB に十分収録されておらず、TIMA は無関係な候補しか返さなかった — [ACS Omega 2025](https://pubs.acs.org/doi/10.1021/acsomega.5c10395)
- **SNAP-MS での観察**：参照ライブラリに無関係な分類群を加えると偽陽性が増えた（全細菌に広げたら、シアノバクテリア限定のファミリーが 1 件偽陽性になった） — [SNAP-MS (Europe PMC full text)](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9852437/fullTextXML)

### Inferences
- **2019 の改善幅はオラクル前提の上限に近い。** 種レベルの起源がオラクル的に既知、かつ候補 DB と起源 DB が同じ DNP、という条件の値である。回収可能な正解の 86〜95% が Top-1 に来ていることから、事前分布が順位をほぼ決めていると考えられる。CASMI 2026 のように起源（植物種）が参加者に開示されないなら、この改善幅は実現できない。
- **使えるのは弱い事前分布だけになりそう。** 「植物（Streptophyta）由来と報告された化合物」のような粗い事前分布は使えるかもしれない。ただし TIMA の既定では上位階層の点数が低く（domain 0.10 から variety 1.00 へ段階的に増える）、効果は小さいと考えられる。この規模の改善を測った文献は見つからなかった。
- **起源不明でもラベル無しで使える部分がある。** 起源が不明でも、TIMA の chemical consistency（近傍候補のクラス一致率）は試料メタデータなしに計算できる。主催者が許可する「テストスペクトル間の類似性の利用」と整合するので、このコンポーネントは CASMI でも利用可能と考えられる。
- **報告済み化合物への偏りに注意。** 分類学的な事前分布は既報の化合物を優遇する（文献バイアス）。テストに新規または稀な化合物が多い場合、事前分布が正解を押し下げるリスクがある。2019 の論文も、普遍的な化合物では効きにくく、未報告の組み合わせは加点されないだけだと述べている。

### Gaps
- TIMA-R の現行既定重み（0.4/0.4/0.2、LOTUS）について、Top-1 改善を数値で示した査読付きベンチマークは見つからなかった。LOTUS 論文でも該当する評価は確認できなかった。
- 起源が不明・誤り・混合の場合の定量評価は見つからなかった。劣化実験の性能比較も同一尺度では報告されていない。
- 改善が species・genus・family のどの階層の一致から来たかの内訳は無い。
- ベンチマーク化合物のうち、複数の起源を持つものの割合は不明。

## KQ3. 検証方法（保留した参照スペクトル、模擬 unknown、実データ）と既知の落とし穴（誤アンカーからの誤り伝播、循環、ネットワーク密度、アンカー既知によるリーク）

### Takeaway
検証デザインは次の 5 系統に分かれる。
- (a) ライブラリスペクトルどうしでネットワークを作り、各スペクトルを未知とみなす（NAP、ChemWalker）
- (b) ライブラリ一致を正解とする（ConCISE、ZODIAC の 4 データセット）
- (c) シードを保留する、または構造が重ならない CV にする（MetDNA3 の 30/70、ZODIAC のアンカー評価）
- (d) target–decoy で FDR を見積もる（NetID、MetDNA3）
- (e) ケーススタディ

楽観バイアスの源は、オラクル的なアンカー、評価データでの閾値調整、DB・学習データの重複である。手法上の落とし穴として定量的に示されているのは次の 3 つ。
- modified cosine は 2 箇所以上の修飾差を結べない
- 真の 1 段階反応ペアの約 40% は MS/MS 類似度が低い
- 特異性の低いエッジで接続性を上げると FDR が 15.8% から 36〜45% に悪化する

### Cited Findings

#### 検証デザインの比較

| 手法 | 正解・評価の作り方 | 楽観バイアスになり得る点 |
|---|---|---|
| NAP | NIST17 の [M+H]+ スペクトル（類縁体を持つ 5,467 件）と CASMI 2016。Fusion は全直接隣接の注釈を使う。構造同一性による偏りを抑えるため cosine<0.7 の部分集合も評価し、結果は「非常に類似」 — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089) | 隣接の正体が既知（オラクル的アンカー）。クエリ自身の正体が除外されたかは本文から不明 — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089) |
| ChemWalker | NIST 555 スペクトル。シードは最大 10% — [ChemWalker](https://pmc.ncbi.nlm.nih.gov/articles/PMC9991053/) | 数値は補遺のみ |
| ConCISE | ライブラリ一致 1,789 件を正解とし、ライブラリを外して実行した結果を照合 — [ConCISE](https://pmc.ncbi.nlm.nih.gov/articles/PMC9786801/) | 閾値は評価にも使ったケーススタディ 1 で経験的に決めた。よく研究された化合物に偏る — [ConCISE](https://pmc.ncbi.nlm.nih.gov/articles/PMC9786801/) |
| ZODIAC | 4 データセットはライブラリ一致（cosine ≥0.7、共有ピーク ≥6）、dendroides は専門家の注釈。アンカー評価は構造が重ならない 10-fold CV — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf) | 正解はライブラリで同定できる化合物に偏る |
| TIMA 2019 | GNPS×DNP で起源が単一種の 2,107 件 — [Rutz 2019](https://www.frontiersin.org/articles/10.3389/fpls.2019.01329/full) | 候補 DB と起源 DB が同じ（循環）。SIRIUS の学習データと重なる |
| SNAP-MS | NIH 純品ライブラリ、自社の海洋細菌ライブラリ（925 prefraction）、公表済み 6 ネットワーク — [SNAP-MS](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9852437/fullTextXML) | 正解の作り方が不明瞭。数値が不整合（31/35 対 194/219） |
| KGMN | 標準品で手動検証した 3,451 ピーク（242 代謝物）。top-3 に入れば正解 — [KGMN](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9636193/fullTextXML) | シードを保留した評価は記載なし |
| MetDNA3 | 20 の Orbitrap データセットで level-1 注釈の 30% をシード、70% を保留して 10 回反復。decoy スペクトルで FDR を推定 — [MetDNA3](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398597/) | in silico ツールとの一致は学習データ重複の恐れ（著者が言及） |
| NetID | 手動正解 314 ピークと、1:1 の target–decoy 分子式 — [NetID](https://pmc.ncbi.nlm.nih.gov/articles/PMC8733904/) | 正確な FDR は図のみ |

#### 誤アンカー・誤り伝播
- NAP の糞便データでは、glucose のライブラリ一致が手動確認の結果「誤り」と判断された。誤ったアンカーが近傍の注釈に影響し得る実例だが、伝播した誤りの量は定量されていない — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- KGMN は再帰的に伝播するが、伝播ラウンド数や距離ごとの精度は報告していない — [KGMN](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9636193/fullTextXML)
- MetDNA3 では top-3 正解率が伝播ラウンドを通じて安定していた（平均 82.4%） — [MetDNA3](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398597/)
- リポジトリ規模の suspect ライブラリには FDR や precision の推定が無い。頻出する質量差 1,350 件のうち説明できたのは 498 件（約 37%）。修飾の位置は一般に不明で、suspect はレベル 3（ファミリー）相当 — [Bittremieux 2023](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10733301/fullTextXML)

#### エッジの特異性と接続性（ネットワーク密度）
- MetDNA3 の decoy 評価（top-3）で、エッジの種類による差が出た — [MetDNA3](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398597/)

| エッジの種類 | 正解率 | FDR | 同じ superclass 内での伝播の割合 |
|---|---|---|---|
| 反応ネットワーク MRN | 73.3% | 15.8% | 80.8% |
| 構造類似ネットワーク SMN | 65.1% | 36.4% | 62.6% |
| 全結合 FCN | 58.3% | 44.5% | 24.9% |

  - FCN は m/z＋RT 照合とほぼ同等
  - 著者の結論は「特異性を伴わない接続性の増加は精度を下げる」
- NAP では n-first を大きくしても必ずしも良くならない。n-first=1 のほうが 5〜20 より「独自に改善した正解」が多く、最適値は「研究ごとに調整し、理想的には手で精査すべき」とされる — [NAP](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006089)
- 分子ネットワークの top-k 近傍数の推奨は、1,000 ノード超で約 15、500 ノード未満で約 5 — [Wang et al. 2024 JASMS](https://escholarship.org/uc/item/4bq907gr)
- ネットワークを間引いて密度を下げると、CAST＋Transitive Alignment の GNPS Classic に対する優位は小さくなる（交差点の N20 が 50→20 に低下） — [Wang et al. 2024 JASMS](https://escholarship.org/uc/item/4bq907gr)
- ZODIAC はエッジの大半を偽とみなす閾値（非ゼロスコアの 95%）を置き、各化合物で最低限の接続数を保証して、孤立や過密を抑えている — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)
- SNAP-MS では組み立てを誤ったサブネットワークで 2 件誤答した。super-cluster や過度に分割されたファミリーも起こり得る。結果グラフが大きすぎるサブネットワーク（ノード 2,000 超、エッジ 10,000 超）は除外されるため、未注釈が増える — [SNAP-MS](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9852437/fullTextXML)

#### スペクトル類似 ≠ 構造的な関係
- modified cosine は、2 箇所以上で修飾が異なる化合物どうしの MS/MS を整列できない — [Wang et al. 2024 JASMS](https://escholarship.org/uc/item/4bq907gr)
  - 例：X–Y と Y–Z は高類似だが、X–Z の cosine は 0.0951。Y を経由する Transitive Alignment で 0.872 に上がった
  - 真菌の argyrotoxin 類の例：0.11/0.07 が 0.55/0.57 に上がった
- Network Accuracy Score（エッジが結ぶ 2 構造の Tanimoto）は、NIH SPAC で N20 が 2〜10 の範囲において、modified cosine の最良値 0.65 に対し MS2DeepScore では 0.84 — [Wang et al. 2024 JASMS](https://escholarship.org/uc/item/4bq907gr)
- KGMN によると、反応で結ばれた代謝物ペアのうち MS/MS dot product が 0.5 を超えるのは約 60% で、残りの約 40% は構造が近くても類似度が低い — [KGMN](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9636193/fullTextXML)
- 前駆体 m/z が同じ（5 mDa 以内）スペクトル集合 8,290 個で 20 種の類似度指標を比べた結果、推奨閾値 0.7 で同一性を完全に分離できたのは約 8%、個別に最適化しても約 20% だった（査読前） — [Turkina et al. 2025 ChemRxiv](https://www.cambridge.org/engage/chemrxiv/article-details/6929724fa10c9f5ca12d55ee)
- cosine、modified cosine、neutral loss の比較では、全条件で modified cosine が最良（ペプチド約 95.5 万対、小分子 1,000 万対） — [Bittremieux et al. 2022 JASMS（WUR 要旨）](https://research.wur.nl/en/publications/comparison-of-cosine-modified-cosine-and-neutral-loss-based-spect)
- Spec2Vec の著者は、Spec2Vec が cosine や modified cosine より構造類似と強く相関すると報告している — [Spec2Vec (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7909622/)

#### adduct・ion 種・異性体
- ZODIAC の dendroides での誤りは 6/6 が [M+H]+ と [M+Na]+ の取り違え。正しい adduct を与えると誤りは 68 倍減った — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)
- NetID は共溶出する異性体を無視し、プロトン化（脱プロトン化）イオンのない adduct は注釈しないか誤注釈し得る — [NetID](https://pmc.ncbi.nlm.nih.gov/articles/PMC8733904/)
- KGMN は、1 つの既知物質から生じた複数の未知異性体を区別できない（isocitrate の例） — [KGMN](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9636193/fullTextXML)
- ion identity networking（IIMN）がデータベース注釈の伝播を改善する、という記述がある（要旨レベルの情報） — [ACS Omega 2025](https://pubs.acs.org/doi/10.1021/acsomega.5c10395)

#### シングルトン・確信度
- MolNetEnhancer では、一致 1 件のシングルトンがクラススコア 1 になり誤解を招く — [MolNetEnhancer](https://pmc.ncbi.nlm.nih.gov/articles/PMC6680503/)
- 孤立ノードへの対処は手法ごとに異なる
  - ConCISE：シングルトンに in silico 注釈を付けない — [ConCISE](https://pmc.ncbi.nlm.nih.gov/articles/PMC9786801/)
  - TIMA：近傍が 2 つ以上ある feature だけで consistency を計算 — [clean_bio.R](https://github.com/taxonomicallyinformedannotation/tima/blob/main/R/clean_bio.R)
- ZODIAC の確信度
  - ZODIAC score は確率としては不正確だが、正誤を分けるのには使える — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)
  - score ≥0.95 の誤答にも明確な原因は見つからなかった — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)
  - 新規分子式の報告では「5 化合物以上と接続」を条件にした。接続の乏しい化合物では、結果が SIRIUS とほぼ同じになるため — [ZODIAC reprint](https://bio.informatik.uni-jena.de/wp-content/uploads/2025/07/LudwigEtAl_DatabaseIndependentMolecularFormula_reprint_2020.pdf)

### Inferences
- **1〜2 編集の関係は modified cosine のネットワークに十分現れないかもしれない。** CASMI テストの「1〜2 回の生合成編集で導ける 30%」（課題前提）のうち、2 編集のペアは modified cosine ベースの分子ネットワークでは結ばれにくいと予想される（2 箇所以上の修飾で整列が破綻するため）。1 編集のペアでも、約 40% はスペクトル類似度が低い可能性がある（KGMN の哺乳類代謝での値を外挿）。したがって、label-free の類似度で実際に有用なエッジを持てる分子は 30% を下回りそうである。学習型の類似度（MS2DeepScore 系）や transitive alignment が有効と考えられる。
- **エッジは特異的なものに限る。** MetDNA3 の比較から、ノードを「似ている」だけで結ぶと FDR が倍以上になる。NP ファミリーでは、エッジを「候補構造のペアが生合成編集（質量差・変換規則）で説明できる場合」に限るなど、特異性を持たせる設計が望ましい。
- **手元の検証デザイン案（250 分子の例示セット）**
  - ラベルを隠したまま全スペクトルでグラフを作り、伝播の前後で分子ごとの Top-1 を比べる
  - 改善だけでなく悪化した件数も報告する
  - 「近縁あり（約 30%）」と「孤立（約 70%）」のサブセットに分けて評価する
  - 学習する重みはファミリー単位で分割した CV で決める
  - エッジをシャッフルした対照（FCN 相当）で、見かけ上の改善を検出する
  - いずれも NAP、MetDNA3、ZODIAC が使ったか、欠いていた要素であり、それらからの推論
- **アンカーのリークに注意。** 例示セットやテストに同一化合物の重複スペクトル（別 adduct や別エネルギー）があると、伝播が「同一性」を運んで改善を過大評価する。NAP が cosine<0.7 の部分集合を、ZODIAC が構造非重複の評価を使ったのと同じ配慮が必要。

### Gaps
- 誤アンカーが何割の近傍を誤らせるかを系統的に測った論文は見つからなかった。
- データセット内でファミリー構造が占める割合（5% と 30% など）と伝播による改善幅の関係を調べた研究は見つからなかった。
- 植物天然物、timsTOF、[M+Na]+ が多い条件での伝播ベンチマークも見つからなかった（ZODIAC の dendroides が最も近い）。

## KQ4. 2022–2026 の深層学習・GNN による transductive 注釈（分子ネットワーク上の GNN 伝播、結合推論）と数値

### Takeaway
GNN でスペクトル分子ネットワーク上のノード単位の構造注釈を transductive に行い、Top-1 を報告した査読付き研究は見つからなかった。最も近いのは MetDNA3（2025）である。GNN で反応関係を予測して知識層を拡張し、伝播自体は学習しない再帰的伝播で行う。保留したシードでの成績は Top-1 68.0%、Top-3 84.4%、Top-10 91.0%。もう一つの流れは、学習型の類似度（MS2DeepScore、DreaMS）でネットワーク構築の精度を上げる方向（Network Accuracy 0.65→0.84）である。

### Cited Findings
- **MetDNA3（Nat Commun 2025, doi:10.1038/s41467-025-63536-6）の知識層**：KEGG、MetaCyc、HMDB の 53,583 代謝物から出発する — [MetDNA3 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398597/)
  - GNN（SMILES のグラフ畳み込み、fingerprint、Tanimoto、反応クラスを入力）で反応ペアを 1,432,469 件予測した。閾値は 0.7
  - BioTransformer で生成した未知物質を加え、765,755 代謝物・2,437,884 反応ペアの MRN を作った
- **MetDNA3 のデータ層とシード** — [MetDNA3 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398597/)
  - データ層のエッジは MS1 15 ppm、予測 RT 30%、MS2 dot ≥0.5 で作る
  - シードは level 1（15 ppm、RT 25 秒、MS2 dot ≥0.8）
  - 再帰的に伝播し、1 feature あたり候補は最大 5 個
  - スコアは m/z 0.25＋RT 0.25＋スペクトル 0.5
- **MetDNA3 の成績**（20 データセット、シード 30% / 保留 70%、10 回反復） — [MetDNA3 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398597/)
  - カバー率 39.9%（MetDNA2）→68.1%
  - top-3 正解率 65.6%→84.4%
  - Top-1/3/10 = 68.0%/84.4%/91.0%、top-3 FDR 15.6%
  - level-3 注釈 12,508 件（既知 9,410、未知 3,098）
  - 計算時間は平均 1,082 分→77 分
  - GNN 自体の AUC は本文に数値が無い
- **MetDNA3 の限界**：評価は哺乳類・ヒトの試料だけ。予測した MRN は実験で検証していない。BioTransformer は哺乳類代謝に偏る — [MetDNA3 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398597/)
- **KGMN（2022、非 DL の多層ネットワーク）**
  - データセットあたり平均 100〜300 の未知代謝物を注釈した
  - S9 インキュベーションの未知物質 175 件の裏付け：標準品と一致 16%、公開ライブラリと一致 30%、in silico ツールの支持 94%
  - NIST 尿の未知物質で、少なくとも 1 ツールが支持した割合：positive 80.9%、negative 86.7%（MetFrag、CFM-ID、MS-FINDER）
  - 「支持」は精度の指標ではない
  - — [KGMN](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9636193/fullTextXML)
- **学習型類似度でネットワークを作る**：特定のベンチマークを除いて再学習した MS2DeepScore でネットワークを作ると、Network Accuracy が 0.84（modified cosine の最良は 0.65）になった。ただし CAST＋Transitive Alignment には及ばない。ClassyFire の「分類一貫性」でも MS2DeepScore は GNPS Classic を上回った — [Wang et al. 2024 JASMS](https://escholarship.org/uc/item/4bq907gr)
- **DreaMS（Nat Biotechnol 2025）**：transformer を数百万の未注釈 MS/MS で自己教師あり事前学習し、2.01 億スペクトルを結ぶ DreaMS Atlas（分子ネットワーク）を公開した。Atlas 上での注釈伝播の精度評価は見つからなかった — [DreaMS](https://www.nature.com/articles/s41587-025-02663-3), [DreaMS docs](https://dreams-docs.readthedocs.io/)
- **ChemWalker（2023）**：グラフ上の random walk による伝播で、深層学習ではない。NAP と同等の性能 — [ChemWalker (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9991053/)
- **関連研究（transductive ではない）**
  - JESTR：スペクトルと分子の共同埋め込みで候補を順位付けする（arXiv 2024） — [JESTR arXiv](https://arxiv.org/pdf/2411.14464)
  - 構造グラフから天然物クラスを分類する GNN（GCN、GAT、GIN）：スペクトルやネットワークではなく構造を入力とする — [CSBJ 2025](https://www.sciencedirect.com/science/article/pii/S2001037025003538)
  - ModiFinder：既知化合物とその修飾類縁体のスペクトルを整列し、原子ごとに修飾部位の尤度を出す。1 編集の類縁体ペアで修飾位置を絞り込む用途。ベースライン（ランダム選択と、真の部位を知るオラクル）と比較している — [ModiFinder bioRxiv](https://www.biorxiv.org/content/10.1101/2024.02.17.580849.full.pdf)

### Inferences
- **公表数値がある「学習型 transductive」は限られる。** 実質的には MetDNA3 型（学習で知識グラフを拡張し、伝播はルールベース）と、学習型類似度によるグラフ構築だけである。テスト集合上で GNN を label-free に学習して構造候補を再ランキングする手法には、NP 領域の公表数値が無い。CASMI で試すなら、手元の例示セットでの検証が必須になる。
- **実装しやすい組み合わせの案。** (1) 学習型類似度で kNN グラフを作る（top-k は小さなネットワーク向けの約 5 から始める）。(2) ZODIAC 型の確率的な結合推論（「該当なし」のダミー候補と、エッジの偽陽性を前提にした閾値を持つ）を使う。(3) NAP Consensus 型の候補間 Tanimoto による適合度か、TIMA 型のクラス一貫性を軽い重みで加える。いずれも各論文の構成要素からの推論であり、組み合わせた効果を示した研究は無い。
- **生合成編集で説明できる候補ペアにエッジを限る。** MetDNA3 の「反応特異的なエッジは FDR が低い」という結果を NP ファミリーに当てはめると、候補構造のペアが既知の生合成変換（水酸化、メチル化、配糖化など）で説明できるときだけ互換性を加点する設計が考えられる。CASMI テストの「1〜2 編集」構造（課題前提）と合致する。

### Gaps
- GNN による transductive 構造注釈（分子ネットワーク上のノード分類や再ランキング）の論文は、2022–2026 の範囲で見つからなかった。検索語を変えて 3 回探したが、ヒットしたのは scRNA-seq など他分野の label propagation だった。
- DreaMS Atlas での伝播精度は見つからなかった。
- MetDNA3 の GNN 単体の AUC は本文に無い。
- 植物や天然物のデータで MetDNA3 を独立に追試した例は見つからなかった。
- Metabolomics 2026 の二部グラフ（代謝物–反応）上の network propagation は、データ探索が目的で注釈精度の数値は未確認 — [Metabolomics 2026](https://link.springer.com/article/10.1007/s11306-026-02529-y)
