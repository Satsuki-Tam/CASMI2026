# 080 開発の結果(2026-10-27 15:01 JST、gen_eval2pv、rank_v7a)

| aggregate | EA on v7f (080) | EA on v4b (074) |
|---|---|---|
| primary 053 NP C2 (H,N) | +0.0180 [+0.0090, +0.0286] | +0.0295 [+0.0180, +0.0426] |
| panel C1 clean | +0.0038 [-0.0028, +0.0122] | -0.0005 [-0.0022, +0.0008] |
| G C1 (f1,f2) | -0.0023 [-0.0075, +0.0007] | -0.0021 [-0.0063, +0.0004] |
| f1/f2 NP C2 C-F | +0.0089 [+0.0054, +0.0130] | +0.0183 [+0.0129, +0.0244] |
| 053 NP C1 (stress) | -0.0166 [-0.0310, -0.0050] | -0.0035 [-0.0219, +0.0135] |
| dev2 NP C2 (stress) | +nan [+nan, +nan] | +0.0096 [+0.0051, +0.0153] |

v7f main vs v4b main (mean RR over all rows, sanity of the v7f reproduction): np053f1dev 0.5955 vs 0.5658; np053f2dev 0.6438 vs 0.6187; panel 0.9350 vs 0.9353; f1dev 0.6018 vs 0.5868; f2dev 0.6128 vs 0.5950
GATE to the 053 conf: PASS (primary >= +0.005: True; panel C1 clean lower > -0.01: True; G C1 lower > -0.01: True; f1/f2 NP C2 not harm: True)

## 読み
- **関門 = 合格**(主指標 +0.0180 ≥ +0.005、パネル C1 clean と G C1 の下限 > −0.01、f1/f2 NP C2 に害なし)。
- 交互作用: v7f の上の EA は主指標で +0.018(v4b の上の +0.030 より小さい)= v7f の fallback 改善(MetFrag-lite・analog)と EA の効果が一部重なる。非 timsTOF の NP C1(stress)の費用は v7f の上で −0.017(v4b の上 −0.004)と大きい(fallback の得点の尺度が違うため w=1 の相対的な強さが変わる可能性)。
- v7f の主出力の再現の目安: NP dev で v4b の主出力より +0.025〜+0.030、f1/f2 で +0.015〜+0.018、パネルは同等。厳密な一致は parity(pc_parity080.sh の noea)で、053 conf を開く前に確認する(Codex 081)。dev2(stress)は 15:28 に完了(上の表の行)。

## 053 conf を開く前の確認(15:51、Codex 081)
- v7f 単体の parity(c2、同じ PC の評価表、pipeline の forward を共有): **PARITY PASS**(候補集合・fp・主出力と保険の順序付き top 25 が 250/250)。
- 確認に使う評価器 gen_eval2pv の主出力と本番 pipeline の出力の照合(c2、pipeline の GL を共有): **v7f 単体の RR 250/250 一致、v7f + EA の RR 250/250 一致**(最初の照合は評価表に GL が無く全分子が fallback 経路で計算されていた = 手順の誤りで 207/250、GL を揃えて解消)。
- c1 の parity は pipeline の実行中(kernel の push 前に確認する)。→ 053 NP_H/NP_N conf を一回だけ開く。
