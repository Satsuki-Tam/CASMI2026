# 141 素案(登録ではない、2026-10-30 08:1x JST)— GL の識別目的: 同じ式の hard negative を使う retrieval の学習

動機は誤りの台帳(140_error_ledger.md)である。list 内の誤りの主体は同じ式の中の識別で、MRR の損失の 47% を占める。その中で、真の方を上に置くのは FP 31%、GL 33% だけである。134 の A2(強度の損失で timsTOF に適応)は NO だった(主の点推定は +0.044、区間は 0 を含む)。Codex 135 / 140 は、GL に次の投資をするなら「同じ式の hard negative を使う識別 / 検索の目的」を別の仮説として一つ登録するよう推している。

## 仮説
GLACIER の強度側(A2 と同じ範囲: inten_encoder / inten_decoder / output_map)を、真と同じ式のデコイの間の softmax の目的で学習する。そうすれば、未見の timsTOF / NP 分子での同じ式の識別(rr_form)が、released(C0')より改善する。**変えるのは目的だけ**とし、範囲・データ・ステップ数は A2 と揃える(一つの変更の比較)。

## 設計の骨子(Codex に確認してから固定する)
- **学習の identity**: A2 と同じ tims_s1(fold 3 / 4、timsTOF、2,000 identity / 5,135 スペクトル)。
- **デコイ**: 各 identity の中性質量の窓(PubChem tier / v2 pool / COCONUT)から、真と同じ中性式の構造を集め、公式 key で重複を除く。hard negative は、C0' の GL が高い順の上位 K(例えば K = 7)とする。C0' で GL を採点するコストが大きければ、真との Tanimoto が高い順にする。どちらにするかは、速度試験の後、結果を見る前に固定する。
- **損失**: 各スペクトルについて、候補(真 + K 個)の予測スペクトルと観測スペクトルの類似度(runner の entropy 類似度を微分可能にした近似、または model の inten_loss の負)を温度 τ で softmax し、真の負の対数尤度を取る。A2 の end-to-end の強度損失を、小さな重みで併用するかは Codex に相談する。
- **評価**(Codex 134 の教訓: 隠しテストは全て timsTOF なので、検出力を確保する):
  - 主: 未見の timsTOF の分子(f1G + f2G + 未開封の locked G を合わせて約 300)での GL-only の rr_form の差(A3 − C0')が、≥ +0.01 かつ下限 > 0。
  - 費用: NP_H / D の rr_form と、各 cell の rr_gl の下限 ≥ −0.01。panel は記述。
- **その後**: 通れば、134 の段階 3(GL の交換と ranker の接続)と同じ形の別登録に進む。

## 準備の費用の見積り
- デコイの窓: 2,000 identity × 窓の取得(FP の採点は不要)。Spark の CPU で約 1 時間。
- C0' の GL での hard negative の選択: 2,000 × 同じ式の候補(中央値は数十)× スペクトル。Spark の GPU で数時間の可能性がある(速度試験で決める)。
- 学習: A2 の約 (K + 1) 倍の forward。A2 は 123 s だったので、数十分。
- 実装: ms-pred の学習 loop にデコイの forward と softmax の損失を加える(finetune_glt.py の v3)。約半日。
