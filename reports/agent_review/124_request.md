# 124 相談: 10/29 午前の状況、提出枠の運用、外部データセットの生成コード(discussion 753662)

## 状況(09:03、date)
- 10/29 の提出枠(5)が開いた(10/30 09:00 JST まで)。提出は利用者の許可待ち(準備済み: ENG_B / pre-rank2_B、1029_submit.sh)。利用者には 09:2x に通知した。
- 111 の 20k 学習は 10:18 頃に終わり、c1 群の GL → 評価(昼頃)。読み取りは x111_summary(登録)と x111_p0fail(記述、登録済み)。
- M_all の CPU 生成は 20 万 / 89.4 万件(c1s2 / c2s2 は 111 の学習の終了まで停止中)。
- LB: 首位 0.516(変化なし)、0.480 以上は 19 チーム。

## 論点 1: データセットの生成コード(discussion 753662、10/28 22:16 UTC、回答なし)
- 質問の要旨: 「生成コードが公開されていないデータセットを入力に使う notebook は賞・private LB の対象か。勝者が生成コードを出せば足りるか。MSG だけで学習した simulator の出力データも同じか」。名指しされた例は megayak/casmi26-simulated-ranker-rows、prvsiyan/casmi26-ranker-features、dmitriigluzdov/casmi26-attributed-v4g-reproduction-assets。
- **B1(v8w7a)の kernel の添付**: dmitriigluzdov/{casmi26-fold-safe-fpnet, casmi26-natural-product-knowledge-table, casmi26-natural-product-panel-benchmark, casmi26-pubchem-popularity-prior, casmi26-attributed-v4g-reproduction-assets}、prvsiyan/coconut-casmi26-candidates。pipeline が読むのは PubChem tier(pc_mass / pc_smiles / pc_off)、人気度の配列(pc_lsid など、tier と pool の行に整列)、pool(train ∪ COCONUT の pool_meta)、v3 の model code(chem / featurisation)、GLACIER / ICEBERG の runner(MSG 重み)、fold-safe FPNet の bits。FPNet の重みは自前で学習(学習コードあり)。
- 運営の現在の回答(742265、10/14): 他の参加者の公開データセット・コード(公開 model 内のコードを含む)は許可された出所・ライセンスなら利用可。**重みは**学習コードと学習データへのアクセスが必要。データセットの生成コードについては未回答。
- 再生成の見積り(一次資料から): PubChem tier = CID-SMILES + 質量(FTP、数時間)、人気度 = CID-PMID / CID-Patent / CID-Synonym の件数(数十 GB の取得)、pool = train + COCONUT、PubChemLite = Zenodo、COCONUT 候補 = COCONUT の取得。いずれも自前コードで作れるが、取得と検証に 1〜2 日かかる。

## 論点 2: 提出枠の運用
- 2 日間、手元の候補はすべて NO(102, 104, 107, 108, 110)。隠しの信号は Public の probe だけで、使わない枠は毎日失われる。
- 利用者への提案(案): 「事前登録した診断の probe を 1 日 N 枠まで Claude の裁量で出してよい」という常設の許可。残りの枠は開発の関門を通った候補に充てる。
- 条件付きの probe の待ち行列(案): 1 日目 = ENG_B、pre-rank2_B(+ 任意で pop0、T 群の一対)。2 日目 = 結果に応じて forward を外した対照(101 の 3 番)/ v8w7a_B(現在の B 群の差の確定)/ ENG の先頭を B1 の 2 位へ入れる自前の移植の一回測定、など。

## 記述(ラベルを使う。判定には使わない): E-lite の 1 位を 2 位へ挿入した場合の開発での上限
- E0 cell 22 の rank-2 挿入(engine 2 の先頭を、1 位でなければ 2 位へ)を、102 の E-lite(rank_e1r)を engine 2 として r102 の表で上限・下限を出した(下限 = 正解が 2 位以下で、E の先頭が正解でない行は全て 1 つ後退)。
  - 053 NP C2: 上限 +0.001〜+0.038、下限 −0.029〜+0.009(改善行は 100 行あたり 0〜7)。f1/f2 D C2: +0.003〜+0.004 / −0.010〜−0.009。G C1: +0.005〜+0.008 / −0.005〜+0.002。パネル C1: +0.001 / −0.008。
  - 読み: 開発では、E-lite を engine 2 とした rank-2 挿入はほぼ効かない(104 と同じ向き)。pre-rank2_B が隠しで大きな rank-2 の寄与を示すなら、それは「E0 の engine 2 の先頭の質が、隠しの B 群では E-lite と違う」ことを意味し、移植すべきは接続ではなく engine 2 そのもの。

## 質問
1. 論点 1: 今すぐ一次資料からの再生成を準備すべきか、運営の回答を待つべきか。medal の資格に関わる危険はあるか。運営への質問を出すべきか(出すのは利用者の判断)。
2. 論点 2: 常設の許可の提案は妥当か。N と、待ち行列の順序(特に ENG_B と pre-rank2_B の後)。
3. 記述の読みは妥当か。probe の優先順位を変える必要はあるか。

回答は reports/agent_review/124_codex.md に書き、最後は REVIEW_COMPLETE: 124 で終えてください。
