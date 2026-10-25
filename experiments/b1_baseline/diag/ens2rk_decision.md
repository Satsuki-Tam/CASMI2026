# pre-registered decision table (ens2rk_eval; comparisons ['main: ENS2_new - M2x_fe=ENS2_new:M2x_fe', 'whole: ENS2_new - M2x=ENS2_new:M2x'])

Main output = blend21 (+ GL-cover fallback, registered evaluator). Paired molecule-level bootstrap (10,000, seed 0). eps = 0.02.

## main: ENS2_new - M2x_fe -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9248 | 0.9122 | +0.0126 | [-0.0009, +0.0272] | 19 / 6 |
| panel C1 clean | 202 | 0.9095 | 0.8971 | +0.0123 | [-0.0040, +0.0293] | 17 / 6 |
| panel C1 uncertain | 48 | 0.9896 | 0.9757 | +0.0139 | [+0.0000, +0.0382] | 2 / 0 |
| panel C2 all | 250 | 0.9431 | 0.9521 | -0.0089 | [-0.0207, +0.0020] | 6 / 9 |
| panel C2 clean | 202 | 0.9321 | 0.9407 | -0.0086 | [-0.0221, +0.0045] | 6 / 8 |
| panel C2 uncertain | 48 | 0.9896 | 1.0000 | -0.0104 | [-0.0312, +0.0000] | 0 / 1 |

## main: ENS2_new - M2x_fe -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.9192 | 0.8989 | +0.0203 | [-0.0076, +0.0496] | 9 / 2 | PASS |
| C_np_crosslib C2 | 100 | 0.5874 | 0.6013 | -0.0138 | [-0.0431, +0.0140] | 10 / 14 | point ok, lower < -eps (undetermined) |
| D_np_single C2 | 100 | 0.2507 | 0.2514 | -0.0007 | [-0.0275, +0.0277] | 8 / 8 | point ok, lower < -eps (undetermined) |
| E_np_negonly C1 | 59 | 0.5751 | 0.5669 | +0.0082 | [-0.0031, +0.0277] | 8 / 4 | PASS |
| E_np_negonly C2 | 100 | 0.2648 | 0.2406 | +0.0242 | [+0.0066, +0.0455] | 23 / 6 | PASS |
| F_np_uncovered C1 | 38 | 0.6143 | 0.6304 | -0.0161 | [-0.0479, +0.0028] | 5 / 4 | point ok, lower < -eps (undetermined) |
| F_np_uncovered C2 | 100 | 0.2314 | 0.2333 | -0.0019 | [-0.0211, +0.0157] | 13 / 6 | point ok, lower < -eps (undetermined) |
| G_tims_crosslib C1 | 100 | 0.6334 | 0.6035 | +0.0299 | [-0.0081, +0.0703] | 17 / 10 | PASS |
| G_tims_crosslib C2 | 100 | 0.6479 | 0.6495 | -0.0016 | [-0.0264, +0.0224] | 13 / 6 | point ok, lower < -eps (undetermined) |

## main: ENS2_new - M2x_fe -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|

## whole: ENS2_new - M2x -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9248 | 0.8819 | +0.0429 | [+0.0217, +0.0662] | 31 / 4 |
| panel C1 clean | 202 | 0.9095 | 0.8621 | +0.0474 | [+0.0223, +0.0741] | 28 / 4 |
| panel C1 uncertain | 48 | 0.9896 | 0.9653 | +0.0243 | [+0.0000, +0.0556] | 3 / 0 |
| panel C2 all | 250 | 0.9431 | 0.9045 | +0.0386 | [+0.0157, +0.0635] | 23 / 9 |
| panel C2 clean | 202 | 0.9321 | 0.8934 | +0.0387 | [+0.0122, +0.0667] | 20 / 9 |
| panel C2 uncertain | 48 | 0.9896 | 0.9514 | +0.0382 | [+0.0000, +0.0868] | 3 / 0 |

## whole: ENS2_new - M2x -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.9192 | 0.9117 | +0.0075 | [-0.0257, +0.0400] | 8 / 5 | point ok, lower < -eps (undetermined) |
| C_np_crosslib C2 | 100 | 0.5874 | 0.6120 | -0.0246 | [-0.0664, +0.0171] | 14 / 15 | FAIL |
| D_np_single C2 | 100 | 0.2507 | 0.2673 | -0.0166 | [-0.0475, +0.0116] | 7 / 10 | point ok, lower < -eps (undetermined) |
| E_np_negonly C1 | 59 | 0.5751 | 0.5608 | +0.0143 | [-0.0163, +0.0487] | 7 / 4 | PASS |
| E_np_negonly C2 | 100 | 0.2648 | 0.2353 | +0.0295 | [+0.0044, +0.0591] | 22 / 9 | PASS |
| F_np_uncovered C1 | 38 | 0.6143 | 0.5896 | +0.0247 | [-0.0340, +0.0815] | 6 / 4 | point ok, lower < -eps (undetermined) |
| F_np_uncovered C2 | 100 | 0.2314 | 0.2287 | +0.0027 | [-0.0264, +0.0302] | 15 / 8 | point ok, lower < -eps (undetermined) |
| G_tims_crosslib C1 | 100 | 0.6334 | 0.5997 | +0.0337 | [-0.0071, +0.0767] | 23 / 10 | PASS |
| G_tims_crosslib C2 | 100 | 0.6479 | 0.6371 | +0.0108 | [-0.0206, +0.0422] | 18 / 6 | point ok, lower < -eps (undetermined) |

## whole: ENS2_new - M2x -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
