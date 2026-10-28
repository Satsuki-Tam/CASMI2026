# スペクトル–分子 joint embedding (対照学習) による MS/MS 構造検索: 文献調査

- 作成: 2026-10-28 21:35 (ローカル時刻、`date` で取得)。Web 調査のみ (コード実行・学習なし)。
- 目的: 111 (FPNet 初期化スペクトル塔 + 10,226 bit FP 上の MLP 分子塔、cos スコア、±10 ppm 窓の 63 負例 (48 は同式強制)、補助 FP 損失、P の 1 位固定 + RRF(K=10, w=0.5) 融合) の設計判断材料。
- 数値は原典 (arXiv/PMC/bioRxiv 本文または公式 repo) で確認したもの。確認できない事項は「未確認」「見つからず」と明記。hit@k / rank@k / R@k / HR@k はいずれも「正解が上位 k 件に入る割合 (%)」。MSG = MassSpecGym。

## 要約

1. MSG (MCES 分割 test fold、**同式候補だけの bonus 設定**、最大 256 件) の hit@1: FP 予測 MIST 9.57% に対し JESTR 11.85%、MVP 11.10% (単一スペクトル)、De Waele らの Emb-Cos 13.62%、FLARE 22.66%。**大域ベクトル 1 本の dual-encoder の同式異性体での上積みは +1.5〜4 pt 程度**で、2 倍超はピーク–原子の細粒度アラインメント (FLARE) のみ。
2. 111 に最も近い既報は MIST の contrastive head (FP の単層射影 + 同式 PubChem 異性体の hard decoy): top-1 31.70% → 37.39%、FP 距離との加重和は単独より良い。
3. 「FP ビット上の MLP 分子塔 > 線形射影 (f·z 型)」の直接証拠は**見つからず**。同一バックボーン比較では線形射影が生 FP cos より同式候補で +2.25 pt、同質量候補で ±0。MLP スコアラーは最良の線形版を上回らず、同質量候補では悪化。
4. 候補由来の負例は in-batch より大幅に強い (MSAlign 47.5% vs 19.5%) が、**PubChem から Tanimoto 順に掘った「難しい」負例は MSG 自身の候補より悪い** (64 件で 7.74% vs 12.29%)。効くのは難しさよりテスト候補分布との一致。
5. 候補ベース学習はスペクトル非依存の「正解らしさ」事前分布も学ぶ。MSG ではスペクトルを使わない SMILES 分類器が 8.2% (同じ表の MIST 9.57%)、PubChem 既定順だけで 49.98%。82% 級の SOTA 主張は SMILES 正規化差のショートカットで、補正後 6.7%。**「学習正例だった分子がテスト候補に混ざる」バイアスを MS 分野で定量した論文は見つからず** (最も近い類例は一般化ゼロショット学習の seen-class bias)。
6. 融合: MSAlign の late fusion は R@1 47.5 → 58.2 (MSAlign と質量スコアの失敗の重複 <55%)。同系統 FP 系スコア同士 (IOKRfusion) は +0.2〜2 pt。**相補性はモダリティが違うほど大きい**。
7. 学習: 有効な設定はどれも短い (MSG FP-FFN は 4–5 epoch で最良、SpecBridge 2 epoch、JESTR は候補正則化を最後の 3% epoch のみ)。温度は 0.05–0.07 が多く grid では 1/64 が最良の例。負例数は 32–256。

## 1. 主要手法 (Q1)

| 手法 [文献] | 分子側 | 負例 | 主な結果 (split / 候補) | 注意 |
|---|---|---|---|---|
| MIST contrastive [5] | Morgan 4096 bit FP の**単層射影** | 同式 PubChem 異性体の Tanimoto 近傍 256 件から類似度の指数に比例してサンプル。repo 設定: decoy 64、scale 16、contrastive weight 0.6 | 遡及データ・PubChem 同式候補 top-1: 予測 FP cos 31.70% → contrastive 37.39% (CSI:FingerID 38.24%) | bioRxiv v1 の値。論文は同点を楽観側で数え、repo は後に悲観側へ変更し値が下がると注記 |
| JESTR [2] | GCN (キラリティ等の原子・結合特徴) | in-batch (batch 32, τ=0.05) + 最後の 3% epoch だけ同式 PubChem 候補 32 件 (Tanimoto 順) との類似度を下げる正則化 | NPLIB1 (InChIKey 構造分離、PubChem 同式候補。NPLIB1/NIST/MoNA の平均候補数は 1.3–2.5 千件) rank@1 45.76% (MIST 27.96%)。MSG mass 15.13%、formula 11.85% | 正則化: NPLIB1 41.06→45.76、MSG mass 15.62→15.13 (悪化)、formula 11.82→11.85 |
| MVP [3] | GCN と FP (Morgan 1024) の 3 層 MLP の多視点 | in-batch のみ (τ=0.05, batch 64, 1,500 epoch) | MSG rank@1 mass/formula: 単一スペクトル 26.37/11.10、同一分子の consensus spectrum 35.99/13.96 | consensus はテスト分子の全スペクトルを使う。分子側は GCN が FP より良い |
| FLARE [4] | GCN ノード埋め込み。peak (subformula)–原子の最大類似を平均 | in-batch (詳細未記載) | MSG mass 43.15%、formula 22.66% | 監査論文 [9] の表でも 22.66% が有効値 |
| De Waele ら [7] | Fp-Cos (予測 FP と生 FP の cos) / Emb-Cos (FP の 256 次元**線形射影**) / Fp-MLP・Emb-MLP (連結 MLP スコア) | 候補集合全体 (≤256) を softmax 分母に | MSG test 5 run 平均 HR@1 mass/formula: BCE 10.12/10.08、Fp-Cos 12.30/11.37、Emb-Cos 12.29/13.62、Fp-MLP 9.72/12.28、Emb-MLP 11.08/12.46 | 111 に最も近い対照実験 |
| MSAlign [8] | 凍結 DreaMS + 凍結 MolDeBERTa + MLP アダプタ | 候補 128 件/クエリ + batch 128、τ 学習可能 (初期 0.07) | 独自候補 (PubChem ±10 ppm、256 件) で再評価: formula 分割 R@1 47.5% (MIST 41.4、FLARE 32.8)、MCES 分割 19.0% (FLARE 28.4、MVP 25.6、MIST 16.4、Emb-Cos 12.6) | SMILES は RDKit で統一正規化と明記 |
| CSU-MS2 [13] | 未確認 (本文非公開) | 未確認 | CFM-ID/ICEBERG 模擬スペクトルで事前学習→実測で微調整。100 万化合物ライブラリで Recall@1 75.45% (独自ベンチ) | MSG 比較なし |
| CMSSP [14] | 抄録に記載なし | 未確認 | CASMI 2017 top-1 +30% (抄録)。JESTR の再学習比較では NPLIB1 13.92% (公開重みは 54.09%、学習データ重複の可能性) | |
| SpecBridge [11] / GLMR [12] | 凍結 ChemBERTa / ChemFormer (SMILES) | SpecBridge は MSE 整列 (負例なし)、GLMR は in-batch の双方向 InfoNCE (τ=0.1) | MSG で R@1 84.7% / 68.5% を主張 | 監査 [9] が、正解 SMILES (リポジトリ表記) と PubChem decoy (RDKit 正規化) の表記差を突くショートカットと判定。同型の再実装は補正後 6.70% / 7.60% |
| MSG baseline [1] | 予測 FP (Morgan r=2, 4096) と cos | (FP 回帰) | hit@1 mass/formula: FP-FFN 2.54/5.09、DeepSets+Fourier 5.24/6.56、MIST 14.64/9.57 | 候補は 10 ppm・最大 256 件 (87%/66% が上限到達) |

補足: MIST-CF [6] は化学式・付加イオン候補を順位付けするエネルギーベースモデルで、構造の joint embedding ではない。CLERMS [16] はスペクトル–スペクトル埋め込み (分子側なし)。DreaMS [17] は自己教師スペクトルエンコーダで、構造検索では MSAlign/SpecBridge のバックボーン。MVP/FLARE の mass 候補での大きな伸びは、スペクトル側が subformula (元素組成) 付きピークを使い化学式判別が効くためと推測される (同式候補での伸びは小さい)。参考: JESTR 論文は MSG formula 候補で SIRIUS (CSI:FingerID) 19.04% (全 test、JESTR 11.85%) と報告。ただし SIRIUS の学習重複を除いた部分集合では 10.41% vs 13.65%。

## 2. FP ビット MLP vs 線形内積、FP 衝突 (Q2)

- **同一バックボーンの直接比較** (De Waele ら [7]、MSG test): 線形射影の Emb-Cos は生 FP の cos (Fp-Cos) より formula 候補で +2.25 pt (13.62 vs 11.37)、mass 候補で同等 (12.29 vs 12.30)。予測 FP と候補 FP を MLP に入れるスコアラー (Fp-MLP) は mass で 9.72 に低下 (formula では 12.28 と Fp-Cos より高いが Emb-Cos 未満)。著者も「cos 版が学習 MLP 版より良い」と結論。ただし 111 の「FP→MLP→cos」(MLP 塔) そのものは試されていない。
- MIST [5] の分子側は単層射影 (線形) で、それでも top-1 +5.7 pt。
- MVP [3]: FP 視点 (3 層 MLP) より GCN 視点が良い。ただし FP 視点を学習に加えると GCN 側も向上 ([M+H]+ 部分集合 mass rank@1 25.56→29.73)。
- MSAlign [8]: Morgan FP + MLP アダプタは分子基盤モデルより 8.9 pt 低い (DreaMS+Morgan 38.6 vs DreaMS+MolDeBERTa 47.5、formula 分割)。
- ADAPTIVE [18] (2019): グラフ MPNN から学習した 300 次元ベクトル vs 2,765 bit FP (IOKR)。top-1 31.03 vs 30.66 (ほぼ同じ)、top-10 70.89 vs 66.51。
- **結論**: FP ビット上の非線形塔が線形射影を上回る証拠は見つからず。分子側の表現力向上で効果が出ているのは FP を捨てグラフ/言語モデルに移ったケース。
- **FP 衝突**: MSG 論文 [1] は非同一構造でも FP 衝突で類似度 1 になり得ると明記。De Waele ら [7] も候補内に正解と同一 FP ベクトルの候補が存在することを図示 (頻度は未報告)。MIST [5] の同点処理の変更 (上記) も同点の影響が無視できないことを示す。g(FP) は線形でも MLP でも同一 FP の候補に同じスコアを与えるので、**どちらの塔でも上限は「正解の FP が候補内で一意な割合」**。CASMI の採点キー (立体除去→互変異性体正規化→InChIKey 先頭 14 文字) では立体異性体の衝突は無害だが、構造異性体のビット衝突は P の非 FP 特徴 (GLACIER、事前分布) でしか解けない。衝突頻度の文献値は**見つからず**。

## 3. 既知分子バイアスとショートカット (Q3)

- **分割**: MSG [1] は MCES 距離の凝集クラスタリングで fold 間に距離 <10 の分子対が出ないようにした (2D InChIKey 分割では Tanimoto >0.85 の近縁分子が漏れる。膨張量の定量はなし)。NPLIB1 (MIST/JESTR) は InChIKey による構造分離。MSAlign [8] は train–test の分布差をランダム分割比で測り (InChIKey 4.76、formula 5.19、MCES 9.10、Murcko 9.24)、漏洩抑制と分布シフトのトレードオフを指摘。Kretschmer ら [24] は学習データが生体分子空間を均一に覆わないことを MCES 距離で示した。
- **学習分子が候補に混ざる問題**: MSG 論文は候補が学習分子を含むか否かに触れていない。「学習正例だった分子がテスト候補にいると不当に上位に来る」ことを測った MS 論文は**見つからず**。
- **近い証拠**:
  - 候補ベースの目的関数は、ベンチマークの decoy に対するスペクトル非依存の事前分布で得点できる [10] (抄録のみ)。
  - 監査 [9] の leaderboard 表 (MIST 9.57%、最近傍法 9.58% と同じ表): スペクトル無しの ChemBERTa 分類器が補正後 8.2%、キラル原子数だけで 4.88%、PubChem 既定順 49.98%。MIST-CF の式正解率は train のみで学習 50.5%、train+test 59.0%、test のみ 66.5% (記憶による膨張の大きさの目安)。推奨: 入力スペクトルを定数でマスクし性能が落ちることの確認、SMILES 統一正規化、物性を合わせた decoy。
  - 一般化ゼロショット学習 (Chao ら [21]): seen と unseen のクラスを同時に候補にすると unseen の正解率が A_U→U 35.8–73.4% から A_U→T 0.3–13.2% に崩れる。seen クラスのスコアから定数 γ を引く calibrated stacking で AUSUC が新規性検出系の対策より高い (例: AwA 0.583 vs 0.424)。「学習正例が候補に混ざる」111 と構造的に同型。

## 4. 融合の証拠 (Q4)

- **MIST** [5]: contrastive 距離と FP 距離の加重和 (λ_r=0.3、1 fold で手調整) がどちら単独より良い (GNPS 部分集合 top-1 30.7%、top-20 75.7%。単独値は補遺表で本文に数値なし)。MIST が CSI:FingerID と同等以上の順位を付けるのは 66% の例。
- **MSAlign** [8]: 7 スコア (エンコーダ対 4 + 質量スコア 3) の凸結合 (重みは検証 R@1 で決定)。R@1 は formula 分割で 47.5→58.2、MCES 分割で 19.0→30.8。エンコーダ対の融合だけで 47.5→54.4。質量スコアは単独 R@1 0.6–0.8% でも融合で +3.8 pt。MSAlign と質量スコアの失敗の重複は 55% 未満。
- **IOKRfusion** [19] (2019): spectrum→分子空間 (IOKR) と分子→スペクトル空間 (IOKRreverse) のスコアを学習重みで線形結合。top-1 は正イオン 37.6 (reverse のみ)→37.8、負イオン 30.1→32.1。**同系統スコア同士の上積みは小さい**。
- CASMI 2016 [20]: 機械学習系と化学知識系の手法は相補的と結論。
- **前向きモデルは「融合」より「データ拡張」で大きく効いた例** [9]: 学習分割のみで学習した ICEBERG で PubChem 構造の模擬スペクトルを作って MIST を学習すると、formula 候補 R@1 が 9.57%→53.76% (著者が漏洩なしとした設定)。test 分子を混ぜる・test で学習した ICEBERG を使うと 63.85/67.75% に膨らむ。
- RRF [23] は個別システムや Condorcet 融合より良いと報告され、k=60 が標準として広く引用される (k 値の原文は未確認)。**P の 1 位を固定する型の融合の先行例は見つからず**。

## 5. 学習長・温度・負例数 (Q5)

- **長さ**:
  - MSG [1]: 最良は FP-FFN 4–5 epoch、DeepSets 1–3 epoch (検証損失 3 回連続非改善で停止)、MIST 32 epoch。
  - SpecBridge [11]: 2 epoch、DreaMS の最後の 2 ブロックのみ微調整 (Spectraverse R@1 36.58、凍結 31.33、ランダム初期化 24.34。4 ブロック解凍は過学習の可能性と推測)。同論文の MSG 値は監査 [9] で疑義があるため参考程度。
  - JESTR [2]: 候補正則化は最後の 3% epoch のみ (全体 800–1000 epoch で記載が不整合)。
  - De Waele ら [7]: 指標ごとに最良時点が違うため checkpoint を指標別に選択。
  - 一般論 [22]: 事前学習特徴の全面微調整は線形 probe より OOD で約 7% 悪く、LP-FT は全面微調整より OOD で約 10% 良い。
- **温度**: JESTR 0.05、MVP 0.05、GLMR 0.1、MSAlign 学習可能 (初期 0.07)、Yoo ら [15] 0.07、MIST scale 16 (定義未記載)。De Waele らの grid {1/256…4} では Emb-Cos 1/64、Fp-Cos 1/256、MLP 系 1/16 が最良。SpecBridge は InfoNCE の学習が不安定と報告。
- **負例**: MIST 64、JESTR 32、MSAlign 128 + batch 128 (候補型 47.5 vs in-batch 19.5)。De Waele ら [7] (評価は MSG 同質量候補):
  - MSG 同質量 256 件で学習: 12.29
  - MSG 同式 256 件で学習: 10.43
  - PubChem Tanimoto 上位 64 件で学習: 7.74
  - 同 1024 件で学習: 11.64

  著者は理由として PubChem 負例の多くが天然物でないことを挙げる。

## 111 の設計への示唆

1. **期待値**: 111 は文献上 Emb-Cos / MIST-contrastive 系。同式候補での単独上積みは FP cos 比 +2〜6 pt 程度。価値は融合時の相補性次第だが、FPNet 初期化・同一ビット入力のため FP 系スコアと相関しやすい (IOKRfusion 型の小さい上積みになるリスク)。本学習の前に fusion-tune 群で次を測る。
   - P の top-1 誤り (社内 P1 では FP top-1 誤りの 91% が同式異性体) のうち、111 が正解を P の 1 位より上に置く割合
   - P と 111 の同式群内の順位相関
   - 失敗の重複率 (MSAlign 流)
2. **分子塔は単層射影をベースラインに**: MLP の優位を示す証拠はなく、MLP は学習正例の FP を記憶する容量が大きい。線形 vs 2 層 MLP を比べ、差が CI 内なら線形を採用。
3. **衝突と偽負例**:
   - 負例から「正例と同じ採点キー (立体・互変異性体違い)」と「正例と同一 FP ベクトル」を必ず除外 (勾配が矛盾し学習不能)。
   - FP は正例・候補とも採点キー正規化後の構造から計算し、立体・表記差のショートカット ([9] のキラル原子数 4.88%) を断つ。
   - 同点は P の順位で決定的に解き、評価は悲観側の同点処理で。
   - 「正解 FP が候補内で一意な割合」(= FP 系の上限) を集計。
4. **負例分布はテスト候補に合わせる**: 111 が並べ替えるのは P のファネル候補 (PubChem/COCONUT/train ±10 ppm)。[7] の結果から、Tanimoto 的な難しさより生成過程の一致を優先する。
   - P の上位 decoy (P が迷う候補) を厚めに入れる。
   - 同式 48 件は維持しつつ式違いも残す (融合は 2–25 位を跨式で並べ替える。同式負例だけで学習すると同質量評価が 12.29→10.43 に低下 [7])。
   - 63 件は文献の下限寄り。127/255 件か in-batch 負例の追加 (安価) を試す価値あり。
5. **既知分子バイアスは自前で測る** (文献で未定量):
   - (a) 「正解は学習外、候補には学習正例が現実的な比率で混在」の評価群で、学習正例 decoy が正解を上回る率を P と 111 で比較。
   - (b) スペクトルマスク試験で分子塔単独の MRR を測る。ランダムを大きく超えるなら事前分布を学んでおり、P の popularity prior と二重計上になる (社内 E1 の文書化 prior 71% vs FP 7.7% と同じ構図)。
   - (c) 対策候補: in-batch 負例 (学習正例を他スペクトルの負例として押し下げる)、分子側 dropout/重み減衰、seen フラグへの定数ペナルティ γ (calibrated stacking 型) を fusion-tune で調整。
   - class 1 (ライブラリ既知) ではこのバイアスが得になるので class 別に評価する。
6. **学習は短く、選択は融合後の指標で**:
   - LP-FT 順: スペクトル塔を凍結して射影と分子塔のみ学習 → 上位ブロックを低 LR で解凍。
   - checkpoint は 111 単独ではなく融合後 MRR@25 (fusion-tune 群) で選ぶ。
   - 補助 FP 損失は残す (MIST と同型)。
   - τ は学習可能 (初期 0.07) か 0.05 固定。1/64 も試す。
7. **融合パラメータは検証で決める**: K=10, w=0.5 は検証済みの値ではない (RRF 標準は k=60。MIST/MSAlign/IOKRfusion は重みを検証データで決定)。(K, w) を小グリッドで探り、z-score 加算 (社内で FP+GL に効いた形) とも比較する。leader-safe は P の 1 位誤りを直せず、P が正解を r 位に置くスペクトルの改善は最大 1/2−1/r に制限される (2 位の正解は改善余地ゼロ)。改善が起き得るのは P の正解順位が 3 位以下のケースなので、その分布 (特に 3–10 位の割合) を先に数え、上限を見積もる。
8. **評価衛生**: bootstrap CI、class 別の層別、111 も P と同じ fold で OOF 化。統一正規化とスペクトルマスク試験 [9] も行う。
9. **代替レバー (参考)**: 前向きモデルの知識は late fusion より模擬スペクトルによる学習データ拡張で大きく効いた報告がある (9.57→53.76% [9])。ただし GLACIER/ICEBERG は MSG で学習済みで、社内パネルの多くが MSG に含まれるため漏洩管理が前提。

## 見つからなかった / 未確認

- CSU-MS2・CMSSP の分子エンコーダと負例の詳細 (本文非公開)
- FP ビット MLP 塔と線形射影の同条件比較
- 候補内 FP 衝突の頻度
- 学習正例が候補に混ざるバイアスの MS 分野での定量
- P の 1 位固定型融合の先行例
- [10] の本文・数値 (抄録のみ確認)

## 参考文献

1. Bushuiev R. et al. MassSpecGym: A benchmark for the discovery and identification of molecules. NeurIPS 2024 Datasets & Benchmarks. arXiv:2410.23326. https://arxiv.org/abs/2410.23326
2. Kalia A., Chen Y.Z., Krishnan D., Hassoun S. JESTR. Bioinformatics 41(7):btaf354 (2025). https://doi.org/10.1093/bioinformatics/btaf354 (arXiv:2411.14464)
3. Chen Y.Z., Hassoun S. Learning from All Views: A Multiview Contrastive Framework for Metabolite Annotation (MVP). bioRxiv 10.1101/2025.11.12.688047 (2025). https://pmc.ncbi.nlm.nih.gov/articles/PMC12642559/
4. Chen Y.Z., Rushing B., Hassoun S. FLARE: Fine-grained Learning for Alignment of spectra-molecule REpresentation. bioRxiv 10.64898/2026.01.27.702086 (2026). https://pmc.ncbi.nlm.nih.gov/articles/PMC12873900/
5. Goldman S. et al. Annotating metabolite mass spectra with domain-inspired chemical formula transformers (MIST). Nat. Mach. Intell. 5:965–979 (2023). bioRxiv v1: https://www.biorxiv.org/content/10.1101/2022.12.30.522318v1 / repo: https://github.com/samgoldman97/mist
6. Goldman S., Xin J., Provenzano J., Coley C.W. MIST-CF: Chemical formula inference from tandem mass spectra. J. Chem. Inf. Model. 64(7):2421–2431 (2024). https://doi.org/10.1021/acs.jcim.3c01082
7. De Waele G., Wydmuch M., Dembczyński K., Kotłowski W., Waegeman W. Small molecule retrieval from tandem mass spectrometry: what are we optimizing for? arXiv:2602.16507 (2026). https://arxiv.org/abs/2602.16507
8. Krzakala P. et al. MSAlign: Aligning Molecule and Mass Spectra representations for Metabolite Identification. arXiv:2605.19752 (2026; NeurIPS 2026 poster). https://arxiv.org/abs/2605.19752
9. Liu H., Bushuiev R. et al. MassSpecGym in the Wild: Uncovering and Correcting Evaluation Pitfalls in AI-Driven Molecule Discovery. arXiv:2606.19624 (2026; ICML 2026 workshop). https://arxiv.org/abs/2606.19624
10. Musielinski K., Teh C.-E., Koyama T., Dubrawski A. Separability Is Not Alignability: Representations for Spectrum-to-Molecule Retrieval. NeurIPS 2026 workshop (抄録のみ). https://neurips.cc/virtual/2026/174022
11. Wang Y., Chen Y.Z., Chen X., Liu L.-P., Hassoun S. SpecBridge. arXiv:2601.17204 (2026). https://arxiv.org/abs/2601.17204
12. Zhang Y. et al. Breaking the Modality Barrier: Generative Modeling for Accurate Molecule Retrieval from Mass Spectra (GLMR). arXiv:2511.06259 (2025). https://arxiv.org/abs/2511.06259
13. Xie T. et al. CSU-MS2. Anal. Chem. 97(25):13350–13360 (2025). https://doi.org/10.1021/acs.analchem.5c01594
14. Chen L. et al. CMSSP: A Contrastive Mass Spectra-Structure Pretraining Model for Metabolite Identification. Anal. Chem. 96(42):16871–16881 (2024). https://doi.org/10.1021/acs.analchem.4c03724
15. Yoo S., Kim S., Yoon N., Kim H. Contrastive Domain Generalization for Cross-Instrument Molecular Identification in Mass Spectrometry. arXiv:2602.00547 (2026). https://arxiv.org/abs/2602.00547
16. Guo H. et al. Contrastive Learning-Based Embedder for the Representation of Tandem Mass Spectra (CLERMS). Anal. Chem. 95(20):7888–7896 (2023). https://doi.org/10.1021/acs.analchem.3c00260
17. Bushuiev R. et al. Self-supervised learning of molecular representations from millions of tandem mass spectra using DreaMS. Nat. Biotechnol. (2025). https://doi.org/10.1038/s41587-025-02663-3
18. Nguyen D.H., Nguyen C.H., Mamitsuka H. ADAPTIVE: leArning DAta-dePendenT, concIse molecular VEctors for fast, accurate metabolite identification from tandem mass spectra. Bioinformatics 35(14):i164–i172 (2019). https://pmc.ncbi.nlm.nih.gov/articles/PMC6612897
19. Brouard C., Bassé A., d'Alché-Buc F., Rousu J. Improved Small Molecule Identification through Learning Combinations of Kernel Regression Models. Metabolites 9(8):160 (2019). https://pmc.ncbi.nlm.nih.gov/articles/PMC6724104/
20. Schymanski E.L. et al. Critical Assessment of Small Molecule Identification 2016: automated methods. J. Cheminform. 9:22 (2017). https://pmc.ncbi.nlm.nih.gov/articles/PMC5368104/
21. Chao W.-L., Changpinyo S., Gong B., Sha F. An Empirical Study and Analysis of Generalized Zero-Shot Learning for Object Recognition in the Wild. ECCV 2016. arXiv:1605.04253. https://arxiv.org/abs/1605.04253
22. Kumar A., Raghunathan A., Jones R., Ma T., Liang P. Fine-Tuning can Distort Pretrained Features and Underperform Out-of-Distribution. ICLR 2022. arXiv:2202.10054. https://arxiv.org/abs/2202.10054
23. Cormack G.V., Clarke C.L.A., Büttcher S. Reciprocal rank fusion outperforms Condorcet and individual rank learning methods. SIGIR 2009, pp. 758–759. https://research.google/pubs/pub36196/
24. Kretschmer F., Seipp J., Ludwig M., Klau G.W., Böcker S. Coverage bias in small molecule machine learning. Nat. Commun. (2025). https://doi.org/10.1038/s41467-024-55462-w
