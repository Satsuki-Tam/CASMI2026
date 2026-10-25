# pre-registered decision table (c1s_eval_1; comparisons ['main: C - B (fp_pos)=C:B', 'rows: B - A=B:A', 'whole: C - A=C:A'])

Main output = blend21 (+ GL-cover fallback, registered evaluator). Paired molecule-level bootstrap (10,000, seed 0). eps = 0.02.

## main: C - B (fp_pos) -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9201 | 0.9181 | +0.0020 | [-0.0084, +0.0124] | 8 / 6 |
| panel C1 clean | 202 | 0.9011 | 0.9012 | -0.0000 | [-0.0122, +0.0119] | 7 / 6 |
| panel C1 uncertain | 48 | 1.0000 | 0.9896 | +0.0104 | [+0.0000, +0.0312] | 1 / 0 |
| panel C2 all | 250 | 0.9429 | 0.9476 | -0.0047 | [-0.0109, -0.0003] | 1 / 5 |
| panel C2 clean | 202 | 0.9293 | 0.9351 | -0.0058 | [-0.0136, -0.0004] | 1 / 5 |
| panel C2 uncertain | 48 | 1.0000 | 1.0000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |

## main: C - B (fp_pos) -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.8542 | 0.8438 | +0.0104 | [-0.0036, +0.0299] | 3 / 2 | PASS |
| C_np_crosslib C2 | 100 | 0.5618 | 0.5728 | -0.0110 | [-0.0292, +0.0007] | 4 / 11 | point ok, lower < -eps (undetermined) |
| D_np_single C2 | 100 | 0.2674 | 0.2622 | +0.0052 | [-0.0106, +0.0238] | 5 / 3 | PASS |
| E_np_negonly C1 | 59 | 0.5603 | 0.5603 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| E_np_negonly C2 | 100 | 0.2499 | 0.2499 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C1 | 38 | 0.6100 | 0.6100 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C2 | 100 | 0.2318 | 0.2318 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| G_tims_crosslib C1 | 100 | 0.5939 | 0.5655 | +0.0283 | [-0.0009, +0.0602] | 19 / 6 | PASS |
| G_tims_crosslib C2 | 100 | 0.6326 | 0.6290 | +0.0036 | [-0.0037, +0.0152] | 4 / 3 | PASS |

## main: C - B (fp_pos) -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|

## rows: B - A -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9181 | 0.9208 | -0.0026 | [-0.0156, +0.0101] | 7 / 13 |
| panel C1 clean | 202 | 0.9012 | 0.9044 | -0.0033 | [-0.0177, +0.0112] | 6 / 12 |
| panel C1 uncertain | 48 | 0.9896 | 0.9896 | +0.0000 | [-0.0312, +0.0312] | 1 / 1 |
| panel C2 all | 250 | 0.9476 | 0.9402 | +0.0073 | [+0.0013, +0.0151] | 8 / 1 |
| panel C2 clean | 202 | 0.9351 | 0.9260 | +0.0091 | [+0.0015, +0.0184] | 8 / 1 |
| panel C2 uncertain | 48 | 1.0000 | 1.0000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |

## rows: B - A -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| C_np_crosslib C1 | 95 | 0.8438 | 0.9016 | -0.0579 | [-0.0948, -0.0246] | 2 / 16 |
| C_np_crosslib C2 | 100 | 0.5728 | 0.5734 | -0.0006 | [-0.0217, +0.0223] | 8 / 5 |
| D_np_single C2 | 100 | 0.2622 | 0.2623 | -0.0000 | [-0.0151, +0.0147] | 5 / 6 |
| E_np_negonly C1 | 59 | 0.5603 | 0.5603 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| E_np_negonly C2 | 100 | 0.2499 | 0.2499 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| F_np_uncovered C1 | 38 | 0.6100 | 0.6100 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| F_np_uncovered C2 | 100 | 0.2318 | 0.2318 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| G_tims_crosslib C1 | 100 | 0.5655 | 0.6485 | -0.0829 | [-0.1261, -0.0415] | 5 / 30 |
| G_tims_crosslib C2 | 100 | 0.6290 | 0.6398 | -0.0108 | [-0.0323, +0.0087] | 5 / 8 |

## rows: B - A -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|

## whole: C - A -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9201 | 0.9208 | -0.0007 | [-0.0097, +0.0086] | 5 / 10 |
| panel C1 clean | 202 | 0.9011 | 0.9044 | -0.0033 | [-0.0133, +0.0069] | 4 / 10 |
| panel C1 uncertain | 48 | 1.0000 | 0.9896 | +0.0104 | [+0.0000, +0.0312] | 1 / 0 |
| panel C2 all | 250 | 0.9429 | 0.9402 | +0.0026 | [-0.0036, +0.0097] | 6 / 3 |
| panel C2 clean | 202 | 0.9293 | 0.9260 | +0.0033 | [-0.0047, +0.0117] | 6 / 3 |
| panel C2 uncertain | 48 | 1.0000 | 1.0000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |

## whole: C - A -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.8542 | 0.9016 | -0.0474 | [-0.0889, -0.0096] | 4 / 15 | FAIL |
| C_np_crosslib C2 | 100 | 0.5618 | 0.5734 | -0.0116 | [-0.0277, +0.0003] | 5 / 10 | point ok, lower < -eps (undetermined) |
| D_np_single C2 | 100 | 0.2674 | 0.2623 | +0.0051 | [-0.0128, +0.0257] | 4 / 5 | PASS |
| E_np_negonly C1 | 59 | 0.5603 | 0.5603 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| E_np_negonly C2 | 100 | 0.2499 | 0.2499 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C1 | 38 | 0.6100 | 0.6100 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C2 | 100 | 0.2318 | 0.2318 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| G_tims_crosslib C1 | 100 | 0.5939 | 0.6485 | -0.0546 | [-0.0911, -0.0207] | 7 / 22 | FAIL |
| G_tims_crosslib C2 | 100 | 0.6326 | 0.6398 | -0.0072 | [-0.0310, +0.0153] | 6 / 9 | point ok, lower < -eps (undetermined) |

## whole: C - A -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
