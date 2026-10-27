# 080 development: EA (ea0.5w1) on the v7f main vs on the v4b main (074)

| aggregate | EA on v7f (080) | EA on v4b (074) |
|---|---|---|
| primary 053 NP C2 (H,N) | +0.0180 [+0.0090, +0.0286] | +0.0295 [+0.0177, +0.0431] |
| panel C1 clean | +0.0038 [-0.0028, +0.0122] | -0.0005 [-0.0023, +0.0009] |
| G C1 (f1,f2) | -0.0023 [-0.0075, +0.0007] | -0.0021 [-0.0062, +0.0004] |
| f1/f2 NP C2 C-F | +0.0089 [+0.0054, +0.0130] | +0.0183 [+0.0128, +0.0246] |
| 053 NP C1 (stress) | -0.0166 [-0.0310, -0.0050] | -0.0035 [-0.0210, +0.0146] |
| dev2 NP C2 (stress) | +0.0089 [+0.0039, +0.0148] | +0.0096 [+0.0048, +0.0156] |

v7f main vs v4b main (mean RR over all rows, sanity of the v7f reproduction): np053f1dev 0.5955 vs 0.5658; np053f2dev 0.6438 vs 0.6187; panel 0.9350 vs 0.9353; f1dev 0.6018 vs 0.5868; f2dev 0.6128 vs 0.5950; p2dev 0.6178 vs 0.5953
GATE to the 053 conf: PASS (primary >= +0.005: True; panel C1 clean lower > -0.01: True; G C1 lower > -0.01: True; f1/f2 NP C2 not harm: True)
