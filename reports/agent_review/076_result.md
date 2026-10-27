# 076 確認の結果(2026-10-27 12:45 JST、073 を一回だけ開封)

- 073 fold 3: rows 429, molecules 366, views {'c2': 366, 'c1': 63}
- 073 fold 4: rows 455, molecules 381, views {'c2': 381, 'c1': 74}
- **073 NP C2 (H, N equal; blocks equal): +0.0246 [+0.0169, +0.0333]** | blocks f3 / f4 +0.0238 / +0.0254
    f3 NP_H c2: n 214 main 0.6253 -> 0.6342 (+0.0089; up 14 / down 0)
    f3 NP_H c1: n 36 main 0.9167 -> 0.8889 (-0.0278; up 0 / down 2)
    f3 NP_N c2: n 139 main 0.5505 -> 0.5891 (+0.0386; up 33 / down 0)
    f3 NP_N c1: n 27 main 0.8627 -> 0.8586 (-0.0040; up 1 / down 2)
    f3 NP_X c2: n 13 main 0.3821 -> 0.3883 (+0.0062; up 5 / down 0)
    f4 NP_H c2: n 268 main 0.5757 -> 0.5836 (+0.0079; up 15 / down 0)
    f4 NP_H c1: n 41 main 0.8844 -> 0.8823 (-0.0020; up 0 / down 1)
    f4 NP_N c2: n 110 main 0.5660 -> 0.6089 (+0.0429; up 22 / down 0)
    f4 NP_N c1: n 33 main 0.9038 -> 0.8712 (-0.0326; up 0 / down 4)
    f4 NP_X c2: n 3 main 0.6905 -> 0.6970 (+0.0065; up 1 / down 0)
- reach-conditional (truth in the view shortlist) NP C2: +0.0265 [+0.0183, +0.0354]
- **f3b/f4b G C1 (2 blocks equal): -0.0020 [-0.0069, +0.0028]** | blocks -0.0030 / -0.0011 | n [169, 167] | worsened [6, 2] improved [4, 1]
- f3b/f4b G C2 (C2 is non-worsening by construction): +0.0015
- stress: 073 NP_H C1 (non-timsTOF, new identities): -0.0149 [-0.0357, +0.0000]
- REGISTERED VERDICT: PASS (073 point >= +0.005: True; 073 lower > -0.01: True; G C1 lower > -0.01: True)

## 判断
- **登録の判定 = 合格**: 073 の NP C2 +0.0246 [+0.0169, +0.0333](点推定 ≥ +0.005、下限 > −0.01)、費用側 f3b/f4b の G C1 −0.0020 [−0.0069, +0.0028](下限 > −0.01)。開発(074)の +0.0295 とほぼ同じ大きさで再現。
- 費用は非 timsTOF の NP C1 に出る(073 NP_H C1 −0.015、NP_N C1 fold 4 −0.033)。隠しの既見 C1(timsTOF)ではパネル C1 clean −0.0005・G C1 −0.002 と小さい。「本番全体の既見 C1 費用を独立に確認した」とは書かない(Codex 076)。
- 次: parity(PC、パネル 250 の両 view、EA flag の全候補一致)→ kernel casmi26-b1-fpnet-ea05w1 の push と smoke → 10/28 に 0.379 → EA の一変更比較(読み: ≥ +0.008 暫定採用の候補 / −0.015〜+0.008 保留 / ≤ −0.015 点検)。
- v7f(0.390)が作業基準になったので、v7f + EA は別候補として開発の交互作用確認から(076 の確認は引き継がない)。

## parity(14:25)
- Spark で作った評価表との照合(076): 正解の RR は両 view・主出力・保険とも 250/250 一致、EA flag は c2 で 1,715 件全一致。ただし FPNet の GPU 数値差(平均 0.13)で候補集合の境界と正解以外の並びがずれ、順序付き top 25 は 0.37〜0.72 → 環境差の診断。
- **同じ PC で評価表(run_panel_fe_pc)を作り直した照合(076b)**: **c2 = PARITY PASS**(候補集合 1.000、fp 差 0、主出力・保険の順序付き top 25 が 250/250)。**c1 は出力が全て一致**(主出力・保険の top-1・RR・集合・順序付き top 25 が 250/250)だが、全共有候補の EA flag 1,713 件のうち **1 件だけ不一致**で FAIL 判定: SQFSKOYWJBQGKQ の候補 BEBLLQPTMVOKAX(正解とは別の identity group 196705、raw の別表記を 3 つ持つ key)を、評価表は train 構造・参照 24 件・lib 0.376、pipeline の C1 評価モードは参照 0 件・lib 0 と扱う。EA の実装ではなく、評価モードの C1 で別表記 key の参照の扱いが二つの経路で違う既存の差(この候補の flag の違いは順位を一つも変えていない;本番は mask が無いので起きない)。
- kernel casmi26-b1-fpnet-ea05w1 v1 を push(smoke 中)。この 1 件の扱いは Codex 082 に確認する。
- **Codex 082 / 082b(14:58 記録)**: parity は「**C2 PASS、C1 は全出力一致(順序付き top 25 まで 250/250)、候補属性・EA flag に既知の 1 件の例外**」として記録(1 件を除外して PASS にする処理は入れない)。原因は評価器が C1/C2 の shortlist の和集合で別表記を集約し、pipeline が view ごとに集約する差(本番は shortlist が一つ)。頻度はパネルの両 view 共通の非正解候補 55,861 件中 1 件。**10/28 の 0.379 + EA の一変更比較は進める**。評価器の view 別集約への修正と、パネル・073・G への影響監査は別作業(合否を変える規模の影響が提出前に分かれば見送る)。kernel casmi26-b1-fpnet-ea05w1 v1 は smoke COMPLETE。
