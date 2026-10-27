# 080 確認の結果(2026-10-27 16:26 JST、053 NP_H/NP_N conf を一回だけ開封)

- 053 conf fold 1: rows 387, molecules 320, views {'c2': 320, 'c1': 67}
- 053 conf fold 2: rows 416, molecules 320, views {'c2': 320, 'c1': 96}
- **053 conf NP C2 (H, N equal; blocks equal): +0.0163 [+0.0086, +0.0252]** | blocks f3 / f4 +0.0201 / +0.0124
    f1 NP_H c2: n 200 main 0.5784 -> 0.5927 (+0.0144; up 14 / down 0)
    f1 NP_H c1: n 45 main 0.8763 -> 0.8578 (-0.0185; up 0 / down 4)
    f1 NP_N c2: n 60 main 0.5811 -> 0.6069 (+0.0258; up 8 / down 0)
    f1 NP_N c1: n 19 main 0.8947 -> 0.8947 (+0.0000; up 0 / down 0)
    f1 NP_X c2: n 60 main 0.7242 -> 0.7520 (+0.0278; up 4 / down 0)
    f1 NP_X c1: n 3 main 0.8333 -> 0.6667 (-0.1667; up 0 / down 1)
    f2 NP_H c2: n 200 main 0.6130 -> 0.6249 (+0.0119; up 18 / down 0)
    f2 NP_H c1: n 61 main 0.9084 -> 0.8985 (-0.0099; up 1 / down 4)
    f2 NP_N c2: n 60 main 0.6113 -> 0.6244 (+0.0130; up 6 / down 0)
    f2 NP_N c1: n 21 main 0.9286 -> 0.9048 (-0.0238; up 0 / down 1)
    f2 NP_X c2: n 60 main 0.5483 -> 0.5526 (+0.0043; up 7 / down 0)
    f2 NP_X c1: n 14 main 0.7113 -> 0.7173 (+0.0060; up 1 / down 0)
- reach-conditional (truth in the view shortlist) NP C2: +0.0185 [+0.0102, +0.0284]
- stress: 053 conf NP_H C1 (non-timsTOF, new identities): -0.0142 [-0.0333, -0.0016]
- REGISTERED VERDICT: PASS (point >= +0.005: True; lower > -0.01: True); C1 cost side = the dev values (panel C1 clean, G C1) restated in 080_result

## 判断
- **登録の判定 = 合格**: v7f + EA − v7f = 053 conf の NP C2 **+0.0163 [+0.0086, +0.0252]**(点推定 ≥ +0.005、下限 > −0.01)。開発(+0.0180)と同じ大きさで再現。費用側(C1)は開発の値(パネル C1 clean +0.0038 [−0.0028, +0.0122]、G C1 −0.0023 [−0.0075, +0.0007])の再掲で独立の確認ではない;053 conf の NP_H C1 は −0.0142 [−0.0333, −0.0016](非 timsTOF、stress)。
- parity(同じ PC、b1_v7fea、pipeline の forward 共有): v7f 単体 c2 / c1 = PASS、v7f + EA c2 = PASS、v7f + EA c1 = **全出力一致**(主出力・保険の順序付き top 25 が 250/250)で EA flag に既知の 1 件の例外(076 と同じ別表記集約の差、Codex 082b の扱い)。評価器の --alias_perview はその 1 件で pipeline と同じ値(C1: train でない・参照 0・lib 0)を再現(ALIASTEST)。
- 次: kernel casmi26-b1-fpnet-v7fea(b1_v7fea sha 58596c3f、rank_v7a、v7f と同じ引数 + --ea_w 1 --ea_theta 0.5)を push → smoke → 10/28 枠 4 で **v7f(0.390)→ v7f + EA** の一変更比較(読み: ≥ +0.008 暫定採用の候補 / −0.015〜+0.008 保留 / ≤ −0.015 点検)。
