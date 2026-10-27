# 089 事前登録: DreaMS-FP view の段 (a) — pool 窓での FP 単独の識別力(学習・評価の前に固定)

作成: 2026-10-27 18:33 JST(Claude Code、Codex 088 の回答前の暫定;回答が結果の前に届けば条件を追記で調整、結果の後は変えない)。
- **埋め込み**: dreams_min.py(DreaMS 推論、MIT;注意 bias の厳密な O(N) 化のみ変更)、fp32、store の全行(data/processed/dreams_emb)。
- **頭(固定)**: dreams_fp_train.py、入力 = 埋め込み 1024 + adduct one-hot 11 + 極性 + CE 2、MLP 2048-2048、dropout 0.1、出力 10,226 bit の logit。損失 = pool の ±10 ppm 負例 63 個との順位 CE + BCE(train_fpnet.py と同じ形)。30,000 step、bs 512、AdamW lr 1e-3(warmup 1,000、cosine)、wd 0.01、seed 0。**fold 1 と fold 2 の二本**(fold k の identity とパネル 250 identity を学習から除外)。構成の探索はしない(この一回で読む)。
- **評価**: fold k の全分子(パネル除外)、一分子 ≤ 8 スペクトル(seed 123 で選択)、logit 平均。真の順位 = その分子の質量 ±10 ppm の pool 窓全体での順位。比較: rF = 公開 fold-safe FPNet fold k(同じスペクトル、単スペクトル入力の logit 平均)、rD = DreaMS 頭、rE1.0 = z(F) + z(D)、rE0.5 = z(F) + 0.5 z(D)(z は窓内で標準化)。
- **主層 = 真が COCONUT 構造(pool src 2/3)の分子**(クラス 2 の NP 経路の化学)。併記: 全体、非 COCONUT、ライブラリ別。
- **段 (b) へ進む条件**: COCONUT 層の MRR@25 で rE1.0 − rF ≥ +0.01 が fold 1・fold 2 の両方(点推定)かつ両 fold を合わせた分子単位の paired bootstrap(2,000 回)の 95% 下限 > 0。満たさなければ段 (b) は行わず記録(fine-tune 等の別案は別登録)。rD 単独は記録のみ。
- 注意(記録): DreaMS の事前学習(GeMS、MassIVE の無ラベル スペクトル)は train / 隠しの分子のスペクトルを含み得る(ラベルの漏れではない)。段 (a) の fold-safe は「頭の学習に fold k の identity を使わない」意味に限る。
