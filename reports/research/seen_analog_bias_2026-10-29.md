# 訓練構造バイアス (seen analog bias) と異性体曖昧性: MS/MS→構造検索の文献調査

- 作成: 2026-10-29 01:46 (ローカル時刻、`Get-Date` で取得)。Web 調査のみ (コード・モデル・データのダウンロード/実行/学習なし)。
- 背景 (依頼文の社内監査): 未知化合物シミュレーション (正解のライブラリスペクトルを隠す) で、正解が候補内にあるのに 1 位でないとき、誤 1 位の 91% は正解と同式、57% は同 Murcko 骨格 (Tanimoto≈0.89。脂質鎖/二重結合位置、ステロイド水酸基位置、ペプチド残基入替など) でその約 2/3 が FPNet 学習構造、43% は別骨格 (Tanimoto≈0.45) だが FP 予測器が誤構造 (多くは学習構造) を強く選ぶ。学習類似体を降格するルールは未知側で得、既知側で大きく損。
- 表記: hit@k / R@k / top-k = 正解が上位 k 件に入る割合 (%)。pt = パーセントポイント。MSG = MassSpecGym (公式 test は学習構造と MCES 距離 ≥10)。formula 候補 = 同式候補 (≤256 件、bonus 設定)、mass 候補 = 同質量候補 (≤256 件)。seen = 2D 構造が学習集合に含まれること。π = 隠し test のうち構造が学習集合にある (既知) 割合。
- 数値は原典 (arXiv/bioRxiv/PMC 本文、公式 docs、著者 GitHub) で確認した。確認できないものは「未確認」、探して無かったものは「見つからず」と明記。
- 前回 `contrastive_msms_retrieval_2026-10-28.md` §3 (既知分子バイアス) の更新を含む。**訂正**: 前回「著者が漏洩なしとした設定」として紹介した ICEBERG 拡張 MIST (formula R@1 9.57→53.76%) について、同じ Coley 研の FRIGID v3 (2026-10-25) 付録 B.2.3 が「旧 (v2) の ICEBERG 拡張分子は test 構造の近縁類似体に偏るよう選ばれていた (2D InChIKey 完全一致のみ除外)」と自己訂正している [9]。In the Wild 論文 [2] は 435,072 構造の拡張プールの選び方を書いておらず、両者は同じ「MIST (vFRIGID)」チェックポイントである可能性が高い (未確認)。**53.76% は類似体リークを含みうる上限値として扱う** (§Q2-b)。

## 要約

1. 学習に同じ構造があるかどうかで精度が数倍変わることは古典的に再現されている。CSI:FingerID は構造分離 CV で top-1 34.4%、同一構造が学習側に入る CV で 58.5% [6]。MIST は random 分割 84.0% に対し scaffold 分割 23.1% (MSG formula 候補。test 構造の学習内含有率は 95.3% と 14.3%) [3]。
2. 新規構造 (MSG 公式 MCES 分割) では、MIST の hit@1 9.57% が「最も近い学習スペクトルの FP を写すだけ」の最近傍法 9.58% と同じ [2]。新規構造に対する FP 予測の 1 位は、実質的に学習近傍の検索になっている。
3. 「見たことがある」効果は模擬スペクトルや類似体でも起きる。ICEBERG 拡張プールに正解構造を足すだけで R@1 +10.1 pt (53.76→63.85) [2]。test 類似体に偏った拡張プールでは de novo top-1 18.29% だったが、偏りを除くと 9.05% [9]。デコーダ事前学習から Tanimoto ≥0.7 の類似体を除くと 11.6→8.0% [2]。SIRIUS も MSG で 19.04% だが、自分の学習分子を除くと 10.41% [7]。
4. 「誤った 1 位が学習構造である割合」を直接測った MS 論文は見つからず。社内の「同骨格誤り 1 位の約 2/3 が学習構造」は新しい定量。
5. 前向きモデルは新規性に強い。MSG MCES 分割の formula R@1 は GLACIER 49.88% (mass 69.95%)、ICEBERG 36.18〜44.35% で、MIST は 9.57% [10][2]。random→scaffold の top-1 低下は GLACIER (NIST20) 52.5→46.0 (相対 −12%) で、MIST (MSG) の 84.0→23.1 (相対 −72%) より小さい。ただしデータセットが異なる [10][3]。
6. 候補を意識した対照学習・hard negative は、random/InChIKey 分割で JESTR +2.2〜7.2 pt、MIST +5.7 pt。MSG MCES 分割では JESTR −0.49〜+0.03 pt、対照型損失 (De Waele) +3.5 pt にとどまる [7][8][13]。FP 確率の依存構造を入れた較正は CV +2.85〜3.9 pt、CASMI 2016 で +10.2 pt (26.38→36.61%) [15]。
7. 人気度事前分布は「既知らしさ」を強くエンコードする。MSG ではスペクトルを見ない PubChem 既定順だけで hit@1 49.98% [2]。CASMI 2016 ではメタスコアだけ (MS/MS 不使用) で 72.4% [36]。新規化合物で人気度や既見性をデバイアスした効果を測った MS 論文は見つからず。
8. 異性体に起因する不可避誤り率の直接推定は見つからず。予測 CCS の誤差は中央値 1.2〜2.3% (天然物 2.25%) [27][28]。不確かさ 3.25% で区別できる異性体ペアは 12.6〜31.6%、95% を区別するには 0.04〜0.15% が必要 [24]。CCSP 2.0 は ΔCCS 2.8% で異性体候補の 19.3% を、正解を落とさずに除外 [26]。TIMS と DTIMS の CCS 差は平均 0.47% [25]。
9. 既知/未知の判定: COSMIC は CASMI 2016 で AUC 0.82 (生スコアは 0.40〜0.55)。重要特徴は 1 位と 2 位のスコア差と候補数。ただし最も自信のある誤り 9 件中 7 件は「正解が DB に無く、ごく近い類似体が 1 位」だった [16]。学習データからの埋め込み距離で失敗を予測しても、ほぼランダム (relAURC 0.89〜0.99)。検索レベルの確信度が最良 (0.35〜0.37) [14]。閾値はデータセット間で移らない [16][19]。
10. 示唆の上位 3 つ: (1) 学習構造ペナルティを π 依存の連続値 γ にし、まず損益分岐 π* を出す。(2) 構造分離 OOF 特徴で既知/未知の両レジームを学習させ、前向きモデルを重く使える再ランカーにする。(3) COCONUT 全体の模擬スペクトルで「既見性」を平準化する。

## Q1. 訓練構造への偏り (記憶・最近傍化) は MS/MS で記録されているか

### 1a. 学習に同じ/近い構造があるかで精度が何倍も変わる

| 文献 | 比較 | 数値 | 備考 |
|---|---|---|---|
| CSI:FingerID, PNAS 2015 [6] | 構造分離 CV と測定単位 CV (同一構造の別測定が学習側に入る) の比較。Agilent+GNPS、N=5,923、PubChem 検索 | top-1 34.4% vs 58.5% (+24.1 pt、1.7 倍) | 著者は「同一構造の別化合物の MS/MS は酷似する」と説明。358 件の "新規" MassBank 化合物では全手法の同定率が下がり、原因は説明できないと記載 |
| Coley 研の監査 [3] (GitHub 技術報告、2026-10-05) | Comment [4] が使った random 分割と scaffold 分割 (MSG 公式分割とは別)。test 構造の学習内含有率は MSG 95.3%/14.3%、NPLIB1 62.9%/1.6% | MIST top-1 (random→scaffold): MSG formula 84.0→23.1、MSG mass 89.1→34.7、NPLIB1 (PubChem 同式) 61.8→12.4。最近傍 (NN): MSG formula 60.0→9.3 | random 分割の FP Jaccard では formula 優先 NN 0.929 が MIST 0.859 を上回る |
| MassSpecGym in the Wild [2] (arXiv 2606.19624) | MSG 公式 MCES 分割、formula 候補 | MIST hit@1/5/20 = 9.57/22.11/41.12、最近傍 (再実装) = 9.58/22.26/39.92 | 新規構造では MIST は最近傍と同等 |
| JESTR 論文内の SIRIUS 比較 [7] | MSG formula 候補 | SIRIUS: 全 test 19.04%、SIRIUS 学習分子を含む test を除いた 12,314 スペクトルで 10.41% (1,281 件正解)。同じ部分集合で JESTR は 11.85→13.65% | 全 test 側の母数は SIRIUS が構造を返した 7,766/17,556 スペクトルとみられ、厳密な対比較ではない |
| MIST-CF (式予測) [2] | train のみ / train+test / test のみで学習 | top-1 式正解率 50.5 / 59.0 / 66.5% | 記憶による膨張の目安 |
| NN ベースライン [5] (arXiv 2610.02249、単著、2026-09-30) | 式注釈ピークを使う NN の FP Jaccard | MSG random 0.947 vs scaffold 0.381、NPLIB1 0.758 vs 0.337。同式の学習スペクトルがある test の割合: MSG random 97.1% vs scaffold 41.0% | 査読前 |

- Khoo & Barzilay の Comment (Nature Metabolism 8:1247–1249, 2026) [4] は「SOTA 手法が最近傍ベースラインに勝てない」「data attribution によると学習表現は MS の意味を捉えていない」と主張している。本文は未読で、監査 repo と著者投稿の記述による。監査 [3] は、評価の是正後は強い主張は成立しない (MIST は全設定で検索 top-1 が NN を超える) と結論した。一方で、random 分割の高精度が学習重複に支配されている点は双方の数値が一致している。
- In the Wild [2] は、MSG 結果を報告した 26 本中少なくとも 17 本に評価上の問題 (リーク、ショートカット、実装バグ) があったと報告している。

### 1b. 「見たことがある」は模擬スペクトルや類似体でも効く

| 文献 | 操作 | 数値 |
|---|---|---|
| In the Wild Table 1 [2] | MIST を MSG 学習データ + ICEBERG 模擬スペクトルで学習し、拡張分子集合に test 構造 (正解) を足す。さらに ICEBERG も test で学習する | formula R@1: 拡張なし 9.57 → PubChem 拡張 53.76 → 正解構造を追加 63.85 → test でも学習した ICEBERG 67.75。spec2fp Tanimoto は 0.262 → 0.581 → 0.617 → 0.640 |
| FRIGID [9] | v2 では ICEBERG 拡張分子を test 構造の近縁類似体に偏らせて選んだ (2D InChIKey 完全一致のみ除外)。v3 では MCES ≤2 を除いた MSG 公式 unlabeled 3,922,525 分子を GLACIER で模擬 (7,845 万対 + 実測 194,119 対) | MSG de novo top-1: 18.29% (v2 = ICML 2026 版) → 9.05% (v3)。NPLIB1 は 25.03 → 14.16% (NPLIB1 側の変更内容は未確認) |
| In the Wild Table 6 [2] | MIST+MolForge のデコーダ事前学習 (2.5M) から test 類似体を除外 | Acc@1: 除外なし 11.6 → 完全一致除外 11.0 → Tanimoto ≥0.8 除外 10.4 → ≥0.7 除外 8.0 (≥0.6 除外 7.8)。0.7 で最大の落差 |
| In the Wild Fig. 2 [2] | 事例 | デコーダが事前学習分子 (正解と Tanimoto 0.98) をそのまま出力した。符号化器の予測 FP の Tanimoto は 0.61 で、正解は符号化器ではなくデコーダの記憶による |
| MIST+MolForge [31] | 元論文の主張値 | MSG top-1 28.27%。In the Wild の是正後は 10.73% (バッチ依存バグ) |
| MIST [8] | 前向きモデル拡張に val/test 分子を含めた場合 | "surprisingly strong effect in biasing our model" (数値なし)。以後は除外して実験 |

### 1c. 新規構造での絶対水準 (参考)

- MSG [1] の mass 候補 hit@1: Random 0.37、DeepSets 1.47、FP-FFN 2.54、DeepSets+Fourier 5.24、MIST 14.64。formula 候補: 3.06 / 4.42 / 5.09 / 6.56 / 9.57。de novo のベースライン (SMILES/SELFIES Transformer) は top-1 0%。
- DiffMS [22]: MSG 2.30%、NPLIB1 8.34%。MADGEN は MSG 1.31% (検索要約経由。DiffMS の NPLIB1 値のみ FRIGID 本文 [9] でも確認)。MSNovelist [21]: GNPS 3,863 スペクトルで top-1 25%、候補内回収 45% (CSI:FingerID の DB 検索 top-1 は 39%)。
- Coverage bias [38]: MS/MS 学習データは生体分子空間を一様には覆わない。scaffold 分割でも「ほぼ全ての test 構造について、学習側にある程度近い構造がある」と指摘。
- 誤った 1 位候補が学習構造である頻度を直接報告した論文: **見つからず**。

### 1d. 社内監査との対応

- 同骨格誤り (57%) の約 2/3 が学習構造であることは、1a/1b の「見た構造に寄る」効果と整合する。
- 別骨格誤り (43%、Tanimoto≈0.45) で FP 予測器が誤構造を強く選ぶことは、新規構造で MIST ≈ 最近傍 (1a) と整合する。予測 FP が最近傍の学習構造の FP に引き寄せられている、という解釈ができる。

## Q2. 緩和策と新規構造での効果量

### 2a. 候補を意識した学習 (hard negative / 同式対照 / 損失の選択)

| 手法 | 評価分割 | 効果 |
|---|---|---|
| MIST contrastive [8]: 同式 PubChem 異性体を Tanimoto の指数に比例してサンプル | 構造分割 (3 split) の遡及データ、PubChem 同式候補 | top-1 31.70 → 37.39% (+5.7 pt)。CSI:FingerID は 38.24% |
| JESTR 候補正則化 [7]: 同式 PubChem 候補を最後の 3% epoch だけ押し離す | InChIKey 分割 (NPLIB1 / NIST20 / MoNA) と MSG MCES | +4.70 / +2.24 / +7.18 pt。MSG は mass −0.49、formula +0.03。著者も「MSG の難しい分割では効かない」と記載 |
| 損失比較 (De Waele ら) [13] | MSG (MCES)、5 run 平均 | formula HR@1: BCE 10.08、Focal 11.15、Cosine 9.12、IoU 6.48、対照 Emb-Cos 13.62 (最良)。FP Tanimoto は IoU 19.42 が最高で、対照 Fp-Cos は 7.86。FP 精度と検索精度はトレードオフ |
| GLACIER contrastive finetune [10]: PubChem 同式 + 1 段変異の decoy | NIST20 random / scaffold、MSG | top-1: 39.0→52.5 / 38.4→46.0。MSG は mass 69.69→69.95、formula 48.49→49.88 |

- 新規構造 (MCES 分割) での上積みは 0〜3.5 pt で、random/InChIKey/scaffold 分割では 2〜13 pt。hard negative は「既知寄り」の評価ほど大きく効いて見える。

### 2b. 模擬スペクトルによるデータ拡張

- In the Wild Table 1 [2] (§1b の表): formula R@1 9.57 → 53.76%。各エポックの学習データの 92% (約 2.23M) が合成対で、実測は 194,119 対。拡張プールは 435,072 の PubChem 構造で、test と重複する分子は除外。プールの選び方は本文に記載が無い。
- **注意**: FRIGID v3 付録 [9] は、v2 の ICEBERG 拡張分子が test 近縁類似体に偏って選ばれていたと訂正している。53.76% はこの類似体リークを含む上限値の可能性がある (同一チェックポイントかどうかは未確認)。リークの無い拡張 (ランダム PubChem や MCES >2) での検索性能は、FRIGID v3 でも報告が無い (MIST 2M-aug / 4M-aug は de novo の値のみ)。
- MIST [8]: 学習データの 10 倍にあたる 300,000 分子を前向きモデルで模擬して学習。効果は図のみで、数値は本文に無い。
- Test-time tuning [39]: 模擬スペクトルで事前学習した言語モデルを、test の予測 FP に近い学習例で微調整する方式。MSG de novo top-1 は通常の微調整 1.13% に対し 3.16%。

### 2c. 前向きモデル (スペクトル予測) による再スコア

| モデル | MSG MCES 分割 R@1 (mass / formula) | NIST20 top-1 (random / scaffold) |
|---|---|---|
| GLACIER (contrastive finetune あり) [10] | 69.95 / 49.88 | 52.5 / 46.0 |
| GLACIER (なし) [10] | 69.69 / 48.49 | 39.0 / 38.4 |
| ICEBERG 2.0 [10][12] | 63.95 / 44.35 (別報告で top-1 46.0%、top-10 86% [12]) | 33.5 / 31.6 |
| ICEBERG (In the Wild の再評価、CE は半数を補完) [2] | – / 36.18 | – |
| FraGNNet [10] | 46.64 / 31.93 | – |
| (参考) FP 予測 MIST [1][3] | 14.64 / 9.57 | 監査の random→scaffold は MSG formula で 84.0→23.1 |

- スペクトル cos (NIST20、random / scaffold) [11]: ICEBERG 0.727 / 0.699、MassFormer 0.721 / 0.682、NEIMS-FFN 0.617 / 0.546、CFM-ID 0.412 / 0.411。前向きモデルは分割を変えても劣化が小さい。
- 生成候補の前向き再スコア [9]: DiffMS + ICEBERG 洗練で NPLIB1 top-1 8.34→13.33% (1 試料 1,423 s)。FRIGID-base→FRIGID は MSG 8.21→9.05%、NPLIB1 13.31→14.16%。
- ICEBERG 2.0 [12]: MSnLib 8,519 スペクトルで PubChem 全体 (1 億構造超) を検索し、top-1 38.0%、top-10 80.3%。SIRIUS を上回ると記載 (SIRIUS の数値は本文抜粋に無し)。
- 注意: 前向きモデルも公開ライブラリで学習しており、それ自体の seen bias は測られていない。衝突エネルギー (CE) 情報も必要 (In the Wild は半数を補完)。

### 2d. FP スコアの較正

- Ludwig ら [15] (10-fold CV、PubChem 9,386 万構造、学習 16,865 測定) の top-1: Platt (独立) 39.72 → modified Platt 40.77 → Bayes 固定木 41.51 → 生体変換木 42.92 → 個別木 43.62%。
- 同 [15] の外部データ: Agilent 3,451 スペクトルで Bayes が modified Platt を 1.28 pt 超上回る (39.86%)。CASMI 2016 正イオン 127 件では Platt 26.38 → modified Platt 30.31 → Bayes 36.61% (+10.2 pt)。外部データほど較正の効果が大きい。
- COSMIC の E 値 [16]: PubChem 候補スコアの KDE (対数正規混合) で較正する。生スコアより分離は「わずかに」良い。

### 2e. 不確実性・アンサンブル

- 選択的予測 [14] (MSG formula 候補、17,556 スペクトル、MLP deep ensemble S=5)。1 位を棄却する基準としての relAURC (0 = 理想、1 = ランダム):
  - 検索レベル: total entropy 0.347、confidence (最大候補確率) 0.366、aleatoric 0.364、epistemic 0.438、score gap 0.439
  - その他: 候補数 0.548、bit 単位の不確実性 0.917、潜在空間の kNN 距離 0.985、Mahalanobis 距離 0.977
  - 基礎精度: Transformer 17.44%、MLP アンサンブル 13.12%
- アンサンブル自体が新規構造の精度を上げるという定量: **見つからず**。

### 2f. 候補事前分布 (人気度) とデバイアス

- In the Wild [2]: PubChem 既定順 (CID 順、スペクトル不使用) だけで MSG hit@1 49.98% (hit@5 54.13、hit@20 61.04)。キラル原子数だけで 4.88%、スペクトル無しの SMILES 分類器で 8.2% (是正後)。後者は MIST の 9.57% とほぼ同じ。
- 同 [2] のレビューガイドは「未補正データセットでは頻度事前分布ベースラインが R@1 90% を超え得る」と書いている。v1.5 はスペクトル入力を定数化/置換した対照で事前分布の寄与を測ることを推奨。
- MAD HATTER [36] (評価の落とし穴を示す風刺論文): CSI:FingerID + メタスコア (融点、説明文中の 'u' で始まる単語数など) で CASMI 2016 正イオン 97.6%。MS/MS を使わなくても 72.4%。
- MetFrag [35] (473 スペクトル、PubChem): MS/MS のみでは top-1 30 件。参照数 + RT を加えると 336 件 (71%)。
- CSI:FingerID [6]: 生体 DB に絞ると top-1 34.4 → 55.2% (生体化合物のみなら 68.5%)。
- COSMIC の著者 [16]: 引用数などのメタスコアは新規化合物には存在しないので使うべきでないと主張。生体 DB から PubChem に広げると、低 FDR での正解数が大きく減る。
- 新規化合物で人気度・既見性のデバイアス効果を測った MS 論文: **見つからず**。機械学習側の類例は一般化ゼロショット学習の calibrated stacking (seen クラスのスコアから定数 γ を引く。前回レポート §3、Chao ら [41])。

## Q3. 位置/領域異性体の曖昧さと tie-break 情報

### 3a. 誤りに占める「MS/MS で決まらない異性体」

- 不可避率 (MS/MS では原理的に区別できない異性体による誤りの割合) を定量した査読論文: **見つからず**。
- MARLIN [23] (arXiv 2607.04774、NPLIB1、top-1 16.94〜19.18%): 完全一致しなかった top-1 の約 70% が正解から MCES ≤10。中央値は 6 (検索要約による。ページ抽出では 66 と読めたが、70% が ≤10 という記述と整合するのは 6)。典型的な近接誤りはラクトン位置、環の位置化学、二重結合位置、ジペプチド配列の入替。著者はこれを「タンデム MS が決めない縮退」と呼び、完全一致精度の上限を縛ると書いている。
- ICEBERG 2.0 [12]: Leu/Ile のように MS/MS で区別できない異性体があるので、完全な top-1 は難しいと記載。
- COSMIC [16]: 最も確信度の高い誤り 9 件はすべて正解とごく類似で、うち 7 件は正解が DB に無かった。「MS/MS だけでは原理的に区別できない可能性」に言及。
- SIRIUS 6 [17]: この状況に対応するため、別に approximate 確信度を用意している。1 位が正解と MCES ≤2 (「単純な化学反応 1 段」以内) なら正解とみなす。
- LIPID MAPS の略記法 [32]: 階層的な表記 (種、分子種、sn 位置、二重結合位置) は MS アッセイごとの構造分解能の違いを反映する。sn 位置や二重結合位置が決まらない場合の表記規則のみで、頻度の数値は無い。
- MSG の MCES@1 (formula 候補): Random 13.87、MIST 12.75、ICEBERG 6.61、MIST (vFRIGID) 5.16 [2]。
- CASMI の採点は 2D (InChIKey 先頭 14 文字) なので、立体異性は問題にならない。問題は構造 (位置) 異性体 (前回レポート)。

### 3b. 保持時間 (RT)

- Akhlaqi ら [24]:
  - 予測 RT (RMSE 1.55 min、拡張不確かさ ±3.1 min) で区別できた異性体ペアは 10.5% (別データの 432 ペアでは 13.6%)。5 特徴中 4 特徴で候補を 1 つも除外できなかった。
  - 95% のペアを区別するには、予測区間を 0.15 min 未満 (別データでは 0.05 min) にする必要がある。
  - 5 つの異性体グループ中 4 つで MS2 断片の m/z が同一だった。
- LC-MS2Struct [33]: 保持順序と MS2 を組み合わせ、MS2 スコアラーの精度を最大 106% (相対) 向上させた。キラル FP により立体異性体も順位付けできる。
- 隠し test で RT が使えるかどうか: 未確認。

### 3c. CCS / イオン移動度 (timsTOF の 1/K0 → CCS)

- **予測精度**:
  - SigmaCCS [28]: 中央値相対誤差 (MRE) 1.18% (test)、1.82% (外部)
  - AllCCS [27] (外部検証): 代謝物・脂質 1.66% / 1.74% (正 / 負イオン)、薬物 1.81%、天然物 2.25%
  - CCSP 2.0 [26]: [M−H]− 1.25%、[M+H]+ 1.73%、[M+Na]+ 1.87%
  - Akhlaqi ら [24] は予測 RMSE を >2% と記載
- **測定の再現性**:
  - Feuerstein ら [25] (ステロイド、DTIMS 基準の平均絶対差): TIMS 0.47% (95 パーセンタイル 1.03%)、TWIMS 0.82%。±1% の許容では、テストステロン/エピテストステロン抱合体の大半がプラットフォーム間で区別できない。
  - METLIN-CCS [29]: 脂質で DTIMS vs TIMS ±1.03%。
- **異性体の区別能**:
  - Akhlaqi ら [24]: 不確かさ 3.25% で区別できる異性体ペアは、4 つの文献データで 31.6 / 12.6 / 28.0 / 17.5%。95% を区別するには 0.04〜0.15% が必要。
  - CCSP 2.0 [26]: ΔCCS 2.8% で、正解を 100% 残したまま異性体候補 (0 ppm) の 19.3% を除外。同 superclass の誤候補なら 36.1% を除外。
  - 測定 CCS (予測ではない) では、アフィジコラン異性体ペアの 64/104 (60% 超) が区別できた [30]。
- **候補削減**:
  - AllCCS [27]: m/z + MS/MS + CCS で候補が 553→144 (74%)。CFM-ID/MetFrag/MS-FINDER の正解順位が 81.2〜88.8% の化合物で改善した。ただし弱い MS/MS スコアラーとの組合せでの結果。
  - SigmaCCS [28] (脂質 761 件、LipidBlast、m/z・RT・CCS によるフィルタ。MS/MS は使っていないとみられる): recall@1 15.2% (m/z のみ) → 24.6% (+RT) → 28.9% (+CCS)、recall@30 47.6 → 78.4 → 91.2%。
- **分解能**: DTIMS/TWIMS の分解能 40〜60 では異性体分離は限られ、200 で部分分離、500 でベースライン分離 [27]。高分解能 TIMS が PC/DG の sn・二重結合異性体を分離した報告もあるが、特別な設定での結果 (詳細未確認)。
- **含意**: 予測 CCS の誤差 (≈2%) は多くの位置異性体の ΔCCS より大きいので、同骨格誤りへの効果は小さい。別骨格誤り (43%) は形状差が大きく効きやすいはずだが、この区分別の定量は見つからず。

### 3d. 分類学・出現情報

- Rutz ら [34]: 試料生物と候補構造の報告生物の分類学的距離で再ランクした (ISDB-DNP、MS-Finder、SIRIUS)。F1 が 1.5〜7 倍になった。
- 隠し test に生物種のメタデータがあるかどうか: 未確認。

## Q4. 既知/未知 (ライブラリ内/外) の判定と方針切替

| 手法 | 判定の仕組み | 報告された精度 | 装置間 |
|---|---|---|---|
| COSMIC [16] | 方向制約つき線形 SVM + Platt。特徴は 1 位と 2 位のスコア差・候補数 (「非常に重要」)、E 値、断片木の説明強度、FP の基数 | CASMI 2016 (生体 DB 123 件): AUC 0.82 (MetFrag/MAGMa+/CFM-ID/CSI の生スコアは 0.40〜0.55)、FDR<10% で 57 件正解。確信度 0.94 / 0.64 / 0.34 / 0.14 が正確 FDR 5 / 10 / 20 / 30% に相当するが、他データへ移る保証は無いと明記。正解が DB に無いクエリは CV で 22.70%、独立データで 17.29% | Orbitrap (NIST) で学習し、QTOF (Agilent、Sciex) で評価。Sciex では CSI 生スコアも較正スコアもヒットの並べ方がランダム以下。COSMIC は FDR<5% で 23 件、<15% で 166 件 |
| SIRIUS 6 [17] | exact と approximate (MCES ≤2) の 2 種の確信度。expansive search は、指定 DB の後に PubChem も検索し、PubChem 1 位の確信度が 2 倍以上なら PubChem 側の結果を表示する | 公開評価は**見つからず** (docs のみ) | – |
| MS2Query [18] | MS2DeepScore / Spec2Vec / 前駆体質量差などをランダムフォレストで統合 | 類似体 test で閾値 0.633 → recall 35%、平均 Tanimoto 0.63 (修正 cos は 0.45)。完全一致の検出は MS2DeepScore や cos より良い (図のみ)。事例研究では質量差 1 Da 未満を exact、超を analog とラベル (精度は未報告) | 負イオンで性能が落ちる (数値なし)。GNPS ライブラリにある既知天然物は約 2.5% (序論の背景値) |
| 選択的予測 [14] | 検索レベル / FP レベル / 入力レベルの不確実性 | 検索レベルの relAURC 0.35〜0.37 が最良、潜在距離は 0.89〜0.99 でほぼランダム。K=20 なら目標リスク 0.5 で 87% を保持 | 装置別の分析なし |
| スペクトルライブラリ FDR [19][20] | target-decoy (断片木 decoy が最良) / entropy 類似度 | 70 の公開データで「全データの FDR を制御できる普遍的なスコア閾値は無い」[19]。entropy 類似度 ≥0.75 で天然物 37,299 スペクトルの FDR <10% [20] | 閾値はデータごとに較正が必要 |
| Hybrid search (NIST) [40] | 直接のピーク一致と中性損失の一致を組み合わせ、同族体 (cognate) を探す | 類似化合物を見つける可能性が高いと報告 (数値は本文未確認) | – |

- 既知/未知を判定して方針を切り替えるパイプラインの、切替込みの精度評価: SIRIUS expansive search 以外の公開例は**見つからず**。その評価値も未確認。
- timsTOF データでの既知/未知判定や閾値の移植性の報告: **見つからず**。参考までに、de novo の test-time tuning [39] では MSG 内で Orbitrap 2.86%、QTOF 5.24% (部分集合が異なる)。
- 最も重要な含意: COSMIC の誤り分析 (9 件中 7 件) は、確信度型の判定が「正解が DB に無く、MS/MS がほぼ同じ類似体が 1 位」の場面で高確信のまま誤ることを示している。これは社内の同骨格・学習構造誤りそのものである。この部分はクエリ単位の判定では扱えず、集団レベルの事前確率 (π) でしか扱えない。一方、別骨格誤りではライブラリ一致も弱くなるはずなので、クエリ単位の判定が効く余地がある。

## このプロジェクトへの示唆 (期待値順)

### 1. 学習構造ペナルティを π 依存の連続値にし、先に損益分岐 π* を出す (コスト最小)

- **内容**:
  - 降格ルールを、スコア − γ·seen (seen は 2D InChIKey ∈ FPNet 学習集合。学習構造への最大 Tanimoto で段階化してもよい) という連続ペナルティに置き換える。
  - 既存の既知/未知シミュレーションで MRR@25_known(γ) と MRR@25_unknown(γ) を測り、期待値 E(γ, π) = π·K(γ) + (1−π)·U(γ) を求める。
  - 現行の硬いルールが損益ゼロになる π* = ΔU/(ΔU+ΔK) を出す (ΔU = 未知での得、ΔK = 既知での損)。
  - γ は、もっともらしい π の範囲 (例: 0.2〜0.6) で最悪時の後悔が最小になる値を選ぶ。人気度事前分布にも同じ考え方を当てる (人気構造 ≈ 学習構造なので)。
- **検証**: γ 曲線と bootstrap CI を既知・未知別に出す。スペクトル入力を置換した対照 [2] で、事前分布だけの寄与もレジーム別に測る。
- **根拠**:
  - 既見性バイアスは系統的で大きい: +24 pt [6]、3.6〜5 倍 [3]、新規構造で MIST ≈ 最近傍 [2]、拡張で正解構造を足すと +10 pt [2]、類似体プールで 2 倍 [9]。
  - 一般化ゼロショット学習では、定数 γ を引く calibrated stacking が標準的な対処法 [41]。
  - COSMIC [16] は、同骨格の近縁誤りがクエリ単位の確信度では検出できないことを示している。π による集団レベルの補正が、同骨格誤りに対して筋の通るレバーになる。
- **主なリスク**: 隠し test の π は不明 (主催者情報は「多くがライブラリに無い」という定性のみ)。公開 test はダミーなので検証できない。π が想定より高いと既知側で失点する。timsTOF への移行でスコア尺度もずれる。

### 2. 既知/未知の両レジームを学習した LambdaRank (構造分離 OOF + 前向きモデル重視)

- **内容**:
  - 再ランカーの学習クエリを 2 種類用意し、目標 π で重み付けする: (a) 構造分離 OOF の FPNet 予測 (正解が未学習 = 未知レジーム)、(b) 既知レジーム。
  - 特徴を追加する:
    - 候補側: seen フラグ、学習集合への最大 Tanimoto
    - クエリ側の既知らしさ: 前駆体一致を条件とした最良ライブラリ entropy 類似度、FPNet の 1 位と 2 位の差、候補数、FPNet と GLACIER/ICEBERG の順位一致度
  - 相互作用は木に学習させる。人気度事前分布の重みも既知らしさと相互作用させる。
- **検証**: MRR@25 を既知・未知・混合で出し、特に別骨格誤り (43%) の区分を見る。既知らしさの判定 AUC も出す。
- **根拠**:
  - 前向きモデルは新規構造で強い: MSG MCES 分割の formula R@1 は GLACIER 49.88% / ICEBERG 36〜44% に対し MIST 9.57%。scaffold 分割での劣化も小さい [10][2][11]。
  - CSI:FingerID と COSMIC は、構造分離 CV の予測で較正・学習している [6][16]。COSMIC の主要特徴はスコア差と候補数で、AUC は 0.82 [16]。
  - 埋め込み距離を既知らしさの代理にするのは無効 (ほぼランダム) [14]。
  - 確信度比で検索先を切り替える先例として、SIRIUS expansive search (2 倍ルール) がある [17]。
- **主なリスク**:
  - 確信度型の判定は近縁の学習類似体に騙される [16] ので、改善は主に別骨格誤りに限られる。
  - GLACIER/ICEBERG 自身の seen bias は測られていない。
  - timsTOF の CE 設定と学習分布がずれている。
  - シミュレーションで設定した π への過適合。

### 3. 模擬スペクトルで「既見性」を平準化する (COCONUT 全体を GLACIER で模擬し、FPNet を追加学習)

- **内容**:
  - COCONUT の全構造と、学習構造の PubChem 同式異性体を GLACIER で模擬する。GLACIER は従来の 2 段階モデルより約 8 倍速い [10]。
  - 実測と混ぜて FPNet を微調整する。In the Wild では合成が 92% を占めた [2]。
  - こうすると、正解も decoy も少なくとも模擬スペクトル経由で「見た」状態になる。seen フラグは「実測で見た」の意味に再定義する。
- **検証**: シミュレーションでは、未知の正解だけを拡張に入れないこと (decoy と同じ割合で入れる)。既知・未知別の MRR 変化を見る。
- **根拠**:
  - In the Wild [2]: 9.57→53.76% (上限)。正解構造を足すとさらに +10 pt。
  - FRIGID v2→v3 [9]: 類似体に偏った拡張プールで 2 倍。
  - MIST [8]: test 分子を拡張に入れると強いバイアス。
  - つまり「拡張プールに入っている」ことの利得は大きい。全候補に均等に与えれば非対称が消え、前向きモデルの知識の蒸留にもなる。
- **主なリスク**:
  - 計算と時間のコスト。
  - リークの無い効果量は不明 (53.76% は類似体リークを含みうる)。
  - 模擬と実測 (timsTOF) の差。
  - 既知側の精度を削るおそれ。

### 4. FP スコアの OOF 較正と、同式 hard negative 微調整

- **内容**:
  - 構造分離 OOF の予測で bit 別の較正 (Platt/温度) を学習し、cos の代わりに較正後の対数尤度で候補を採点する (CSI:FingerID 方式)。可能なら相関する bit の依存木も入れる。
  - 候補 DB 由来の同式 decoy で対照微調整する。
- **根拠**:
  - 較正は CV +2.85〜3.9 pt、CASMI 2016 +10.2 pt [15]。
  - 対照型損失は MSG MCES 分割で +3.5 pt [13]。
  - ただし JESTR の正則化は MCES 分割では ≈0 [7]。GLACIER CF は scaffold で +7.6 pt、MSG formula で +1.4 pt [10]。
- **主なリスク**: 真に新規な構造での利得は小さい見込み (0〜3.5 pt)。LambdaRank が既に一部を吸収している可能性がある。10,226 bit の依存モデル化は重い。

### 5. 不可避な異性体誤りの上限を見積もり、効く所にだけ直交情報 (CCS/分類学) を足す

- **内容**:
  - 未知シミュレーションの誤りについて、正解と誤 1 位の GLACIER 予測スペクトル類似度と FP の一致を計算し、「MS/MS 縮退」と判定された割合を改善余地の上限として出す。
  - 隠し test に 1/K0 があれば、予測 CCS (天然物でσ≈2%) との |ΔCCS|/σ を特徴に加える。主に別骨格誤り向け。
  - 生物種のメタデータがあれば、LOTUS/COCONUT の出現事前分布を加える。
- **根拠**:
  - 誤りの多くが MS/MS の縮退 [23][12][16]。
  - CCS で区別できる異性体ペアは 12.6〜31.6%、RT では 10.5〜13.6% [24]。CCSP 2.0 は異性体候補の 19.3% を除外 [26]。TIMS と DTIMS の差は 0.47% [25]。天然物の予測 MRE は 2.25% [27]。CCS 追加で recall@1 +4.3 pt (脂質、MS/MS なし) [28]。
  - 分類学的再ランクで F1 1.5〜7 倍 [34]。
- **主なリスク**: CCS や生物種情報が提供されない可能性。位置異性体では予測誤差 ≈ ΔCCS なので利得が小さい。出現・人気系の事前分布は既見性バイアスを再導入しうる (§2f)。

## 見つからなかった / 未確認

- 「誤った 1 位候補が学習構造である頻度」を直接測った MS 論文 (見つからず)。
- MS/MS で区別できない異性体による誤り (不可避率) の定量推定 (見つからず)。
- In the Wild の 435,072 構造プールの選び方 (本文に記載なし)。FRIGID v3 の訂正対象と同一かどうか (推定のみ)。
- GLACIER 拡張 MIST (FRIGID v3 の MIST 2M/4M-aug) の検索性能・FP 精度 (報告なし)。
- SIRIUS approximate / expansive search の公開評価値 (docs のみ)。
- アンサンブルが新規構造の精度を上げる定量 (見つからず)。
- timsTOF スペクトルでの既知/未知判定、閾値の移植性 (見つからず)。
- Khoo & Barzilay の Comment 本文 (未読。監査 repo と検索要約による)。
- DiffMS/MADGEN の MSG 値 (検索要約経由)。MARLIN の MCES 中央値 (6 か 66 か、抽出に揺れ)。Hybrid search の数値。高分解能 TIMS による脂質異性体分離の詳細。
- 一般化ゼロショット学習の数値は前回レポート経由 (今回は再確認していない)。

## 参考文献

1. Bushuiev R. et al. MassSpecGym: A benchmark for the discovery and identification of molecules. NeurIPS 2024 Datasets & Benchmarks. arXiv:2410.23326. https://arxiv.org/abs/2410.23326
2. Liu H., Bushuiev R., et al., Pluskal T., Coley C.W. MassSpecGym in the Wild: Uncovering and Correcting Evaluation Pitfalls in AI-Driven Molecule Discovery. arXiv:2606.19624 (2026-06-17). https://arxiv.org/abs/2606.19624 (本文 HTML: https://arxiv.org/html/2606.19624v1)
3. Coley group. Does Machine Learning Really Fail at Mass Spectrometry? Re-evaluating the MIST and Nearest-Neighbour Benchmarks (技術報告、2026-10-05). https://github.com/coleygroup/Audit_ML_MS_analysis (数値: DETAILED_RESULTS.md)
4. Khoo L.M.S., Barzilay R. Why machine learning fails at mass spectrometry for small molecules. Nat. Metab. 8:1247–1249 (2026). doi:10.1038/s42255-026-01544-6 (本文未読)
5. Khoo L.M.S. Nearest-neighbour baselines for fingerprint prediction from MS/MS spectra under different assumptions. arXiv:2610.02249 (2026). https://arxiv.org/abs/2610.02249
6. Dührkop K., Shen H., Meusel M., Rousu J., Böcker S. Searching molecular structure databases with tandem mass spectra using CSI:FingerID. PNAS 112(41):12580–12585 (2015). https://pmc.ncbi.nlm.nih.gov/articles/PMC4611636/
7. Kalia A., Chen Y.Z., Krishnan D., Hassoun S. JESTR: Joint Embedding Space Technique for Ranking candidate molecules. Bioinformatics (2025). arXiv:2411.14464. https://arxiv.org/abs/2411.14464
8. Goldman S. et al. Annotating metabolite mass spectra with domain-inspired chemical formula transformers (MIST). Nat. Mach. Intell. 5:965–979 (2023). bioRxiv: https://www.biorxiv.org/content/10.1101/2022.12.30.522318
9. Bohde M., Liu H., Manjrekar M., Lederbauer M., Ji S., Wang R., Coley C.W. FRIGID: Scaling Diffusion-Based Molecular Generation from Mass Spectra at Training and Inference Time. ICML 2026 (PMLR 306; v2 相当) https://proceedings.mlr.press/v306/bohde26a.html / arXiv:2604.16648 v2 (2026-07-27)、v3 (2026-10-25、付録 B.2.3 で訂正) https://arxiv.org/abs/2604.16648
10. Wang R.-X., Wang R., Coley C.W. GLACIER: Rethinking Mass Spectrum Prediction as an Object Detection Problem. NeurIPS 2026. arXiv:2606.29161. https://arxiv.org/abs/2606.29161
11. Goldman S., Li J., Coley C.W. Generating molecular fragmentation graphs with autoregressive neural networks (ICEBERG). arXiv:2304.13136. https://arxiv.org/abs/2304.13136
12. Wang R., Manjrekar M., et al., Coley C.W. Neural Spectral Prediction for Structure Elucidation with Tandem Mass Spectrometry (ICEBERG 2.0). bioRxiv 10.1101/2025.05.28.656653 (v2). https://www.biorxiv.org/content/10.1101/2025.05.28.656653v2
13. De Waele G., Wydmuch M., Dembczyński K., Kotłowski W., Waegeman W. Small molecule retrieval from tandem mass spectrometry: what are we optimizing for? arXiv:2602.16507 (2026). https://arxiv.org/abs/2602.16507 。同著者の NeurIPS 2026 ポスター "On objective mismatch in molecular retrieval from tandem mass spectrometry" (同一研究と推定) https://neurips.cc/virtual/2026/poster/151639
14. Jürgens M., De Waele G., Rakhshaninejad M., Waegeman W. When should we trust the annotation? Selective prediction for molecular structure retrieval from mass spectra. arXiv:2603.10950 (v2 2026-08-10). https://arxiv.org/abs/2603.10950
15. Ludwig M., Dührkop K., Böcker S. Bayesian networks for mass spectrometric metabolite identification via molecular fingerprints. Bioinformatics 34(13):i333–i340 (2018). https://academic.oup.com/bioinformatics/article/34/13/i333/5045720
16. Hoffmann M.A. et al. High-confidence structural annotation of metabolites absent from spectral libraries (COSMIC). Nat. Biotechnol. 40:411–421 (2022). https://pmc.ncbi.nlm.nih.gov/articles/PMC8926923/
17. SIRIUS 6 documentation, Methods background (COSMIC exact/approximate、expansive search). https://v6.docs.sirius-ms.io/methods-background/
18. de Jonge N.F. et al. MS2Query: reliable and scalable MS2 mass spectra-based analogue search. Nat. Commun. (2023). doi:10.1038/s41467-023-37446-4. https://pmc.ncbi.nlm.nih.gov/articles/PMC10060387/
19. Scheubert K. et al. Significance estimation for large scale metabolomics annotations by spectral matching. Nat. Commun. 8 (2017). doi:10.1038/s41467-017-01318-5. https://pmc.ncbi.nlm.nih.gov/articles/PMC5684233/
20. Li Y., Kind T., Folz J., Vaniya A., Mehta S.S., Fiehn O. Spectral entropy outperforms MS/MS dot product similarity for small-molecule compound identification. Nat. Methods 18:1524–1531 (2021). https://escholarship.org/uc/item/0249w6hk
21. Stravs M.A., Dührkop K., Böcker S., Zamboni N. MSNovelist: de novo structure generation from mass spectra. Nat. Methods (2022). doi:10.1038/s41592-022-01486-3. https://pmc.ncbi.nlm.nih.gov/articles/PMC9262714/
22. Bohde M. et al. DiffMS: Diffusion Generation of Molecules Conditioned on Mass Spectra. ICML 2025. arXiv:2502.09571. https://arxiv.org/abs/2502.09571
23. Che X., Du X., Xu D. MARLIN: De Novo Molecular Structure Elucidation from Tandem Mass Spectra without a Ground-Truth Formula. arXiv:2607.04774 (2026). https://arxiv.org/abs/2607.04774
24. Akhlaqi M., Wang W.-C., Möckel C., Kruve A. Complementary methods for structural assignment of isomeric candidate structures in non-target LC-IM-HRMS analysis. Anal. Bioanal. Chem. 415(21):5247–5259 (2023). https://pmc.ncbi.nlm.nih.gov/articles/PMC10404200/
25. Feuerstein M.L. et al. Comparability of Steroid Collision Cross Sections Using Three Different IM-HRMS Technologies: An Interplatform Study. J. Am. Soc. Mass Spectrom. 33(10):1951–1959 (2022). https://pmc.ncbi.nlm.nih.gov/articles/PMC9545150/
26. Rainey M.A., Watson C.A., Asef C.K., Foster M.R., Baker E.S., Fernández F.M. CCS Predictor 2.0: An Open-Source Jupyter Notebook Tool for Filtering Out False Positives in Metabolomics. Anal. Chem. 94(50):17456–17466 (2022). https://pmc.ncbi.nlm.nih.gov/articles/PMC9772062
27. Zhou Z. et al. Ion mobility collision cross-section atlas for known and unknown metabolite annotation in untargeted metabolomics (AllCCS). Nat. Commun. 11 (2020). https://pmc.ncbi.nlm.nih.gov/articles/PMC7455731/
28. SigmaCCS (Zhang Z. ら). Highly accurate and large-scale collision cross sections prediction with graph neural networks. Commun. Chem. (2023). https://pmc.ncbi.nlm.nih.gov/articles/PMC10319785/
29. Baker E.S. et al. METLIN-CCS: an ion mobility spectrometry collision cross section database. Nat. Methods 20(12):1836–1837 (2023). https://pmc.ncbi.nlm.nih.gov/articles/PMC10843661
30. Ion Mobility-Derived Collision Cross-Sections Add Extra Capability in Distinguishing Isomers and Compounds with Similar Retention Times: The Case of Aphidicolanes (2022). https://pmc.ncbi.nlm.nih.gov/articles/PMC9503386/
31. One Small Step with Fingerprints, One Giant Leap for De Novo Molecule Generation from Mass Spectra (MIST+MolForge). arXiv:2508.04180. https://arxiv.org/abs/2508.04180
32. Liebisch G. et al. Update on LIPID MAPS classification, nomenclature, and shorthand notation for MS-derived lipid structures. J. Lipid Res. 61(12):1539–1555 (2020). https://escholarship.org/uc/item/8pt1f9w7
33. Bach E., Schymanski E.L., Rousu J. Joint structural annotation of small molecules using liquid chromatography retention order and tandem mass spectrometry data (LC-MS2Struct). Nat. Mach. Intell. (2022). doi:10.1038/s42256-022-00577-2. https://orbilu.uni.lu/handle/10993/54236
34. Rutz A. et al. Taxonomically informed scoring enhances confidence in natural products annotation. Front. Plant Sci. 10:1329 (2019). https://doi.org/10.3389/fpls.2019.01329
35. Ruttkies C., Schymanski E.L., Wolf S., Hollender J., Neumann S. MetFrag relaunched: incorporating strategies beyond in silico fragmentation. J. Cheminform. 8:3 (2016). https://pmc.ncbi.nlm.nih.gov/articles/PMC4732001/
36. Hoffmann M.A., Kretschmer F., Ludwig M., Böcker S. MAD HATTER Correctly Annotates 98% of Small Molecule Tandem Mass Spectra Searching in PubChem. Metabolites 13(3):314 (2023). https://pmc.ncbi.nlm.nih.gov/articles/PMC10053663/
37. 前回レポート (社内): C:\kaggle\CASMI\reports\research\contrastive_msms_retrieval_2026-10-28.md
38. Kretschmer F., Seipp J., Ludwig M., Klau G.W., Böcker S. Coverage bias in small molecule machine learning. Nat. Commun. (2025). doi:10.1038/s41467-024-55462-w. https://pmc.ncbi.nlm.nih.gov/articles/PMC11718084/
39. Mismetti et al. Test-Time Tuned Language Models Enable End-to-end De Novo Molecular Structure Generation from MS/MS Spectra. ICLR 2026. arXiv:2510.23746. https://arxiv.org/abs/2510.23746
40. Cooper B.T. et al. Hybrid search: a method for identifying metabolites absent from tandem mass spectrometry libraries. Anal. Chem. 91 (2019). doi:10.1021/acs.analchem.9b03415. https://pmc.ncbi.nlm.nih.gov/articles/PMC7299168
41. Chao W.-L., Changpinyo S., Gong B., Sha F. An Empirical Study and Analysis of Generalized Zero-Shot Learning for Object Recognition in the Wild. ECCV 2016. arXiv:1605.04253 (前回レポート `contrastive_msms_retrieval_2026-10-28.md` §3 で確認した数値を参照)。https://arxiv.org/abs/1605.04253
