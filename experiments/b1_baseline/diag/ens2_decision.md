# pre-registered decision table (ens2_eval; comparisons ['main: ENS2 - M2x_fe=ENS2:M2x_fe', 'whole: ENS2 - M2x=ENS2:M2x'])

Main output = blend21 (+ GL-cover fallback, registered evaluator). Paired molecule-level bootstrap (10,000, seed 0). eps = 0.02.

## main: ENS2 - M2x_fe -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9077 | 0.9122 | -0.0045 | [-0.0144, +0.0051] | 8 / 8 |
| panel C1 clean | 202 | 0.8916 | 0.8971 | -0.0056 | [-0.0181, +0.0060] | 8 / 8 |
| panel C1 uncertain | 48 | 0.9757 | 0.9757 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| panel C2 all | 250 | 0.9483 | 0.9521 | -0.0038 | [-0.0121, +0.0034] | 4 / 5 |
| panel C2 clean | 202 | 0.9360 | 0.9407 | -0.0047 | [-0.0152, +0.0043] | 4 / 5 |
| panel C2 uncertain | 48 | 1.0000 | 1.0000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |

## main: ENS2 - M2x_fe -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.9169 | 0.8989 | +0.0180 | [+0.0001, +0.0410] | 6 / 2 | PASS |
| C_np_crosslib C2 | 100 | 0.6075 | 0.6013 | +0.0062 | [-0.0159, +0.0310] | 10 / 10 | PASS |
| D_np_single C2 | 100 | 0.2728 | 0.2514 | +0.0215 | [+0.0002, +0.0482] | 9 / 4 | PASS |
| E_np_negonly C1 | 59 | 0.5751 | 0.5669 | +0.0082 | [-0.0031, +0.0277] | 8 / 4 | PASS |
| E_np_negonly C2 | 100 | 0.2648 | 0.2406 | +0.0242 | [+0.0066, +0.0455] | 23 / 6 | PASS |
| F_np_uncovered C1 | 38 | 0.6143 | 0.6304 | -0.0161 | [-0.0479, +0.0028] | 5 / 4 | point ok, lower < -eps (undetermined) |
| F_np_uncovered C2 | 100 | 0.2314 | 0.2333 | -0.0019 | [-0.0211, +0.0157] | 13 / 6 | point ok, lower < -eps (undetermined) |
| G_tims_crosslib C1 | 100 | 0.5596 | 0.6035 | -0.0439 | [-0.0732, -0.0183] | 7 / 19 | FAIL |
| G_tims_crosslib C2 | 100 | 0.6574 | 0.6495 | +0.0079 | [-0.0184, +0.0356] | 11 / 6 | PASS |

## main: ENS2 - M2x_fe -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|

## whole: ENS2 - M2x -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9077 | 0.8819 | +0.0258 | [+0.0040, +0.0488] | 27 / 11 |
| panel C1 clean | 202 | 0.8916 | 0.8621 | +0.0295 | [+0.0035, +0.0562] | 25 / 10 |
| panel C1 uncertain | 48 | 0.9757 | 0.9653 | +0.0104 | [-0.0208, +0.0417] | 2 / 1 |
| panel C2 all | 250 | 0.9483 | 0.9045 | +0.0438 | [+0.0221, +0.0675] | 25 / 6 |
| panel C2 clean | 202 | 0.9360 | 0.8934 | +0.0427 | [+0.0180, +0.0695] | 21 / 6 |
| panel C2 uncertain | 48 | 1.0000 | 0.9514 | +0.0486 | [+0.0104, +0.1007] | 4 / 0 |

## whole: ENS2 - M2x -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.9169 | 0.9117 | +0.0052 | [-0.0135, +0.0249] | 6 / 4 | PASS |
| C_np_crosslib C2 | 100 | 0.6075 | 0.6120 | -0.0046 | [-0.0336, +0.0271] | 11 / 13 | point ok, lower < -eps (undetermined) |
| D_np_single C2 | 100 | 0.2728 | 0.2673 | +0.0056 | [-0.0120, +0.0249] | 8 / 5 | PASS |
| E_np_negonly C1 | 59 | 0.5751 | 0.5608 | +0.0143 | [-0.0163, +0.0487] | 7 / 4 | PASS |
| E_np_negonly C2 | 100 | 0.2648 | 0.2353 | +0.0295 | [+0.0044, +0.0591] | 22 / 9 | PASS |
| F_np_uncovered C1 | 38 | 0.6143 | 0.5896 | +0.0247 | [-0.0340, +0.0815] | 6 / 4 | point ok, lower < -eps (undetermined) |
| F_np_uncovered C2 | 100 | 0.2314 | 0.2287 | +0.0027 | [-0.0264, +0.0302] | 15 / 8 | point ok, lower < -eps (undetermined) |
| G_tims_crosslib C1 | 100 | 0.5596 | 0.5997 | -0.0400 | [-0.0759, -0.0067] | 14 / 20 | FAIL |
| G_tims_crosslib C2 | 100 | 0.6574 | 0.6371 | +0.0203 | [+0.0009, +0.0425] | 15 / 4 | PASS |

## whole: ENS2 - M2x -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
