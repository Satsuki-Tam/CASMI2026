# 105 計画(草稿): GLACIER の timsTOF 適応の予備試験(Codex 103 Q2 の段階設計)

状態: 草稿。**開始には利用者の許可が要る**(ms-pred の GitHub リポジトリ = 外部コードの取得と、学習用の依存パッケージの導入)。登録(結果の前の固定)は段階 2 の前に別に行う。

## 目的と仮説
- 異性体の区別で最も強い単独の証拠は前方モデル(P1 timsTOF 集合: GL 単独 0.643 vs FP 0.465;E2b 未見・最近傍 decoy: GL 0.64 vs FP 0.59)。公開 GLACIER は MassSpecGym(主に Orbitrap / QTOF)で学習済み。隠しテストは timsTOF。
- 仮説: enveda-180(timsTOF、合成化学、115 万スペクトル)等で追加学習すると、timsTOF の query に対する GL の識別(真 vs 同じ分子式の decoy)が上がる。FOAM の「予測精度が律速」は別条件の所見で、これの直接の証拠ではない(Codex 103)。

## 段階と関門(拡張は各関門を通った場合だけ)
| 段階 | 内容 | 関門 |
|---|---|---|
| 0 準備 | ms-pred を固定 commit 708148c2(手元の推論資産と同じ)で取得、学習用の環境を既存と別に作る(DGL / pygmtools / LinSATNet 等の本来の依存;推論用 shim では学習しない)。ARM(Spark)で不可なら x86(手元の PC、時間を区切る)で | 少数 batch の forward / backward が有限、重みが実際に更新される |
| 1 データ / 実装の往復 | 既使用の学習 identity 少数で、competition のスペクトル → ms-pred の入力形式(adapter)→ MAGMa 前処理(本家の手順)→ 1 回の更新 → checkpoint の export → 現行の gl_runner(--ckpt)で再読込。timsTOF の instrument token、adduct、CE の単位・欠測、ピーク処理を本番と対応させる | C0'(同じ重みを新しい学習・export 環境に通しただけ)が C0(凍結 GLACIER)と同じ予測を出す(gl score の差が許容内) |
| 2 小規模の適応 | enveda-180 から固定した 1,000〜3,000 identity(公式 identity 単位で fit / tune、同一分子の複数スペクトルを独立標本として重く数えない)。最初は限定した更新を一つ(例: 強度側のみ、断片検出は固定) | 開発の固定群(G 型 timsTOF と NP の D / COCO を分けて)で、同じ候補・同じ質量条件の **GL 単独** の MRR@25・top1・真と decoy の差・同分子式内の順位が CFT > C0'。真の注入なし、未到達 0、対象外 adduct と失敗は分ける |
| 3 主出力への接続 | v8w7a の候補と出力規則を固定し、GL だけ交換。単体が良くても旧 ranker では利得が出ない可能性 → 旧 / 新 GL の OOF 特徴で ranker を同じ手順で学習する比較へ | 102 / 104 と同じ主指標・保護(新しい登録で) |
| 4 本番 | 全データで再学習した checkpoint、学習コード・前処理・split・export を公開可能な形で保存、Kaggle(x86 / T4、9 時間、internet 無効)での予測一致と時間 | parity と実行時間 |

## 露出の台帳(fold-safe の範囲)
- 追加学習の positive から、評価に使う開発 / 確認 identity(公式 identity / alias group 単位)を除外。checkpoint 選択・CE 補正・hard negative・補助統計も同じ範囲で。
- 公開 GLACIER が既に見ていた identity(MSG の学習 positive)は消せない → 評価行ごとに「ベース GLACIER の既見 / 未見」「追加学習の既見 / 未見」を記録し、**両方に未見**の行を新規 identity への効果の主評価にする。パネル(236 / 250 が MSG)は既知 identity・新しい取得の側の保護に使い、cold C2 の確認には使わない。
- enveda-180 での改善は化学空間の適応も含む → G だけでなく NP 側(D / COCO)の費用を必ず見る。

## 未解決のリスク
- DGL 等の ARM 対応(Spark は aarch64)。不可なら x86 での学習が要る(手元の PC は利用者の許可の範囲で)。
- MAGMa 前処理の計算量(数千 identity なら数時間の見込み、要実測)。
- 強度の適応だけでは識別が動かない場合 → 同分子式の hard negative を使う既存の contrastive fine-tuning を次の仮説に(GLACIER 論文はスペクトル精度が少し下がっても retrieval が上がる例を報告)。
- 学習コードの公開義務(勝者は training / inference code と環境・再現方法を提供)→ 最初から引渡し可能な形で書く。
