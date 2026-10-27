# 069 E0(公開 0.464 系譜)の棚卸し — 原理的な部品と LB 合わせの定数の切り分け、B1 への移植候補

- 作成: 2026-10-27 08:43 JST 着手(`date` で取得)、Claude Code(サブエージェント)。読み取りのみ(コード実行・既存ファイル変更・ネットワーク・資格情報への接触なし。pickle は開いていない)。
- 対象: E0 = `kernels/baseline-v18/casmi26-baseline-v18.ipynb`(Public 0.464、提出 57567821)。比較対象 B1 = 0.379 構成(`experiments/b1_ana035/` + rank_v4b + anaw0.5、提出 57650023)。
- data_role: (1) コードと公開資産の静的読解、(2) 既存の開発 run の集計(W7 600 分子・C2 代理 `experiments/e0_offline/runs/c2_full3r/`、E0 のモデルは全分子を学習済み = リーク込み)、(3) 公開系譜の版ごとの Public(`docs/official_1026/notebooks/public_chain/chain_data.json`、以下 CHAIN)。隠しテストの性質はここから推測しない。

## 0. 要点
1. E0 は「三つの候補経路 + 順位融合」。engine 1 = v2 pool(train ∪ COCONUT)±10 ppm 窓(中央値 75 候補、生成物込み)を 160 特徴の LambdaRank(4 本)で並べる。engine 2 = COCONUT + ChEBI/LIPID MAPS + PubChemLite + train の窓を、notebook 内で学習する HistGB 2 系統(class-1/class-2 の模擬行)で並べる。PubChem チャネル = tier 1.06 億 + 補遺から pool に無い 25 件。これを固定枠・昇格・RRF・rank-2 挿入で 1 本にし、forward(GLACIER)は「同じ分子式の群の中だけ」で使う。
2. B1 との構造差の主なもの: (a) 主リストに PubChem tier のみの候補が入らない source の階層、(b) 学習行の作り方(推論と同じ engine で class 1/2/3 を模擬した数千〜2 万群)、(c) 生成物を本体 ranker で採点する class-3 経路、(d) 独立な 2 エンジンの融合と hedge、(e) forward の proxy 被覆。
3. Public は約 132 分子(CHAIN の `PUBLIC_FRACTION` 0.33 × 400、chain_data.json:3-4)で 1 分子の 1 位化 ≈ +0.0076。系譜の単一変更の大半は 0〜1 分子分。系譜表の「Data Behind v20 +0.023」を CHAIN で分解すると、動いたのは N1 challenger・engine-2 ranker の深さ・promotion 閾値・rank-2 挿入で、5-fold FPNet・NP/LOTUS/同義語 prior・補遺・6th slot はすべて ±0(§3.1)。
4. S 6 / pop 5 / rel 150・600 / LIB_TAU 0.9 / slot 位置 / α 0.6・K 3 / λ 1・1 / window 40 / CELL19_ICE・BASE_ICE = False / GLACIER の [M+H]+ 限定 / 生成の親 6 は LB 合わせ。移植しない。
5. 学習コードが揃うのは公開 fold-safe FPNet 5 本だけ。fpnet_full1・fe_A/B/D・ranker_v4b(sim1x)・fragnet・derivation prior・prvsiyan FP・PubChem FPNet A+B は資産フォルダに学習ループ・模擬スクリプトが無い(fpnet_full1 は VD:248 が「学習コード公開」と記すが、所在は本報告では未確認)、engine 2 の ranker は notebook 内学習だが学習行の生成コード無し → E0 の重みは使わず仕組みを B1 の自前コードで再実装する。prvsiyan のコードは CC BY-NC-SA なのでコードの転用ではなく考え方の移植にする。
6. 移植候補の順位(§5): ① OOF の fold-safe FPNet で作る「同一 pipeline の class 1/2/3 模擬」学習表の大規模化、② source の事前確率(PubChem tier のみの候補の降格)を probe と混合比の感度で決める、③ forward 被覆の補完、④ 生成物を ranker の中で採点、⑤ 第二の独立リストと identity 単位の RRF / rank-2 hedge、⑥ 複数 FPNet の view、⑦ 学習型の断片スコア、⑧ 候補源の到達監査。今日の E0_B / B1_B probe(055)の値で ①④⑤ と ② の優先度を入れ替える。

## 1. 読み方
- 引用: CELL = `experiments/e0_offline/cells/NN.py`(notebook のコードセル順、NN = (notebook のセル番号 − 2) / 2。系譜表は markdown セル 0)。V4B = `data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v4b-models/code/casmi/casmi26-v4b-models/code/casmi/`、FAMS = 同 dataset の `.../code/fe_v4/fams/casmi26-v4b-models/code/fe_v4/fams/`、FE = 同 `.../code/fe_v4/casmi26-v4b-models/code/fe_v4/`、MAN = 同 `.../casmi26-v4b-models/casmi26-v4b-models/MANIFEST.json`。ICE = 同 dataset の `casmi26-iceberg/casmi26-iceberg/`(fuse.py、ice_runner.py)、GLP = `casmi26-glacier/casmi26-glacier/`(gl_fuse.py、gl_runner.py)。cell 08 は 3 ファイルを 1 行目の dict に埋め込むので ce:L / pv:L / pvfp:L は casmi_engine.py / pv.py / pv_fp.py の内部行。cell 09 は V17:L(1 行目)、CORE:L(3 行目)、RUN:L(4 行目)。SIMR = `.../casmi26-simulated-ranker-rows/casmi26-simulated-ranker-rows/README.md`、POPR = `data/external/pubchem_popularity/README.md`、B1 = `experiments/b1_ana035/b1_pipeline.py`、VD = `docs/validation_design.md`。
- LB の段: 系譜表(markdown セル 0)は「連続した公開スコアの差で因果分離ではない」と自ら注記。CHAIN の一変更記録で補う。±0.008 は 1 分子の 1 位化と同じ大きさで、別 fork での「再現」も同じ隠しデータでの決定的な再計算なので独立な証拠ではない。
- 判定: (a) 原理的で移植可能、(b) LB 合わせの定数・閾値、(c) 不明。

## 2. データフロー(段階別)

### 2.0 全体
```
test spectra ─┬─ engine 1 (CELL 10-12): pool 窓 ±10 ppm + 生成 → LambdaRank 160 特徴 → top-60 → pool 人気で再順位 = BASE
              ├─ engine 2 (CELL 08): COCONUT+BIO+PubChemLite+train 窓 → HistGB 2 系統の blend → top-40 = ENG
              └─ PubChem (CELL 09): tier+補遺 ±10 ppm、pool 外、FP(A+B + 0.5·fold5) + prior → 25 件 = PC
forward (CELL 13): ICE/GL は「リスト内で同じ式が 2 個以上の候補」だけ。PC 25 は z(pc_fz)+ICE+GL で群内並べ替え
CELL 14: lib_max≥0.9 → BASE のまま / それ以外は PC を固定枠へ(昇格あり)= PREFUSION
CELL 15: RRF(PREFUSION ×1、ENG ×0.6、K=3)top-40 → GL 群内 rerank(26〜40 位は overflow)
CELL 16-17: 公式 identity で重複除去・空き枠補充 / CELL 18: identity 1 票の RRF top-40 → GL rerank
CELL 21 (E006): window 40、GL → FragGap → ICE の順に群内 rerank、25 に補充 / CELL 22: ENG の 1 位を 2 位へ
```

### 2.1 入力とスペクトル
- 分子の目標中性質量 = 全スペクトルの neutral_mass の中央値(CELL 12.py:3, 16;engine 2 も 1 分子 1 目標 pv:169-190・ce:357-361;PubChem RUN:76-79)。アダクトの電子質量補正はある(V4B chem.py:34-43, 118-127)が timsTOF の +0.5 mDa バイアス補正は無い。
- engine 1: 先頭 16 スペクトル(V4B engine.py:38, 243)。FPNet は単スペクトル view と極性ごとの merged view の平均 `z_avg = 0.5(z_single + z_merged)`(engine.py:338-366)。merged view のアダクトは最頻値で、同数時の非決定性を CELL 05 が `max(set(adducts),…)` → `max(adducts, key=count)` に置換(CELL 05.py:10)= v20 の「決定的なアダクト選択」。
- engine 2: precursor + 2 Da 以下、最大値正規化、スペクトル数の上限無し(ce:352-356)。FP は単スペクトル model の平均と merged model(先頭スペクトルのアダクト、CE 25 固定)の平均(pvfp:132-182)。
- PubChem チャネル: 最大 16 スペクトル、単/merged の平均(CORE:30-60、RUN:88)。

### 2.2 engine 1(CELL 10-12、V4B、FE)
- 窓: v2 pool 710,701(train のみ 248,440 / COCONUT のみ 436,515 / 両方 25,746)、±10 ppm、空なら ±30 ppm(engine.py:32-33, 210-214)。PubChem は含まない。shortlist による切り捨ては無く窓全体を採点。生成物は最大 150(engine.py:42-47)。W7 実測で窓は中央値 75(q10 14 / q90 255、`runs/c2_full3r/compare/stages.csv` の e1_window)。
- ライブラリ: train スペクトル(cleaned、precursor+2 Da 以下、0.1% floor、top 512;V4B build.py:3-4, 68, 76)+ 外部参照 751 本(469 の train 構造に限る、MassBank/MoNA/GNPS/MSnLib;CELL 10.py:76-112、件数の pin は `'added_rows': 751, 'added_keys': 469`)。
- FPNet: engine bank = `fpnet_full1.pt`(無ければ fpnet_0 = FPNet A)(CELL 11.py:15-17)。f·z = cand_fp · z_avg(V4B fpnet.py:3-5)。model_views に fe_A(fpnet_0 と同じ SHA)/ fe_B / fe_D(DreaMS を FP 予測に fine-tune)(MAN:80-93)。
- 特徴 160(MAN:97): v1 ブロック 94(ライブラリ 10、analog propagation 16 = top-100 analog の max Tanimoto × sim⁴ と NP ライブラリ版、FP 17 + 元素 5、MetFrag-lite 9 + subformula 5 + 式 3、文脈 10、交互作用 5、生成 6、xs_* 8 は死に特徴;engine.py:66-79, 307-462)+ family 5 種 66(derivation 19、frag2 13、analog_struct 13、model_views 7、fragnet 14;MAN:5-78)。gain 上位は mass_ppm_rank、el_rank、sf_rank、lib_max_rank、lib_nspec、ap_rank、best_tan_np、fzABD_gap、fzD_gap(ranker 内のモデル文字列の読み取り)。
- ranker: ranker_v4b = LambdaRank 4 本 × 500 rounds(lr 0.03、63 leaves、label_gain [0,1])、160 特徴、4 本の単純平均(MAN:94-99、CELL 11.py:24-31)。
- 学習行「sim1x」: engine 自体に模擬の切替がある — `exclude`(ライブラリスペクトルの mask)、`exclude_sid / exclude_lib`(analog 代表を query ライブラリだけで隠す = class 1、全ライブラリ = class 2)、`drop_pid`(真を pool 窓から除く = class 3、生成でしか届かない)(engine.py:236-251)。最終 ranker は「v1 engine の模擬 sim1x」で再学習(CELL 04.py:5-7)。family の開発は engine_v6 の sim10_s2(23,748 query、regime c1 / c2 / c2L / C2FAM / C2FAM_wt / C3FAM、構造単位の CV と 90% 区間;FE ctxlib.py:273-301、FAMS fragnet.py:60-64、derivation.py:25-36)。sim1x の規模・regime 比は非公開。学習行の FP 特徴は FPNet A(sampler が fold np/nplib/syn/plusk/twin を保留する設計、V4B traindata.py:11, 38-43。模擬 query がその fold なら OOF だが、split と模擬スクリプトは非公開で未確認)で、本番では fpnet_full1 に差し替え → f·z の分布がずれる(B1 の 063 と同種の問題)。
- 生成(V4B derive.py、engine.py:176-207): analog 上位 6(sim ≥ 0.3)を親に、46 の生合成的 SMARTS 変換の 1〜2 段の組(derive.py:17-66, 83-104)、質量差 max(0.004 Da, 10 ppm)、親あたり 60・合計 150、窓内に既にある key は除外。生成物は pid=-1 で同じ候補表に入り、同じ ranker が採点(gen 特徴 6 + derivation family:変換の発見率と部位環境の back-off prior。prior_tables.pkl は「COCONUT の親 → 生成物が pool にあるか」から作り、非 train-fold の key を除く = holdout-clean、FAMS derivation.py:84-88)。offline 効果は C3FAM +0.07〜+0.10、全 regime で +0.008(derivation.py:25-36)。
- pool 人気の再順位: top-60 の score を z 化し、pool 候補にだけ +0.15·(ln(1+substance) + ln(1+PubMed))、生成物は位置固定・分子式に '|gen'(CELL 12.py:6-7, 39-47)。BASE = top-60、BASE_TAIL も同じ 60(12.py:36, 56)。engine 1 の prior はこれだけで、NP・LOTUS・同義語・寄託源の項は PubChem チャネルにだけある(CELL 04.py:41-59)。

### 2.3 engine 2(CELL 08)
- 別プロセス・4 時間で打ち切り、失敗時は engine 1 のみ(08.py:10-17)。
- 窓: COCONUT(prvsiyan、約 43.6 万)+ BIO(sergiomalv の標準化 ChEBI 2/3 星 + LIPID MAPS で COCONUT に無い 98,433)+ PubChemLite CC0 385,760(既存 key 以外)+ train 構造(runtime で指紋)、±10 ppm(空なら 30)、上限無し(ce:147-188, 364-365)。
- AFIX: ライブラリスペクトルの中性質量を precursor/adduct ではなく分子式から計算(riken の 0.005 Da 精度・GNPS のアダクト誤記に強い)。ライブラリ・analog の索引だけに効き、pool には効かない(ce:18-26, 89-92)。
- 証拠: entropy 類似度のライブラリ(precursor 差でずらした比較の max も;pv:70-139、ce:258-274)、analog propagation(±200 Da、200 analog = 08.py:6 の N_ANALOG、Tanimoto × sim³、極性別 sim⁶ も;ce:206-251, 277-313、pv:215-226)、MetFrag-lite(pv:298-357)、FP(prvsiyan fp_merged_m1 + fp_single_s2、6,930 bit;08.py:6)。
- ranker(notebook 内で学習): sklearn HistGradientBoostingClassifier(点ごとの log-loss、depth 6、500 iter、lr 0.03、min leaf 80;ce:31-34, 407-410)。
  - pv(prvsiyan): `rank_train.npz` 142,762 行 × 31 特徴 = 819 分子 × 2 模擬、class-1 模擬行に重み w1 ∈ {0.30, 0.60} × seed 0-3 = 8 本(ce:422-427)。FP 特徴の出所は文書無し(公開の、学習済みの可能性が高い FP model 由来と推定、SIMR:12 → (c))。
  - ours(megayak): `sim_rank_rows_nofp.npz` 399,790 行 × 51 特徴 = 2,250 分子(パネル 250・gnps 400・riken/mona/msdial/massbank 各 300・pluskal 400)× 2 模擬、FP 無し、wA ∈ {0.35, 0.55} × seed 0-1 = 4 本(ce:413-419、08.py:6、SIMR:5)。
  - 真の隠し方(SIMR:6-7): S=0 = class-1 模擬(query のライブラリだけ除去、他ライブラリにある真のスペクトルは残す)、S=1 = class-2 模擬(真のスペクトル全除去、構造は pool に残す)。模擬の pool は COCONUT + train。class-3 行は無い。推論の窓は BIO・PubChemLite を足すので窓サイズ系の特徴がずれる((c))。
  - blend: 0.88·(1 − rank_pv) + 0.12·(1 − rank_ours)(ce:441-447、08.py:6)。出力 top-40。
- megayak の leak-free FPNet(ours_fpnet_*)と fp16k / fppair 行は E0 では未使用(SIMR:11-17、全セル grep)。

### 2.4 PubChem チャネル(CELL 09、gate は CELL 14)と prior 資産
- FP: v3 の fpnet_0/1(A+B)の logit 平均 + 0.5 × fold-safe 5 本の平均(raw logit で加算)(RUN:22-57、CELL 04.py:32-40)。
- 窓: tier 105.9M + delta 36,303 + growth 11,177 の ±10 ppm(V17:135-189、CELL 04.py:60-64)。pass 1 = ECFP4 部分の FP で上位 5,000 + prior 上位 200、pass 2 = 10,226 bit の全 FP(CORE:22, 76-77、V17:53-91)。
- 得点 = z(FP)(pass-2 集合で標準化)+ 0.15 × prior、prior = ln(1+SID) + ln(1+PMID) + 0.5·[寄託源あり] + 1.0·[COCONUT/LOTUS/NPAtlas] + 0.5·ln(1+LOTUS) + 0.5·ln(1+同義語)(V17:69-78, 106-111、CELL 04.py:41-59)。
- 出力: score 順、scorer key で重複除去、train ∪ COCONUT pool にある構造は除外、25 件(V17:112-124)。BIO・PubChemLite は除外しないので engine 2 と重なり得る。
- gate 用に出す値: fz_top(pool 外最良の生 FP)、best_pool_fz、S(リスト 1 位の融合得点)、top_pop(RUN:95-115、V17:102-127)。lib_max < 0.9 のとき ICE → GL で同一式群の中を並べ替え(13.py:87-100, 1327-1337)。
- NP knowledge table: natural_products.parquet はどのセルも読まない(パスを CELL 03.py:14 で探すだけ)。使われるのは外部参照スペクトル(CELL 10)と popularity prior の配列(NP・LOTUS・同義語)だけ。

### 2.5 forward(CELL 13 / 20 / 21)
- engine 1 の BASE 自体は forward で並べ替えない(`BASE_ICE = False`、「b420 showed it costs 0.009」CELL 13.py:9)。forward が働くのは (A) PC 25 と、(B) 融合後の 40 件の中だけ。
- 入力: base top-60 + ENG top-40(base に無いもの)+ PC 25(lib_max < 0.9 のときのみ)のうち、リスト内で同じ分子式が 2 個以上ある候補だけ(ICE fuse.py:98-105、CELL 13.py:65-100)。生成物は '|gen' で別の群(12.py:47)。W7 では約 81 候補/分子(48.6k / 596、`work/e0_run_audit.json`)。
- アダクト: ICEBERG は [M+H]+ / [M+Na]+、GLACIER は [M+H]+ のみ(13.py:120「v29: GLACIER on [M+H]+ only (v27: +0.006)」)。負イオンは forward 無し。CE は 5 eV bucket、CE 無しは 20/40/60 eV の予測を合成、timsTOF は 'QTOF' 扱い(GLP gl_runner.py:25-30, 409-436)。類似度は entropy、分子の被覆スペクトルの平均(gl_runner.py:344-387, 727-749)。
- 予算: ICE 5,400 s(CELL 04.py:13)、GL 4,000 s(13.py:114)、N1 1,200 s(13.py:150)。lib_max の低い分子から(13.py:63-64)。CELL 17.py:18-20 が ICE/GL の status 'ok' を assert するので、予算切れはそのまま失敗になり得る。
- N1A proxy: [M+H]+ が無く [M+NH4]+ か [M−H2O+H]+ がある分子で、[M+H]+ に作り直したスペクトルを GLACIER に(13.py:171-251, 977-1004)、CE は merged(13.py:149)。N1 challenger: `N1_COMPLEMENT = False` で ICE がある分子にも proxy GL を残し、E006 で z + 1·z(ICE) + 1·z(proxyGL)(13.py:154-161、21.py:77-91)。
- 融合の形: 同じ分子式の群の中だけ z(base) + Σλ z(score)、群の位置は保持、被覆の無い候補は z = 0(ICE fuse.py:109-160、GLP gl_fuse.py:94-139)。cell 15 は ICE を使わない(`CELL19_ICE = False`、根拠は b420 0.402 vs b416 0.417 の LB 比較、CELL 15.py:2-7)。E006 は window 40 で、GL → FragGap(λ 0.5、GL と ICE が無い分子)→ ICE(GL が無い分子)の三分岐(21.py:77-113, 219)。
- FragGap(CELL 20): 学習無しの MetFrag-lite(2 結合まで、2 結合目 0.6、0.005 Da、H シフト −2〜+3)、説明強度の割合を最大 16 スペクトルで平均(20.py:7, 27)。

### 2.6 統合(CELL 14 → 22)
- CELL 14: `lib_max ≥ 0.9` → BASE のまま(14.py:54-55)。それ以外は rel = fz_top − best_pool_fz(raw)で、rel > 600 → slot [2,4,6,8,10,24]、他 → [4,8,12,16,20,24](CELL 04.py:12-17、14.py:57-58)。PC の 1 位を rank 1 に昇格: (S > 6 かつ top_pop ≥ 5) または rel > 150(14.py:25, 64-66)。pool にある PC は落とし、PC は枠にだけ入る(14.py:2-13)。
- CELL 15: fuse2 = Σ w/(3 + r)、PREFUSION 1.0・ENG 0.6、top-40(15.py:1, 15-25)→ GL の群内 rerank(15.py:36-45)、26〜40 位は FUSION_OVERFLOW(15.py:49)。
- CELL 16/17: 公式 identity(RemoveStereochemistry → TautomerEnumerator → InChIKey14)で重複除去、既存の first rank を悪化させない補充(16.py:6-35, 58-86、17.py:33-59)。補充順 = overflow → base tail → ENG → PC → DreaMS(資産欠落で不活性、17.py:43-56)。
- CELL 18(E004): エンジンごとに identity 1 票の RRF(α 0.6、offset 3、limit 40)→ GL rerank → safe_extend(18.py:4-43)。
- CELL 21(E006): 上記の三分岐。window 40・fallback 無しなら E004 と一致することを assert(21.py:154-157)。W7 では全分子が [M+H]+ を持つので 600 中 0 分子が変化。
- CELL 22: ENG の 1 位を、最終 1 位と別 identity なら閾値無しで 2 位へ(22.py:18-27)。

### 2.7 開発 run での実測(W7 600、C2 代理、E0 は全分子を学習済み = 上限寄り)
| 段 | MRR@25 | 候補数(中央値) | 真の含有 |
|---|---:|---:|---:|
| e1 window | — | 75 | 0.971 |
| e1 base-60 | 0.939 | 60 | 0.953 |
| ENG list40 | — | 40 | 0.127 |
| PC list25 | — | 25 | 0.000(真は全員 pool 構造) |
| merge(CELL 14) | 0.907 | | |
| fuse2 + GL(CELL 15) | 0.696 | | |
| final(rank-2 後) | 0.681 | | |
| B1 window / shortlist | — | 9,254 / 247 | 0.958 / 0.755 |

出典: `runs/c2_full3r/compare/report.md`、stages.csv の集計。昇格 62/600(rel>150 が 53、`work/e0_merge_decisions.json`)、rank-2 挿入 385/600(`work/rank2_overlay.json`)。昇格は −0.032、rank-2 は −0.015 = 「base が正しいときの費用」で、隠しでの利得の推定ではない。fuse2 段の −0.21 は、記憶を持つ engine 1 と真を 87% 欠く engine 2 の食い違いで、隠しの class 2(engine 1 に記憶が無い)では符号が分からない。

## 3. 部品表(何をするか / 主な定数 / LB の段 / 判定)
| # | 部品 | 主な定数(file:line) | LB の段(系譜表の行 / CHAIN の一変更) | 判定 |
|---|---|---|---|---|
| 1 | pool(train∪COCONUT)窓を shortlist 無しで全採点 | ±10 ppm、fallback 30(engine.py:32-33) | 自前 engine の v2-baseline 0.348 | (a)。30 ppm fallback は (b/c) |
| 2 | 同じ engine の模擬(class 1/2/3)で ranker を学習 | exclude / exclude_lib / drop_pid(engine.py:236-251) | v4b(family + sim1x)0.354 vs v3.6 0.358(CELL 04.py:5-7)= LB では無効 | 設計 (a)、regime の比率 (c) |
| 3 | 160 特徴 LambdaRank 4 本平均 | 500 rounds、63 leaves(MAN:94-99) | 同上 | (a)/(c) |
| 4 | fpnet_full1 を engine bank に | CELL 11.py:15-17 | v4m 単独 +0.005(CELL 04.py:1)、CHAIN v4n 0.379→0.382。系譜表「v4n-engine-fusion +0.013」は forward と同梱 | (c): class-1 の記憶。学習時(FPNet A)と分布がずれる |
| 5 | model views(fe_A/B/D と不一致特徴) | 7 特徴(model_views.py:16-32) | 単独記録無し。fe_A/B を差し替えた v23a は −0.009 | 機構 (a)、重みは学習コード無し |
| 6 | analog propagation | e1: 100 個・sim⁴、e2: 200 個・sim³(engine.py:35-36、08.py:6) | 系譜の起点(prvsiyan V10 0.335) | 機構 (a)、定数 (b)。B1 に移植済み |
| 7 | 学習型断片スコア fragnet | Dirichlet α80 + LambdaRank 300 rounds(fragnet.py:33-44) | 単独記録無し | (a)。保留構造で式内 MRR 0.6465→0.7712(fragnet.py:45-47) |
| 8 | 生成物を同じ ranker で採点 | 親 6・sim≥0.3・60/150・0.004 Da(engine.py:42-47) | 親 6→20 で −0.008(CHAIN DB v17)、生成物の 1 位強制 −0.007(v12-gentop-p1b)、追加 C3 pass −0.001(v18-c3r3) | 機構 (a)、上限・親数 (b) |
| 9 | derivation prior(変換の発見率・部位環境) | prior_tables.pkl(derivation.py:84-88) | v4b に含まれ単独記録無し | (a)。holdout-clean な作り方が記述済み |
| 10 | pool 人気の再順位(top-60 内) | μ 0.15(CELL 12.py:6) | V10 Apex(+0.002、0.398→0.400) | 機構 (a)、μ (b) |
| 11 | engine 2(別 pool・別 FP・別 ranker) | top-40、blend 0.88(08.py:6) | v4n-e5c(+0.006;CHAIN では二エンジン RRF で v4g 0.369→0.386、GL 込み) | 多様性 (a)、0.88 は (b)(w088 で LB 調整) |
| 12 | engine-2 学習行(S=0/S=1 の混合と重み) | w1 {0.30,0.60}、wA {0.35,0.55}(ce:413-427) | megayak two-rankers 0.343、seed/depth の調整 +0.003〜+0.007、0.464 土台では depth 7 が −0.008(discussion 752356) | 混合 (a)、重み・深さ・seed (b) |
| 13 | BIO(ChEBI/LIPID MAPS)候補 | 98,433(ce:152-158) | e5c に含まれる。CC BY 版への置換 +0.001(v52) | (a)/(c) 到達次第 |
| 14 | AFIX(ライブラリ質量を分子式から) | ce:18-26 | e5c | (a) |
| 15 | PubChemLite を engine 2 の窓へ | 385,760(ce:159-175) | DB v7 −0.003、v447 +0.006 | (c) |
| 16 | PubChem 専用チャネル(pool 外 25 件) | pass 1 = 5,000 + prior 200(CORE:22) | v4i(PC_N1=5000 の基準 0.373)。チャネル導入は CHAIN v3-inference v6 +0.016(0.337→0.353) | 二段検索 (a)、深さ (b) |
| 17 | PubChem の FP ensemble | A+B + 0.5·mean(fold5)(CELL 04.py:40) | fold0 追加 ±0(DB v12)、5 本 ±0(v18/v19) | 機構 (a)、0.5 は (b) |
| 18 | PubChem prior の各項 | 0.15、寄託 0.5、NP 1.0、LOTUS 0.5、同義語 0.5(CELL 04.py:41-59) | NP ±0(v5)、LOTUS ±0(v8)、pop 0.25→0.15 ±0(v10)、同義語 ±0(v14)、LOTUS 1.0 ±0(v496) | 機構 (a)、重み (b) |
| 19 | PubChem 補遺(delta・growth) | 36,303 / 11,177 | v15 ±0(外部参照と同梱) | (c) |
| 20 | 固定枠への挿入と昇格 | slot、S 6、pop 5、rel 150/600、LIB_TAU 0.9 | V1(+0.008)。rel 250→150 で +0.003/+0.004、6th slot ±0、閾値の緩和 ±0(v497) | (b)。形としては全体融合が良い(P1 で −0.06〜−0.08) |
| 21 | forward 再採点を同一式群・slot 保持で | ICE fuse.py:123-160 | v4f(ICE 再採点、v4 model と同梱で 0.353→0.369)、v4h GL 追加 +0.009 | 再採点 (a)、slot 保持 (c)(P1 では全体 z 融合が上) |
| 22 | ICE_LAM = GL_LAM = 1.0 | CELL 04.py:13、13.py:114 | v4l(系譜表 +0.007、CHAIN 0.378→0.379) | (b) |
| 23 | ICE を主 rerank から外す | BASE_ICE / CELL19_ICE = False | b420→b421 の LB 比較のみ | (b)。P1 では ICE +0.038 と逆 → 写さない |
| 24 | GLACIER を [M+H]+ に限定 | 13.py:120 | コメント「v27 +0.006」、他系譜で −0.001 | (b)/(c) |
| 25 | N1A proxy | 13.py:171-251 | 単独 ≈0(+0.001、±0、±0) | (a)。CUT 1.5 Da は (b) |
| 26 | N1 challenger(ICE がある分子にも proxy GL) | N1_COMPLEMENT = False(13.py:160) | +0.008(3 系譜)、外すと −0.008 | 考え方 (a)、大きさ (c)(1 分子分) |
| 27 | ICE fallback / window 40 / FragGap | 21.py:77-113, 219、λ 0.5 | ICE fallback +0.002 / E006 window-40 +0.002(80 でも同じ)/ v7c +0.001 | 機構 (a)、定数 (b) |
| 28 | RRF(identity 1 票) | α 0.6、K 3、40(15.py:1、18.py:4) | E004/v80 +0.003 | 機構 (a)、定数 (b) |
| 29 | rank-2 挿入 | 閾値無し(22.py:18-27) | +0.002(2 系譜) | hedge の考え方 (a)、無条件は (b) |
| 30 | metric-safe tail | 16.py / 17.py | V1.1 +0.008(壊れた DreaMS tail の置換を含む) | (a) 衛生 |
| 31 | 外部参照スペクトル(train 構造のみ) | 751 / 469(CELL 10.py) | v15 ±0 | (a)、規模小 |
| 32 | 系譜表「V44 LambdaRank + top-1 保護 +0.016」 | v18 のコードに該当箇所無し(セルの grep、engine 1 の確認) | 親が engine 2 を外した壊れた版(0.37→0.42) | 帰属不能 |

CHAIN の該当行: v3-inference v6、v4f/g/h、v4l/m/n、e5c、V10 Apex、v80、v7c、e2rank2、rel150、DB v1〜v24、v12-gentop-p1b、v18-c3r3、v16-pcbank-d2、v19-bioext、v23a。

### 3.1 「Data Behind v20 +0.023」の分解(CHAIN)
- v7c 0.441 → rank-2 0.443 → rel150 0.446 → engine-2 seed/depth7 0.450 → BIO 0.451 →(DB 系譜)PubChemLite 0.448 → depth 6 0.455 → N1A 0.456 → challenger 0.464 → 親 20 で 0.456 / 6 に戻して 0.464 → 6th slot 0.464。
- 動いたのは forward 被覆(challenger)、engine-2 ranker の容量(深さ・seed、土台によって符号が変わる)、promotion 閾値、rank-2 挿入。系譜表が名前を挙げる「5-fold FPNet・化学 prior・候補挿入」は ±0。分解能(1 分子 ≈ 0.008)から、どの段も「本物の効果」とも「雑音」とも言えない。

## 4. B1 との設計比較

### 4.1 構造の違い
| 観点 | E0 | B1(0.379) |
|---|---|---|
| 主窓 | v2 pool ±10 ppm、生成物込みで中央値 75 | PubChem tier + pool + COCONUT store の ±10 ppm(B1:327-340)、中央値 9,254 |
| 絞り込み | 無し(窓全体を ranker → top-60) | FP top-100 ∪ z(FP)+0.15pop top-200 ∪ lib top-20 ∪ prior top-50 = 中央値 247(B1:421-426) |
| pool 外の候補 | PubChem 25 件を固定枠・昇格で。engine 2 の BIO / PubChemLite を RRF と rank-2 で | 同じリストで対等に競合 |
| FPNet | e1: fpnet_full1、特徴用に fe_A/B/D。PubChem: A+B + fold 5 本。e2: prvsiyan FP | 自前 full_eval 1 本(B1:260-264, 349-357) |
| ranker | e1: LambdaRank 160 特徴(sim1x)。e2: HistGB 2 系統(S=0/S=1 行、計 6,138 群) | LambdaRank 23 特徴、1,304 群、fold-0 FPNet の特徴で学習(b1_rankfeats.py:9-10、`experiments/b1_baseline/rank_v4b/rank_results.json`) |
| ライブラリ | train + 外部 751 本。lib_max ≥ 0.9 なら BASE を保護 | train のみ(B1:391-418)。lib ≥ 0.9 & margin 0.2 の優先は固定経路だけ(B1:536-538) |
| prior | pool: top-60 内で 0.15(lsid+lpmid)。PubChem: 6 項 | pop = lsid+lpmid+0.5syn+NP+0.5src+0.5log1p(LOTUS)(B1:388)。固定則で 0.5、ranker の特徴にも |
| forward | ICE+GL(群内・slot 保持)、N1A/challenger、E006 の cascade | GL のみ(shortlist の ≤100 重原子、B1:460, 481)、全体 z 融合、proxy 無し(b1_common.py:103-105 は H/Na が無い分子だけで、0.379 では off) |
| 生成 | 常時 on(親 6)、同じ ranker で採点 | 0.379 では無し(gt3 / ggt3t は Public 待ち) |
| hedge | PubChem 固定枠、RRF、rank-2 挿入、metric-safe tail | 無し(analog は z の加算、B1:555-557) |

### 4.2 クラス別に効きそうな差(仮説、未検証)
**クラス 2 の NP(COCONUT にあり train に無い)**
- E0: 真は engine 1・2 両方の窓に必ず入り、デコイは train/COCONUT/BIO の同質量構造だけ。engine 2 は S=1 模擬(構造は pool に残す)で学習 = このクラスの状況そのもの。B1: 真は 9,254 の窓から FP・prior・ライブラリで 247 に絞られる。
- ただし B1 で COCONUT 収載の正解が 1 位を逃すときの勝者は「COCONUT 収載・prior が高い・同じ式」が GL ありで 52.5%(docs/essential_2026-10-27.md:6)→ pool への制限だけでは救えない部分が大きい。
- 差が出得る点: (i) 学習表の regime(E0 は「真が pool にあり参照が無い」群を数千、B1 は dev 集合の C2 view 約 1,300 群で FP 特徴は fold-0 FPNet)、(ii) 2 エンジンの RRF(誤りが独立なら効く)、(iii) FP の多 view。
- 否定済み: pool 窓の FP top-60 を shortlist に足す k_pool60 は全層 0〜負(VD:366-376)。窓を絞ること自体ではなく「その窓で学習した ranker」の方が差の候補。

**クラス 1(公開スペクトルあり、隠しでは多くが train)**
- E0: fpnet_full1(記憶)、ライブラリ特徴(train + 外部 751)、engine 2 の S=0 模擬(query のライブラリだけ除き他は残す)、lib_max ≥ 0.9 で PubChem から保護。
- B1: full_eval(記憶)、train のみのライブラリ、C1 view は 3 倍複製だが「timsTOF query × 他装置の参照」の行が少なかった(v8w で G C1 +0.087〜+0.101、064_result.md:12)。学習経路には参照優先の hard gate が無い(B1:540-551)。
- パネル型(有名な NP)ではすでにほぼ同等(パネル C1:E0 0.948〔query まで学習済み〕vs B1 full_eval 0.933、VD:358-364、`experiments/b1_baseline/diag/g048_panel.md:5`)。差が残るとすれば G 型(timsTOF × 他装置参照)。

**PubChem のみの真**
- E0 は pool 外の候補を固定枠(通常 4,8,…,24)か昇格でしか上位に置かない → 多くは最良でも 4 位。B1 は同じリストで 1 位にできる(B1 の Pc probe は Public 0.046、VD:513)。この群で E0 が B1 より強い理由はコード上は見当たらない(engine 2 経由の PubChemLite・BIO を除く)。

**クラス 3**
- E0 は常に生成し、生成物を同じ ranker(derivation prior、C3FAM の模擬で学習)で採点する。公開議論では「DB に無い 130 分子で 1 位 7」(docs/official_1027/discussion/750241_*.md)。B1 は 0.379 では 0(gt3 / ggt3t は Public 待ち)。

### 4.3 差の候補のまとめ
1. 学習表の作り方(推論と同じ engine での大規模模擬、class 1/2/3 の混合、OOF の FP 特徴)。
2. 2 エンジン + PubChem チャネルの多様性と順位融合。
3. class-3 生成の常時稼働。
4. forward の proxy 被覆。
5. source の階層 — ただし B1 の probe では群の取り違えを完全に解いても +0.028 まで(VD:515-516)なので、単独では差 0.085 を説明しない。

→ 今日の E0_B / B1_B の一対 probe(055)で、COCONUT 非 train 群の中の順位付けの差(1 + 2 の寄与)が直接見える。

## 5. 移植候補(順位付き)

### P1. 同じ pipeline の大規模模擬で ranker を学習する(class 1/2/3、OOF の FP 特徴)
- 機構: E0 の sim1x(engine.py:236-251 の切替で c1/c2/c3 を作る)と engine 2 の S=0/S=1 行(SIMR:6-7)の本質は「推論と同じ候補生成・特徴計算を、真の情報を規則的に隠した query で再現し、その上で学習する」こと。E0 は 23,748 query(family 開発)、engine 2 は 1,638 + 4,500 群。B1 の rank_v4b は dev 集合由来の 1,304 群。
- B1 での形: 公開 fold-safe FPNet 5 本で、fold k の分子に fold k の FPNet を当てれば全 train 分子の OOF FP 特徴が作れる(学習コードあり、prize 可)。b1_features の C1 view(query ライブラリの参照だけ除く)・C2 view(全参照を除く、出典の無い候補は除外)・C3 view(真を DB から除き生成物で到達)を folds 0/3/4 の数千分子に広げ、class 1 では G 型(timsTOF query × 他装置参照)と NP の他ライブラリ参照を意図して厚くする。v8w(train_pool_f3a/f4a)はこの方向の小規模版で、確認 +0.0067 [+0.0023, +0.0112](056_conf_results.md:26)。
- 必要なもの: 既存の b1_features / b1_rank_train の拡張と Spark の計算(全学習行に GL を付けると重い → GL は shortlist の一部だけ、または GL 欠損を学習時に再現)。E0 の学習行は使わない(数値のみで生成コード無し、prvsiyan の特徴は CC BY-NC-SA)。
- 検証: 学習 = folds 0/3/4(使用済み identity を除く)、開発 = f1dev / f2dev(公開 fold1/2 の表)と 053 dev、確認 = 053 の NP_H / NP_N conf(未開封)、既見クラス 1 の保護 = パネル C1 clean(full_eval の表)、stress = EXT 60。本番 FPNet(full_eval)との特徴分布のずれは 063 / 064 と同じ交差比較で確認。
- リスク: 選択に使った集合での楽観(dev2 の例)、学習表の class 比率が暗黙の class prior になる(E0 でも regime 比は不明)、f·z の尺度差。LB 合わせの定数は無い。

### P2. source の事前確率(PubChem tier のみの候補の降格)を、probe と混合比感度で決める
- 機構: E0 は主リストから PubChem tier のみの候補を外し、固定枠と昇格でだけ入れる(CELL 14.py:2-13, 54-68)。B1 側では同じ考えを「w·1[Pc] の降格」として評価済み(pcd1 / pcd2 / gdP0.7w4 は 54 シナリオ中 49〜51 で正、最悪 −0.004、VD:417-449)。
- 移植の形: E0 の固定枠(slot4 は dev2 C2 で −0.096、最悪シナリオ −0.031)ではなく、連続の降格重み w か、ranker に source の事前確率を明示して学習させる(学習群を仮定した source 構成に重み付け)。
- 判断材料: 今日の prior-only probe と E0_B / B1_B probe(055、1027_submission_plan.md)。E0_B ≫ B1_B なら pool 群の中の順位付け(P1・P4・P5)を優先、差が小さければ P2 は群間の取り違え(上限 +0.028)だけの小さな手。
- 必要なもの: 既存コードに一項(`--pcl_boost` と同じ箇所、B1:517-522)。学習コード不要。
- リスク: 隠しの PubChem のみの真の割合に強く依存(Pc probe 0.046)。重みを Public で調整しない。

### P3. forward 被覆の補完(N1A の条件と challenger 相当)
- 機構: 証拠の無い分子を減らす。E0 の N1A は「real [M+H]+ が無い」が条件で、challenger により ICE がある分子にも proxy GL を残し、両方を同時に使う(13.py:154-161、21.py:77-91)。系譜で再現した唯一の段(+0.008、ただし同じ隠しデータでの決定的な再計算)。
- B1 の現状: `forward_proxies` は正イオンの H も Na も無い分子だけ(b1_common.py:105)で、0.379 では off。050 は開発 F C2 +0.022 / +0.067 だが確認で登録上不合格(fold-1 C1 の 3 分子)。B1 の GL は [M+Na]+ も採点するので、E0 の「GLACIER [M+H]+ 限定」は写さない。
- 移植の形: (i) 条件を「[M+H]+ が無い」に広げ、[M+Na]+ の GL と proxy GL を併用、(ii) CE が複数の proxy は merged CE で予測、(iii) 負イオンのみの分子は b1_frag(既存の MetFrag-lite)。
- 検証: proxy の対象を含む層だけで(dev2/locked2 の E・F、053 NP_X dev、パネルの 34 分子)。W7・p1 は [M+H]+ を持つ分子だけなので無効。053 NP_X conf は 050 で開封済みなので、確認には fold 3/4 から NP_X 型の新しい集合を作る。
- リスク: 対象が少なく(Public で 1〜2 分子)判定が難しい。GL の追加呼び出しの時間は小さい。

### P4. 生成物を本体 ranker の中で採点する(派生特徴 + C3 模擬)
- 機構: E0 は生成物を pool 候補と同じ表に入れ、is_gen・親 sim・親 Tanimoto と derivation prior(変換の発見率、部位環境、holdout-clean)を特徴にした ranker で並べる(engine.py:176-207、derivation.py:44-88)。offline C3FAM +0.07〜+0.10。B1 の gt3 / ggt3t は「3 位に 1 個」(`experiments/b1_baseline/b1_pipeline.py` の `--gen_rank`)。
- 移植の形: B1 の b1_gen(36 変換、E0 の 46 と同型)の出力に派生特徴を付け、P1 の C3 view(真を DB から除いた模擬)を学習表に入れる。prior_tables は E0 の記述どおり「COCONUT の親 → 生成物が pool にあるか(評価 fold の key を除く)」で自前に作る(E0 の表は学習コード無し)。
- LB の記録からの注意: 生成の範囲を広げると −0.008(親 20)、生成物を 1 位に強制すると −0.007(CHAIN)。discussion 752356 の指摘どおり、list 内の相対特徴があると生成物を足しただけで元の候補の順位も動く → 生成物を足しても DB 候補の特徴が変わらない設計を保つ(B1 の gt3 は満たしている)。
- 検証: 053 dev の c3 view(NP_X で真の生成率 55〜58%、059)、f1/f2 dev の c3、保護は C1・C2 の主層。gt3 の Public の結果を先に読む。
- リスク: 生成物が DB のデコイより上に来る誤り(クラス 2 の損失)。T4 の時間(生成物の GL は ggt3t で計測済み)。

### P5. 第二の独立リストと、identity 単位の RRF / rank-2 hedge
- 機構: E0 は engine 2 を独立に作り、identity 1 票の RRF(18.py:4-20)と rank-2 挿入(22.py:18-27)で混ぜる。MRR では「主の 1 位が外れ、別系の 1 位が当たる」確率が「主の 2 位が当たる」確率より十分大きければ 2 位挿入で期待値が上がる。e5c で +0.017(融合後の ICE/GL 再採点込み)、rank-2 で +0.002(2 回)。
- B1 での形: 第二のリスト = FP を使わない証拠(analog・ライブラリ・MetFrag・prior)だけの ranker、または pool 窓だけの ranker。主リストと食い違ったときだけ 2 位に入れる、または RRF。
- 検証: 既存の特徴表だけで正確に計算できる(GPU 不要)。f1/f2 dev・053 dev・パネル C1 clean・EXT で、挿入の当たり / 外れ(主の 2 位の真を 3 位に落とす費用)を分解して出す。末尾に別順位を足す tail hedge は全層 ≤ +0.0005 だった(VD:540-541)ので、効くとすれば上位の hedge。
- リスク: W7 では −0.015(base が正しい分子での費用)。無条件の挿入は (b)。発火条件(主の確信度・食い違いの度合い)は開発で決める。

### P6. 複数 FPNet の view と不一致特徴
- 機構: E0 の model_views(fzD_gap / rank_spread / rank_worst / fzABD)は gain 上位。B1 は 058 で公開 5 本の平均が未見パネルの FP 順位 +0.033 [+0.005, +0.060]、067 で混合を locked2 で確認中。
- 移植の形: 自前 full_eval + 公開 fold 5 本(学習コードあり)の logit 平均に、不一致の特徴(順位の広がり・最悪順位)を足して ranker へ。
- 検証の難所: dev 分子は公開 fold のうち 4 本に既見なので、「共通 holdout の 2 本」(Codex 049)で特徴を作る必要がある。regime ごと(クラス 1 = 既見 5・未見 1、クラス 2 = 未見 6)に評価。
- リスク: 学習時と本番の view の既見性の違い。T4 の負荷は小さい(窓の FP は内積)。

### P7. 学習型の断片説明スコア(fragnet 型)
- 機構: 「この断片がこの強度で出る」確率を構造の部分型で数え(Dirichlet 平滑の対数尤度比)、LambdaRank で集約(fragnet.py:28-47)。保留 3,103 構造の式内 MRR 0.6465 → 0.7712、COCONUT デコイにも同程度の利得。GLACIER が使えない分子(負イオン・NH4 のみ)で効く。
- 移植: 学習コード(res_fragnet)は無いので、記述に従って自前で再実装・学習(train の fold を分けて)。負イオンの E 層、forward 無しの F 層で評価。
- リスク: 開発 2〜3 日。GL と重なる分子では利得が小さい可能性。

### P8. 候補源と参照の到達監査(BIO・AFIX・外部参照)
- BIO(COCONUT に無い ChEBI/LIPID MAPS 98,433)・PubChemLite・PubChem 補遺が、B1 の窓(tier + pool + COCONUT)に無い真をどれだけ持つかを、053 / f1 / f2 / EXT の真の key で数える(GPU 不要)。到達が増える場合だけ候補源に足す。LB は BIO +0.001、bioext −0.008、PubChemLite ±。
- AFIX: B1 のライブラリは pool key → 参照行で引くので、影響は analog の窓(±200 Da の中性質量)だけ。riken・GNPS の質量誤差で analog が落ちる例があるかを確認。
- 外部参照スペクトル: E0 は train 構造の 469 だけに追加(10.py:85)。EXT は knowledge table の「train スペクトルの無い構造」から作ったので、それらの記録を B1 に足すと EXT が汚れる → 足すなら train 構造の記録に限る。

### 移植しないもの(LB 合わせ、または B1 の結果と矛盾)
- slot 位置・昇格閾値・rel 150/600・S 6・pop 5・rank 24 の 6th slot、α 0.6・K 3、λ 1/1、window 40、POOLPOP 0.15、PubChem prior の各重み、engine-2 の blend 0.88・深さ・seed。
- ICE を主 rerank から外すこと(label-free の P1 では ICE +0.038 [+0.016, +0.060]、memory の 10/24 の記録)、GLACIER の [M+H]+ 限定、同一式群・slot 保持の rerank(P1 で全体 z 融合より −0.06〜−0.08)。
- E0 の重み(fpnet_full1、fe_*、ranker_v4b、fragnet、prior_tables、prvsiyan FP、engine 2 の学習行): 学習コード無し。

## 6. 未解決と次の確認
- 今日の prior-only probe と E0_B / B1_B probe の値で、P2 と P1 / P4 / P5 の優先度を入れ替える(055 の読みの表どおり)。
- E0 の engine-1 ranker が隠しの class 2 でどれだけ効いているかは、手元では測れない(E0 の全モデルが dev 分子を学習済み、prvsiyan の FP も既見の可能性)。測るには E0 を fold-safe FPNet に替えて fold 1/2 の分子で走らせる必要がある(E0 は資産 hash を固定しているので改変が要る。方針上は「分析」に留める)。
- E0 の gain 上位の lib_nspec / lib_hit は train 所属の信号。B1 の学習経路が class 1 で崩れた原因(10/25、memory)と同じ型の特徴で、E0 では c1 模擬の比率が符号を決めている。B1 の P1 でも regime 比率を明示して設計・記録する。
- E0 の hidden rerun の弱点: cell 17 の assert(ICE/GL の status)で落ち得る(17.py:18-20)。B1 は fallback 設計済み。T4 の時間は E0 hidden rerun 約 4 時間 15 分、B1 commit run 約 3.2 時間(memory)。P3〜P5 の追加分は小さく、P1 / P4 / P6 は推論時間をほとんど増やさない。
