# 090 development reading (amended registration)

tables missing (stress only): ['p2dev']

## Implementation check (fallback rows must satisfy R0 == R2 and R1 == R3)
- f1dev: fallback rows 331, max |R2-R0| 0.000000, max |R3-R1| 0.000000
- f2dev: fallback rows 318, max |R2-R0| 0.000000, max |R3-R1| 0.000000
- np053f1dev: fallback rows 137, max |R2-R0| 0.000000, max |R3-R1| 0.000000
- np053f2dev: fallback rows 154, max |R2-R0| 0.000000, max |R3-R1| 0.000000
- panel: fallback rows 68, max |R2-R0| 0.000000, max |R3-R1| 0.000000

## Registered variants vs R0

| variant | (i) f1/f2 NP strict C2 | fold1 / fold2 | G C1 (f1/f2) | 053 NP C1 | panel C1 clean | eligible |
|---|---|---|---|---|---|---|
| R1 ('rank_v7a_pc', 'pw0.15') | -0.0095 [-0.0183, -0.0006] | -0.0085 / -0.0104 | +0.0086 [-0.0014, +0.0195] (non-inferior) | -0.0153 [-0.0408, +0.0070] (undetermined) | -0.0240 [-0.0430, -0.0073] (undetermined) | no |
| R2 ('rank_v7a_np4', 'main') | -0.0077 [-0.0164, +0.0009] | -0.0007 / -0.0147 | -0.0410 [-0.0678, -0.0145] (harm) | -0.0083 [-0.0243, +0.0040] (undetermined) | -0.0063 [-0.0206, +0.0065] (undetermined) | no |
| R3 ('rank_v7a_np4', 'pw0.15') | -0.0226 [-0.0356, -0.0093] | -0.0189 / -0.0262 | -0.0506 [-0.0796, -0.0240] (harm) | -0.0237 [-0.0597, +0.0056] (undetermined) | -0.0500 [-0.0759, -0.0237] (harm) | no |
| R4 ('rank_v7a_np7', 'pw0.0') | -0.0573 [-0.0739, -0.0418] | -0.0510 / -0.0635 | -0.0549 [-0.0821, -0.0271] (harm) | -0.0654 [-0.1129, -0.0242] (harm) | -0.2255 [-0.2707, -0.1828] (harm) | no |

R4 - R3 on (i): -0.0347 [-0.0455, -0.0240] (folds -0.0321 / -0.0373)
**SELECTED (registered rule): none -> no normal candidate**

## 2x2 decomposition on (i)

- R1-R0 (fixed-rule prior 0.5 -> 0.15, original ranker): -0.0095 [-0.0185, -0.0007]
- R2-R0 (ranker without 4 popularity features): -0.0077 [-0.0167, +0.0007]
- R3-R1 (ranker change at prior 0.15): -0.0131 [-0.0229, -0.0037]
- R3-R2 (prior change with the new ranker): -0.0149 [-0.0241, -0.0055]
- interaction R3-R2-R1+R0: -0.0054 [-0.0112, +0.0001]

## Breakdowns of (i) (f1/f2 pooled blocks)

| variant | C | D | E | F | truth COCONUT | truth not COCONUT | GL path | fallback |
|---|---|---|---|---|---|---|---|---|
| R1 | -0.0052 | +0.0058 | -0.0196 | -0.0190 | -0.0320 | +0.0025 | +0.0003 | -0.0186 |
| R2 | -0.0303 | -0.0006 | +0.0000 | +0.0000 | +0.0006 | -0.0116 | -0.0159 | +0.0000 |
| R3 | -0.0459 | -0.0058 | -0.0196 | -0.0190 | -0.0376 | -0.0137 | -0.0268 | -0.0186 |
| R4 | -0.0988 | -0.0108 | -0.0733 | -0.0461 | -0.1208 | -0.0236 | -0.0568 | -0.0578 |

## Sensitivity: 053 dev C2 by the truth's prior rank (f1+f2 pooled) and re-weighted scenarios (reached molecules; not a condition)

| stratum | n | R0 | R1-R0 | R2-R0 | R3-R0 | R4-R0 |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 135 | 0.9369 | -0.0665 | -0.0190 | -0.1041 | -0.2244 |
| 2-3 | 121 | 0.7465 | -0.0412 | -0.0229 | -0.0665 | -0.1171 |
| 4-10 | 143 | 0.5408 | -0.0106 | +0.0058 | -0.0146 | -0.0923 |
| 11-25 | 63 | 0.5118 | +0.0085 | +0.0236 | +0.0096 | -0.0405 |
| 26+ | 89 | 0.4491 | -0.0075 | +0.0316 | +0.0181 | -0.0030 |
| unreached | 89 | 0.0000 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
- S1 9/18/30/43: R1-R0 -0.0169, R2-R0 +0.0081, R3-R0 -0.0194, R4-R0 -0.0769
- S2 15/20/30/35: R1-R0 -0.0217, R2-R0 +0.0042, R3-R0 -0.0282, R4-R0 -0.0913
- S3 5/15/30/50: R1-R0 -0.0131, R2-R0 +0.0115, R3-R0 -0.0123, R4-R0 -0.0657
- plain 053 C2 (all molecules): R1-R0 -0.0244, R2-R0 -0.0003, R3-R0 -0.0343, R4-R0 -0.0945
