# 148 依頼の下書き(2026-10-30 11:56 JST = git a04bd24、Claude Code)— S2 の候補 (iv): forward モデルの合成スペクトルで FPNet を増強する

147 の回答を読んでから送る。

## 動機
- **文献**(research_notes の rank_fusion_methods.md / ms_ml_benchmarks.md)
  - MassSpecGym では、forward(GLACIER / ICEBERG)による検索が、同じ分子式の異性体の識別で R@1 50〜70% と最も強い。
  - FRIGID は、PubChem の構造の合成スペクトル(ICEBERG。MSG train だけで学習した、test を漏らさない版)で MIST を増強した。分子式が既知の設定で、R@1 は 9.6% → 53.8% になった。
- **私たちの課題**
  - P の C2 の損失の 47% は、同じ分子式の異性体。
  - 隠しテストの B 群(train に無い COCONUT の正解)が、P の最大の寄与(0.220)で、E0(0.259)との差の主因。
  - 合成スペクトルの増強は、FPNet に「train に無い COCONUT / PCL の化学」を直接教える。
- **構造としての位置づけ**: forward モデルを最後の並べ替えに使うのではなく、FP モデルへ蒸留する。これは、P と E2 が共有している f.z の質そのものを変える。E2 を別の FP にする S2 (i)(ii) とは、狙いが違う。

## 最小の確認(案)
1. COCONUT の構造(436k)と PubChemLite の tier の構造の合成スペクトルを、GLACIER(現行の C0′ / 公開の重み)で作る。[M+H]+ と [M−H]−、CE は 2〜3 点。
   - A3 の採点の実績は約 100 候補/秒なので、約 1.5〜6 時間。
2. fold 1 を除いた FPNet を、既存の学習ループ(train_fpnet.py、4 時間)に合成のスペクトルを一定の比率で混ぜて、1 本学習する。
3. fold 1 の開発(np053_f1dev / eval_set_f1)の C2 で比べる。
   - f.z だけの E 窓の MRR、P の shortlist での MRR、異性体の識別(同じ分子式の中での真の順位)。
   - 対照は、既存の fold 1 の FPNet。
   - 開発の分子は MSG と重ならないので、GLACIER の既見の問題は無い。パネルは 226/250 が MSG にあるため、使わない。
4. 通ったら、fold 3/4(E2 / P の学習用)と full_eval(提出用)を学習し直し、P と E2 の両方に入れる。

## 確認したい点
1. 隠しテストの class 2 の正解の構造が、増強に入ることの扱い。公開の DB の構造であり、ラベルは使っていない。競技上の正当性と、開発の評価との整合をどう考えるか。
2. 合成と実測の domain gap(timsTOF、CE)に対する設計。比率、CE の選び方、A3 の適応済みの重みを使うかどうか。
3. 関門と費用(GPU で 1 本あたり約 10 時間)。
