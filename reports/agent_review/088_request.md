# 088 相談: E0 の B 群の優位をどう分解するか、次の大きな手(DreaMS 由来の FP view)の評価設計

作成: 2026-10-27 18:32 JST(Claude Code)。読み取り専用で構いません(PC は 086 / 087 の評価と DreaMS の埋め込み計算で使用中、Spark は利用者の別件で使用不可)。

## 事実の整理
1. Public の一対 probe: E0_B 0.259 vs B1_B 0.204(0.379 版、Δ +0.055)。053 dev の台帳(085)では B1 の B probe 相当 0.693(v4b)/ 0.700(v7f)、「B へ先に絞ってから top 25」の上積みは +0.0067 だけ。**EA は T 群の候補を下げるだけなので B probe(T を除いた後の順序)をほぼ動かさない** → E0 の B での優位は「B 候補の中の順序」か「top 25 への採用」(開発では小さい)にある。
2. E0 に未見の清潔な集合は小さすぎる: EXT 60 分子のうち COCONUT 正解は 12、MassSpecGym の非 train 分子は 232(MSG の val/test fold は 111)。E0 の全部品は train 全体で学習済みなので、train 由来の dev では E0 を非リークで評価できない。→ B 群の問いを E0 と同じ分子で直接比べられるのは隠しテストだけ。
3. E0 の B 順序に関わり得る部品(069 の棚卸し): engine 1 = pool 窓(中央値 75)を模擬学習の LambdaRank 160 特徴で採点(gain 上位: mass_ppm_rank、el_rank、sf_rank、lib_max_rank、lib_nspec、ap_rank、best_tan_np、**fzABD_gap、fzD_gap** = DreaMS を FP 予測へ fine-tune した view を含む多 view の FP)、engine 2 = prvsiyan の別 FP + HistGB(パネル 250 を含む S=0/S=1 模擬行)、RRF・rank-2、forward は式内のみ、N1A proxy。
4. 公開 fold-safe FPNet の README: 未見分子の pool 窓 top-1 は 68%、**未見の天然物では 33%**。クラス 2 の NP では FP の汎化が中心的な弱点(E0 の開発者ログでも式内の識別は f·z が最強特徴)。
5. 新規の準備(18:00〜): ホストが名指しで許可した DreaMS の推論専用実装(hengck23 の dataset、MIT)を自前のコードに複製(帰属を明記)。注意の一つの変更: パラメータの無い graphormer の注意 bias Σ_k(f_ik − f_jk) を s_i − s_j として計算(厳密な恒等式;[B,N,N,980] の実体化を避け 178 → 1,000 spectra/s、fp32)。bf16 は Fourier 特徴が壊れる(fp32 との cosine 中央値 0.27)ので fp32 のみ。dataset の事前計算埋め込みとの一致: cosine 中央値 1.0000(4096 行)。**store の全 2.54M スペクトルを埋め込み中(19:15 頃完了)**。

## 提案(DreaMS-FP view)
- 頭: 凍結した DreaMS 埋め込み(1024)+ adduct・極性・CE → FPNet と同じ 10,226 bit の logit。学習は train_fpnet.py と同じ損失(pool の ±10 ppm 負例との softmax 順位 CE + BCE)、**identity fold k を除外(+ パネル 250 identity を除外)した fold-safe の頭を 5 本**(本番用はさらに別)。
- 段 (a)(安価、今夜): fold k の分子(一分子 ≤ 8 スペクトル、logit 平均)で **pool 窓全体での真の順位**を、同じスペクトルに対する公開 fold-safe FPNet fold k と比較。D 単独、F 単独、z(F) + w z(D)(w = 0.5, 1)。ライブラリ別(NP 系)に報告。
- 段 (b)(a が有望なら): 053 dev f1/f2(頭 1/2)・f1dev/f2dev・パネル(本番頭)の shortlist 候補に f·z_D を付け、v7f 主出力への (i) 固定則への加算、(ii) ranker 特徴(学習表は頭 0/3/4 で OOF)を、事前登録の上で一変更比較。

## 質問
- Q1: E0 の B 優位の分解として、この DreaMS-FP view は筋の良い次の大きな実験か。見落としている落とし穴(例: DreaMS の事前学習データ GeMS = MassIVE の無ラベル スペクトルに隠し分子のスペクトルが含まれる可能性 = ラベルの漏れではないが「既視感」の効果、train の NP ライブラリとの重複、fold 間の構造類似による楽観)は。
- Q2: 段 (a) から (b) へ進む条件を、(a) の結果を見る前にどう固定するか。私の案: **NP 系ライブラリ(gnps / riken / massbank / mona / msdial / spectraverse)の分子で、fold 1・fold 2 の両方で z(F) + z(D) の MRR@25 が F より +0.01 以上**。D 単独の値は記録のみ。
- Q3: 別の分解手段として、E0 の段別の B probe(engine 1 の BASE を B に絞る / engine 2 の ENG を B に絞る;それぞれ Kaggle で ~4 時間、提出枠 1)の優先度。10/28 の枠は 4 本予定(v8w、ggt3t、EA、v7f+EA;利用者の許可待ち)で 1 枠空き。T 群の一対 probe(E0_T / B1_T)とどちらを先にすべきか。
- Q4: 他に、E0 の B 優位について安く確かめられる説明(例: B1 の ranker が人気度特徴 7 個に依存し、隠しの有名でない B 正解で順序を崩している、など)があれば。
