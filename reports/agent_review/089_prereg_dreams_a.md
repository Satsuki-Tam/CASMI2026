# 089 事前登録: DreaMS-FP view の段 (a) — pool 窓での FP 単独の識別力(学習・評価の前に固定)

作成: 2026-10-27 18:33 JST(Claude Code、Codex 088 の回答前の暫定;回答が結果の前に届けば条件を追記で調整、結果の後は変えない)。
- **埋め込み**: dreams_min.py(DreaMS 推論、MIT;注意 bias の厳密な O(N) 化のみ変更)、fp32、store の全行(data/processed/dreams_emb)。
- **頭(固定)**: dreams_fp_train.py、入力 = 埋め込み 1024 + adduct one-hot 11 + 極性 + CE 2、MLP 2048-2048、dropout 0.1、出力 10,226 bit の logit。損失 = pool の ±10 ppm 負例 63 個との順位 CE + BCE(train_fpnet.py と同じ形)。30,000 step、bs 512、AdamW lr 1e-3(warmup 1,000、cosine)、wd 0.01、seed 0。**fold 1 と fold 2 の二本**(fold k の identity とパネル 250 identity を学習から除外)。構成の探索はしない(この一回で読む)。
- **評価**: fold k の全分子(パネル除外)、一分子 ≤ 8 スペクトル(seed 123 で選択)、logit 平均。真の順位 = その分子の質量 ±10 ppm の pool 窓全体での順位。比較: rF = 公開 fold-safe FPNet fold k(同じスペクトル、単スペクトル入力の logit 平均)、rD = DreaMS 頭、rE1.0 = z(F) + z(D)、rE0.5 = z(F) + 0.5 z(D)(z は窓内で標準化)。
- **主層 = 真が COCONUT 構造(pool src 2/3)の分子**(クラス 2 の NP 経路の化学)。併記: 全体、非 COCONUT、ライブラリ別。
- **段 (b) へ進む条件**: COCONUT 層の MRR@25 で rE1.0 − rF ≥ +0.01 が fold 1・fold 2 の両方(点推定)かつ両 fold を合わせた分子単位の paired bootstrap(2,000 回)の 95% 下限 > 0。満たさなければ段 (b) は行わず記録(fine-tune 等の別案は別登録)。rD 単独は記録のみ。
- 注意(記録): DreaMS の事前学習(GeMS、MassIVE の無ラベル スペクトル)は train / 隠しの分子のスペクトルを含み得る(ラベルの漏れではない)。段 (a) の fold-safe は「頭の学習に fold k の identity を使わない」意味に限る。

## 追記(19:08、学習・評価の前;Codex 088 の評価契約に合わせる)
- **評価は学習と分離**(dreams_fp_eval.py;頭の学習は dreams_fp_train.py --eval 0、構成は上記のまま)。
- **評価単位** = fold k の identity × library × 極性(一回の取得の近似;限界として記録)。query は本番と同じ選択(試験 adduct、select_queries の round-robin、最大 8、store 行順)。
- **候補集合** = query 由来(adduct ごとの中性質量の中央値)の ±10 ppm 窓の和集合の pool 構造。真が窓外 = 未到達(全手法で RR 0、件数を記録)。
- **主対照 F = 本番入力の FPNet fold k**(単位内のスペクトルを merge_spectra、precursor 中央値、最頻 adduct、CE 平均、n_merged = min(n, 8))。単スペクトル平均 Fs は診断。
- **主融合 E = z(F) + z(D)**(z は同じ候補集合で、分散 0 は 0)。E05 = z(F) + 0.5 z(D)、ES = z(Fs) + z(D)、D 単独は診断のみで主判定の不合格を救済しない。
- 順位は score 降順、同点は pool index 昇順(真に依存しない);D の埋め込みが単位に無いときは E = F(件数を記録)。
- **評価集合(固定)**: fold k の COCONUT 正解 identity の全部 + 非 COCONUT identity 5,000(seed 0)。identity の得点 = 単位の RR の平均(単位等重み)。
- **進行条件(変更なし、母集団を明確化)**: COCONUT identity で E − F(RR@25 の identity 平均)が fold 1・fold 2 の両方で ≥ +0.01、かつ fold 内で identity を再標本化する paired bootstrap(2,000)で、両 fold 等重みの結合差の 95% 下限 > 0。
- 併記: library / 極性 / adduct 類(H・Na・その他)、窓サイズ、F が外れ E が救った数と逆、同じ分子式内の順位(診断)。
- **既視の注意**: DreaMS の埋め込みモデル(ContrastiveHead)は MoNA の約 25,000 スペクトル / 約 5,500 構造で同一分子の対照学習を経ている(論文)。backbone は「identity 未見」ではない(MoNA 等の再配布を含め seen / unseen / unknown の区別は未実施)。fold-safe は「頭の学習」についてのみ。MoNA の単位を別に報告する。
- 083(fold 4)は DreaMS の頭・設定の選択に使わない(使うなら別登録で、fold 4 を除いた頭で)。
