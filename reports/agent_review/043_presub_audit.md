# 043 提出前の監査(gt3、19:09 JST 時点)

## (a) 公式 key での新規性(Codex 043 Q5a、`diag/gt3_audit.md`)
- 全評価集合(dev2 v2・パネル・conffit・conffit2・conf3・W7、c1/c2 view)で gt3 が挿入した **1,123 構造**について、精密質量 ±10 ppm・同じ分子式の PubChem tier・v2 pool・COCONUT 構造を公式 key に正規化して照合(1 構造あたりの同式構造の中央値 250〜3,357)。
- **既知(公式 key 一致)は 2 件(0.18%)**、いずれも tier/COCONUT の別表記(互変異性)、train だけの構造との一致は 0。→ 凍結版の「raw-window 不在規則」は、挿入された構造については公式 key での不在とほぼ一致(99.8%)。仕様は変えず、規則名は「raw-window 不在」と記録する。
- (未実施の補足) 窓の外の DB 全体での存在は照合していない(±10 ppm の同式構造だけ)。

## (b) alias の gate(進行中)
- parity16 には DB 3 位が alias 行の分子が無かったため、**パネル 250 分子すべて**で凍結 pipeline(gt3)と gen_eval2p の選択・gate・挿入、基準リスト(b1_parity)を比較中(`spark_gt3_panelpar.sh`)。
- **C2 の結果(19:11)**: 基準リスト(anaw0.5)250/250 一致(top-1・RR・順序付き top-25)、アナログ特徴 56,130 候補で差 0、生成の parity **250 分子で不一致 0**(挿入 96 件 = 評価器の 96 件)。DB 3 位が alias 行の分子は 3 件、うち 2 件は新規生成物があり gate が alias の fp と比較された → 一致を確認。**C1(19:51): 基準リスト 250/250、アナログ特徴 56,116 候補で差 0、生成の parity 0 不一致(挿入 145 件 = 評価器の 145 件)。両 view PASS。**
- 提出ファイル(同じ凍結 pipeline のパネル 250 分子の出力): 250 行・id 一意・全リスト 25 件以内・公式 key 重複 0。

## smoke(Kaggle、12 分子)
- `casmi26-b1-fpnet-gt3` v1: 完走 674 s、FPNet sha 5b8d1c31(full_eval)、引数 gen_rank 3 / gen_rule fzgate / gen_dv 0 / analog_w 0.5、生成物あり 11、挿入 8、400 行出力。提出ファイル本体のダウンロードは Kaggle API の rate limit(出力に pip site の多数のファイルを含むため一覧取得で上限)で未取得 → 同じ凍結 pipeline のパネル 250 分子の出力で行数・25 件上限・公式 key 重複を確認する。

## 結論
- 043 の提出前条件(a 新規性、b alias の gate、smoke、提出ファイル、累積 D の記録)をすべて満たした → **10/27 枠 3 = gt3**(kernel `casmi26-b1-fpnet-gt3` v1)。
