# 近縁既知化合物からの候補構造生成と順位付け（biotransformation / de novo 生成）

調査日: 2026-10-28（システムクロック: 2026-10-28 14:09 JST）。
対象: DB に存在しない構造を「近縁既知構造の編集」または「スペクトル条件付き生成」で提案する手法と、その候補をスペクトルに対してどこまで順位付けできるか。

---

## Q1. ツールと研究: 真の unknown の何割が到達可能で、順位付け後の Top-1/Top-k はどれだけか

### Takeaway
「到達率（候補集合に真構造が入る率）」は編集ベース・生成ベースいずれでも 30–70% 程度まで到達できる一方、**順位付け後の Top-1 は一桁〜25% に落ちる**という非対称性が文献全体で一貫している。最も直接的に比較可能な事例は FOAM（formula 固定の遺伝的アルゴリズムで構造を編集）で、NIST'20 探索中に真構造に **68.1%** 到達するが、3世代後に Top-1 に置けるのは **11%**、Top-10 で **31%** に過ぎない（ユーザーの「54% 生成 / 1/4 を rank 3」という観測とほぼ同型の現象）。

### Cited Findings

**編集ベース（反応規則 / 誘導体化）**

- BioTransformer 1.0: 単段ヒト代謝（40化合物）で TP 188 / FP 198 / FN 26、**precision 0.49, recall 0.88**（Meteor Nexus は Equivocal 0.35/0.71、Plausible 0.56/0.45、Probable 0.59/0.13）。ヒト＋腸内細菌（20化合物）precision 0.69/recall 0.87。CYP450（60化合物）BioTransformer 0.46/0.90 vs ADMET Predictor 0.47/0.61。EAWAG-BBD/PPS の 15 反応・18 代謝物を 100% 再現 — [BioTransformer, J Cheminform 11:2 (2019)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6689873)
- BioTransformer の規則数は本文で 797、Table 1 のモジュール別合計は 1,147 と**論文内で不一致**（EC-based 408 / CYP450 163 / human gut 201 / Phase II 74 / environmental 301）。v1 では全反応パターンが同一尤度のため**反応スコアによる順位付けを持たない** — [同](https://pmc.ncbi.nlm.nih.gov/articles/PMC6689873)
- BioTransformer の MetID モジュール（BMIT）は親構造＋中性質量を入力し、**質量一致（既定 0.01 Da）または組成式一致のみ**でマッチし、MS/MS 予測もスコア順位付けも行わない。エピカテキン事例: 260 中性質量に対し 37 候補/20 質量、既報代謝物 39 を提案、9 質量に対する 15 候補は未報告。2段抱合のため既知代謝物 10 個を取りこぼし、isobaric 候補は区別不能 — [同](https://pmc.ncbi.nlm.nih.gov/articles/PMC6689873)
- GLORYx: テストセット 37 親化合物 / 既知代謝物 136 で **recall 0.77, precision 0.061（予測 1,724 件、TP 105）**、SyGMa は recall 0.68, precision 0.12（予測 800 件、TP 93）。すなわち GLORYx は親化合物あたり約 47 候補、SyGMa は約 22 候補（予測数/親数からの算術、論文は per-parent を報告せず） — [GLORYx, Chem Res Toxicol (2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7887798)
- 独立比較（新規精神活性物質）では **SyGMa が最も網羅的（437 代謝物）**、MetaTrans が最少（61）。「単独で完全な予測を与えるツールはない」 — [Identifying metabolites of NPS using in silico prediction tools](https://pmc.ncbi.nlm.nih.gov/articles/PMC12198081/)
- Ridder et al. 2014: 腸内分解＋ヒト代謝の反応規則を緑茶 75 成分に適用し **27,245 化合物の仮想ライブラリ**を構築、尿試料で既報 74 代謝物に一致、**26 の新規由来代謝物を putative 同定**。注釈された代謝物の **77% は PubChem に存在しない** — [Anal Chem 86:4767–4774 (2014), doi:10.1021/ac403875b](https://research.wur.nl/en/publications/in-silico-prediction-and-automatic-lcmsn-annotation-of-green-tea-)
- 同グループの緑茶抽出物（2013）では既報 85 化合物の fractional rank の中央値 3.5、第3四分位 7.5 — [同 search 経由](https://research.wur.nl/en/publications/in-silico-prediction-and-automatic-lcmsn-annotation-of-green-tea-)
- MINE（Jeffryes 2015）: 198 の BNICE 一般化規則で KEGG を拡張し **571,368 化合物（43倍、PubChem 収載率 6.99% = 93% が PubChem 外）**。667 MassBank スペクトルに対し **98.6% で「候補を提案できた」が、これは候補が 1 つ以上返った率であり正解包含率ではない**。正解包含率は KEGG 68.6% / KEGG MINE 66.8% / PubChem 89.8%、候補数中央値は 3 / 46 / 1,714.5 — [MINEs, J Cheminform (2015)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4550642)
- MINE は in silico フラグメンテーション（CFM-ID/MetFrag）を使わず、KEGG ゲノム所属・logP・Kováts RI で絞り込むのみ。未同定 feature では EcoCyc MINE が 493 feature 中 **132 に候補を提案**（従来法は 30）、うち 79 が BNICE 予測代謝物と一致 — [同](https://pmc.ncbi.nlm.nih.gov/articles/PMC4550642)
- MINE 2.0（Bioinformatics 2022）は 17 倍規模で、未注釈ピークに一致する化合物が 40% 増加 — [Bioinformatics 38(13):3484](https://academic.oup.com/bioinformatics/article/38/13/3484/6589885)
- ATLASx: BNICE.ch の **490 双方向一般化規則**で bioDB 化合物間に約 160 万の生体内変換、さらに化学 DB のみに存在する分子への 360 万反応を予測（総計 500 万反応超・約 200 万化合物） — [Nat Commun 13 (2022), doi:10.1038/s41467-022-29238-z](https://pmc.ncbi.nlm.nih.gov/articles/PMC8943196/)
- KGMN/MetDNA2: BioTransformer 1.0.8（EC-based、2段）を KEGG 基質に適用し、**193 反応・114 酵素で 50,471 unknown を生成**、反応ペア Tanimoto > 0.7 で絞って 41,336 ノード（既知 6,478 / unknown 34,858）・52,137 エッジ。うち 405 が known-unknown（HMDB 収載）、34,453 が unknown-unknown。175 の注釈 unknown のうち **28 (16%) を標準品、53 (30%) を公開ライブラリ、165 (94%) を in silico ツールで裏付け** — [KGMN, Nat Commun (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9636193/)
- COSMIC の仮説ライブラリ事例: SmiLib で **322 scaffold × 91 building block → 28,630 の仮説胆汁酸抱合体**を生成し検索。PubChem 既知を除いた上位 12 注釈を手動検証し **90% 超が正しい**、2 件（Phe-CDCA, Trp-CDCA）を合成標準品で確認（abstract は「9 構造を手動評価、2 構造を標準品で確認」と記載）。17,400 実験への適用で **スペクトルライブラリに無い高信頼注釈 1,715 件** — [COSMIC, Nat Biotechnol (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8926923/)
- VarQuest（既知 PNP に単一の質量シフト ≤ 300 Da を任意位置に許す「1編集」探索）: GNPS 全体・FDR 5% で DEREPLICATOR 14,746 PSM / 420 variant / 420 PNP（143 family）に対し **179,448 PSM / 19,619 variant / 2,025 PNP（648 family）**（PSM 10倍超、PNP 約5倍）。648 family は DB の 1,582 family の **41%**。648 のうち無修飾の親が検出されたのは 143 のみ = **78% は分子ネットワークでは到達不能** — [VarQuest, Nat Microbiol (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5951390)
- 近傍 suspect ライブラリ（注釈済み近傍＋質量オフセットで「構造は family レベルのまま」注釈を伝播）: 1,335 公開プロジェクト・5.21 億スペクトルから **87,916 suspect スペクトル**。GNPS 既定ライブラリのみでのマッチ率平均 5.5%（中央値 3.6%）→ suspect 追加で **9.3%（中央値 6.4%）**、約 1,900 万マッチ増。後から登録された 72 データセットでも 5.7% → 8.9%。試料種別では food で 1.7±0.3 倍、environmental で 3.0±0.7 倍 — [Nat Commun 14:8488 (2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10733301/)

**de novo 生成（スペクトル条件付き）**

- MSNovelist（Stravs 2022）: GNPS 3,863 スペクトルで**正解を候補中に 45%、rank 1 に 25%**。同条件の PubChem DB 検索（CSI:FingerID）は **top-1 39%**。fingerprint を入力しない naive generator は 31%/17%、RNN スコアのみの順位付けは 19% が top-1。正しい組成式の valid SMILES は 99.5%。GNPS-OK 部分集合（n=1,507、正解が DB にある系）では 68% 到達 / 61% top-1。CASMI 2016（n=127）で 57% 到達 / 26% top-1、CASMI-OK（n=47）で 74%/64% — [MSNovelist, Nat Methods 19:865–870 (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/)
- MSNovelist の beam 幅は既定 k=128。**MSNovelist 候補 16 個が naive 候補 top-128 を（CASMI 全体到達率以外の）全指標で上回った** — [同](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/)
- 既知組成式を仮定した de novo ベンチマーク（FRIGID 論文 Table 1、Top-1 / Top-10 exact-match accuracy）:
  - **NPLIB1**: Spec2Mol 0.00%/0.00%、MADGEN 2.10%/2.39%、MIST+Neuraldecipher 2.32%/6.11%、MIST+MolForge 2.24%/5.11%、MIST+MSNovelist 5.40%/11.04%、MS-BART 7.45%/10.99%、DiffMS 8.34%/15.44%、FRIGID-base 19.80%/24.41%、**FRIGID 25.03%/33.37%**
  - **MassSpecGym**: MIST+MSNovelist 0.00%/0.00%、Spec2Mol 0.00%/0.00%、MIST+Neuraldecipher 0.00%/0.00%、MS-BART 1.07%/1.11%、MADGEN 1.31%/1.54%、FOAM(DiffMS+PubChem) 1.50%/10.28%、DiffMS 2.30%/4.25%、MIST+MolForge 10.73%/14.48%、FRIGID-base 16.09%/18.19%、**FRIGID 18.29%/22.00%** — [FRIGID, ICML 2026 (PMLR 306:8948–8969)](https://proceedings.mlr.press/v306/bohde26a.html)
- MADGEN（scaffold 条件付き生成）は **scaffold 予測精度（SPA）が律速**: 予測 retriever の SPA は NIST23 57.8% / CANOPUS 37.9% / MassSpecGym 34.8% で Top-1 はそれぞれ 10.3% / 1.0% / 0.8%。**oracle scaffold（SPA 100%）なら Top-1 49.0% / 8.9% / 18.8%、Top-10 65.5% / 14.7% / 38.6%** — [MADGEN, ICLR 2025 (arXiv:2501.01950)](https://arxiv.org/html/2501.01950v1)
- MIST+MolForge は MassSpecGym Top-1 28.27% / Top-10 36.11%、真の fingerprint を与えると 46.00%/59.28%、MassSpecGym のみ（約 17k 化合物）で学習すると 0% と報告 — [arXiv:2508.04180v3](https://arxiv.org/html/2508.04180v3)。ただし FRIGID 著者は再実装でこの数値を再現できず、**MIST の batched inference のバグ（padding への attention mask が −inf でなく 0）による leakage** と結論（後述 Q4） — [FRIGID](https://proceedings.mlr.press/v306/bohde26a.html)
- DualLGD: NPLIB1 Top-1 **34.37%**、MassSpecGym **23.89%**（「従来 SOTA の約3倍」と主張、Top-10 は abstract に無し、査読前） — [arXiv:2605.07048](https://arxiv.org/abs/2605.07048)
- MARLIN（組成式を一切使わない設定）: NPLIB1 Top-1 **16.9%**（IEEE BIBM 2026 採択版の拡張、査読前） — [arXiv:2607.04774](https://arxiv.org/abs/2607.04774)
- Test-time tuning（事前学習済み de novo モデルを推論時に実験データへ適応）: MassSpecGym Top-1 **3.16%**、NPLIB1 **12.88%**、ベースライン比 +27% / +67%、平均 Tanimoto 相対 +64% / +83%。「正解を当てられない場合でも生成物は化学的に有意味」と主張 — [arXiv:2510.23746](https://arxiv.org/abs/2510.23746v2)
- MS2Mol（Enveda）: 主要 DB に無い天然物 **226 化合物の EnvedaDark** ベンチマークで「close-match 閾値内 21%、meaningful similarity 62%」、confidence scorer 上位 10% では 98%（meaningful）/63%（close match）。**プレプリントの自己報告で、閾値の定義と独立再現が確認できていない** — [MS2Mol, ChemRxiv (2023)](https://chemrxiv.org/engage/chemrxiv/article-details/6492507524989702c2b082fc)（本文は 403 で取得不可、数値は検索スニペット経由＝二次情報）
- **FOAM（本件に最も近い設計）**: 組成式を固定した graph genetic algorithm で seed 構造を編集し、ICEBERG 前方モデルで採点。NIST'20 では **探索中に真構造に 68.1% 到達、到達例の 50.6% は最初の 3 世代以内**。しかし **3 世代後の Top-1 は 11%、Top-10 は 31%**。best-of-10 Tanimoto は seed 0.52 → 2 世代後 0.62 — [FOAM, arXiv:2602.07709](https://arxiv.org/html/2602.07709v1)
- FOAM の到達率は seed の近さに強く依存: 最近傍 seed の類似度 0.2–0.4 のとき Top-10 exact match 8.1%、0.4–0.6 のとき **31.5%**。真構造の予測スペクトル類似度が 0.8 以上なら Top-10 成功率 **53.4%** — [同](https://arxiv.org/html/2602.07709v1)
- FOAM を MassSpecGym で DiffMS 出力＋PubChem 同組成式構造を seed にして回すと **Top-1 は 2.30% → 1.50% に悪化する一方、Top-10 は 4.25% → 10.28% に倍増以上**。真構造への到達は 1 世代後に 33%（DiffMS サンプルのみでは 5.8%） — [同](https://arxiv.org/html/2602.07709v1)

### Inferences
- 「生成（到達）」と「選抜（順位付け）」の落差は手法系統を問わず再現する構造的な現象で、ユーザーの観測（54% 生成 / その 1/4 を rank 3）は FOAM の 68.1% → Top-10 31% とほぼ同じ比率。したがってボトルネックは編集集合の設計ではなくスコアリング側にあると見るのが文献と整合的。
- FOAM の「seed 類似度 0.4–0.6 で Top-10 が 4 倍」は、neighbour の選び方（spectral analog の質）が編集ベース生成の実効精度を支配することを示す。CASMI 2026 で family 構造を持つテストセットなら、neighbour 選定の精度向上が候補生成の多様化よりリターンが大きい可能性が高い。
- MADGEN の oracle-vs-predicted scaffold の差（MassSpecGym 0.8% → 18.8%）は「正しい親/scaffold を与えられれば生成は解ける」ことを示し、逆に親の選択誤りがそのまま最終精度を決めることを意味する。
- Top-10 を伸ばす手法（FOAM）と Top-1 を伸ばす手法（FRIGID）は別物であり、競技指標が Top-1 相当（CASMI 2026 の scorer は 1 構造）なら FOAM 型の「候補プールを広げる」戦略単独では逆効果になりうる（FOAM の MassSpecGym Top-1 低下が実例）。

### Gaps
- 「編集回数 1–2 回で真構造に到達する率」を天然物で直接報告した査読論文は見つからなかった。FOAM は編集回数ではなく世代数・oracle 呼び出し数で報告し、VarQuest は 1 修飾のみ、suspect ライブラリは質量オフセットのみで構造を確定しない。
- MetWork（Beauxis & Genta-Jouve, Bioinformatics 35(10):1795–1796, 2019, doi:10.1093/bioinformatics/bty864）は **定量評価が公表されていない**（Application Note で、abstract にも精度指標なし）。到達率・Top-k の数値は引用できない。
- MS2Mol の「close match」「meaningful similarity」閾値の定義と独立評価が確認できなかった。
- MINE/ATLASx を MS/MS 採点と組み合わせた Top-k は報告されていない（MINE は候補提示率のみ）。

---

## Q2. 生成候補のスコアリング・順位付け方式、特に同一編集の位置異性体の識別

### Takeaway
実運用で最も効いているのは **(a) 予測 fingerprint との類似度（modified Platt / Tanimoto）による一次順位付け**と **(b) 前方スペクトル予測（ICEBERG 等）による再採点**の二段構成。ただし**位置異性体の識別は前方モデルの弱点が明確に実測されており**、CFM-ID は regioisomer に対してほぼ同一のスペクトルを出すためランダム以下（ModiFinder 比較）。位置特定は「候補を順位付ける」より「シフトしたピークから修飾部位の原子スコアを出す」方式（ModiFinder / ICEBERG の部位局在）のほうが成績が良い。

### Cited Findings

**fingerprint ベースの一次順位付け**
- MSNovelist は LSTM の RNN スコア（系列対数確率）で生の出力を並べたうえで、**最終順位は query fingerprint に対する modified Platt score** で決める。これが RNN スコア単独より多くの正解を与える（RNN 単独の top-1 は 19% に対し最終 25%） — [MSNovelist](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/)
- MSNovelist の「最良の誤り候補」の Tanimoto 中央値は MSNovelist 0.80、学習セット最良 0.76、DB 最良 0.84、RNN のみ 0.74 — [同](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/)
- FRIGID は生成構造を**まず組成式一致でフィルタし、次に MIST 予測 fingerprint への Tanimoto で順位付け**。各 refinement ラウンド後も「ユニーク候補プールを fingerprint（＋組成式）で再順位付け」して Top-k を算出 — [FRIGID](https://proceedings.mlr.press/v306/bohde26a.html)

**前方スペクトル予測による再採点・修正**
- FRIGID の inference-time scaling: ICEBERG で生成構造のスペクトルを模擬し、観測スペクトル（20 ppm 許容）に一致しないピーク＝hallucination を原子レベル consistency スコアに落とし、**トークン単位では min 集約**（トークンが覆う原子のうち最悪のものを採用）して masking 確率に変換、該当部分構造だけを remask して再 denoise。これで FRIGID-base 比 **Top-1 相対 +14–26%**、推論計算量に対し log-linear にスケール — [FRIGID](https://proceedings.mlr.press/v306/bohde26a.html)
- 同じ ICEBERG-guided refinement は**モデル非依存**で、DiffMS に適用すると NPLIB1 Top-1 **8.34% → 13.33%**、Top-1 Tanimoto 0.35 → 0.43、Top-10 15.44% → 23.29%（Tanimoto 0.47 → 0.54）。ただしレイテンシは 131.21 s/sample → **1,423.30 s/sample**（FRIGID は 6.58 → 86.49 s） — [同](https://proceedings.mlr.press/v306/bohde26a.html)
- FRIGID の対照実験では、同じ計算量を**ランダム masking に使うより ICEBERG 誘導 remasking のほうが良い**（「利得は単なる計算量増加ではない」） — [同](https://proceedings.mlr.press/v306/bohde26a.html)
- FOAM の目的関数は **ICEBERG 予測スペクトルと実測の entropy similarity（複数衝突エネルギーをピーク数重みで平均）＋ 正規化 SAScore (10−SAScore)/9** の 2 目的を NSGA-II で最適化（fingerprint は使わない）。交叉は同一部分組成式を持つ断片の交換、変異は 7 種の演算子（H/単結合の交換、環の生成・開裂、結合次数変更、ヘテロ原子移動、環縮合）で**すべて組成式を保存**、変異確率 0.20 — [FOAM](https://arxiv.org/html/2602.07709v1)
- ICEBERG 自体の候補識別性能: NIST'20 [M+H]+ random split の top-1 retrieval は 25.1%（95% CI 23.5–26.7）→ **40.0%（39.2–40.8）**、scaffold split 22.9% → **33.5%**、top-10 は約 92%。全アダクト平均の ablation では baseline top-1 0.203 / top-10 0.765 → full 0.335 / 0.892 — [ICEBERG/neural spectral prediction, bioRxiv 2025.05.28.656653](https://pmc.ncbi.nlm.nih.gov/articles/PMC12154671/)
- ICEBERG の contrastive finetuning の decoy は **50% が PubChem 同一組成式、50% が single-step graph mutation で生成**（1 サンプルあたり 10 decoy、生成に 28.1 GPU 時間）。しかし ablation 上の効果は小さい（top-1 0.288 → 0.294、top-10 0.844 → 0.842） — [同](https://pmc.ncbi.nlm.nih.gov/articles/PMC12154671/)
- GLACIER は fragment 候補列挙を廃した単段 transformer で、MassSpecGym の top-1 retrieval を従来 SOTA 64.0% から **70.0%（contrastive finetuning あり）/ 69.7%（なし）** に改善、推論は約 8 倍高速と主張。NIST'20 について 33.2% → 52.5% および 38.5% という数字があるが**どの指標かは検索スニペットからは特定できなかった** — [GLACIER, arXiv:2606.29161](https://arxiv.org/abs/2606.29161)
- MARASON は ICEBERG に neural graph matching を加え、Tanimoto 類似の参照分子（NIST）の実測ピーク強度を対応付けて予測。**構造同定 top-1 27%（非 retrieval SOTA の 19% に対し）** — [MARASON, ICML 2025 (arXiv:2502.17874)](https://arxiv.org/pdf/2502.17874)
- MAGMa は in silico 部分構造木でフラグメントを説明し、強度重み付き部分構造ペナルティ（結合種・ヘテロ原子依存、上限 10、未説明ピークは 10）で候補を順位付け。**同スコア候補は平均順位を割り当てる**（タイ処理） — [MAGMa in CASMI 2013, Mass Spectrom (Tokyo) 3:S0033](https://pmc.ncbi.nlm.nih.gov/articles/PMC4321337)
- 反応規則側の事前確率: GLORYx のスコアは **FAME 3 の site-of-metabolism 確率 × 反応種重み（common 1、uncommon 0.2）**。テストセットで rank-based AUC 0.79 / score-based AUC 0.81（SyGMa は 0.74 / 0.77、SyGMa は Metabolite DB の経験的出現比に基づく） — [GLORYx](https://pmc.ncbi.nlm.nih.gov/articles/PMC7887798)
- KGMN は生成した unknown を **Siden = 0.25·S(m/z) + 0.25·S(RT) + 0.5·S(MS/MS)**、Stotal = Siden + Sconfidence で採点（MS1 15 ppm、予測 RT 30%、MS2 dot product > 0.5 もしくは共有フラグメント 4 超でリンク）。in silico 採点は順位付けではなく事後の裏付けに使用（MetFrag/CFM-ID/MS-FINDER） — [KGMN](https://pmc.ncbi.nlm.nih.gov/articles/PMC9636193/)

**位置異性体 / 修飾部位**
- ModiFinder: GNPS/Berkeley の 4 ライブラリから **1 修飾差の [M+H]+ ペア 12,909 件**、説明可能なシフトピークが 1 つ以上あるのは **8,033 件（62%）**。評価は原子ごとの尤度分布に対する average-distance 型 Evaluation Score（0–1）。MF-R は random choice に対し **+0.181（81% のペアで優越）**、random distribution に対し +0.180（80%）、**CFM-ID ベース手法に対し +0.266** — [ModiFinder, bioRxiv 2024.02.17.580849 / JASMS](https://www.biorxiv.org/content/10.1101/2024.02.17.580849.full)
- **CFM-ID ベースの部位決定は random choice / random distribution より悪かった**。理由は「regioisomer に対する模擬スペクトルがほぼ同一で、分布が平坦になる」ため — [同](https://www.biorxiv.org/content/10.1101/2024.02.17.580849.full)
- ModiFinder の全体スコアは MF-N 0.603 / MF-R 0.625 / MF-O（真の部位を知る oracle）0.652。フラグメント深さを 2 → 4 にすると注釈されたシフトピークは 19% 増えるが**曖昧性が増して MF-R の成績は下がる**。Naphthomycin B では高スコア部位 24 → 精緻化後 2 — [同](https://www.biorxiv.org/content/10.1101/2024.02.17.580849.full)
- ICEBERG の部位局在（withanolide 経路）: 既知反応基質を参照に、**15.999 Da 差のピークペア**（水酸化）を探し、ICEBERG のピーク注釈から部分構造を取り、各原子に「その原子を含む一致ピーク強度の和」を与えて 0–1 正規化（200 m/z 超のピークは無視）、**0.8 超の原子を候補部位とする**。未知中間体 6 件（24–29）に対し候補部位は **3–8 個**で、「真の修飾部位は常に 3–8 の候補内に含まれる」。ただし **ICEBERG は各中間体に一意な構造を提案しない** — [ICEBERG](https://pmc.ncbi.nlm.nih.gov/articles/PMC12154671/)
- FOAM の失敗例も位置異性体型: rank 2 が真の angular furanocoumarin ではなく linear furanocoumarin（「他の連結性は全て同一」）、プロスタグランジン例では top-1 が「わずかな連結性の差」のみ — [FOAM](https://arxiv.org/html/2602.07709v1)
- KGMN も「異性体の識別は困難」と明記（isocitrate の生成物異性体を解決できない）。さらに**反応ペアの約 40% は構造が似ているのに MS2 dot product が 0.5 未満** — [KGMN](https://pmc.ncbi.nlm.nih.gov/articles/PMC9636193/)
- MAGMa の議論でも「MS/MS だけでは区別できない同族体が含まれうる」 — [MAGMa CASMI 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC4321337)
- 分析化学側の一般的知見として、位置異性体（ortho/meta/para）は保持時間も MS/MS も非常に似るため、HCD の高エネルギー条件、多段 MSn、赤外イオン分光（DFT 併用）、イオンモビリティなど**追加次元が必要**とされる — [検索結果の総括（RSC Analyst d0an01119c 等）](https://pubs.rsc.org/en/content/articlehtml/2020/an/d0an01119c)

### Inferences
- 「どのスコアが位置異性体に最も効いたか」に対する文献の答えは「前方スペクトル予測のスペクトル類似度では決まらない」。ModiFinder の CFM-ID 比較と ICEBERG の「一意な構造を提案しない」記述が直接証拠。実務的には**シフトピーク由来の部位尤度（ModiFinder / ICEBERG 流の原子スコア）で候補位置集合を絞り、その中では順位を付けずに代表 1 つを出す**のが現状の上限に近い。
- ユーザーの「1/4 しか rank 3 に置けない」のうち、同一編集の位置違いが占める割合が大きいなら、スコアの改良ではなく**位置違いを 1 つに畳む（部位尤度で代表を選ぶ、または documentation 的事前確率で選ぶ）**ほうが期待値が高い。
- fingerprint スコアと前方モデルスコアは相補的で、文献の最良構成は「fingerprint で一次順位 → 前方モデルで上位のみ再採点/修正」。これはユーザーの E2c の知見（FP top-100 を z(FP)+z(GL) で再採点して MRR 0.446 → 0.615）と同じ形。
- 前方モデルの再採点は計算量が支配的（DiffMS+ICEBERG で 1,423 s/sample）。Kaggle のカーネル時間制約下では「候補数 × 衝突エネルギー数」の予算設計が設計変数になる。

### Gaps
- CFM-ID / ICEBERG / GLACIER を**位置異性体のみのセット**でベンチマークした数値は ModiFinder の比較（Evaluation Score 差 +0.266）以外に見つからなかった。ICEBERG 論文は定性記述のみ（GABA-Arg の異性体 2/11/12 を区別、精度数値なし）。
- 「編集の妥当性に関する事前確率（反応頻度プライア）」を MS スコアと融合して Top-k を改善した定量報告は見つからなかった。GLORYx の反応種重みは代謝物予測の順位付け用で、MS 証拠との融合は評価されていない。
- GLACIER の NIST'20 の 2 つの数値（52.5% / 38.5%）がどの指標かを一次情報で確認できていない。

---

## Q3. 生成候補を DB 候補より上位に入れる挿入規則・信頼度規則と、そのトレードオフ

### Takeaway
**明示的な「挿入規則」を定量評価した論文は見つからなかった。** 現状のベストプラクティスは「別々に検索して、較正済み信頼度（FDR 閾値）で切る」方式（COSMIC）と、「de novo と DB 検索は相補的」という定性的主張（MSNovelist）に留まる。一方で、DB 候補側では**文献被引用数的な事前確率がスペクトル証拠を大きく上回る**という定量結果があり（MetFrag2.2）、生成候補には原理的にこの事前確率が付かないため、素朴な統合は DB 側の成績を壊すリスクが高い。

### Cited Findings
- COSMIC の confidence score は **E-value 較正（PubChem 候補を decoy 代理とした対数正規混合）＋ 方向制約付き線形 SVM ＋ Platt scaling**。重要特徴は「較正済みスコア」「hit と runner-up のスコア差」「候補数」。fragmentation tree score と fingerprint 品質の重みはほぼ 0。候補が 1 つだけの場合は別 SVM — [COSMIC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8926923/)
- COSMIC の閾値校正: 独立データで **0.94 / 0.64 / 0.34 / 0.14 がおおよそ exact FDR 5% / 10% / 20% / 30%**。リポジトリ規模の注釈には 0.64 を使用。CASMI では 0.53 が exact FDR 10%。「confidence score を注釈が正しい確率と誤解してはならない」と明記 — [同](https://pmc.ncbi.nlm.nih.gov/articles/PMC8926923/)
- COSMIC の定量成績: CASMI biomolecule DB（123 query）で FDR<10% のヒット 57 件、Sciex データで FDR<5% 23 件 / FDR<15% 166 件 — [同](https://pmc.ncbi.nlm.nih.gov/articles/PMC8926923/)
- **候補 DB を大きくすると正解率が劣化する**: 「検索する DB が大きくなりすぎると正しい注釈の率は劣化する」と明記。biomolecule DB の代わりに PubChem を検索すると分類器が悪化し、**小さい FDR 域で正解注釈が大幅に減少** — [同](https://pmc.ncbi.nlm.nih.gov/articles/PMC8926923/)
- 新規性の基礎率（DB 欠損率）: 正解が検索 DB に無かったのは **CV の query の 22.70%、独立データの 17.29%**。これらは評価から除外していない。さらに**信頼度の高い誤りヒット上位 9 件のうち 7 件は真の構造が DB に無かった事例** — [同](https://pmc.ncbi.nlm.nih.gov/articles/PMC8926923/)
- MSNovelist は「両アプローチは相補的」とし、bryophyte データ（MTBLS709、576 スペクトル中 224 が組成式信頼度を通過）で **169 件（75%）は MSNovelist 構造のほうが DB 候補より高スコア**。ただし詳細レビューした 7 件のうち MSNovelist がスペクトルをよく説明したのは 4 件、同程度が 1 件。**どちらを優先すべきかの規則は示していない** — [MSNovelist](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/)
- FOAM は候補採用の信頼度としてロジスティック回帰モデルを学習し **平均 AUROC 0.841** を報告（探索の成否予測） — [FOAM](https://arxiv.org/html/2602.07709v1)
- FOAM のトレードオフは数値で明示的: DiffMS に FOAM を重ねると MassSpecGym **Top-1 は 2.30% → 1.50% に低下、Top-10 は 4.25% → 10.28% に向上**。原因は「真構造よりスペクトル類似度の高い decoy」 — [同](https://arxiv.org/html/2602.07709v1)
- 同じ現象の定量: **NIST'20 の探索の 95.2% で、真構造より高スコアの decoy が少なくとも 1 つ現れる**。構造類似度は 2–3 世代でピークを打ち、その後低下する（最適化が不完全な oracle を exploit するため）。著者は「スペクトル予測精度が成功率の主要なボトルネック」と結論 — [同](https://arxiv.org/html/2602.07709v1)
- DB 候補側の事前確率の強さ: MetFrag2.2 は参照情報（ChemSpider reference count）を加えると **ChemSpider で 420 件、PubChem で 336 件が Top-1（それぞれ 89% / 71%）**、CFM-ID と組み合わせると PubChem で最大 343 件。**HR-MS/MS 情報のみ**だと MetFrag2.2 は 30 件、CFM-ID は 43 件しか Top-1 にできない（PubChem） — [MetFrag relaunched, J Cheminform 8:3 (2016)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4732001/)
- MAGMa も「Refscore（PubChem substance 数）」を関連性指標・フィルタ・タイブレークに使用 — [MAGMa CASMI 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC4321337)
- 候補集合サイズのトレードオフの実測: MINE は「PubChem よりはるかに少ない候補数」（中央値 46 対 1,714.5）と引き換えに正解包含率が PubChem 89.8% に対し 66.8% — [MINEs](https://pmc.ncbi.nlm.nih.gov/articles/PMC4550642)
- 伝播型注釈の信頼度の扱い: 近傍 suspect ライブラリは**修飾部位を特定しないため MSI level 3（family レベル）**として提示（フラグメント証拠で局在できる一部アシルカルニチンを除く）。1,350 の頻出 delta mass のうち **852 は未説明**。質量オフセットは「10 回未満の出現は破棄」 — [Nat Commun 14:8488](https://pmc.ncbi.nlm.nih.gov/articles/PMC10733301/)
- KGMN も生成 unknown を**既知より一段低い信頼度階層（level 3.2 対 3.1）**に置くという形で区別している — [KGMN](https://pmc.ncbi.nlm.nih.gov/articles/PMC9636193/)

### Inferences
- 文献にある唯一の運用パターンは「生成候補と DB 候補を**混ぜて 1 本に並べる**のではなく、(i) 別チャネルとして検索し、(ii) 較正済み信頼度/FDR で切り、(iii) 低信頼側は family レベル注釈に格下げする」。CASMI 2026 のように 1 分子 1 解答を要求される設定では、この (iii) に相当する操作が「DB 候補を出す」に当たる。
- MetFrag の数値（スペクトルのみ 30/43 Top-1 → 参照情報込みで 336–420 Top-1）は、ユーザーの E1 パネル観測（fingerprint 単独 7.7% 対 documentation prior 71%）と同方向で、**生成候補はこの prior を持てないという構造的ハンデ**を持つ。したがって「生成候補を DB 候補より上に出す」判断は、スペクトル証拠だけで prior 由来の差を超える必要があり、閾値は保守的に取るべき。
- FOAM の Top-1 低下（2.30% → 1.50%）は、「生成候補を無条件に上位へ挿入すると DB/既存経路の成績を壊す」ことの直接の実測例であり、挿入は**高信頼サブセットに限定**すべきという示唆になる。
- COSMIC の FDR 閾値テーブル（0.64 ≈ 10% FDR）は、「novel 候補を出すか DB 候補を出すか」を決める二値ゲートを作る際の既製の雛形として最も近い。

### Gaps
- 「生成候補を DB 候補の上に挿入する条件」を**定量的に最適化・評価した研究は見つからなかった**。COSMIC（別検索＋FDR）、MSNovelist（相補性の定性主張）、FOAM（信頼度 AUROC 0.841 だが挿入規則としては評価せず）が最も近い。
- DB にある化合物の成績を生成候補の混入がどれだけ悪化させるかを、DB 内/DB 外に層別して報告した研究も見つからなかった（COSMIC は「DB が大きすぎると劣化」と述べるが、仮説構造の混入による干渉は直接検証していないと明記）。
- 生成候補に付けられる「構造としての事前確率」（生合成的妥当性、天然物らしさ、反応頻度）を MS スコアと融合した評価は未発見。FOAM の SAScore は合成容易性で、天然物の事前確率としては代理に過ぎない。

---

## Q4. 検証上の落とし穴（近縁な親によるリーク、DB から除いた既知化合物での評価、テストに合わせ込んだ編集集合）

### Takeaway
2026 年時点で、この分野の評価は**系統的に汚染されている**ことが明示的に報告されている: MassSpecGym 採用1年目の論文 26 本のうち**少なくとも 17 本に評価上の問題**が見つかり、具体的なバグ由来のリーク（MIST の batched inference）では Top-1 が 10.73% → 31.75% に膨らむことが再現されている。編集ベース手法に固有の落とし穴は「親の近さ」依存と「不完全な oracle の exploit」。

### Cited Findings
- 「MassSpecGym in the Wild」: MassSpecGym の結果を報告した 26 本のうち **少なくとも 17 本に評価上の問題**。失敗様式を **data leakage / shortcut learning / implementation bugs with metric divergence** の 3 類型に整理し、推奨を反映した **MassSpecGym v1.5** を公開 — [arXiv:2606.19624 (2026-06-17)](https://arxiv.org/abs/2606.19624)
- 具体的なリーク事例（実測）: MIST の batched inference で padding 位置の attention mask に **−inf ではなく 0 を加算**するバグがあり、短いスペクトルが padding に attend してバッチ内最長スペクトルへ崩れる。MassSpecGym は**同一分子のスペクトルをまとめている**ため、batch size > 1 で fingerprint 品質が水増しされる。batch size 24 で MIST Tanimoto 0.457 → 0.812、**MIST+MolForge Top-1 10.73% → 31.75%、Top-10 14.48% → 40.55%** — [FRIGID Appendix A.3](https://proceedings.mlr.press/v306/bohde26a.html)
- 事前学習データ経由のリーク: Multimodal Spectroscopic Dataset（シミュレーション由来）に **NPLIB1 テスト構造 122 件（テストの 14.90%）、MassSpecGym テスト構造 1,820 件（10.37%）**が含まれる（2D InChIKey 一致）。さらに「このシミュレーションデータを作ったモデル自体がテスト構造を含むデータで学習された可能性が高い」として、FRIGID 著者は test-time tuning 手法との比較を**公平に行えないと判断して除外** — [FRIGID Appendix A.6](https://proceedings.mlr.press/v306/bohde26a.html)
- リーク対策の実例: FRIGID は SAFE-GPT コーパス（最大 10 億構造）から **NPLIB1/MassSpecGym の test+validation 構造を 2D InChIKey の除外リストで削除**し、「ラベルなしの評価構造さえ見せない」。再採点に使う ICEBERG も**各ベンチマークの学習サブセットのみ**で学習（NPLIB1 6,810 構造/9,272 スペクトル、MassSpecGym 13,543/101,573） — [FRIGID](https://proceedings.mlr.press/v306/bohde26a.html)
- MSNovelist のリーク対策: fingerprint シミュレーションに使った構造と評価セットの構造を **RNN の学習から除外**、**structure-disjoint cross-validation**、CASMI の全構造を同一 fold に割り当ててモデルが一切見ないようにした（学習 1,232,184 分子 / 1,048,512 のユニーク InChIKey2D を 10 fold） — [MSNovelist](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/)
- COSMIC: 評価は **structure-disjoint**（query 構造を学習から除外）。これを行わないと「分離がはるかに良く見える」ことを学習・評価構造の重複に帰している — [COSMIC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8926923/)
- 「既知化合物を DB から除いて評価する」設計の実例と結果: VarQuest の decoy/FDR 検証では、**実験 1（全スペクトルが真）で FDR 0.5%、実験 2（正しいペプチドを DB から除去）で FDR 55.0%**（期待値約 50% に近い）。従来の shuffling decoy は実験 1 で FDR を過大評価し、DEREPLICATOR の decoy は実験 2 で過小評価した — [VarQuest](https://pmc.ncbi.nlm.nih.gov/articles/PMC5951390)
- 編集集合を「近い親」に合わせ込むことの効果（＝親の近さ依存）: FOAM の Top-10 exact match は最近傍 seed 類似度 0.2–0.4 で 8.1%、**0.4–0.6 で 31.5%**。真構造の予測スペクトル類似度 ≥0.8 の場合は Top-10 成功率 53.4%。seed の質によって成績が数倍変わる — [FOAM](https://arxiv.org/html/2602.07709v1)
- 不完全な oracle の exploit: **NIST'20 探索の 95.2% で真構造より高スコアの decoy が出現**し、構造類似度は 2–3 世代でピーク後に低下。著者は「最適化器が不完全な oracle を首尾よく exploit して真構造を上回る decoy を生成する」と記述 — [同](https://arxiv.org/html/2602.07709v1)
- ModiFinder のベンチマーク偏り: ライブラリ別にベースラインとの差が異なり、**lib4 で差が最大**であることを著者自身が「結果を偏らせうる」と注意。また「説明可能なシフトピークが 1 つ以上」という**フィルタで 12,909 → 8,033 ペア（62%）に絞った**うえでの成績であることに注意が必要 — [ModiFinder](https://www.biorxiv.org/content/10.1101/2024.02.17.580849.full)
- 伝播型ライブラリの構築フィルタがそのまま評価に効く例: suspect ライブラリは **cosine ≥ 0.8 かつ一致イオン ≥ 6**、かつ**出現 10 回未満の質量オフセットを破棄**という条件で作られており、頻出 delta mass 1,350 のうち 852 は未説明のまま。組成式の一致も不完全（SIRIUS と BUDDY が一致したのは 32,302 suspect、SIRIUS が異なる 32,508、BUDDY が異なる 47,508） — [Nat Commun 14:8488](https://pmc.ncbi.nlm.nih.gov/articles/PMC10733301/)
- 近縁分子の split 汚染対策としての MassSpecGym 設計: 学習/テスト間の **MCES 編集距離閾値 10** で、似すぎる分子が両側に現れないよう分割していると説明される（**二次情報: レビュー/要約サイト経由**、一次論文の本文は未確認） — [themoonlight.io レビュー](https://themoonlight.io/review/massspecgym-a-benchmark-for-the-discovery-and-identification-of-molecules)
- データセット自体の偏り: 公開分子データセット 10 種を MCES 距離＋UMAP で調べ、**学習・評価データが生体分子空間の一様な部分標本ではない**ことを示した（coverage bias）。MCES は NP-hard のため「myopic」近似を提案 — [Coverage bias in small molecule machine learning, Nat Commun 16 (2025), doi:10.1038/s41467-024-55462-w](https://pmc.ncbi.nlm.nih.gov/articles/PMC11718084/)
- 既知化合物に対する評価の歪み（DB 欠損を分母に含めるか）: COSMIC は正解が DB に無い query（CV 22.70% / 独立 17.29%）を**評価から除外していない**と明記。MSNovelist は逆に「正解が DB にある」部分集合（GNPS-OK、CASMI-OK）を**別に報告**し、全体 25% に対し GNPS-OK では 61% と大きく違う — [COSMIC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8926923/); [MSNovelist](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/)
- MINE の「98.6%」のような指標の読み違いリスク: これは**候補が 1 つ以上返った率**で、正解包含率（KEGG MINE 66.8%）とは別物 — [MINEs](https://pmc.ncbi.nlm.nih.gov/articles/PMC4550642)

### Inferences
- CASMI 2026 で「他のテスト分子の予測構造」を neighbour に使う設計は、FOAM の seed 類似度依存と同じ感度を持つはずで、**neighbour の予測が誤っていた場合に系統的な誤りが伝播**する。評価時は「neighbour が正しかった場合/誤っていた場合」で層別しないと到達率が楽観側に偏る。
- 「シミュレーション test 分子を novel 扱いにして自前の編集集合で評価する」設計は、ModiFinder の「シフトピークがあるペアだけに絞った 62%」と同じ選択バイアスを持ちうる。編集集合の設計に使った分子群と評価分子群を分けること（ユーザーの既存ルールと一致）が必須。
- 前方モデル（ICEBERG/GLACIER）を再採点に使う場合、その重みが MassSpecGym 由来だと**テスト分子を見ている可能性**がある（ユーザーの既存知見: enveda-np-examples 250 分子中 236 が MassSpecGym に存在）。FRIGID が ICEBERG をベンチマークの学習サブセットのみで再学習したのと同じ配慮が必要。
- 生成候補の自己採点に単一の前方モデルを使うと、FOAM の 95.2% decoy 出現と同じ「oracle exploit」が起きる。独立な 2 種以上の証拠（fingerprint + 前方モデル、あるいは部位尤度）で合議するほうが安全という読みが立つ。

### Gaps
- 「MassSpecGym in the Wild」の本文（どの論文のどの数値がどれだけ下がったか、MADGEN/DiffMS/FRIGID 個別の影響）は abstract しか取得できておらず、方法別の補正後数値を引用できない。
- 「近縁な親による leakage」を定量化した研究（例: 親が学習データにある場合と無い場合の到達率/Top-k の差）は見つからなかった。FOAM の seed 類似度層別が最も近い代理指標。
- MassSpecGym の MCES 閾値 10 は二次情報でしか確認できていない（一次論文 arXiv:2410.23326 の本文未確認）。
- 「編集集合をテストに合わせ込んだ」ことによる楽観バイアスを直接測った報告は見つからなかった。

---

## 補足: 本件に直接効く数値の要約（レポート作成者向け）

| 手法 | 候補生成の仕組み | 到達率（真構造が候補に入る） | 順位付け後 Top-1 | 順位付け後 Top-10 | 出典 |
|---|---|---|---|---|---|
| FOAM (NIST'20) | 組成式固定 GA（PubChem 同組成式を seed に編集） | 68.1%（探索中に遭遇） | 11%（3世代後） | 31%（3世代後） | [arXiv:2602.07709](https://arxiv.org/html/2602.07709v1) |
| FOAM (MassSpecGym, DiffMS+PubChem seed) | 同上 | 33%（1世代後。DiffMS 単独 5.8%） | 1.50% | 10.28% | 同 |
| MSNovelist (GNPS) | fingerprint 条件付き LSTM 生成 (beam 128) | 45% | 25%（DB 検索 39%） | — | [Nat Methods 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/) |
| MSNovelist (GNPS-OK) | 同上 | 68% | 61% | — | 同 |
| MADGEN (MassSpecGym) | scaffold 条件付き生成 | SPA 34.8%（予測）/100%（oracle） | 0.8% / 18.8% | 1.6% / 38.6% | [ICLR 2025](https://arxiv.org/html/2501.01950v1) |
| FRIGID (MassSpecGym) | 拡散 LM + ICEBERG 誘導 remask | — | 18.29% | 22.00% | [ICML 2026](https://proceedings.mlr.press/v306/bohde26a.html) |
| FRIGID (NPLIB1) | 同上 | — | 25.03% | 33.37% | 同 |
| ModiFinder | 既知＋1修飾ペアの部位局在 | シフトピーク説明可能 62%（8,033/12,909） | — | 真部位は 3–8 候補内（ICEBERG 版） | [bioRxiv 2024](https://www.biorxiv.org/content/10.1101/2024.02.17.580849.full); [ICEBERG](https://pmc.ncbi.nlm.nih.gov/articles/PMC12154671/) |
| VarQuest | 既知 PNP＋単一質量シフト ≤300 Da | PNP family 41%（1,582 中 648） | — | — | [Nat Microbiol 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC5951390) |

注: FRIGID Table 1 の MCES / Tanimoto 列は PDF からのテキスト抽出で列対応が崩れていたため、本ノートでは **accuracy 列のみ**を引用した（DiffMS 8.34%/15.44%、MADGEN 1.31%/1.54% など既知値と一致することを確認済み）。Tanimoto は Table 3（DiffMS 0.35 → +ICEBERG 0.43 等）のように対応が明確な箇所のみ引用している。
