# pre-registered decision table (fernew_eval; comparisons ['main: FE_new - M2x_fe=FE_new:M2x_fe', 'whole: FE_new - M2x=FE_new:M2x', 'submitted: M2x_fe - M2x=M2x_fe:M2x'])

Main output = blend21 (+ GL-cover fallback, registered evaluator). Paired molecule-level bootstrap (10,000, seed 0). eps = 0.02.

## main: FE_new - M2x_fe -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9308 | 0.9122 | +0.0186 | [+0.0044, +0.0342] | 18 / 4 |
| panel C1 clean | 202 | 0.9143 | 0.8971 | +0.0172 | [+0.0006, +0.0343] | 16 / 4 |
| panel C1 uncertain | 48 | 1.0000 | 0.9757 | +0.0243 | [+0.0000, +0.0625] | 2 / 0 |
| panel C2 all | 250 | 0.9447 | 0.9521 | -0.0074 | [-0.0176, +0.0015] | 3 / 7 |
| panel C2 clean | 202 | 0.9315 | 0.9407 | -0.0091 | [-0.0216, +0.0018] | 3 / 7 |
| panel C2 uncertain | 48 | 1.0000 | 1.0000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |

## main: FE_new - M2x_fe -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.9131 | 0.8989 | +0.0142 | [-0.0202, +0.0500] | 10 / 5 | point ok, lower < -eps (undetermined) |
| C_np_crosslib C2 | 100 | 0.5870 | 0.6013 | -0.0143 | [-0.0503, +0.0221] | 10 / 17 | point ok, lower < -eps (undetermined) |
| D_np_single C2 | 100 | 0.2397 | 0.2514 | -0.0117 | [-0.0322, +0.0066] | 9 / 8 | point ok, lower < -eps (undetermined) |
| E_np_negonly C1 | 59 | 0.5669 | 0.5669 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| E_np_negonly C2 | 100 | 0.2406 | 0.2406 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C1 | 38 | 0.6304 | 0.6304 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C2 | 100 | 0.2333 | 0.2333 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| G_tims_crosslib C1 | 100 | 0.6461 | 0.6035 | +0.0426 | [+0.0108, +0.0784] | 17 / 5 | PASS |
| G_tims_crosslib C2 | 100 | 0.6479 | 0.6495 | -0.0016 | [-0.0231, +0.0202] | 6 / 8 | point ok, lower < -eps (undetermined) |

## main: FE_new - M2x_fe -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|

## whole: FE_new - M2x -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9308 | 0.8819 | +0.0489 | [+0.0256, +0.0737] | 36 / 6 |
| panel C1 clean | 202 | 0.9143 | 0.8621 | +0.0522 | [+0.0251, +0.0808] | 33 / 6 |
| panel C1 uncertain | 48 | 1.0000 | 0.9653 | +0.0347 | [+0.0000, +0.0799] | 3 / 0 |
| panel C2 all | 250 | 0.9447 | 0.9045 | +0.0402 | [+0.0166, +0.0651] | 25 / 8 |
| panel C2 clean | 202 | 0.9315 | 0.8934 | +0.0382 | [+0.0116, +0.0666] | 21 / 8 |
| panel C2 uncertain | 48 | 1.0000 | 0.9514 | +0.0486 | [+0.0104, +0.1007] | 4 / 0 |

## whole: FE_new - M2x -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.9131 | 0.9117 | +0.0014 | [-0.0370, +0.0402] | 8 / 6 | point ok, lower < -eps (undetermined) |
| C_np_crosslib C2 | 100 | 0.5870 | 0.6120 | -0.0251 | [-0.0765, +0.0267] | 11 / 18 | FAIL |
| D_np_single C2 | 100 | 0.2397 | 0.2673 | -0.0275 | [-0.0646, +0.0053] | 8 / 10 | FAIL |
| E_np_negonly C1 | 59 | 0.5669 | 0.5608 | +0.0061 | [-0.0299, +0.0441] | 8 / 6 | point ok, lower < -eps (undetermined) |
| E_np_negonly C2 | 100 | 0.2406 | 0.2353 | +0.0053 | [-0.0232, +0.0337] | 21 / 16 | point ok, lower < -eps (undetermined) |
| F_np_uncovered C1 | 38 | 0.6304 | 0.5896 | +0.0407 | [-0.0137, +0.0985] | 8 / 5 | PASS |
| F_np_uncovered C2 | 100 | 0.2333 | 0.2287 | +0.0045 | [-0.0315, +0.0379] | 15 / 10 | point ok, lower < -eps (undetermined) |
| G_tims_crosslib C1 | 100 | 0.6461 | 0.5997 | +0.0465 | [+0.0021, +0.0921] | 26 / 8 | PASS |
| G_tims_crosslib C2 | 100 | 0.6479 | 0.6371 | +0.0108 | [-0.0223, +0.0440] | 15 / 9 | point ok, lower < -eps (undetermined) |

## whole: FE_new - M2x -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|

## submitted: M2x_fe - M2x -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9122 | 0.8819 | +0.0303 | [+0.0083, +0.0532] | 25 / 13 |
| panel C1 clean | 202 | 0.8971 | 0.8621 | +0.0350 | [+0.0098, +0.0628] | 23 / 12 |
| panel C1 uncertain | 48 | 0.9757 | 0.9653 | +0.0104 | [-0.0208, +0.0521] | 2 / 1 |
| panel C2 all | 250 | 0.9521 | 0.9045 | +0.0476 | [+0.0265, +0.0711] | 26 / 5 |
| panel C2 clean | 202 | 0.9407 | 0.8934 | +0.0473 | [+0.0238, +0.0735] | 22 / 5 |
| panel C2 uncertain | 48 | 1.0000 | 0.9514 | +0.0486 | [+0.0104, +0.1007] | 4 / 0 |

## submitted: M2x_fe - M2x -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| C_np_crosslib C1 | 95 | 0.8989 | 0.9117 | -0.0128 | [-0.0388, +0.0098] | 6 / 4 |
| C_np_crosslib C2 | 100 | 0.6013 | 0.6120 | -0.0108 | [-0.0463, +0.0265] | 13 / 13 |
| D_np_single C2 | 100 | 0.2514 | 0.2673 | -0.0159 | [-0.0484, +0.0134] | 8 / 8 |
| E_np_negonly C1 | 59 | 0.5669 | 0.5608 | +0.0061 | [-0.0303, +0.0446] | 8 / 6 |
| E_np_negonly C2 | 100 | 0.2406 | 0.2353 | +0.0053 | [-0.0236, +0.0337] | 21 / 16 |
| F_np_uncovered C1 | 38 | 0.6304 | 0.5896 | +0.0407 | [-0.0127, +0.0982] | 8 / 5 |
| F_np_uncovered C2 | 100 | 0.2333 | 0.2287 | +0.0045 | [-0.0312, +0.0380] | 15 / 10 |
| G_tims_crosslib C1 | 100 | 0.6035 | 0.5997 | +0.0039 | [-0.0325, +0.0408] | 18 / 11 |
| G_tims_crosslib C2 | 100 | 0.6495 | 0.6371 | +0.0124 | [-0.0175, +0.0429] | 14 / 6 |

## submitted: M2x_fe - M2x -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
