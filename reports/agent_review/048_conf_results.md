# 048 確認の結果(conf_g_f1a 474 分子、一回だけ読んだ、01:47 JST)

出力は ggt3(対照)と ggt3t だけ。fpnet_fold1。表 `diag/g048_confg.md`。

| 層 | ggt3t − main | ggt3 − main |
|---|---:|---:|
| C1 C / E / F / G | −0.0017 / −0.0049 / −0.0046 / −0.0021 | −0.0017 / −0.0057 / −0.0057 / −0.0021 |
| C2 C / D / E / F / G | −0.0027 / −0.0019 / −0.0058 / −0.0046 / −0.0013 | −0.0027 / −0.0019 / −0.0072 / −0.0051 / −0.0013 |
- (a) C3 NP 等重み **ggt3t − ggt3 = −0.0008**(C 0、D 0、E −0.0033、F 0)≥ −0.002 ✓
- (b) C1/C2 全層で ggt3t ≥ −0.0058 ✓(−0.01 未満なし)
- (c) 参考: 最悪の層が ggt3 の −0.0072(C2 E)から −0.0058 に改善。
- **判定: ggt3t は合格** → ggt3 の改良版(GL 経路は同じ gg3、fallback の f·z gate を「主出力 2・3 位の f·z の最大以上」に締める)。gt3 / ggt3 の後継の候補。
- 併記: この新しい集合では ggt3 自体も全層 ≥ −0.0072(C1 F −0.0057)で、fold-2 locked の C1 F −0.0126 は小さな層(n 50)の揺れを含むと考えられる(判定には使わない)。
- 次: pipeline に締めた gate(新しい --gen_rule)を実装し、parity(全リスト)・smoke を経て、gt3 の Public 結果の後の比較候補にする。

## 追記(2026-10-27 04:19): ggt3t の実装と parity
- pipeline: `--gen_rule fzgate2`(GL の無い分子で「生成 f·z ≥ max(主出力 2・3 位の f·z)」)、凍結 `experiments/b1_gen048`(pipeline b48feb7f)。
- パネル 250 の両 view で全 parity **PASS**: 基準リスト(b1_parity)、全リスト(gen_parity4 --rule ggt3t: c2 は 250 query・GL 経路 132・挿入 73・失敗 0)、GL 規則(gen_parity3: c2 は 132 分子・挿入 59・不一致 0)、c1 も PASS(`logs/spark_ggt3t_panel.log` の GGT3T_P250_DONE PASS)。
- kernel `hayatetaf/casmi26-b1-fpnet-ggt3t` v1 を push(commit run の smoke 待ち)。提出は gt3 の Public の結果の後(045/046 の条件)。
