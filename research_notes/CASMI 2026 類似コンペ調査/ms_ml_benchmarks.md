# ML benchmarks, academic challenges and reference methods for MS/MS → small-molecule structure (as relevant to Enveda CASMI 2026)

Research date: 2026-10-24. All numbers are dated by the publication/version they come from. "MSG" = MassSpecGym. "Top-1" always means exact structure match unless stated otherwise. Where a result is self-reported and not yet independently reproduced, it is flagged.

Reading guide for the competition: the CASMI 2026 metric (MRR@25 on tautomer-canonical InChIKey14, stereo ignored) is closest to MSG's retrieval "hit rate @k" / de novo "top-k accuracy" families; none of the benchmarks below use MRR, so direct score transfer is impossible, but the ranking of methods is informative.

---

## Key Question 1: MassSpecGym (Bushuiev et al., NeurIPS 2024 D&B) — tasks, split, metrics, baselines, current SOTA

### Takeaway
MSG is the only identity-controlled public benchmark whose test molecules are guaranteed to be ≥10 MCES edits from any training molecule; on it, de novo generation without a formula is still essentially unsolved (best official leaderboard entry 1.07% top-1, Oct 2025), formula-given de novo has climbed from 0% (2024) to 2.3% (DiffMS, 2025) → 9.05% (FRIGID, leak-corrected, 2026) → 23.9% (DualLGD, May 2026, self-reported/unverified), spectrum-to-fingerprint retrieval over 256 mass-matched candidates sits at ~15% hit@1 (MIST/JESTR), while forward-simulation-based ranking on the same candidate construction reaches 64–70% hit@1 (ICEBERG 2.0 / GLACIER, 2025–2026).

### Cited Findings

**Tasks and inputs**
- Three challenges: (1) de novo generation: MS/MS spectrum → set of k molecular graphs (118-element or 10-common-element vocabulary, single/double/triple/aromatic bonds, no 3D); (2) molecule retrieval: rank up to 256 candidates that share the precursor mass; (3) spectrum simulation: molecular graph + instrument type (QTOF or Orbitrap) + adduct + collision energy → spectrum, restricted to [M+H]+; simulated spectra are also scored by retrieval hit rate. Each has a "bonus" variant where the true chemical formula is given (de novo: atom set known; retrieval: candidates restricted to same formula) — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3); [GitHub README](https://github.com/pluskal-lab/MassSpecGym)
- Retrieval candidate construction: "Mass Challenge" samples up to 256 candidates with the same mass; "Formula Challenge" samples up to 256 with the same formula — [GLACIER arXiv v2 describing MSG protocol](https://arxiv.org/html/2606.29161v2)

**Data**
- 231K labeled spectra / 29K unique molecules from MoNA, MassBank, GNPS and in-house MSnLib (~10K molecules, 33%, in-house); adducts only [M+H]+ or [M+Na]+; 98% of spectra from Orbitrap or QTOF; ~53% have normalized collision energy — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3)
- GLACIER reports the official split as 231,104 spectra from 31,602 molecules (molecule count differs from the paper's 29K, probably different canonicalization) — [GLACIER arXiv v2](https://arxiv.org/html/2606.29161v2)
- Unlabeled companions: GeMS-A10 (24M spectra) and 1M / 4M / 118M PubChem molecule sets for pretraining — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3)
- Dataset on Hugging Face as roman-bushuiev/MassSpecGym; repo MIT-licensed; NeurIPS 2024 Spotlight — [GitHub README](https://github.com/pluskal-lab/MassSpecGym)

**MCES split rationale**
- Molecules are clustered by agglomerative clustering on MCES (maximum common edge subgraph) edit distance with minimum-distance linkage, threshold 10, so no two molecules in different folds have edit distance < 10; folds stratified by instrument, collision energy, adduct and molecule frequency. The commonly used 2D-InChIKey-disjoint split was shown to leak near-duplicates (test molecules with Tanimoto > 0.85 to training molecules, Fig. 3) — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3)
- The authors state the MCES approach "significantly surpasses the commonly applied 2D InChIKey disjoint approach, used in nearly all related works, in terms of preventing data leakage" — [MassSpecGym arXiv PDF](https://arxiv.org/pdf/2410.23326)

**Metric definitions**
- De novo: top-k accuracy = indicator that the true graph is among the top-k predictions; top-k MCES = minimum MCES distance between any top-k prediction and truth; top-k Tanimoto = max Morgan-fingerprint Tanimoto across top-k. Retrieval: hit rate @k = indicator that the true molecule is within the top-k ranked candidates; MCES@1 = MCES distance of the top-1 candidate to truth. Simulation: cosine similarity on 0.01 Da bins up to 1005 Da with precursor excluded, plus Jensen–Shannon similarity — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3)
- MS-BART notes the leaderboard's accuracy convention: its own paper matches full InChIKey and additionally reports 2D-InChIKey accuracy (1.26% vs 1.07% top-1 on MSG) — [MS-BART arXiv](https://arxiv.org/html/2510.20615v1)

**Baseline results in the paper (Jan 2025 leaderboard date)**
- De novo (no formula): SMILES Transformer 0.00% top-1 / 0.00% top-10, MCES@1 53.80; SELFIES Transformer 0.00%/0.00%, MCES 33.28; random chemical generation 0.00%, MCES 28.59. Bonus (formula given): all 0.00%; random generation MCES@1 21.11 — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3)
- Retrieval (mass-based 256 candidates), HR@1 / HR@5 / HR@20 / MCES@1: Random 0.37/2.01/8.22/30.81; DeepSets 1.47/6.21/19.23/25.11; Fingerprint FFN 2.54/7.59/20.00/24.66; DeepSets+Fourier 5.24/12.58/28.21/22.13; MIST 14.64/34.87/59.15/15.37. Bonus (formula): Random 3.06/11.35/27.74; MIST 9.57/22.11/41.12 — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3)
- Simulation: cosine / JS / HR@1 / HR@5 / HR@20: Precursor-m/z 0.15/0.15/0.38/1.72/7.17; FFN fingerprint 0.25/0.24/8.44/21.43/38.57; GNN 0.19/0.20/3.95/11.92/26.27; FraGNNet 0.52/0.47/46.64/72.56/83.58. Bonus: FraGNNet 31.93/63.20/82.70 — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3)

**Official leaderboard (results CSVs in repo; live site massspecgym.onrender.com returned HTTP 503 on 2026-10-24)**
- Leaderboard is maintained by pull requests to the `results` folder; interactive page at https://massspecgym.onrender.com — [GitHub README](https://github.com/pluskal-lab/MassSpecGym)
- De novo (no formula) CSV: SMILES/SELFIES Transformers and random all 0.00%; MS-BART 1.07% top-1 / 1.11% top-10, MCES 16.47/15.12, Tanimoto 0.23/0.28 (published 2025-10-23) — [de_novo.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/de_novo.csv)
- De novo bonus (formula given) CSV: Spec2Mol 0.00%; MADGEN 1.31%/1.54% (2025-04-29); MIST+MSNovelist 0.00%; MIST+Neuraldecipher 0.00%; DiffMS 2.30%/4.25%, MCES 18.45/14.73, Tanimoto 0.28/0.39 (2025-05-27); OMG_JESTR 0.32%/2.55% and OMG_ESP 0.85%/2.82% (Anal. Chem., 2025-09-16) — [de_novo_bonus.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/de_novo_bonus.csv); OMG paper DOI [10.1021/acs.analchem.5c01770](https://doi.org/10.1021/acs.analchem.5c01770)
- Retrieval CSV (mass): MIST 14.64/34.87/59.15; ESP 10.71/24.84/42.66; JESTR 15.13/36.75/60.32 (2025-06-10). Retrieval bonus (formula): MIST 9.57/22.11/41.12; ESP 11.05/27.42/52.20; JESTR 11.85/32.95/61.46 — [retrieval.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/retrieval.csv); [retrieval_bonus.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/retrieval_bonus.csv)
- Simulation bonus CSV: FraGNNet 31.93/63.20/82.70; MARASON (neural graph matching, Feb 2025) 34.03/64.04/85.39; ICEBERG (bioRxiv June 2025) cosine 0.58, JS 0.48, HR 45.95/75.43/91.69 — [simulation_bonus.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/simulation_bonus.csv)
- README update 2025-10-27: ICEBERG "the current state-of-the-art model for simulation" now has MSG-compatible weights and codebase (ms-pred repo) — [GitHub README](https://github.com/pluskal-lab/MassSpecGym)

**Paper-reported SOTA not (yet) in the official CSVs**
- GLACIER (NeurIPS 2026; arXiv v2 2026-10-05): MSG Mass Challenge Recall@1/@5/@20 = 69.95/86.47/93.52 with contrastive finetuning (69.69/86.58/93.34 without), vs ICEBERG 2.0 63.95/83.83/92.56, MolSpecFlow 55.32/79.98/89.54, FraGNNet 46.64/72.56/83.58; Formula Challenge: GLACIER 49.88/78.13/90.75 vs ICEBERG 2.0 44.35/73.57/89.45, MARASON 34.03/64.04/85.39 — [GLACIER arXiv v2](https://arxiv.org/html/2606.29161v2)
- FRIGID (ICML 2026) corrected README results (formula known): MSG top-1 9.05%, top-10 12.23%, MCES 12.60/11.41, Tanimoto 0.39/0.43; FRIGID-base 8.21%/9.82%; the paper's 18.29% MSG / 25.03% NPLIB1 figures are superseded because "the earlier release used MIST training data selected with test-set formula information, which was a leak" — [FRIGID README](https://raw.githubusercontent.com/coleygroup/FRIGID/main/README.md); the PMLR abstract still states "above 18%" — [PMLR v306](https://proceedings.mlr.press/v306/bohde26a.html)
- DualLGD (arXiv 2026-05-07, self-reported): MSG top-1 23.89%, top-10 33.08%, MCES 10.11/7.69, Tanimoto 0.52/0.61; its table lists MBGen 7.58%/12.54%, MSAnchor 2.68%/4.67%, MS-BART 1.07%/1.11%, DiffMS 2.30%/4.25%, MADGEN 1.31%/1.54%; FRIGID and FOAM are absent from its comparison; evaluation generates 100 candidates per spectrum, accuracy matched by InChI; code at github.com/du-lab-data-science/DualLGD — [DualLGD arXiv](https://arxiv.org/html/2605.07048v1)
- Test-time-tuned LMs (ICLR 2026 workshop, IBM/ETH): MSG top-1 3.16%, NPLIB1 12.88%, end-to-end spectrum+formula → structure without fingerprints — [IBM Research](https://research.ibm.com/publications/test-time-tuned-language-models-enable-end-to-end-de-novo-molecular-structure-generation-from-msms-spectra)
- FOAM (arXiv 2026-02-07): DiffMS+PubChem seeds optimized with ICEBERG: MSG top-1 1.50% (down from DiffMS 2.30%) but top-10 10.28% (up from 4.25%), top-10 MCES 6.06 (vs 11.68), Tanimoto 0.53 (vs 0.39) — [FOAM arXiv](https://arxiv.org/html/2602.07709v1)
- Contrastive domain generalization (arXiv 2026-01-31): 42.16% Hit@1 on a fixed 256-way zero-shot retrieval, but on MassBank-only data with an InChIKey-first-block scaffold split (not the official MSG test set), and only 3.56% Hit@1 / 17.58% Hit@10 when the pool is the global ~26k molecules — [arXiv 2602.00547](https://arxiv.org/html/2602.00547)
- Project launched April 2024 with teams from 14 institutes; presented at NeurIPS Vancouver 2024-12-13 — [ELLIS/CIIRC news](https://ellis.ciirc.cvut.cz/?p=5666)

### Inferences
- The de novo bonus (formula given) numbers are the ones everyone quotes; without formula the best official number is ~1%. CASMI 2026 gives precursor m/z + adduct but not formula, so a competitor's de novo pipeline needs a formula-inference step (SIRIUS/MIST-CF/BUDDY); DiffMS measured the cost of predicted vs true formula on MSG at 1.86% vs 2.30% top-1 (see KQ4).
- On MSG, forward simulation + spectral-similarity ranking (ICEBERG 2.0/GLACIER, 64–70% R@1 on 256 mass-matched candidates) is 4–5× better than fingerprint retrieval (MIST 14.64%) and joint embedding (JESTR 15.13%). Caveat: the simulation challenge only covers [M+H]+ spectra with usable collision-energy metadata, so the two test subsets are not identical; still, the gap is large enough to make forward-model reranking the highest-leverage component for the class-2 isomer problem.
- Because MSG's candidate sets are only 256 and the formula bonus makes candidates isomers, the "formula challenge" hit@1 (GLACIER 49.9%) is the number most comparable to the CASMI 2026 same-formula-isomer discrimination problem; expect lower in CASMI because PubChem+COCONUT mass windows produce thousands of candidates (JESTR: 1,322–2,494 average formula isomers from PubChem; ICEBERG 2.0 case: 8,413 for C9H15N3O2).
- MSG test molecules are MCES≥10 from training, i.e. closest to CASMI novelty class 3 (and hard class 2). CASMI class 1 (reference spectra exist) is far easier than anything MSG measures.

### Gaps
- Live leaderboard page (massspecgym.onrender.com) was unreachable (HTTP 503) on 2026-10-24; CSVs in the repo are the fallback and may lag the site.
- Whether the simulation-challenge test subset equals the retrieval-challenge test subset is not stated in the retrieved text; the 64–70% vs 15% comparison should be treated as indicative, not exact.
- DualLGD's 23.89% has not been reproduced by third parties or added to the official CSVs as of 2026-10-24; FRIGID's own correction (18.29% → 9.05%) shows how fragile leaderboard-level de novo numbers are.
- MolSpecFlow (55.32% R@1 in GLACIER's table) could not be sourced to a paper during this research.

---

## Key Question 2: Fingerprint-prediction retrieval lineage (CSI:FingerID/SIRIUS/CANOPUS, MIST, MIST-CF, JESTR, DreaMS-retrieval)

### Takeaway
Spectrum → fingerprint → candidate ranking (CSI:FingerID, MIST) delivers ~30–38% top-1 among PubChem formula isomers on structure-disjoint but similarity-leaky benchmarks (NPLIB1/GNPS, 2022–2023), ~26–29% top-1 2D structures in the blind CASMI 2022 contest, and only 14.6% hit@1 on the strictly MCES-disjoint MassSpecGym; the lineage's weak points are exactly CASMI 2026's: same-formula isomers and dependence on an upstream formula/fragment annotation (SIRIUS) step.

### Cited Findings

**CSI:FingerID / SIRIUS 4 / CANOPUS**
- SIRIUS 4 abstract claims "identification rates of more than 70% on challenging metabolomics datasets"; a linear SVM separates biomolecule formulas from random decompositions with AUC 0.965; software is Java, GPL v3; Supplementary Fig. 7 benchmarks N = 3,868 GNPS compounds against PubChem (Sept 2014) — [SIRIUS 4, Nat. Methods 2019](https://www.nature.com/articles/s41592-019-0344-8)
- CASMI 2016 category 2 (automated, spectra-only): CSI:FingerID's IOKR variant won and standard CSI:FingerID was second; "for positive ionization, CSI:FingerID identified more than twice as much compounds than any other method" (no exact counts on page) — [Böcker lab news](https://bio.informatik.uni-jena.de/?p=6080)
- CASMI 2022 (blind, raw LC-MS/MS, +ESI and −ESI, 500 compounds), 2D-structure category, % correct top-1 (priority / bonus): Dührkop (SIRIUS/CSI:FingerID) 26 / 29; Nothias 25 / 28; Rutz 25 / 28; Mehta (oloBion) 21 / 21; Nikolic_KUCA 38 (only 55 attempts); Xing 15 / 13; Tsugawa (MS-DIAL) 12; Wang 9 / 4; Young 0; Elser 0. Formula category: Dührkop 94 / 95, Nothias 93 / 94, Rutz 91 / 94; adducts: up to 93–96% — [CASMI 2022 results, Fiehn lab](https://fiehnlab.ucdavis.edu/casmi/casmi-2022-results)
- MSNovelist (which runs on CSI:FingerID fingerprints) reports CSI:FingerID database search ranks the correct structure first for 39% of 3,863 GNPS spectra; also "SIRIUS formula error rates exceed 50% for individual spectra at m/z up to 800" — [MSNovelist, Nat. Methods 2022 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/)

**MIST (Goldman et al., Nat. Mach. Intell. 2023)**
- Comparison dataset: 31,145 [M+H]+ spectra of 27,797 compounds from GNPS, MoNA and NIST20 (NIST portion non-redistributable); three structure-disjoint 20% holdouts. MIST has higher fingerprint cosine than CSI:FingerID on 11,994/18,700 test spectra (~64%); higher log-likelihood on 64.12% of spectra; a single non-ensembled model wins on >55% — [MIST bioRxiv](https://www.biorxiv.org/content/10.1101/2022.12.30.522318v1.full)
- Retrieval among PubChem isomers: MIST contrastive top-1 37.39%, MIST fingerprint-distance 31.70%, CSI:FingerID 38.24% (Bayesian scoring higher still); for k ≥ 20 MIST's contrastive distance beats CSI:FingerID's Bayesian retrieval for nearly all k; MIST matches/beats CSI rank on 66% of examples. Public GNPS/CANOPUS benchmark (8,030 spectra, 7,131 compounds): 30.7% top-1, 75.7% top-20 — [MIST bioRxiv](https://www.biorxiv.org/content/10.1101/2022.12.30.522318v1.full)
- Requirements and limits: needs precursor formula with adduct removed and SIRIUS-style fragment formula annotation of the top-60 peaks; "MIST is currently only trained on annotated spectra"; contrastive fine-tuning uses PubChem isomer decoys weighted by Tanimoto; authors flag dependence on upstream formula assignment and "retrospective data leakage concerns" requiring prospective validation; CSI:FingerID is cited as the top performer at CASMI 2022 — [MIST bioRxiv](https://www.biorxiv.org/content/10.1101/2022.12.30.522318v1.full)
- MIST on MassSpecGym: 14.64 / 34.87 / 59.15 hit@1/5/20 (mass candidates); 9.57 / 22.11 / 41.12 (formula candidates) — [retrieval.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/retrieval.csv)

**MIST-CF (formula inference)**
- Energy-based ranking of formula+adduct assignments from unannotated MS/MS; "absolute improvement of 10% top-1 accuracy over other neural network architectures"; on CASMI 2022 "nearly equivalent performance to the winning entry within the positive mode category without any manual curation or post-processing" (JCIM, DOI 10.1021/acs.jcim.3c01082) — [MIT DSpace record](https://dspace.mit.edu/handle/1721.1/165432)

**JESTR (Bioinformatics 2025) — joint embedding instead of fingerprints**
- GNN molecule encoder + MLP spectrum encoder (1 Da bins, <1000 Da), contrastive loss, cosine ranking; formula assumed known (PubChem formula isomers, mean 1,322–2,494 candidates/target, max ~42–44k). Rank@1/5/20: NPLIB1 (819 test spectra, MIST's structure-disjoint split) JESTR 45.8/81.5/95.8 vs MIST 27.9/62.4/82.1 vs ESP 23.7/44.7/60.2; NIST2020 (29,107 test spectra) JESTR 38.6/59.6/81.0 vs MIST 21.0/57.4/78.8; MoNA JESTR 26.6/64.2/91.2 vs MIST 32.3/52.9/75.3 (MIST wins rank@1 on MoNA). Candidate-regularization (training on ~77M PubChem candidates in the last 3% of epochs) raised rank@1 by 11.4% (NPLIB1), 6.0% (NIST), 37.1% (MoNA) — [JESTR arXiv v2](https://arxiv.org/html/2411.14464v2)
- On MassSpecGym JESTR is only marginally above MIST (15.13 vs 14.64 hit@1 mass; 11.85 vs 9.57 formula) — [retrieval.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/retrieval.csv)

**DreaMS as a fingerprint/retrieval model**
- Fine-tuned DreaMS "performance is on par with MIST on the MIST benchmark" (CANOPUS ~8,000 spectra / ~7,000 molecules; retrieval accuracy at k ∈ {1,5,10,20,50,100,200}, values in Fig. 4e / Extended Data Table 1, not in the retrieved text) — [DreaMS, Nat. Biotechnol. 2025](https://www.nature.com/articles/s41587-025-02663-3)

**Isomer discrimination and instrument transfer evidence within this lineage**
- MSNovelist: in a random sample of ten incorrect predictions, seven were close isomers of the correct structure; "certain isomers fragment (almost) indistinguishably"; median Tanimoto of best incorrect database structure to truth 0.84 — [MSNovelist (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/)
- MassBank manual: mass spectrometry gives the same spectrum to all stereoisomers of the same connectivity — [MassBank manual](https://mssj.jp/english/about/pdf/MassBank_manual-en.pdf)
- No fingerprint-lineage paper retrieved reports a per-instrument (Orbitrap vs QTOF vs timsTOF) breakdown; the only "cross-instrument" ML paper found isolates scaffold shift, not instrument shift — [arXiv 2602.00547](https://arxiv.org/html/2602.00547)

### Inferences
- The lineage's ceiling on same-formula isomer ranking is ~30–46% top-1 on friendly (NPLIB1-style) splits and ~15% hit@1 on MCES-disjoint data; for CASMI class 2 (structure in PubChem/COCONUT, no spectra) a fingerprint model alone will plateau well below the current public LB; it is best used as (a) a fast first-stage filter over thousands of mass-window candidates and (b) one feature in a learned reranker, with forward-model scores doing the fine isomer discrimination (KQ3).
- JESTR's single most transferable trick is candidate-aware training (contrastive regularization against the real PubChem isomer decoys the model will face), worth +6 to +37% relative rank@1; a competitor can do this directly with COCONUT/PubChem mass-window decoys.
- MIST-style models require formula + subformula annotation; in CASMI 2026 the formula must be inferred (MIST-CF/SIRIUS/BUDDY). Because the 2022 CASMI formula category reached 94–95% for the best tools, formula inference is a solved-enough sub-problem for most but not all spectra (SIRIUS error rates >50% for weak single spectra per MSNovelist).
- JESTR's MoNA result (worse than MIST at rank@1 on an inconsistently curated, instrument-heterogeneous library) is the closest proxy to instrument/curation shift in this lineage: joint-embedding models trained on clean data degrade more than annotation-based MIST under messy input.

### Gaps
- CSI:FingerID's exact identification percentages on CASMI 2016/2017 and its training-set size were not in the accessible Nature Methods text (supplementary only); CSI:FingerID's current (SIRIUS 5/6) accuracy on MSG-like splits was not found.
- CANOPUS (compound class prediction) was not researched in depth; it is a class-level, not structure-level, tool.
- No per-instrument accuracy breakdown exists for any fingerprint model in the sources found.

---

## Key Question 3: Forward (structure → spectrum) models for reranking: CFM-ID, ICEBERG/ICEBERG 2.0, GLACIER, FIORA, GrAFF-MS, FraGNNet, MARASON, FOAM

### Takeaway
Neural forward models now dominate candidate ranking: on MSG's 256-candidate retrieval, ICEBERG 2.0 reaches 63.95% and GLACIER 69.95% recall@1 (vs 14.6% for MIST), FraGNNet/ICEBERG reach ~36% top-1 against 49 hard PubChem decoys on NIST20 (2024–2025), and ICEBERG-guided refinement improves de novo top-10 (FRIGID +2.4 pts, FOAM +6 pts); the main constraints are that the strongest weights are NIST-trained and license-restricted, open weights are trained on Orbitrap/QTOF libraries (MSnLib, MSG), positive-mode [M+H]+ dominates, and all models collapsed on the CASMI 2022 out-of-domain data (cosine 0.29–0.38 vs 0.7–0.8 in-domain).

### Cited Findings

**CFM-ID (combinatorial fragmentation, pre-neural baseline)**
- In ICEBERG's benchmark CFM-ID cosine = 0.377 on NPLIB1 and 0.412 on NIST20 random split (vs 0.627 / 0.727 for ICEBERG) — [ICEBERG arXiv v2](https://arxiv.org/html/2304.13136v2)
- In FIORA's benchmark (median cosine, sqrt intensities, with precursor) CFM-ID 0.67 vs FIORA 0.81 vs ICEBERG 0.72 on the [M+H]+ test split, but CFM-ID leads on CASMI 2022 [M+H]+ (0.38 vs FIORA 0.29 vs ICEBERG 0.36); CFM-ID was pre-trained on METLIN rather than retrained; CPU speed 3.43 s/prediction vs FIORA 0.03 s on A100 — [FIORA, Nat. Commun. 2025 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11889238/)

**ICEBERG (Goldman, Li, Coley; arXiv 2023, v2 Jan 2024)**
- Two stages: autoregressive GNN "Generate" predicts atom-level bond breakages to build a fragmentation DAG (trained on MAGMa-enumerated DAGs to depth 3; top-100 fragments kept) and Set-Transformer "Score" predicts intensities over hydrogen shifts (≈ −6…+6 H) — [ICEBERG arXiv v2](https://arxiv.org/html/2304.13136v2)
- Data: NPLIB1 (GNPS natural products) 10,709 spectra / 8,553 structures; NIST20 35,129 spectra / 24,403 structures; structurally disjoint 90/10 splits plus a NIST20 scaffold split. Cosine: NPLIB1 ICEBERG 0.627 vs MassFormer 0.568, SCARF 0.536, NEIMS 0.491, CFM-ID 0.377; NIST20 scaffold 0.699 vs 0.682/0.669. Retrieval vs 49 PubChem decoys with highest Tanimoto to truth: NPLIB1 top-1 29.0% vs MassFormer 19.8%; NIST20 top-10 77.0% vs 71.6%; CASMI22 (303 spectra, PubChem library) top-1 12.9% vs 8.6% for NEIMS — "absolute performance is low". ~1 CPU-s per spectrum. Does not model collision energy, adduct switching, instrument type, rearrangements — [ICEBERG arXiv v2](https://arxiv.org/html/2304.13136v2)

**ICEBERG 2.0 (Wang, Manjrekar, …, Coley; bioRxiv 2025-05-28)**
- Simulates CID with collision energy and polarity awareness; NIST20 [M+H]+ (530,640 spectra, 25,541 molecules, 8:1:1): top-1 retrieval 25.1% → 40.0% (random split) and 22.9% → 33.5% (scaffold split) after contrastive finetuning; 92% of correct structures within top-10; case-study candidate sets of 55–8,413 structures. Pretrained NIST20 weights are available only to NIST'20 license holders; code at coleygroup/ms-pred — [ICEBERG 2.0 bioRxiv](https://www.biorxiv.org/content/10.1101/2025.05.28.656653v1.full)
- MSG-compatible ICEBERG weights/codebase released 2025-10-27 — [MassSpecGym README](https://github.com/pluskal-lab/MassSpecGym); MSG simulation-bonus leaderboard entry: cosine 0.58, JS 0.48, HR@1/5/20 45.95/75.43/91.69 — [simulation_bonus.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/simulation_bonus.csv)

**GLACIER (Wang, Wang, Coley; arXiv 2026-06-28, v2 2026-10-05; NeurIPS 2026)**
- Single-stage transformer "fragment detector" (object-detection analogy) replacing the two-stage generate+score; MSG Mass Challenge R@1 69.95% (w/ CF) / 69.69% (w/o) vs ICEBERG 2.0 63.95%; Formula Challenge 49.88% vs 44.35%; NIST20 random top-1 0.525 (w/ CF) / 0.390 (w/o) vs ICEBERG 2.0 0.335, scaffold 0.460 vs 0.316; MSG cosine 0.58 vs 0.47; 7.95× faster (1.3 ms vs 10.8 ms per spectrum on A5000). Contrastive finetuning samples negatives from PubChem and random mutation; it raises retrieval but slightly lowers spectral similarity and the authors note a shortcut-learning risk. Code: coleygroup/ms-pred; weights not mentioned in page — [GLACIER arXiv v2](https://arxiv.org/html/2606.29161v2); [abs](https://arxiv.org/abs/2606.29161)

**FraGNNet (Young et al.; TMLR Aug 2025)**
- Probabilistic distribution over fragments of a deterministic bond-breaking DAG; NIST20 InChIKey split cosine (C_BIN) 0.736 (D4) vs ICEBERG 0.707, MassFormer 0.639, NEIMS 0.635, GrAFF-MS 0.596; scaffold split 0.678 vs 0.636. Retrieval (truth + 49 high-Tanimoto PubChem decoys, ~4,000 queries): InChIKey split top-1/3/5 FraGNNet 36.0/66.3/78.4 vs ICEBERG 36.0/63.9/75.4 vs NEIMS 26.0; scaffold split 30.3/59.8/73.2 vs ICEBERG 27.9/55.0/68.3. Evaluated merged spectra only; authors call for tests on unmerged spectra, more instruments and adducts — [FraGNNet arXiv v2](https://arxiv.org/html/2404.02360v2)
- MSG baseline: FraGNNet HR@1 46.64 (mass) / 31.93 (formula) — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3)

**FIORA (Nowatzky et al.; Nat. Commun. 2025-03-07, open access CC BY)**
- GNN predicting single-bond cleavage probabilities from local neighborhoods; default model trained on NIST'17 + MS-DIAL (74,401 spectra / 10,692 compounds); open-source "FIORA-OS" trained on MSnLib v1.0 (177,390 spectra / 15,967 compounds); covariates include instrument type; also predicts RT (R² 0.70, small data) and CCS (R² 0.93) — [FIORA (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11889238/)
- Median cosine (FIORA / CFM-ID / ICEBERG): test [M+H]+ 0.81/0.67/0.72; test [M−H]− 0.79/0.57/–; MSnLib [M+H]+ 0.65/0.48/0.58; CASMI 2016 [M+H]+ 0.77/0.70/0.71; CASMI 2022 [M+H]+ 0.29/0.38/0.36; CASMI 2022 [M−H]− 0.32/0.29/–. Cosine without precursor separates correct from incorrect candidates better. Generalization by structural similarity: median cosine ≥0.8 for Tanimoto 0.6–1.0 to training, 0.63 for Tanimoto 0.2–0.3. Limitations: single-step fragmentation only, no ring cleavage; low CASMI 2022 scores attributed to low peak coverage / data quality; only [M+H]+ and [M−H]− in default model. Code + OS weights MIT on GitHub/Zenodo; NIST'17 data license-restricted — [FIORA (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11889238/)

**GrAFF-MS / MassFormer / NEIMS (as baselines)**
- GLACIER's NIST20 retrieval table: GrAFF-MS top-1 0.165 (random) / 0.140 (scaffold); MassFormer 0.212 / 0.179; vs GLACIER 0.525 / 0.460 — [GLACIER arXiv v2](https://arxiv.org/html/2606.29161v2)
- MassFormer's analysis: an InChIKey-based split "was, in essence, a simple random split based on compound identity", whereas a scaffold split introduces distribution shift — [MassFormer arXiv](https://arxiv.org/pdf/2111.04824)

**Evidence that forward models improve de novo / candidate ranking**
- FRIGID's ICEBERG-guided remask-and-denoise (simulate candidate spectra at CE 10–90 eV, 20 ppm match, flag hallucinated fragments, remask corresponding tokens): MSG top-1 8.21% → 9.05%, top-10 9.82% → 12.23%; NPLIB1 top-10 20.15% → 25.27%; cost 6.58 s → 41.3 s per spectrum (10 rounds) — [FRIGID README](https://raw.githubusercontent.com/coleygroup/FRIGID/main/README.md)
- FOAM (ICEBERG + formula-constrained graph GA, NSGA-II on entropy similarity and SAScore): NIST20 holdout (4,925) true molecule encountered in 68.1% of searches; top-10 exact match ~31% after 3 generations; top-10 exact-match reaches 53.4% when ICEBERG similarity of the true molecule ≥ 0.8; but 95.2% of searches eventually found a decoy with equal-or-higher predicted similarity, and the authors state spectral prediction accuracy, not search, is the bottleneck; MSG (DiffMS+PubChem seeds): top-10 4.25% → 10.28%; performance drops when collision energies must be imputed (MSG vs NIST); ICEBERG scores 500 molecules × 3 CEs in ~30 s on an H100 — [FOAM arXiv](https://arxiv.org/html/2602.07709v1)
- LLM-based simulation (GIF, Nov 2025) reaches only cosine 0.36 on an MSG-derived QA set — [GIF arXiv](https://arxiv.org/abs/2511.09571)

**Licences**
- ICEBERG 2.0 NIST20 weights: NIST license holders only — [ICEBERG 2.0 bioRxiv](https://www.biorxiv.org/content/10.1101/2025.05.28.656653v1.full); MSG-trained ICEBERG weights public since 2025-10-27 — [MassSpecGym README](https://github.com/pluskal-lab/MassSpecGym); FRIGID bundles ICEBERG weights trained on each benchmark split on Zenodo (record 23543494), code Apache 2.0 — [FRIGID README](https://raw.githubusercontent.com/coleygroup/FRIGID/main/README.md); FIORA-OS (MSnLib-trained) MIT — [FIORA (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11889238/); DreaMS "NIST20 library is not publicly available due to licensing restrictions" — [DreaMS](https://www.nature.com/articles/s41587-025-02663-3); DiffMS paper under CC BY-NC-SA 4.0 (arXiv license; code license not confirmed) — [DiffMS abs](https://arxiv.org/abs/2502.09571)

### Inferences
- For CASMI class 2 (same-formula isomers), a forward model scoring every PubChem/COCONUT isomer is the single most evidence-backed lever: on comparable candidate constructions it roughly quadruples hit@1 over fingerprint retrieval. GLACIER code (ms-pred) and MSG-trained ICEBERG weights are usable without NIST licences; FIORA-OS adds negative mode and a different inductive bias for ensembling.
- Expect substantial degradation on CASMI's timsTOF natural products: every forward model lost 0.4–0.5 cosine on CASMI 2022 data relative to in-library test sets, and FOAM shows collision-energy imputation hurts. Mitigations supported by the literature: score multiple collision energies and take max/mean (FRIGID uses CE 10–90 eV; ICEBERG 2.0 is CE-aware), use entropy similarity rather than cosine (FOAM), drop the precursor peak when ranking (FIORA), and fine-tune the simulator on the competition's own timsTOF training spectra (enveda-180) since all models generalize poorly beyond Tanimoto ~0.3 from training.
- Forward scores are better as a reranking feature than as a sole scorer: FOAM shows decoys out-score the truth in most searches, so a LightGBM ranker that combines forward-model similarity (multiple CEs, multiple models) with fingerprint/embedding scores and a database prior is the right architecture.

### Gaps
- GLACIER released code but the page did not confirm released weights; whether MSG-trained GLACIER weights exist as of Oct 2026 is unverified.
- No forward model has published results on Bruker timsTOF data; instrument type is a covariate in FIORA only.
- GrAFF-MS's own paper was not fetched; its numbers come from GLACIER's and FraGNNet's tables.
- MARASON's paper could not be located (only its leaderboard row).

---

## Key Question 4: De novo generators — MSNovelist, Spec2Mol, DiffMS, MADGEN, MS-BART, MSAnchor, MBGen, FRIGID, DualLGD, FOAM, MS2Mol/EnvedaDark, MS2Prop, PRISM; what is realistic for class 3

### Takeaway
On MCES-disjoint MSG test molecules with the formula given, verified exact-match top-1 has risen from 0% (2024) to 2.3% (DiffMS, mid-2025), 7.6% (MBGen, Feb 2026) and 9.05% (FRIGID after leak correction, 2026), with a 23.9% claim (DualLGD, May 2026) still unverified; on the natural-product NPLIB1 (similarity-leaky split) numbers are 1.5–3× higher; Enveda's own MS2Mol got 21% "close match" on 226 truly novel natural products in 2023. For CASMI class 3 (not in PubChem), a realistic expectation is single-digit to low-teens exact-match rates even with a perfect formula, so de novo mainly adds value through (a) near-miss structures that still score on MRR only if exactly right — i.e. little — and (b) confidence gating.

### Cited Findings

**MSNovelist (Stravs et al., Nat. Methods 2022)**
- CSI:FingerID fingerprint + formula → LSTM SMILES decoder trained on 1,232,184 structures (HMDB, COCONUT, DSSTox); 3,863 GNPS spectra: correct structure rank-1 25% (vs 39% for CSI:FingerID database search), 45% within top-128; CASMI 2016 (127 positive spectra): 26% top-1, 57% retrieved; on the 47 spectra correctly identified by database search, 64% top-1; naive generator without fingerprint input still 24% top-1 on CASMI 2016; "does not quantify performance on structures absent from training or databases" — [MSNovelist (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/)
- As MIST+MSNovelist on MSG: 0.00% top-1/top-10, MCES@1 45.55; NPLIB1 5.40% / 11.04% — [DiffMS arXiv v2](https://arxiv.org/html/2502.09571v2)

**Spec2Mol (Litsa et al., Commun. Chem. 2023)**
- Encoder–decoder (speech-to-text inspired) producing SMILES; "on par performance when compared to existing fragmentation tree methods" in the authors' words — [Spec2Mol (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10290119/); 0.00% top-1 on both NPLIB1 and MSG in DiffMS's re-implementation, Tanimoto 0.12 — [DiffMS arXiv v2](https://arxiv.org/html/2502.09571v2)

**DiffMS (Bohde et al., ICML 2025; arXiv v2 2025-05-27)**
- MIST-style formula transformer encoder + discrete graph diffusion decoder constrained to the heavy-atom composition of a given formula (hydrogens implicit, so generated molecules may differ in H count); decoder pretrained on 2.8M fingerprint–structure pairs (DSSTox, HMDB, COCONUT, MOSES) with NPLIB1/MSG test+val molecules removed. NPLIB1: 8.34% / 15.44% (top-1/top-10), MCES 11.95/9.23, Tanimoto 0.35/0.47; MSG: 2.30% / 4.25%, MCES 18.45/14.73, Tanimoto 0.28/0.39. Pretraining scaling on NPLIB1: 0 → 0.2M → 0.8M → 1.2M → 2.8M structures gives top-1 2.22 → 3.61 → 5.60 → 7.22 → 8.34%; encoder pretraining 4.36% → 8.34%. Formula source ablation: MIST-CF-predicted formulas give 7.03% (NPLIB1) and 1.86% (MSG) vs 8.34% / 2.30% with true formulas — [DiffMS arXiv v2](https://arxiv.org/html/2502.09571v2)

**MADGEN (Wang, Chen, Liu, Hassoun; ICLR 2025)**
- Two-stage: contrastive scaffold retrieval (SPA 57.8% NIST23, 37.9% CANOPUS, 34.8% MSG) then attention-based completion; predictive-retriever top-1: NIST23 10.3%, CANOPUS 1.0%, MSG 0.8%; oracle-scaffold top-1: 49.0% / 8.9% / 18.8% (MSG top-10 38.6%) — i.e. knowing the scaffold is most of the problem — [MADGEN arXiv v1](https://arxiv.org/html/2501.01950v1); leaderboard lists MADGEN at 1.31% / 1.54% on MSG — [de_novo_bonus.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/de_novo_bonus.csv)

**MS-BART (arXiv 2025-10-23)**
- BART over SELFIES + fingerprint tokens, pretrained on ~4M MSG unlabeled molecules (removing molecules within MCES < 2 of the test fold), fed MIST-predicted fingerprints binarized at ε = 0.11 (MSG); MSG 1.07% / 1.11% (full InChIKey) and 1.26% / 1.28% (2D InChIKey); NPLIB1 7.45% / 10.99%; with gold fingerprints 47.56% / 64.62% on MSG and 73.50% / 79.12% on NPLIB1 — the fingerprint-prediction step is the bottleneck; formulas used only for reranking; 3 s/spectrum vs ~160 s for DiffMS — [MS-BART arXiv](https://arxiv.org/html/2510.20615v1)

**MSAnchor (AAAI-26, published 2026-03-14) and MBGen (arXiv 2026-02-02)**
- MSAnchor: anchor-extended scaffolds marking side-chain attachment points + conditional information bottleneck; SOTA claim on CANOPUS and MSG, largest gains on complex molecules; no numbers on abstract page — [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/37064); DualLGD's table: MSG 2.68% / 4.67%, NPLIB1 8.51% / 16.90% — [DualLGD arXiv](https://arxiv.org/html/2605.07048v1)
- MBGen: bond-centric diffusion with many-body attention; "improvements of up to 230%"; code github.com/biomed-AI/MBGen — [MBGen abs](https://arxiv.org/abs/2602.01643); DualLGD's table: MSG 7.58% / 12.54%, NPLIB1 12.20% / 22.29% — [DualLGD arXiv](https://arxiv.org/html/2605.07048v1)

**FRIGID (Bohde et al., ICML 2026)**
- 247M-parameter masked diffusion LM over SAFE tokens, conditioned via cross-attention on a MIST-predicted 4096-bit Morgan fingerprint and per-element formula counts; NGBoost predicts token length from formula; decoder pretrained on up to 230M SAFE structures (test/val InChIKeys excluded); MIST encoders trained with GLACIER-simulated spectra for 2M PubChem (NPLIB1) / 4M MSG molecules. Corrected results (formula known): NPLIB1 14.16% / 25.27% (DiffMS 8.34% / 15.44%); MSG 9.05% / 12.23% (DiffMS 2.30% / 4.25%); 6.58 s/spectrum base, ~20× faster than DiffMS (131.2 s). Original 25.03% / 18.29% retracted for leakage — [FRIGID README](https://raw.githubusercontent.com/coleygroup/FRIGID/main/README.md); the published abstract still claims >18% MSG top-1 and log-linear inference-time scaling — [PMLR v306](https://proceedings.mlr.press/v306/bohde26a.html)

**DualLGD (arXiv 2026-05-07; self-reported)**
- Dual-stream atom/bond (line-graph) diffusion with incidence-constrained cross-attention; encoder initialized from DiffMS weights; MSG 23.89% / 33.08%, NPLIB1 34.37% / 44.96%; abstract claims ~3× previous SOTA and that an un-pretrained DualLGD beats the previous best pretrained model; comparison table omits FRIGID — [DualLGD arXiv](https://arxiv.org/html/2605.07048v1); [abs](https://arxiv.org/abs/2605.07048)

**Test-time-tuned LMs (ICLR 2026 workshop)**: MSG 3.16%, NPLIB1 12.88% end-to-end from spectrum + formula with transfer from simulated data and test-time tuning — [IBM Research](https://research.ibm.com/publications/test-time-tuned-language-models-enable-end-to-end-de-novo-molecular-structure-generation-from-msms-spectra)

**OMG (Anal. Chem. 2025)**: transfer + reinforcement learning; MSG top-1 0.32–0.85%, top-10 2.55–2.82% — [de_novo_bonus.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/de_novo_bonus.csv)

**MS2Mol and EnvedaDark (Butler, …, Healey; ChemRxiv 2023, DOI 10.26434/chemrxiv-2023-vsmpx)**
- Generative sequence transformer for de novo structure prediction; EnvedaDark = experimental spectra for 226 natural products "not currently found in major databases"; MS2Mol predicts 21% within "close-match" and 62% within "meaningful similarity", both reported as significant improvements over database matching; a confidence scorer gives 98% (meaningful) and 63% (close match) on the top-10% most confident predictions; numeric Tanimoto cutoffs are not in the abstract — [OpenAlex record of ChemRxiv DOI](https://doi.org/10.26434/chemrxiv-2023-vsmpx); announcement 2023-06-21 — [BioSpace/Business Wire](https://www.biospace.com/enveda-biosciences-unveils-new-ai-algorithm-to-unlock-nature-s-chemical-code)

**MS2Prop (Voronov et al., Enveda; bioRxiv 2022-10-10)**
- Transformer predicting 10 RDKit properties directly from spectra; ~1.25M spectra / ~45k molecules (public + proprietary); average R² 0.928 (known molecules, spectrum-disjoint), 0.735 (novel structures), 0.719 (CASMI 2022); multi-stage database/CSI:FingerID approach reaches R² ≈ 22% on novel compounds; 2 ms/spectrum vs 27 s for CSI:FingerID; "random splits overestimate performance" — [MS2Prop bioRxiv](https://www.biorxiv.org/content/10.1101/2022.10.09.511482v1.full)

**PRISM (Enveda + Microsoft, announced 2024-05-29)**
- "Pretrained Representations Informed by Spectral Masking", trained on "over a billion unlabeled mass spectra", translates spectra into representations of structures or properties; runs on Azure; no quantitative results, paper, weights or code in the announcement — [SynBioBeta](https://www.synbiobeta.com/read/enveda-biosciences-collaborates-with-microsoft-to-unveil-prism-revolutionizing-drug-discovery-with-ai); [Business Wire 2024](https://www.businesswire.com/news/home/20240529298878/en/Enveda-Biosciences-Announces-Microsoft-Collaboration-and-Reveals-Foundation-Model-to-Read-and-Translate-Chemistry)
- The CASMI 2026 release describes PRISM as trained on more than one billion spectra and says the competition helps grow PRISM; Enveda's blog (via secondary summary) cites 1.2 billion spectra, about half from public repositories (GNPS, MetaboLights, Metabolomics Workbench) — [Webull mirror of Business Wire 2026-09-15](https://www.webull.com/news/15582421858583552); [search summary of Enveda blog](https://structure-function.notion.site/PRISM-A-foundation-model-for-life-s-chemistry-Enveda-Biosciences-8a3b58b127df4e728978f3e5350e7df5)

### Inferences
- Realistic class-3 expectation: with an inferred formula, the best open, verified generator (FRIGID) would deliver ~7–9% exact top-1 and ~10–12% top-10 on MSG-hard molecules; natural products may be somewhat easier (NPLIB1 14% / 25%) but NPLIB1 is similarity-leaky. If DualLGD's 24% / 33% replicates, class-3 could contribute materially; until then budget de novo as a small MRR increment (each exact hit in top-25 adds at most 1/N_test_molecules × 1/rank).
- Because MRR@25 only rewards exact InChIKey14, de novo's advantage in "near-miss" structures (Tanimoto 0.4–0.6) is worthless for scoring; the only ways de novo helps class 3 are exact hits and using its outputs as seeds for forward-model-guided local search (FOAM: true molecule encountered in 33% of MSG searches after one generation vs 5.8% present in raw DiffMS samples — but top-1 exact dropped, so the reranker must be good).
- Gold-fingerprint oracles (MS-BART 47.6% MSG, MADGEN oracle scaffold 18.8%) show the bottleneck is spectrum → fingerprint/scaffold inference, not decoding; investment in the spectrum encoder (more/augmented data, simulated spectra as in FRIGID's MIST training with GLACIER-simulated spectra for 4M molecules) pays off more than decoder work.
- MS2Mol's confidence scorer result (98% meaningful similarity in the top-10% confident) supports a gating strategy: emit de novo candidates only where a calibrated confidence is high and database retrieval is weak (e.g., no candidate with forward-model similarity > threshold), otherwise fill the 25 slots with database isomers.

### Gaps
- EnvedaDark's "close match" / "meaningful similarity" Tanimoto thresholds were not retrievable (ChemRxiv blocked; abstract does not define them); EnvedaDark itself does not appear to be publicly downloadable from the sources found.
- No PRISM paper, benchmark numbers or weights were found; all PRISM claims are company statements.
- DualLGD, MBGen, MSAnchor numbers come from their own/one another's tables; none appear on the official MSG CSVs yet.
- None of the de novo papers report tautomer-canonical InChIKey14 matching; MS-BART's full vs 2D InChIKey gap (1.07 vs 1.26%) is the only hint of how much stereo/tautomer handling moves the number.

---

## Key Question 5: Self-supervised spectral pretraining and embeddings — DreaMS/GeMS, PRISM, MS2DeepScore (1.0/2.0), Spec2Vec

### Takeaway
DreaMS (Nat. Biotechnol. 2025; MIT-licensed, weights public) is the only open, peer-reviewed spectral foundation model: pretrained on tens of millions of GNPS spectra it beats 44 classical similarity measures for same-compound library retrieval within a 10 ppm precursor window and matches MIST on fingerprint retrieval, with the explicit finding that data quality beats data scale; MS2DeepScore/Spec2Vec are weaker but still useful analog-search scores; PRISM is larger (claimed >1B spectra) but closed.

### Cited Findings
- GeMS mined from GNPS/MassIVE (4,467 datasets, 249,422 MS/MS files, ~714M spectra); quality tiers GeMS-A (42M), -B (100M), -C (201M); LSH deduplication yields GeMS-A10 used for pretraining; positive mode, singly charged, precursor < 1,000 Da, centroided only. Model: 116M parameters, 7-layer transformer, 1,024-d embeddings, Graphormer-style attention over pairwise mass differences; objectives: masked peak prediction (30% of peaks masked, classification over mass bins) and retention-order prediction — [DreaMS, Nat. Biotechnol. 2025](https://www.nature.com/articles/s41587-025-02663-3)
- Downstream: zero-shot embedding cosine correlates better with Tanimoto/MCES than MS2DeepScore; after contrastive fine-tuning (MoNA histogram-disjoint ~25,000 spectra / 5,500 InChI connectivity blocks; positives share the 14-character InChIKey prefix, negatives within 0.05 Da precursor; margin 0.1) DreaMS outperforms 44 spectral similarity measures in library retrieval within a 10 ppm precursor window (benchmark ~750,000 NIST20 pairs); analog search evaluated as AUROC at MCES distance k ∈ {0..7} vs MS2DeepScore, modified cosine, spectral entropy (values in Extended Data Fig. 5, not retrieved); fingerprint prediction/retrieval on par with MIST on the CANOPUS benchmark; fluorine detection precision 0.91 at recall 0.57 on 17,052 in-house Orbitrap spectra (SIRIUS ≤ 0.51 precision) — [DreaMS](https://www.nature.com/articles/s41587-025-02663-3)
- Robustness/shift findings: embeddings cluster by structure across adducts and collision energies; "data quality matters more than data scale: performance drops when lower-quality GeMS-B data is added"; fine-tuned embeddings more robust to input quality than other methods; positive mode only, no MS1 — [DreaMS](https://www.nature.com/articles/s41587-025-02663-3)
- DreaMS Atlas: 3-NN graph over 34M representative spectra covering 201M GeMS-C spectra plus MoNA and NIST20 nodes; median shortest path from random node to a library node = 6 edges — [DreaMS](https://www.nature.com/articles/s41587-025-02663-3)
- Availability: code pluskal-lab/DreaMS (Zenodo 13843034), weights Zenodo 10997887, GeMS/Atlas/fine-tuning data on Hugging Face; docs show MIT license; `dreams_embeddings()` returns 1024-d per spectrum from .mgf; ANN library matching and molecular networking utilities — [DreaMS](https://www.nature.com/articles/s41587-025-02663-3); [DreaMS docs](https://dreams-docs.readthedocs.io/en/latest/)
- MassSpecGym uses GeMS-A10 (24M spectra) as its unlabeled companion set — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3)
- MS2DeepScore (J. Cheminform. 2021): Siamese network predicting Tanimoto from two spectra; trained on >100,000 spectra / ~15,000 compounds; RMSE ≈ 0.15 on 3,600 spectra of 500 unseen compounds (≈0.1 for the most confident subset); outperforms classical measures for retrieving chemically related pairs — [MS2DeepScore](https://link.springer.com/article/10.1186/s13321-021-00558-4)
- MS2DeepScore 2.0 (bioRxiv 2024, DOI 10.1101/2024.03.25.586580): cross-ionization-mode chemical similarity prediction plus a prediction-quality estimate flagging low-information or out-of-distribution spectra — [opus4 record](https://opus4.kobv.de/opus4-hs-duesseldorf/frontdoor/index/index/year/2024/docId/4788)
- Spec2Vec: Word2Vec-style peak embeddings; "notably higher correlation with actual structural similarities than the modified cosine and cosine baselines" — [Spec2Vec bioRxiv](https://www.biorxiv.org/content/10.1101/2020.08.11.245928.full.pdf); MIST's contrastive spectral similarity: top-0.1% MIST-ranked pairs average structural similarity 0.32 vs 0.19 for Spec2Vec — [MIST bioRxiv](https://www.biorxiv.org/content/10.1101/2022.12.30.522318v1.full)
- PRISM: >1B (press) / 1.2B (blog) unlabeled spectra, masked-spectrum pretraining; no public paper, metrics or weights found — [SynBioBeta](https://www.synbiobeta.com/read/enveda-biosciences-collaborates-with-microsoft-to-unveil-prism-revolutionizing-drug-discovery-with-ai); [Webull mirror of 2026 release](https://www.webull.com/news/15582421858583552)

### Inferences
- For CASMI class 1 (reference spectra exist for the molecule), DreaMS fine-tuned similarity within a precursor window is the best-documented library-matching score and should be ensembled with modified cosine/entropy; it also gives an analog-search signal that can propose scaffolds for class 2/3 candidates (nearest library neighbors within MCES ≤ 5).
- DreaMS's "quality over scale" result argues against indiscriminately adding noisy GNPS spectra to a competitor's training set and for weighting the clean timsTOF enveda-180 subset.
- The 1,024-d DreaMS embedding is a cheap, strong input feature for a spectrum → fingerprint head or a learned reranker (it matched MIST on CANOPUS retrieval without formula annotation), which sidesteps MIST's dependence on SIRIUS subformula annotation.

### Gaps
- Exact DreaMS library-matching/analog-search numbers (AUROC tables) are in figures not retrievable here.
- No evidence was found on DreaMS behavior on Bruker timsTOF spectra specifically; pretraining data is GNPS (predominantly Orbitrap/QTOF).
- MS2DeepScore 2.0 quantitative results were not accessible.

---

## Key Question 6: Evaluation-protocol lessons — split design, leakage (tautomers/stereo/formula), instrument shift, honest novel-compound measurement

### Takeaway
The field's consensus since 2024 is that identity-disjoint (InChIKey) splits behave like random splits and inflate scores (test molecules with Tanimoto > 0.85 to training), that MCES- or scaffold-disjoint splits are required to measure novel-compound performance, and that leakage can enter through side channels (formula-selected training data, pretraining corpora, stereo/tautomer variants); every method that reported out-of-domain CASMI numbers lost 50–70% of its in-domain performance.

### Cited Findings
- 2D-InChIKey-disjoint splitting lets near-duplicates leak (Tanimoto > 0.85 test–train pairs); MSG's MCES ≥ 10 agglomerative split, stratified by instrument/CE/adduct/frequency, fixes this — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3)
- MassFormer: an InChIKey split "was, in essence, a simple random split based on compound identity"; scaffold split introduces real train–test shift — [MassFormer arXiv](https://arxiv.org/pdf/2111.04824); ICEBERG shows the scaffold split "better separates models" (NIST20 scaffold cosine 0.699 vs 0.682/0.669 while random split is near-tied) — [ICEBERG arXiv v2](https://arxiv.org/html/2304.13136v2)
- NPLIB1 (CANOPUS/GNPS) remains the second standard benchmark but DualLGD notes its train and test molecules are structurally similar (Tanimoto > 0.85) — [DualLGD arXiv](https://arxiv.org/html/2605.07048v1); consistent with every method scoring 1.5–4× higher on NPLIB1 than on MSG (e.g., FRIGID 14.16% vs 9.05%, DiffMS 8.34% vs 2.30%) — [FRIGID README](https://raw.githubusercontent.com/coleygroup/FRIGID/main/README.md)
- Side-channel leakage case: FRIGID's original 18.29% MSG / 25.03% NPLIB1 were produced with MIST encoders whose training data had been selected using test-set formula information; corrected numbers are 9.05% / 14.16% — [FRIGID README](https://raw.githubusercontent.com/coleygroup/FRIGID/main/README.md)
- FOAM excluded MIST+MolForge, Gaia-01 and TTT baselines "because the authors could not confirm the absence of data leakage" — [FOAM arXiv](https://arxiv.org/html/2602.07709v1)
- Pretraining-corpus hygiene: DiffMS removed all NPLIB1/MSG test+val molecules from its 2.8M fingerprint–structure pretraining set — [DiffMS arXiv v2](https://arxiv.org/html/2502.09571v2); MS-BART removed pretraining molecules within MCES < 2 of the MSG test fold and Tanimoto > 0.5 to the NPLIB1 test set — [MS-BART arXiv](https://arxiv.org/html/2510.20615v1); FRIGID excluded test/val InChIKeys from 230M SAFE pretraining structures — [FRIGID README](https://raw.githubusercontent.com/coleygroup/FRIGID/main/README.md)
- Stereo/tautomer handling: MS gives the same spectrum to all stereoisomers of one connectivity — [MassBank manual](https://mssj.jp/english/about/pdf/MassBank_manual-en.pdf); DreaMS defines positives by shared 14-character InChIKey prefix and splits by Murcko-histogram-disjoint groups — [DreaMS](https://www.nature.com/articles/s41587-025-02663-3); MS-BART: full-InChIKey vs 2D-InChIKey top-1 on MSG 1.07% vs 1.26% — [MS-BART arXiv](https://arxiv.org/html/2510.20615v1); DualLGD matches by InChI — [DualLGD arXiv](https://arxiv.org/html/2605.07048v1); contrastive-DG paper groups by first InChIKey block for its scaffold split — [arXiv 2602.00547](https://arxiv.org/html/2602.00547)
- Random vs structure-disjoint vs time/experiment-disjoint tiers (MS2Prop): R² 0.928 (known) → 0.735 (novel structures) → 0.719 (CASMI 2022); "random splits overestimate performance" — [MS2Prop bioRxiv](https://www.biorxiv.org/content/10.1101/2022.10.09.511482v1.full)
- Out-of-domain collapse on CASMI 2022: FIORA median cosine 0.29 (vs 0.81 in-domain), ICEBERG 0.36 (vs 0.72), CFM-ID 0.38 (vs 0.67) — attributed to low peak coverage and data quality — [FIORA (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11889238/); ICEBERG CASMI22 top-1 12.9% vs 29.0% on NPLIB1 — [ICEBERG arXiv v2](https://arxiv.org/html/2304.13136v2); MS2MetGAN removed 16 CASMI 2022 spectra whose compounds appeared in training — [MS2MetGAN abs](https://arxiv.org/abs/2603.13342)
- Candidate-pool size dominates reported accuracy: the same model scores 42.16% Hit@1 on fixed 256-way retrieval but 3.56% Hit@1 / 17.58% Hit@10 against a ~26k-molecule global pool — [arXiv 2602.00547](https://arxiv.org/html/2602.00547); ICEBERG/FraGNNet use 49 hardest PubChem decoys (top-1 ~36%) — [FraGNNet arXiv v2](https://arxiv.org/html/2404.02360v2); JESTR uses all PubChem formula isomers (mean 1,322–2,494) — [JESTR arXiv v2](https://arxiv.org/html/2411.14464v2)
- Instrument shift: cross-library matching between a QqTOF and an Orbitrap library works best at CE 20–50 eV (QqTOF) vs 30–60 NCE (Orbitrap) — [PMC6359582](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6359582/); the one 2026 "cross-instrument" DG paper never isolates instrument as a variable (MassBank only, scaffold split) — [arXiv 2602.00547](https://arxiv.org/html/2602.00547); DreaMS: only 98%-Orbitrap/QTOF-style GNPS data, positive mode — [DreaMS](https://www.nature.com/articles/s41587-025-02663-3); MSG: 98% Orbitrap/QTOF — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3)
- Shortcut risk from contrastive finetuning against decoys: GLACIER notes a possible shortcut-learning risk and that harsher CF improves retrieval but reduces spectral similarity/coverage — [GLACIER arXiv v2](https://arxiv.org/html/2606.29161v2); DreaMS finds adding lower-quality data hurts — [DreaMS](https://www.nature.com/articles/s41587-025-02663-3)
- Honest "novel compound" evaluation designs in use: MSG MCES ≥ 10 — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3); EnvedaDark (226 natural products absent from major databases) — [MS2Mol DOI](https://doi.org/10.26434/chemrxiv-2023-vsmpx); blind CASMI contests (2D-structure best 26–38%) — [CASMI 2022 results](https://fiehnlab.ucdavis.edu/casmi/casmi-2022-results); ICEBERG 2.0's prospective case studies — [ICEBERG 2.0 bioRxiv](https://www.biorxiv.org/content/10.1101/2025.05.28.656653v1.full)

### Inferences
- A CASMI 2026 local validation should (a) hold out molecules by MCES or scaffold cluster, not by InChIKey, and group all tautomer/stereo variants with their connectivity block; (b) stratify by novelty class: class 1 = held-out spectra of molecules with other spectra in train, class 2 = molecules absent from train but present in PubChem/COCONUT, class 3 = molecules absent from the candidate database; (c) hold out by instrument (train on non-timsTOF, validate on enveda-180 timsTOF, and vice versa) because no public result quantifies the timsTOF gap; (d) use the full mass-window candidate pool, not 256 candidates, since the pool size alone moves hit@1 by an order of magnitude.
- Leakage audits should check not just structures but derived channels: formula-based candidate lists, pretraining corpora (COCONUT contains many test-like natural products), simulated-spectra augmentation sets, and PubChem popularity priors (which encode "known-ness" and will overfit class 1/2 vs class 3).
- Because exact-match metrics on hard splits are tiny and noisy (MSG 95% CIs in the CSVs are ±0.3–1 pt for retrieval), decisions between pipeline variants need bootstrap CIs and per-class breakdowns rather than single aggregate MRRs.

### Gaps
- No paper quantifies tautomer-induced leakage or the effect of tautomer-canonical InChIKey14 scoring; MS-BART's 0.2-pt full-vs-2D-InChIKey gap is the only datapoint.
- No published timsTOF vs Orbitrap/QTOF ML transfer study was found; the instrument-shift risk for CASMI 2026 is unmeasured in the literature.

---

## Key Question 7: Organized challenges/leaderboards since 2023 for spectra → structure

### Takeaway
Between CASMI 2022 (Metabolomics Society 2022, UC Davis) and Enveda's CASMI 2026 on Kaggle there was no organized blind spectra-to-structure contest; the MassSpecGym pull-request leaderboard (NeurIPS 2024 →) is the only standing ML leaderboard, and no NeurIPS/ICML/Metabolomics Society competition on this task in 2023–2025 was found.

### Cited Findings
- CASMI 2022: raw LC-HRMS/MS in +ESI and −ESI for 500 compounds, four categories (adducts, formulas, ClassyFire classes, 2D structures), 16 participant groups; best 2D-structure scores 38% (Nikolic_KUCA, 55 attempts), 26/29% (Dührkop), 25/28% (Nothias, Rutz); several challenges removed for errors — [CASMI 2022 results](https://fiehnlab.ucdavis.edu/casmi/casmi-2022-results); [CASMI site](https://fiehnlab.ucdavis.edu/casmi)
- CASMI 2026: Kaggle, 2026-09-14 → 2026-12-14, $50,000 across top five ($16,000 first), free; ~2.5M training spectra from 275,000 molecules combining open libraries with Enveda-180 (~1.16M spectra from 184,330 synthetic small molecules, ChemRxiv preprint); test ≈ 400 unpublished molecules represented by ≈ 2,500 spectra, "real or potential natural molecules and their analogs" generated on Enveda's platforms; supported by CASMI founders Emma Schymanski and Steffen Neumann; lead organizer David Healey; winning methods to be open-sourced; test set to persist as a benchmark; "first challenge since 2022 and the first designed to reach the broader machine learning community"; motivation: ~10% of signals in untargeted studies are matched to a known molecule (Gauglitz et al. 2022) — [Webull mirror of Business Wire 2026-09-15](https://www.webull.com/news/15582421858583552)
- MassSpecGym leaderboard: results submitted via PR to `results/` and rendered at massspecgym.onrender.com; entries through 2025-10-23 (MS-BART) and ICEBERG MSG weights 2025-10-27 — [GitHub README](https://github.com/pluskal-lab/MassSpecGym); [de_novo.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/de_novo.csv)
- Searches for "CASMI 2024", "CASMI 2025", NeurIPS/ICML 2025 workshop challenges, and a MassSpecGym competition returned no such events; results only surfaced CASMI 2022 and CASMI 2026 — [Fiehn lab CASMI page](https://fiehnlab.ucdavis.edu/casmi); [ELLIS/CIIRC MSG news](https://ellis.ciirc.cvut.cz/?p=5666)
- Derived benchmarks spun off MSG: MassSpecGym QA-sim (LLM fragmentation reasoning) — [GIF arXiv](https://arxiv.org/abs/2511.09571); a simulated multimodal (MS+IR+NMR) MRR benchmark (MSSD; MRR 0.976 with MoE fusion) exists but is simulation-only and not comparable — [arXiv 2609.14360](https://arxiv.org/abs/2609.14360)

### Inferences
- The press release's test-set size (~2,500 spectra) differs from the competition page figure quoted in the task context (~1,500 spectra); the Kaggle data description should be treated as authoritative.
- CASMI 2022's 2D-structure ceiling (26–38% with priority/bonus lists, formula categories at 94–95%) on Orbitrap/QTOF unknowns is a reasonable prior for what expert pipelines (SIRIUS/CSI:FingerID + MetFrag + curation) achieve on blind data; the current CASMI 2026 public LB (~0.46–0.50 MRR@25) is already above that because MRR@25 credits ranks 2–25 and because many test molecules fall in class 1.

### Gaps
- Whether the Metabolomics Society ran any informal CASMI-style session in 2023–2025 could not be confirmed; no results pages exist.
- The Enveda-180 ChemRxiv preprint itself was not retrieved (instrument settings, CE ramps, adduct coverage would be valuable).

---

## Key Question 8 (from the objective): Concrete lessons for the five CASMI 2026 core challenges

### Takeaway
The literature points to a layered system: library/DreaMS matching for class 1, forward-model (GLACIER/ICEBERG/FIORA) reranking of full-formula isomer pools plus candidate-aware fingerprint/embedding scorers and a learned ranker for class 2, confidence-gated FRIGID/DiffMS-style generation with forward-model refinement for class 3, instrument-stratified fine-tuning on enveda-180 for timsTOF shift, and MCES/scaffold- and instrument-disjoint, class-stratified validation with leakage audits.

### Cited Findings
- Candidate coverage / class 2: fingerprint retrieval over 256 mass-matched candidates = 14.6–15.1% hit@1 (MIST/JESTR) vs forward-simulation ranking 64–70% R@1 (ICEBERG 2.0/GLACIER) and 44–50% on same-formula pools — [retrieval.csv](https://raw.githubusercontent.com/pluskal-lab/MassSpecGym/main/results/retrieval.csv); [GLACIER arXiv v2](https://arxiv.org/html/2606.29161v2); JESTR's candidate regularization lifts rank@1 6–37% relative — [JESTR arXiv v2](https://arxiv.org/html/2411.14464v2); MIST contrastive fine-tuning with Tanimoto-weighted PubChem isomer decoys — [MIST bioRxiv](https://www.biorxiv.org/content/10.1101/2022.12.30.522318v1.full)
- Isomer discrimination limits: 7/10 MSNovelist errors were close isomers; some isomers fragment indistinguishably — [MSNovelist (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/); FOAM: decoys out-score the truth in 95.2% of searches — [FOAM arXiv](https://arxiv.org/html/2602.07709v1); ICEBERG 2.0 uses CE-aware simulation and contrastive finetuning to reach 40% top-1 on NIST20 [M+H]+ — [ICEBERG 2.0 bioRxiv](https://www.biorxiv.org/content/10.1101/2025.05.28.656653v1.full)
- De novo for class 3: verified MSG formula-given top-1 9.05% (FRIGID), top-10 12.23%; formula inference costs ~0.4 pts (DiffMS 2.30 → 1.86) — [FRIGID README](https://raw.githubusercontent.com/coleygroup/FRIGID/main/README.md); [DiffMS arXiv v2](https://arxiv.org/html/2502.09571v2); MS2Mol confidence gating: top-10% confident → 98% meaningful similarity — [MS2Mol DOI](https://doi.org/10.26434/chemrxiv-2023-vsmpx)
- Instrument/chemistry shift: in-domain cosine 0.7–0.8 → CASMI 2022 0.29–0.38 for all simulators — [FIORA (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11889238/); cross-platform library matching requires matching CE ranges (QqTOF 20–50 eV ≈ Orbitrap 30–60 NCE) — [PMC6359582](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6359582/); FOAM: imputed collision energies lower simulation accuracy — [FOAM arXiv](https://arxiv.org/html/2602.07709v1); DreaMS: quality over scale — [DreaMS](https://www.nature.com/articles/s41587-025-02663-3)
- Validation design: MCES ≥ 10 split, stratified by instrument/CE/adduct — [MassSpecGym arXiv v3](https://arxiv.org/html/2410.23326v3); formula-channel leakage (FRIGID correction) — [FRIGID README](https://raw.githubusercontent.com/coleygroup/FRIGID/main/README.md); three-tier known/novel/CASMI test sets — [MS2Prop bioRxiv](https://www.biorxiv.org/content/10.1101/2022.10.09.511482v1.full); candidate-pool size effect (42% → 3.6% hit@1) — [arXiv 2602.00547](https://arxiv.org/html/2602.00547)

### Inferences
- What transfers: forward-model reranking (biggest measured gain), candidate-aware contrastive training, multi-CE simulation with entropy similarity and precursor removal, DreaMS embeddings for class-1 matching and as reranker features, fingerprint-pretrained decoders for de novo, confidence gating, MCES/scaffold-disjoint validation with per-class reporting.
- What does not transfer: NIST-trained weights (license), NPLIB1-level accuracies (leaky split), MSG 256-candidate hit rates (pool too small), near-miss de novo quality (MRR ignores it), any assumption that Orbitrap/QTOF-trained simulators keep their accuracy on timsTOF natural products without fine-tuning.
- Why: the benchmarks measure structure novelty but not instrument novelty, cap candidate pools, give the formula, and score exact graphs; CASMI 2026 removes the formula, enlarges the pool, changes the instrument and scores tautomer-canonical InChIKey14 at rank ≤ 25.

### Gaps
- No public experiment combines all of these components on timsTOF data; the public CASMI 2026 LB (~0.46–0.50 MRR@25 per the task context) is the only timsTOF natural-product datapoint and is not broken down by novelty class.
