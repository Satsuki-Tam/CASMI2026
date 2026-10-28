# MS/MS 構造検索の順位融合・LTR stacking・query gating: 手法と MassSpecGym 期 (2023–2026) のエビデンス

調査日 2026-10-28。対象は、primary ranker と独立した第2ランキングエンジンの融合（MRR@25、候補はスペクトルあたり約 100〜10,000）。数値は原典の表記に従う（MS は hit rate / recall %、IR は MAP / NDCG）。「PDF テキストから表を再構成」と書いた箇所は、pdftotext の出力で列がずれていたため、本文の記述と照合して並べ直したもの。

## Q1. MassSpecGym と後続研究で、forward model スコアと fingerprint/contrastive スコアの融合やモデルアンサンブルは hit@1 / hit@20 / MRR をどれだけ上げたか。どの融合形式が使われたか

### Takeaway
MassSpecGym (MSG) 上で forward model（ICEBERG/GLACIER など）と fingerprint model（MIST など）を late fusion し、hit@k を報告した論文は今回の調査範囲では見つからなかった。MS 側で最も直接的な定量証拠は MSAlign (2026) で、7 個の scorer を validation で重み付けした convex late fusion により、単体最良比で R@1 が +9.5〜+11.8 pt 上がった。MSG では forward model 単体が最も強い（GLACIER の R@1: mass 69.95%、formula 49.88%）。また forward model の知識を合成スペクトル経由で MIST に入れる「蒸留型の融合」で、MIST の hit@1 は 9.57% から 53.76%（leakage-free 設定）に上がった。一方、原理の近い古典 in silico ツール同士の投票融合（CASMI 2016）は held-out でほぼ無効だった。2026 年の監査は 26 本中少なくとも 17 本に leakage・shortcut・bug を指摘しており、論文間の数値比較には強い注意が要る。

### Cited Findings
**ベンチマーク仕様とベースライン**
- MSG の retrieval は候補がスペクトルあたり最大 256。standard トラックは同質量、bonus トラックは同分子式の候補を使う。指標は hit rate@1/5/20 と MCES@1 で、MRR は報告されない。split は MCES 距離 10 未満の分子が fold をまたがないように作られている。 — [MassSpecGym (Bushuiev+, NeurIPS 2024)](https://arxiv.org/html/2410.23326v1)
- standard（質量）トラックの Hit@1/5/20: Random 0.37/2.01/8.22、DeepSets 1.47/6.21/19.23、Fingerprint FFN 2.54/7.59/20.00、DeepSets+Fourier 5.24/12.58/28.21、MIST 14.64/34.87/59.15。bonus（分子式）トラック: Random 3.06/11.35/27.74、Fingerprint FFN 5.09/14.69/31.97、MIST 9.57/22.11/41.12。 — [MassSpecGym Table 5](https://arxiv.org/html/2410.23326v1)

**forward model 単体の retrieval（融合ではないが、第2エンジンの強さの目安）**
- GLACIER 論文 Table 1（MSG、R@1/R@5/R@20）
  - mass challenge: NEIMS(FFN) 8.44/21.43/38.57、FraGNNet 46.64/72.56/83.58、MolSpecFlow 55.32/79.98/89.54（0.1 Da bin のため比較に注意と明記）、ICEBERG 2.0 63.95/83.83/92.56、GLACIER w/ CF 69.95/86.47/93.52
  - formula challenge: FraGNNet 31.93/63.20/82.70、MARASON 34.03/64.04/85.39、ICEBERG 2.0 44.35/73.57/89.45、GLACIER w/ CF 49.88/78.13/90.75
  - — [GLACIER (Wang, Wang, Coley 2026)](https://arxiv.org/html/2606.29161v1)
- GLACIER の contrastive finetuning (CF) の効果は分布で大きく違う。NIST'20 では top-1 が random split で 0.390→0.525、scaffold split で 0.384→0.460 と大きく伸びるが、MSG では 69.69→69.95（mass）、48.49→49.88（formula）にとどまる。NIST'20 の他モデルは MassFormer top-1 0.212（random）/ 0.179（scaffold）、ICEBERG 2.0 0.335 / 0.316。 — [GLACIER](https://arxiv.org/html/2606.29161v1)
- ICEBERG 2025 preprint: 同分子式の PubChem 候補を spectral entropy 類似度で順位付けする。NIST'20 [M+H]+ の top-1 は random split で 25.1%→40.0%、scaffold split で 22.9%→33.5% に改善し、正解の 92% が top-10 に入った。 — [Wang+ 2025 (bioRxiv, PMC12154671)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12154671/)
- 監査論文による formula-known トラックの集計（各論文の報告値、Hit@1/5/20）
  - ICEBERG（forward-model retrieval、collision energy を補完）36.18/60.70/78.83
  - JESTR 11.82/33.48/61.46、MVP 13.96/36.88/68.12、FLARE 22.66/50.00/75.15
  - MIST vMassSpecGym 9.57/22.11/41.12、MIST vFRIGID 53.76/65.32/74.71
  - FRIGID（generative retrieval）45.27/58.30/69.46、DiffMS 32.29/54.36/75.47、MIST vDiffMS 46.42/54.74/66.27
  - DiffMS 系と MIST+MolForge は batching/checkpoint 問題の影響ありと注記されている。
  - — [MassSpecGym in the Wild, Table 3](https://arxiv.org/html/2606.19624v1)
- 同じ「ICEBERG の formula トラック R@1」が、GLACIER 論文では 44.35、監査論文では 36.18（CE 補完版）と食い違う。 — [GLACIER](https://arxiv.org/html/2606.29161v1); [MassSpecGym in the Wild](https://arxiv.org/html/2606.19624v1)

**contrastive / joint-embedding 系**
- JESTR
  - MSG の rank@1 は質量候補で 15.62%（ESP 比 +45.9%、MIST 比 +6.7%）、分子式候補で 11.85%。
  - 候補分子による正則化で rank@1 が平均 +5.72%。
  - pretraining と重複しない subset では SIRIUS 比 +31%、CFM-ID 比 +238%（いずれも相対値）。
  - 4 データセット平均で rank@1–20 が他ツール比 55.5%〜302.6% 上。
  - — [JESTR (Kalia+, arXiv 2411.14464 / Bioinformatics 2025)](https://arxiv.org/pdf/2411.14464)
- GLMR（generative retrieval）は MSG で R@1 68.478 を自己報告しているとされる（SpecBridge 自身は 36.58）。評価設定が論文ごとに異なり、監査の集計にも含まれていないため比較不能として扱う。 — [GLMR](https://arxiv.org/pdf/2511.06259); [SpecBridge](https://arxiv.org/html/2601.17204v1)

**明示的な融合・アンサンブルの定量結果**
- MSAlign の late fusion の構成
  - scorer は 7 個。alignment scorer 4 個は、スペクトル側（binned / DreaMS）と分子側（Morgan / MolDeBERTa）の組合せ。mass scorer 3 個は、precursor から求めた中性質量の ppm 誤差に σ∈{0.01, 0.1, 1} ppm の Gaussian をかけたもの。
  - raw score を単体（simplex）上の convex combination で融合する。z / min-max / rank の正規化は使わず、温度 T で割った加重和をとる。
  - 重みは validation の top-1 accuracy の log-softmax 代理目的を最大化して決め、T は grid で選ぶ。test は評価専用。
  - — [MSAlign (Krzakala+ 2026)](https://arxiv.org/html/2605.19752)
- MSAlign の結果（R@1/R@5/R@20）。候補は PubChem から 10 ppm 以内の同質量分子 K=256。
  - MSG formula split（分子式で分けた独自 split、3 seed）: 単体 47.5/71.3/87.0 → 融合 58.2/80.7/92.8（R@1 +10.7）→ 分子式 oracle filter 追加 60.4/82.1/93.6
  - MSG 公式 MCES split（val/test を入れ替えた 2 通りの平均）: 19.0/41.2/64.9 → 30.8/59.3/82.0（+11.8）→ 37.7/67.2/87.1
  - SpectraVerse: R@1 31.8 → 41.3（+9.5）→ 44.4
  - — [MSAlign](https://arxiv.org/html/2605.19752)
- MSAlign のアブレーション: alignment scorer 追加で +6.9、mass scorer 追加で +3.8、両方で +10.7 とほぼ加法的。mass scorer は単体では弱いと記述されている。 — [MSAlign](https://arxiv.org/html/2605.19752)
- 同じ表の比較対象（formula / MCES / SpectraVerse の R@1）: JESTR 13.9 / 7.9 / 5.4。分子式 oracle を前提とする MIST 41.4 / 16.4 / 22.7、MVP 23.3 / 25.6 / 9.6、FLARE 32.8 / 28.4 / 14.2。 — [MSAlign](https://arxiv.org/html/2605.19752)
- FRIGID: forward model を最終順位付けではなく検証器として使う。
  - 生成候補を分子式で絞り、MIST 予測 fingerprint との Tanimoto で順位付けする。上位 M 候補について ICEBERG がスペクトルをシミュレートし、観測ピークと 20 ppm で照合する（一致 +1、幻覚ピーク −γ）。この結果で再マスキングを誘導する。
  - 10 回の refinement で FRIGID-base 比 6.4〜10.2%（相対）改善。
  - 同じ ICEBERG 誘導を DiffMS に適用すると、NPLIB1 の top-1 が 8.34%→13.33%、top-10 が 15.44%→23.29%。ただし 1 サンプル 1423.30 s かかる（FRIGID は約 41.3 s）。
  - MIST は GLACIER で合成した PubChem スペクトル（NPLIB1 用 2M、MSG 用 4M）で学習している。旧版は test 構造情報を不適切に使った augmentation だったと著者自身が記している。
  - — [FRIGID (2026)](https://arxiv.org/html/2604.16648)
- forward model から fingerprint model への「蒸留型の融合」: MIST を ICEBERG 合成スペクトルで augmentation すると R@1 が 9.57%（augmentation なし）→ 53.76% になる。この設定は ICEBERG を MSG train のみで学習し、augmentation に PubChem のみを使う leakage-free 版。ICEBERG を test 込みで学習すると 67.75%、test 分子を augmentation に含めると 63.85% と水増しされる。 — [MassSpecGym in the Wild, Table 1](https://arxiv.org/html/2606.19624v1)
- ESP: MLP と GNN の forward predictor を、候補順位に基づいて学習した重みでアンサンブルする。NIST20 で学習し PubChem 候補で評価すると、平均順位が MLP 比 23.7%、GNN 比 37.2% 改善した。ただし top-5 では MLP 単体も依然強いと記述されている。 — [ESP (Li+, Bioinformatics 2024)](https://pubmed.ncbi.nlm.nih.gov/39180771/)
- 古典的な固定重みの線形融合の例: 予測 fingerprint 類似度と SIRIUS の分子式スコアを 7:3 で加重して再順位付けしている。 — [Metabolites 2025](https://www.mdpi.com/2218-1989/15/2/132)
- CASMI 2016 (Blaženović+ 2017)
  - challenge セット（n=208）の単体 top-1: MetFrag 25%（53 件）、CFM-ID 14%（29 件）、MAGMa+ 28 件、MS-FINDER 23 件。
  - 投票の重みは各ツールの top-10 感度で、training で決めて challenge に固定適用した。
  - MetFrag+CFM-ID の重み付き投票は training で 22%（69/312、MetFrag 単体 17%）に上がったが、challenge では 47 件（約 23%）で MetFrag 単体を超えなかった。
  - DB 存在や MS/MS ライブラリ一致による「boosting」を加えると challenge で 181/208（87%）。boosting 単体でも 180 とほぼ同じ。
  - training の 93% は、57 通りの組合せから training 上で選んだ値。
  - — [Blaženović+ 2017, J Cheminform](https://pmc.ncbi.nlm.nih.gov/articles/PMC5445034/)

**監査 (2026) が示した retrieval 評価の落とし穴**
- 結果を報告した 26 本中、少なくとも 17 本に結論を左右する評価問題があった（data leakage、shortcut learning、実装 bug と metric divergence）。対策として v1.5 を公開。 — [MassSpecGym in the Wild (abs)](https://arxiv.org/abs/2606.19624)
- 分子式 leakage（Hit@1）: Random は 0.43 だが、正解分子式で候補を絞ると 12.98（約 30 倍）。MIST に MIST-CF の top-1 分子式を与えると 26.64、test で学習した MIST-CF の分子式なら 31.39 / 35.15、正解分子式なら 51.45。 — [MassSpecGym in the Wild, Table 2](https://arxiv.org/html/2606.19624v1)
- 正準化 shortcut（RDKit 正準化を統一する前→後の Hit@1）: DreaMS+ChemBERTa 82.41→6.70、ChemFormer two-stage 63.89→7.60、ChemBERTa SMILES 分類器 99.66→8.2。 — [MassSpecGym in the Wild, Table 3](https://arxiv.org/html/2606.19624v1)
- スペクトルを使わない baseline: PubChem の deposition count 降順に並べるだけで Hit@1 49.98 / Hit@5 54.13 / Hit@20 61.04。正解が「よく知られた天然物や一般的な代謝物」に偏っているため。同時期の研究は、property-matched decoy を使うとこの baseline が「ほぼ random」まで落ちると報告している。 — [MassSpecGym in the Wild](https://arxiv.org/html/2606.19624v1)
- MIST encoder の batching/masking bug で類似度が 0.37→0.52 に水増しされる。 — [MassSpecGym in the Wild (abs)](https://arxiv.org/abs/2606.19624)
- v1.5 の推奨
  - RDKit 正準化を統一する。スペクトルを定数で mask して性能が落ちるかを確認する。
  - pretraining から test の InChIKey を除外する。汎化を主張するなら Tanimoto ≥0.7 または MCES <10 の近縁分子も除外する。simulator は benchmark の split を守る。
  - 分子式を使った結果は formula トラックで報告する。
  - 一致判定は InChIKey-14、統計は 20,000 bootstrap の 99.9% CI。
  - — [MassSpecGym in the Wild](https://arxiv.org/html/2606.19624v1); [HF MassSpecGym v1.5](https://huggingface.co/datasets/roman-bushuiev/MassSpecGym)

### Inferences
- MS 文献で使われた融合形式は次の 6 つ。MSG 系で forward × fingerprint の融合に RRF/Borda を使った定量報告は見つからなかった。
  - (a) validation で重みを学習する raw-score の convex 融合（MSAlign）
  - (b) 固定比の加重和（7:3）
  - (c) 感度で重み付けした投票と metadata boosting（CASMI 2016）
  - (d) forward model を top-M の検証器として回すループ（FRIGID）
  - (e) 候補順位で重みを学習する forward predictor のアンサンブル（ESP）
  - (f) 合成スペクトルによる蒸留（MIST-aug）
- 表現の異なる scorer 同士（spectrum alignment と mass、forward と inverse）の融合は、R@1 が 20〜50% の帯で +10 pt 級の改善を出しうる。似た原理の in silico ツール同士（CASMI 2016）は held-out で改善ゼロだった。どちらも「多様性があるときだけ効く」という IR の知見（Q2）と整合する。
- MSG では forward model 単体の R@1 が fingerprint/contrastive の 3〜5 倍ある。融合重みは等重みにせず強い方に寄せるべきで、LambdaMerge が学習した 0.8/0.2（Q4）と同じ構図になる。
- MSAlign の mass scorer の σ=0.01 ppm は、装置精度（数 ppm）よりはるかに狭い。benchmark の precursor m/z が理論値に近ければ、事実上の分子式 oracle として働いた可能性がある（未検証）。実測の timsTOF データでは、同じ +3.8 pt は期待しにくい。
- 監査が示した「forward model を test 込みで学習すると +10〜14 pt 水増し」は、MSG で学習済みの GLACIER/ICEBERG を第2エンジンにして融合重みを調整するとき、その重みが過大評価される経路そのものである。融合重みは、forward model の学習集合と分子レベルで disjoint な panel で検証する必要がある。内部メモでも enveda-np-examples の 250 分子中 236 が MSG 内にある（内部メモ: C:/Users/satsu/.claude/projects/C--kaggle-CASMI/memory/casmi2026-competition-insights.md）。
- PubChem の人気度 prior（MSG で Hit@1 49.98%）と CASMI 2016 の DB boosting（87%）は、「スペクトルに依存しない第3エンジン」として非常に強い。ただし novel（class 3）化合物には効かない shortcut でもある。融合では独立した feature として扱い、novelty の層別に効果を分けて評価すべき。

### Gaps
- MIST / CSI:FingerID と ICEBERG / GLACIER の late fusion を MSG 上で報告した一次資料は見つからなかった。GLACIER と ICEBERG 2025 は appendix の後半を読めていない。
- CSU-MS2（Anal. Chem. 2025, doi:10.1021/acs.analchem.5c01594）、DreaMS の retrieval 数値、MVP 原著の数値は一次資料から取得できなかった。MVP は監査の集計値だけ。
- MassFormer や CFM-ID と fingerprint の融合を報告した数値は見つからなかった。
- MSG は MRR を報告しないため、hit@k から MRR@25 への正確な換算はできない。
- 監査の appendix にある「MIST bug による retrieval Top-1 の水増し幅」は、抽出結果に食い違いがあり確定できなかった。

## Q2. IR 文献では RRF はいつ score fusion に勝つか。定数 k とリスト深さへの感度、システム間の overlap と多様性の役割、相補性の診断法

### Takeaway
RRF（k=60）は、多数のシステムを未較正スコアのまま教師なしで束ねるときの堅牢な既定値である（Cormack 2009: 最良単体比 +4〜5%、k=20〜100 でほぼ平坦）。一方、2 システムの hybrid で少量でも教師データがある場合は、正規化スコアの convex combination（CC）が全データセットで RRF に勝った。しかも RRF の k は感度が高く、tuning しても他分布に転移しにくい（Bruch+ 2023）。融合が効くのは overlap が小さく、片方にしかない正解が上位に入るときだけである（Beitzel+ 2003）。弱いリストを等重みで混ぜると悪化しうる（LambdaMerge の CombSUM）。

### Cited Findings
- RRF の定義は RRFscore(d)=Σ_r 1/(k+r(d))。k=60 は pilot で固定し、その後は変更していない。著者の直感は「上位ほど重要だが、下位の重要度もゼロにはならない」こと。k は外れ値システムが付けた高順位の影響を抑える。 — [Cormack, Clarke, Büttcher, SIGIR 2009](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- k の感度（pilot: 30 構成の融合、TREC topics 351–400、MAP）: k=0 .2072、10 .2123、20 .2134、30 .2139、40 .2138、50 .2144、60 .2145、70 .2146、80 .2147、90 .2145、100 .2142、500 .2098。比較対象は最良単体 .2016、Condorcet .2074、CombMNZ .2039。著者は「k=60 はほぼ最適だが、選択は決定的ではない」と述べている。 — [RRF](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- TREC 提出 run の融合（MAP、RRF / 最良単体 / Condorcet / CombMNZ。PDF テキストから表を再構成）
  - Robust04: .3686 / .3586 / .3652 / .3575
  - TREC3: .4350 / .4226 / .4256 / .4381
  - TREC5: .3394 / .3165 / .3213 / .3237
  - TREC9: .2830 / .3519（人手介在。自動の最良は .2801）/ .2750 / .2671
  - 平均で Condorcet・CombMNZ・最良単体を 4〜5% 上回り、符号検定で有意。
  - — [RRF](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- LETOR 3 で 7 つの LTR 手法の出力を融合（MAP）: RRF 0.6051、CombMNZ 0.6107（差は有意でない、p≈.2）、Condorcet 0.5917、ListNet 0.5846、LGD 0.5837、AdaRank-MAP 0.5778、RankSVM 0.5737、RankBoost 0.5622。RRF は全単体を上回る（p<.003）。 — [RRF](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- RRF 著者の解釈: RRF は個々のランキング内の多様性をうまく活かす（1〜2 システムが高く順位付けた文書が大きく浮上できる）。CombMNZ は未較正スコアを使うので結果の分散が大きい。 — [RRF](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- Bruch+（BM25 + dense の hybrid）: TM2C2（理論 min-max 正規化 + convex、α=0.8）が RRF（k=60）を全データで上回った（NDCG）。
  - in-domain: MS MARCO 0.454 vs 0.425、NQ 0.542 vs 0.514、Quora 0.901 vs 0.877
  - zero-shot: NFCorpus 0.327 vs 0.312、HotpotQA 0.699 vs 0.675、FEVER 0.744 vs 0.721、SciFact 0.753 vs 0.730、DBPedia 0.512 vs 0.489、FiQA 0.496 vs 0.464
  - — [Bruch, Gai, Ingber (ACM TOIS; arXiv 2210.11934)](https://arxiv.org/abs/2210.11934)
- RRF の k をシステム別（η_Lex, η_Sem）に持たせると、NDCG が大きく振れる。(60,60) / (5,5) / (10,4) の順に、MS MARCO 0.425 / 0.435 / 0.451、HotpotQA 0.675 / 0.693 / 0.621、FEVER 0.721 / 0.727 / 0.649、FiQA 0.464 / 0.470 / 0.482。in-domain で tuning した値は OOD に転移しない。 — [Bruch+ (ar5iv)](https://ar5iv.labs.arxiv.org/html/2210.11934)
- CC では正規化（min-max、z-score、TMM など）の選択は「小さな詳細」とされる。1 クエリ内では、線形正規化の違いは α の取り直しで順位等価になる。ただし TMM は最適 α がデータセット間で安定していた。CC の α は学習データの 5% 未満で収束する。RRF は順位だけを使いスコア分布の情報を捨てる。平滑化版の SRRF は HotpotQA で 0.695（RRF は 0.675）。 — [Bruch+ (ar5iv)](https://ar5iv.labs.arxiv.org/html/2210.11934)
- Fox & Shaw (TREC-2) は CombSUM・CombMNZ を含む 6 種のスコア結合を提案した。CombSUM は最良単体 run より有意に良い（p=3.1e-05）が、クエリごとの最良 run と比べると p≈0.2 で、トピックによっては非常に悪い。CombMNZ は CombANZ と同等か、わずかに上。 — [Fox & Shaw, TREC-2](https://trec.nist.gov/pubs/trec2/papers/txt/23.txt)
- Lee (SIGIR 1997) の overlap 仮説: 融合が効くには relevant overlap が non-relevant overlap より大きい必要がある。CombMNZ は単純で有効な手法として後続研究の標準になった。 — [Beitzel+ 2003 による整理](https://ir.cs.georgetown.edu/downloads/SAC03.pdf)
- Beitzel+ (SAC 2003)
  - 同一システム内の強い 3 戦略の融合: MAP は最良比 −0.72%〜−9.53%（TREC6–10）。overlap 59〜63%、relevant overlap 約 86〜90%、non-relevant overlap 約 69〜73%。
  - 異なるシステムの TREC 上位 3 run の融合: +2.91%〜+12.28%、overlap 30〜43%。
  - 結論: 改善には「片方にしかない relevant 文書が多数、しかも上位に」加わる必要があり、relevant と non-relevant の overlap の差だけでは予測できない。
  - — [Beitzel+ 2003](https://ir.cs.georgetown.edu/downloads/SAC03.pdf)
- 弱いリストを等重みで融合した例（LambdaMerge、Bing）: 元クエリ ORG の NDCG@5 は 0.538。質の低い言い換え RW1（0.422）を CombSUM で混ぜると 0.510 に悪化し、ランダムウォーク確率で重み付けした CombRW は 0.542。言い換えを 5 本にすると CombSUM は 0.521→0.497 とさらに下がる。 — [LambdaMerge (Sheldon+, WSDM 2011)](https://www.microsoft.com/en-us/research/wp-content/uploads/2011/02/SheldonSSC-LambdaMerge-wsdm11.pdf)
- 融合の効果は "chorus effect"（複数システムの一致は relevance の証拠）と "skimming"（各リストの上位から拾う）で説明されることが多い。 — [ProbFuse (Lillis+)](https://arxiv.org/pdf/1409.8518)

**相補性の診断に使われた手法**
- 選択 oracle（各クエリで良い方を選んだ場合の上界、RAPP(Ω)）と、クエリ単位の bubble plot（x: 2 リストの差、y: 融合 − 元）。後者で「両リストの最大値を超えた」クエリを数える。 — [LambdaMerge](https://www.microsoft.com/en-us/research/wp-content/uploads/2011/02/SheldonSSC-LambdaMerge-wsdm11.pdf)
- 失敗集合（正解より上に置かれた候補）の Jaccard と、非対称 overlap J′(ρ,ρ′)。J′ は、ρ を誤らせた候補のうち ρ′ も誤らせる割合。 — [MSAlign](https://arxiv.org/html/2605.19752)
- 深さ X ごとの「片方のリストにしかない relevant 文書」の割合。 — [Beitzel+](https://ir.cs.georgetown.edu/downloads/SAC03.pdf)
- 有意性の確認: run 単位の符号検定（RRF）、20,000 bootstrap による 99.9% CI（MSG 監査）。 — [RRF](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf); [MassSpecGym in the Wild](https://arxiv.org/html/2606.19624v1)

### Inferences
- RRF と CC の使い分けは次のとおり。
  - RRF が有利: システム数が多い、スコアの尺度がばらばら、教師データがない、品質が近い（Cormack の条件）。
  - CC が有利: 2 システム、α を調整する教師クエリがある、スコア分布に情報がある（Bruch の条件）。
  - LETOR 3 では CombMNZ と RRF はほぼ同等だった。
- CASMI は正解が 1 つ（InChIKey14）で MRR@25 で評価される。Beitzel の「片方にしかない上位の relevant」は、ここでは「primary が top-1 を外し、第2エンジンが top-1 を当てる rescue」に相当する。融合を導入する前に次を測れば伸び代を見積もれる。
  - (1) oracle-select MRR（各クエリで max(RR_A, RR_B) をとった平均）と現状 MRR の差
  - (2) top-1 の rescue / loss 件数（A✗B✓ / A✓B✗）
  - (3) 正解順位の Spearman 相関
  - (4) 失敗集合の J′
  - (5) 層別の内訳（novelty class、候補数、adduct、CE 有無）
- 2 エンジンかつラベル付き dev 集合がある CASMI の状況は Bruch の設定に近い。既定は「per-query 正規化（z / min-max / TMM）+ α 1 個の CC」とし、α は grouped CV で MRR@25 を最大化して決める。RRF は強さの違う 2 エンジンを等しく扱ってしまうので、使うなら weighted RRF にし、ベースラインや頑健性チェックの位置付けにとどめるのが妥当。
- per-query z-score は「そのクエリでエンジンがどれだけ自信を持っているか（分布の鋭さ）」の情報を消す。ListStd や top1–top2 margin などは、gating 特徴として別に与えるべき（Q4）。
- 深さについて: Cormack の RRF は全リストを融合しており、Beitzel は上位の unique relevant が鍵だとしている。MRR@25 では上位約 25 位しか効かない。そのため各エンジン top-K（例 K=50〜100）の和集合で融合し、片方にしかない候補には既定値（最下位 rank か最小スコア）を与える実装で足りると推測する（未検証）。内部メモの E2c でも window 40 と 100 で有意差はなかった。

### Gaps
- RRF のリスト深さ（打ち切り深さ）への感度を系統的に測った一次資料は見つからなかった。
- Vogt & Cottrell (1999) "Fusion via a linear combination of scores" は存在を確認しただけで、内容（chorus / skimming / dark horse の定義や数値）は検証できていない。
- Montague & Aslam のスコア正規化・Condorcet-fuse や、Kurland & Culpepper の fusion tutorial などのメタ分析は取得できなかった。

## Q3. Learning-to-rank stacking（他システムのスコアを特徴にする LambdaMART/GBDT、leakage を防ぐ cross-fitting）は単純融合よりどれだけ上か。落とし穴は何か

### Takeaway
教師ありの融合は単純融合を上回るが、適切に重み付けした単純融合との差は小さい（LambdaMerge の NDCG@5: 0.555 vs CombRW 0.542、無重み CombSUM は 0.510）。LTR の出力を RRF で束ねるだけでも各 LTR 単体を上回る（LETOR 3）。MS では学習 reranker（MS2Query の RF、MSAlign の validation 重み）がはっきりした利得を出している。最大の落とし穴は、(1) in-sample の level-one 予測、(2) 融合パラメータの validation への過適合、(3) base model 由来の leakage、(4) スペクトルに依存しない shortcut 特徴、の 4 つ。

### Cited Findings
- LambdaMerge は 2 つのネットワークの混合で NDCG を直接最適化する。scoring net は各リストの文書特徴（スコア・順位）を受け取る。gating net はリスト単位の品質・ドリフト特徴（ListMean/Std/Skew、Clarity、RAPP、IsRewrite、RewriteRank、RewriteScore、Overlap@N）を受け取る。評価は 2,303 クエリ（Bing）。 — [LambdaMerge](https://www.microsoft.com/en-us/research/wp-content/uploads/2011/02/SheldonSSC-LambdaMerge-wsdm11.pdf)
- LambdaMerge の結果（NDCG@5 / @10、PDF テキストから表を再構成）: ORG 0.538/0.524、RW1 0.422/0.387、CombSUM 0.510/0.486、CombRW 0.542/0.516、RAPP-L（教師ありで 1 本を選ぶ）0.534/0.524、λ-Merge 0.555/0.539、RAPP(Ω)（選択 oracle）0.556/0.530。λ-Merge と oracle の NDCG@5 の差を除き、全て p<0.01。 — [LambdaMerge](https://www.microsoft.com/en-us/research/wp-content/uploads/2011/02/SheldonSSC-LambdaMerge-wsdm11.pdf)
- 言い換え 5 本の場合（1,872 クエリ）: ORG 0.550/0.535、CombSUM 0.497/0.455、CombRW 0.555/0.524、RAPP-L 0.550/0.535（言い換えを一切信用しないことを学習し、ORG と一致）、λ-Merge 0.563/0.548、oracle 0.587/0.545。λ-Merge は NDCG@10 で選択 oracle を上回った。 — [LambdaMerge](https://www.microsoft.com/en-us/research/wp-content/uploads/2011/02/SheldonSSC-LambdaMerge-wsdm11.pdf)
- RRF で LTR の出力を束ねたメタ学習: LETOR 3 で 0.6051、最良単体 ListNet は 0.5846（+0.02、4%）。 — [RRF](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- stacking の原則（Breiman）: level-one データは CV 予測から作る（訓練 fit をそのまま使うと過適合する）。重みは非負制約付き最小二乗で求める。leave-one-out より 10-fold CV の方が有効だった。 — [Breiman 1996 (tech report 367)](https://statistics.berkeley.edu/sites/default/files/tech-reports/367.pdf)
- 非負制約について: Breiman の回帰では、単一最良モデルの選択を上回るために重要だった。分類では必須ではないという後続分析がある。 — [Ting & Witten 1999](https://arxiv.org/pdf/1105.5466)
- MS2Query: MS2Deepscore で上位 2,000 件を前選択し、5 特徴の random forest で Tanimoto を予測して再順位付けする。閾値 0.633 で analogue test set の recall は 35%、そのときの平均 Tanimoto は 0.67（modified cosine は同じ recall で 0.45）。 — [MS2Query (de Jonge+, Nat Commun 2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10060387/)
- MSAlign は融合重みと温度の選択の 2 段とも validation で行い、test は評価専用にしている。著者は、validation を calibration と checkpoint 選択の両方に使っていることが大きな変動要因だと述べている。 — [MSAlign](https://arxiv.org/html/2605.19752)
- 融合パラメータの過適合例: MS MARCO で tuning した RRF (10,4) は in-domain で 0.451 だが、HotpotQA で 0.621、FEVER で 0.649 となり、既定値 (60,60) の 0.675 / 0.721 を下回った。 — [Bruch+](https://ar5iv.labs.arxiv.org/html/2210.11934)
- 選択バイアスの例: CASMI 2016 で、57 通りの組合せから training 上で選んだ組合せは training 93% だったが、challenge では 87%。 — [Blaženović+ 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5445034/)
- base model 由来の leakage: ICEBERG を test 込みで学習すると R@1 が +14 pt（53.76→67.75）。test で学習した MIST-CF の分子式を使うと +4.8〜8.5 pt（26.64→31.39 / 35.15）。 — [MassSpecGym in the Wild](https://arxiv.org/html/2606.19624v1)
- 識別的な finetuning は in-distribution でより効く: GLACIER の CF は NIST random split で +13.5 pt、MSG では +0.3〜1.4 pt。 — [GLACIER](https://arxiv.org/html/2606.29161v1)

### Inferences
- 推奨する stacking 手順は次の 4 段。
  - (1) 分子（scorer key）単位の grouped K-fold で、全 base エンジンの OOF スコアを作る。第2エンジンが事前学習済みの forward model なら、その学習分子と disjoint な評価分子に限定する。
  - (2) meta-ranker は LambdaMART（lambdarank、query group はスペクトルまたは分子）。特徴は各エンジンの raw / per-query z / rank / 1/(k+rank) / top1–top2 margin / ListStd、両エンジンの top-1 一致フラグ、候補の provenance、クエリ文脈（adduct、CE 有無、候補数、precursor m/z）。エンジンスコアには monotone 制約をかける（Breiman の非負制約に相当）。
  - (3) fusion-train / tune / final-eval を分けた nested 評価にする。
  - (4) 比較対象は CC（α 1 個）と weighted RRF とし、paired bootstrap の CI で比べる。LambdaMerge の結果からみて、CC に対する上積みは小さいと見込むのが妥当。上積みが CI 内なら単純な CC を採る。
- クエリ間の calibration: GBDT は raw score の絶対値をクエリ横断で比べてしまう。per-query 正規化した特徴（z、rank、margin）を併用し、raw score 単独に依存させない。
- 人気度 prior のような shortcut 特徴は、meta-ranker に入れると最強の特徴になりうる（MSG で Hit@1 49.98%）。novelty 層別の評価、特徴除外アブレーション、spectrum mask テスト（監査の推奨）で依存度を確認する。

### Gaps
- MSG 期の MS retrieval で、forward と fingerprint のスコアを GBDT/LambdaMART で stacking し、単純融合と比べた論文は見つからなかった。
- LC-MS2Struct（保持時間順序と MS2 スコアを SSVM で統合）と、Yahoo! LTR Challenge のアンサンブル報告は確認していない。
- Kaggle の retrieval コンペの write-up は今回調べていない（二次資料の扱いの予定だった）。

## Q4. スペクトル同定や類似の検索タスクで、クエリの種類や確信度に応じてリストを選ぶ query-type gating の例と数値はあるか

### Takeaway
クエリごとにどちらか一方を選ぶハードな gating は脆い。LambdaMerge では教師ありの選択器（RAPP-L）が元リスト単独すら超えなかったのに対し、soft gating 付きの融合（λ-Merge）は選択 oracle と同等以上だった。有効だった gating 特徴は上位の一致（Overlap@1）と出所（元クエリか言い換えか）で、スコア分布の統計（Clarity、ListMean/Std/Skew）は単独ではわずかな効果しかなかった。MS では、確信度に基づいて採否を決めるゲートとして COSMIC（top1 と他候補のスコア差を含む SVM）、MS2Query（RF 閾値）、SingleFrag（top1–top2 差）が確立している。ただし、forward model と fingerprint をクエリ別に切り替えて数値を示した MS 論文は見つからなかった。

### Cited Findings
- LambdaMerge の gating 分析
  - Clarity、ListMean、ListStd、ListSkew などの従来の性能予測特徴は、単独では平均 gating に対しごく小さな改善しか生まなかった。
  - overlap 特徴は上位に焦点を当てるほど良く、Overlap@1 が最良だった。
  - 最良の単独特徴は IsRewrite（元クエリか否か）。学習された重みは、元 + 言い換え 1 本で (0.8, 0.2)、5 本で (0.63, 0.07×5)。
  - 弱い ListStats 特徴は、束ねて使うと有益だった。
  - — [LambdaMerge](https://www.microsoft.com/en-us/research/wp-content/uploads/2011/02/SheldonSSC-LambdaMerge-wsdm11.pdf)
- 選択と融合の比較: Table 2 では RAPP-L 0.534 < ORG 0.538（NDCG@5）、λ-Merge 0.555 ≈ oracle 0.556。融合は「各クエリで 2 リストの最大値を超える」点を持ち、これは選択では原理的に届かない。 — [LambdaMerge](https://www.microsoft.com/en-us/research/wp-content/uploads/2011/02/SheldonSSC-LambdaMerge-wsdm11.pdf)
- Balasubramanian & Allan: 予測性能に基づいて 2 つの ranker からクエリごとに良い方を選ぶと、LETOR 3.0 GOV2 で各単体を上回った（LambdaMerge 論文中の引用。数値は未確認）。 — [LambdaMerge](https://www.microsoft.com/en-us/research/wp-content/uploads/2011/02/SheldonSSC-LambdaMerge-wsdm11.pdf)
- COSMIC: CSI:FingerID の top-1 に確信度を付ける。kernel density の P 値と、特徴の向きを固定した SVM を使い、他候補とのスコア差や説明できたピーク強度などを特徴にする。再順位付けはしない。17,400 実験から、ライブラリ未収載の高確信注釈 1,715 件を得た。 — [Jena 研究室](https://bio.informatik.uni-jena.de/2021/10/cosmic-has-appeared-in-nature-biotechnology/); [Hoffmann+ Nat Biotechnol 2021](https://doi.org/10.1038/s41587-021-01045-9)
- MS2Query: RF スコアの閾値 0.633 で analogue の採否を決める（recall 35%）。運用指針は、recall 重視なら低い閾値、信頼性重視なら高い閾値。 — [MS2Query](https://pmc.ncbi.nlm.nih.gov/articles/PMC10060387/)
- SingleFrag: top1 と top2 のスコア差は、top-1 の信頼性について特に情報量が多い。 — [SingleFrag (Brief Bioinform 2025)](https://academic.oup.com/bib/article/26/4/bbaf333/8196360)
- プロテオミクスでの複数 search engine の統合: iProphet は複数エンジンの結果を統合し、PeptideProphet や Percolator と比べて、一定 FDR 下で正しく同定されるペプチド数を増やす。2013 年の MCP レビューは、エンジンごとに得意な PSM の部分集合が違うことを統合の根拠にしている。 — [iProphet (Shteynberg+ 2011)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3237071/); [MCP 2013 review](https://pmc.ncbi.nlm.nih.gov/articles/PMC3769318/)
- CASMI 2016: boosting を入れると、in silico ツールの選択は「ほぼ無関係」になった。 — [Blaženović+ 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5445034/)
- MSAlign: 失敗集合の大きさは heavy-tailed で、R@1 が 47.5% でも正解より上に置かれる候補は平均 9.7 個ある。 — [MSAlign](https://arxiv.org/html/2605.19752)

### Inferences
#### Gating の設計
- ハードな選択より soft gating を使う。小さな gating（例: α(query)=σ(w·z_query)）か、LambdaMART に文脈 × スコアの交互作用を学ばせる形にする。層（候補数の bin、adduct 系、CE 有無、novelty の代理指標としての最近傍ライブラリ類似度など）ごとの α を CV で推定し、全体の α に向けて shrinkage する。
- 証拠が最も強い gating 特徴は次の 4 つ。分布統計は単独ではなく束で使う。
  - 両エンジンの top-1 一致（Overlap@1）
  - 各エンジンの top1–top2 margin（SingleFrag、COSMIC）
  - 出所（IsRewrite に相当するもの、つまり候補 pool の provenance）
  - スコア分布の統計（束で使う）
- gate に投資する前に、oracle-select と「α 固定」の差で上界を測る。LambdaMerge の RAPP-L のように選択器の精度が低いと、単独エンジンより悪化する。

#### CASMI 2026 向けの統合レシピ（推論）
1. 評価基盤: scorer key による分子単位の grouped split、forward model の学習分子と disjoint な評価 panel、paired bootstrap CI（MSG 監査は 20,000 resample の 99.9% CI を推奨）。
2. 事前診断: 単体 MRR@25、oracle-select MRR、top-1 の rescue/loss、失敗集合の J′、層別の内訳。oracle-select の伸び代が小さければ融合には投資しない。
3. 第一候補: 各エンジン top-K の和集合で per-query z（または min-max / TMM）をとり、α 1 個の CC で融合する。α は grouped CV で MRR@25 を最大化して決める（Bruch によれば少量のデータで収束する）。
4. 頑健性ベースライン: weighted RRF（k∈{10,30,60,100}、エンジン重み付き）と等重み RRF。CC が CI 内で RRF に勝てなければ、RRF か単純平均で十分。
5. 第二段: LambdaMART の meta-ranker（OOF スコア、monotone 制約、margin・一致・provenance・クエリ文脈の特徴）を nested 評価で CC と比べ、CI を超えて改善したときだけ採用する。
6. Gating: 層別 α と shrinkage、または soft gating。ハードな切替は選択器の精度が高い場合に限る。
7. leakage / shortcut の防止: 正準化を統一し、spectrum mask テストを行う。分子式や CE などのメタ情報の出所を確認する。人気度 prior への依存度は novelty 層別で報告する。

### Gaps
- forward model と fingerprint/contrastive をクエリ別に切り替える（あるいは MoE gating する）MS 論文の数値は見つからなかった。
- iProphet や Percolator の具体的な改善率（%）、Balasubramanian & Allan の数値は取得できなかった。
- COSMIC の FDR ごとの正答率曲線は取得できなかった。
