# 050 confirmation (arm a, 053 conf NP_X, read once)

| fold | view | n | base | arm a | delta [95%] | up / down |
|---|---|---:|---:|---:|---|---|
| 1 | c1 | 3 | 0.8333 | 0.6667 | -0.1667 [-0.5000, +0.0000] | 0 / 1 |
| 1 | c2 | 60 | 0.5622 | 0.5850 | +0.0228 [-0.0619, +0.1069] | 21 / 18 |
| 2 | c1 | 14 | 0.6798 | 0.7908 | +0.1110 [-0.0577, +0.2896] | 4 / 1 |
| 2 | c2 | 60 | 0.4745 | 0.5411 | +0.0666 [-0.0041, +0.1397] | 26 / 11 |

- primary (C2, blocks equal): +0.0447 [-0.0091, +0.1003]
- C1 per fold: f1 n 3 -0.1667, f2 n 14 +0.1110
- registered verdict: FAIL (primary > 0: True; C1 >= -0.01 per fold: False)
- 049b reading of the primary aggregate (eps 0.01): non-inferior; C1 n is tiny -> protection evidence comes from the dev F C1 and the panel diagnostic

## 判定と補助の結果(2026-10-27 05:04 JST)
- **登録の判定 = 不合格**: 主指標(C2、fold 等重み)+0.0447 [−0.0091, +0.1003] は正だが、登録の保護「C1 ≥ −0.01 を各 fold」が fold-1 で不成立(C1 usable が **3 分子**しかなく、1 分子の 1 位 → 2 位で −0.167)。確認前の監査でこの点は「実質測れない」と記録していたが、規則は変えていないので不合格のまま扱う(049b の三状態では主指標は非劣性、C1 は未確定)。
- 補助(開発側):
  - dev2(full_eval の表、identity 未見)の F: C2 **−0.006**(15 改善 / 14 悪化)、C1 +0.100。
  - パネル(既見、非対応 34 分子): C1 −0.0045(3 分子が全て下降)、C2 −0.0013。
  - fold-safe の公開 FPNet の集合(f1/f2 dev と conf)では一貫して正(dev +0.022 / +0.067、conf +0.023 / +0.067)だが、**本番と同じ full_eval の表(dev2)ではほぼ 0〜負**、既見のパネルでも僅かに負。
- 解釈(仮説): proxy の GL は FPNet が弱いとき(fold-safe の公開モデル)に効き、full_eval のように FP が強い・既見のときは雑音になり得る。本番では隠しのクラス 2 は full_eval にとっても未見だが、full_eval は公開 fold モデルより学習データが多い → 効果は小さい側と見込む。
- 扱い: **今日の提出の入れ替え候補にしない**。kernel(casmi26-b1-fpnet-pxa v1)は smoke 用に push 済みだが提出しない。parity の job は開始前に停止。再検討するなら「full_eval の表での proxy の効果」を主対象に新しく登録する(C1 の保護は既見のパネルと十分な n の集合で)。
