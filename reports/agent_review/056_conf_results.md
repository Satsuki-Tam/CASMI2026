# 056 confirmation (rank_v8w - rank_v4b, reserved 3b/4b, read once)

| block | set | view | n | v4b | v8w | delta | up / down |
|---|---|---|---:|---:|---:|---:|---|
| 3b | C_np_crosslib | c1 | 150 | 0.9613 | 0.9624 | +0.0011 | 2 / 1 |
| 3b | C_np_crosslib | c2 | 161 | 0.5573 | 0.5738 | +0.0165 | 20 / 15 |
| 3b | D_np_single | c1 | 1 | 1.0000 | 1.0000 | +0.0000 | 0 / 0 |
| 3b | D_np_single | c2 | 200 | 0.3054 | 0.3046 | -0.0008 | 12 / 14 |
| 3b | E_np_negonly | c1 | 120 | 0.8510 | 0.8510 | +0.0000 | 0 / 0 |
| 3b | E_np_negonly | c2 | 200 | 0.4453 | 0.4453 | +0.0000 | 0 / 0 |
| 3b | F_np_uncovered | c1 | 33 | 0.8235 | 0.8235 | +0.0000 | 0 / 0 |
| 3b | F_np_uncovered | c2 | 72 | 0.2487 | 0.2487 | +0.0000 | 0 / 0 |
| 3b | G_tims_crosslib | c1 | 169 | 0.7533 | 0.8559 | +0.1026 | 34 / 2 |
| 3b | G_tims_crosslib | c2 | 169 | 0.7461 | 0.7118 | -0.0342 | 13 / 22 |
| 4b | C_np_crosslib | c1 | 148 | 0.9320 | 0.9449 | +0.0129 | 5 / 1 |
| 4b | C_np_crosslib | c2 | 159 | 0.6010 | 0.6318 | +0.0308 | 28 / 10 |
| 4b | D_np_single | c1 | 1 | 1.0000 | 1.0000 | +0.0000 | 0 / 0 |
| 4b | D_np_single | c2 | 200 | 0.2289 | 0.2355 | +0.0066 | 11 / 11 |
| 4b | E_np_negonly | c1 | 114 | 0.8502 | 0.8502 | +0.0000 | 0 / 0 |
| 4b | E_np_negonly | c2 | 200 | 0.4149 | 0.4149 | +0.0000 | 0 / 0 |
| 4b | F_np_uncovered | c1 | 26 | 0.7513 | 0.7513 | +0.0000 | 0 / 0 |
| 4b | F_np_uncovered | c2 | 81 | 0.2623 | 0.2623 | +0.0000 | 0 / 0 |
| 4b | G_tims_crosslib | c1 | 167 | 0.7794 | 0.8984 | +0.1190 | 42 / 1 |
| 4b | G_tims_crosslib | c2 | 167 | 0.6816 | 0.6788 | -0.0028 | 20 / 19 |

- primary NP C2 (blocks equal): +0.0067 [+0.0023, +0.0112]; blocks +0.0039 / +0.0094
- registered verdict: PASS (point > 0: True; lower bound > -0.01: True)

## 判定(2026-10-27 06:20 JST、一回だけ読んだ)
- **登録の判定 = 合格**: 主指標 NP C2(C/D/E/F 等重み、3b・4b の block 等重み)**+0.0067 [+0.0023, +0.0112]**(block +0.0039 / +0.0094)。C C2 が +0.017 / +0.031、D C2 −0.001 / +0.007、E/F は ranker を使わない経路なので 0。C C1 +0.001 / +0.013。G は C1 +0.103 / +0.119、C2 −0.034 / −0.003(stress)。
- 範囲(Codex 062): これは**公開 FPNet の表での再現性**の確認であり、本番(full_eval)への移行の確認ではない。Public 比較の前に、同じ dev2 での FPNet × ranker の交差比較(064、実行中)と full_eval での保護診断、0.379 から model だけを替えた pipeline の全出力 parity(`spark/jobs/spark_v8w_parity.sh`、開始)を行う。

## parity(2026-10-27 07:31)
- 0.379 の pipeline(b1_ana035、ef8f8f96)で ranker の model だけを rank_v8w(b8706359)に替え、パネル 250 の両 view で b1_parity: **PARITY PASS**(c2・c1 とも molecules 250、候補集合の一致 1.000、出力の一致 250/250)。
- kernel `hayatetaf/casmi26-b1-fpnet-v8w` v1(0.379 と同じ sources・引数、埋め込み model だけ v8w)は smoke 完了。
- Codex 062 の 3 条件(3b/4b 確認・交差比較・parity)を満たした → **0.379 → v8w だけの一変更として Public 比較の候補(10/28 の枠)**。読み(結果前に固定): ≥ +0.008 で暫定採用の資格、−0.015〜+0.008 は未確定(維持)、≤ −0.015 は不採用・点検(既定の境界)。
