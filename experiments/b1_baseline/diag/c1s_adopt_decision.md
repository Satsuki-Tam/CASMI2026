# pre-registered decision table (c1s_eval_2; comparisons ['main: FE_C - M2x_fe=FE_C:M2x_fe', 'whole: FE_C - M2x=FE_C:M2x', 'mainB: FE_B - M2x_fe=FE_B:M2x_fe', 'wholeB: FE_B - M2x=FE_B:M2x'])

Main output = blend21 (+ GL-cover fallback, registered evaluator). Paired molecule-level bootstrap (10,000, seed 0). eps = 0.02.

## main: FE_C - M2x_fe -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9297 | 0.9122 | +0.0175 | [+0.0011, +0.0346] | 17 / 5 |
| panel C1 clean | 202 | 0.9130 | 0.8971 | +0.0158 | [-0.0026, +0.0356] | 15 / 5 |
| panel C1 uncertain | 48 | 1.0000 | 0.9757 | +0.0243 | [+0.0000, +0.0625] | 2 / 0 |
| panel C2 all | 250 | 0.9516 | 0.9521 | -0.0004 | [-0.0081, +0.0074] | 4 / 5 |
| panel C2 clean | 202 | 0.9401 | 0.9407 | -0.0005 | [-0.0100, +0.0093] | 4 / 5 |
| panel C2 uncertain | 48 | 1.0000 | 1.0000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |

## main: FE_C - M2x_fe -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.8578 | 0.8989 | -0.0411 | [-0.0895, +0.0066] | 6 / 14 | FAIL |
| C_np_crosslib C2 | 100 | 0.5723 | 0.6013 | -0.0290 | [-0.0614, +0.0003] | 7 / 18 | FAIL |
| D_np_single C2 | 100 | 0.2541 | 0.2514 | +0.0027 | [-0.0168, +0.0230] | 9 / 6 | PASS |
| E_np_negonly C1 | 59 | 0.5669 | 0.5669 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| E_np_negonly C2 | 100 | 0.2406 | 0.2406 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C1 | 38 | 0.6304 | 0.6304 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C2 | 100 | 0.2333 | 0.2333 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| G_tims_crosslib C1 | 100 | 0.6042 | 0.6035 | +0.0007 | [-0.0374, +0.0386] | 12 / 12 | point ok, lower < -eps (undetermined) |
| G_tims_crosslib C2 | 100 | 0.6265 | 0.6495 | -0.0230 | [-0.0438, -0.0055] | 6 / 10 | FAIL |

## main: FE_C - M2x_fe -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|

## whole: FE_C - M2x -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9297 | 0.8819 | +0.0478 | [+0.0245, +0.0726] | 34 / 8 |
| panel C1 clean | 202 | 0.9130 | 0.8621 | +0.0509 | [+0.0236, +0.0794] | 31 / 8 |
| panel C1 uncertain | 48 | 1.0000 | 0.9653 | +0.0347 | [+0.0000, +0.0799] | 3 / 0 |
| panel C2 all | 250 | 0.9516 | 0.9045 | +0.0471 | [+0.0261, +0.0698] | 25 / 4 |
| panel C2 clean | 202 | 0.9401 | 0.8934 | +0.0468 | [+0.0232, +0.0733] | 21 / 4 |
| panel C2 uncertain | 48 | 1.0000 | 0.9514 | +0.0486 | [+0.0104, +0.1007] | 4 / 0 |

## whole: FE_C - M2x -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.8578 | 0.9117 | -0.0539 | [-0.1065, -0.0025] | 6 / 15 | FAIL |
| C_np_crosslib C2 | 100 | 0.5723 | 0.6120 | -0.0398 | [-0.0892, +0.0100] | 12 / 21 | FAIL |
| D_np_single C2 | 100 | 0.2541 | 0.2673 | -0.0131 | [-0.0480, +0.0179] | 9 / 8 | point ok, lower < -eps (undetermined) |
| E_np_negonly C1 | 59 | 0.5669 | 0.5608 | +0.0061 | [-0.0299, +0.0441] | 8 / 6 | point ok, lower < -eps (undetermined) |
| E_np_negonly C2 | 100 | 0.2406 | 0.2353 | +0.0053 | [-0.0232, +0.0337] | 21 / 16 | point ok, lower < -eps (undetermined) |
| F_np_uncovered C1 | 38 | 0.6304 | 0.5896 | +0.0407 | [-0.0137, +0.0985] | 8 / 5 | PASS |
| F_np_uncovered C2 | 100 | 0.2333 | 0.2287 | +0.0045 | [-0.0315, +0.0379] | 15 / 10 | point ok, lower < -eps (undetermined) |
| G_tims_crosslib C1 | 100 | 0.6042 | 0.5997 | +0.0046 | [-0.0346, +0.0437] | 18 / 15 | point ok, lower < -eps (undetermined) |
| G_tims_crosslib C2 | 100 | 0.6265 | 0.6371 | -0.0106 | [-0.0477, +0.0248] | 15 / 12 | point ok, lower < -eps (undetermined) |

## whole: FE_C - M2x -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|

## mainB: FE_B - M2x_fe -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9301 | 0.9122 | +0.0179 | [+0.0023, +0.0341] | 15 / 4 |
| panel C1 clean | 202 | 0.9135 | 0.8971 | +0.0164 | [-0.0010, +0.0347] | 13 / 4 |
| panel C1 uncertain | 48 | 1.0000 | 0.9757 | +0.0243 | [+0.0000, +0.0625] | 2 / 0 |
| panel C2 all | 250 | 0.9520 | 0.9521 | -0.0000 | [-0.0076, +0.0078] | 4 / 5 |
| panel C2 clean | 202 | 0.9406 | 0.9407 | -0.0000 | [-0.0096, +0.0096] | 4 / 5 |
| panel C2 uncertain | 48 | 1.0000 | 1.0000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |

## mainB: FE_B - M2x_fe -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.8880 | 0.8989 | -0.0109 | [-0.0604, +0.0368] | 8 / 12 | point ok, lower < -eps (undetermined) |
| C_np_crosslib C2 | 100 | 0.5780 | 0.6013 | -0.0233 | [-0.0550, +0.0050] | 8 / 16 | FAIL |
| D_np_single C2 | 100 | 0.2459 | 0.2514 | -0.0055 | [-0.0258, +0.0143] | 9 / 6 | point ok, lower < -eps (undetermined) |
| E_np_negonly C1 | 59 | 0.5669 | 0.5669 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| E_np_negonly C2 | 100 | 0.2406 | 0.2406 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C1 | 38 | 0.6304 | 0.6304 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C2 | 100 | 0.2333 | 0.2333 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| G_tims_crosslib C1 | 100 | 0.5760 | 0.6035 | -0.0275 | [-0.0653, +0.0095] | 11 / 22 | FAIL |
| G_tims_crosslib C2 | 100 | 0.6386 | 0.6495 | -0.0110 | [-0.0318, +0.0081] | 6 / 9 | point ok, lower < -eps (undetermined) |

## mainB: FE_B - M2x_fe -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|

## wholeB: FE_B - M2x -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9301 | 0.8819 | +0.0482 | [+0.0245, +0.0727] | 33 / 8 |
| panel C1 clean | 202 | 0.9135 | 0.8621 | +0.0514 | [+0.0239, +0.0804] | 30 / 8 |
| panel C1 uncertain | 48 | 1.0000 | 0.9653 | +0.0347 | [+0.0000, +0.0799] | 3 / 0 |
| panel C2 all | 250 | 0.9520 | 0.9045 | +0.0475 | [+0.0259, +0.0713] | 26 / 4 |
| panel C2 clean | 202 | 0.9406 | 0.8934 | +0.0473 | [+0.0231, +0.0746] | 22 / 4 |
| panel C2 uncertain | 48 | 1.0000 | 0.9514 | +0.0486 | [+0.0104, +0.1007] | 4 / 0 |

## wholeB: FE_B - M2x -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.8880 | 0.9117 | -0.0237 | [-0.0781, +0.0295] | 7 / 12 | FAIL |
| C_np_crosslib C2 | 100 | 0.5780 | 0.6120 | -0.0341 | [-0.0844, +0.0158] | 11 / 19 | FAIL |
| D_np_single C2 | 100 | 0.2459 | 0.2673 | -0.0213 | [-0.0590, +0.0124] | 9 / 9 | FAIL |
| E_np_negonly C1 | 59 | 0.5669 | 0.5608 | +0.0061 | [-0.0300, +0.0439] | 8 / 6 | point ok, lower < -eps (undetermined) |
| E_np_negonly C2 | 100 | 0.2406 | 0.2353 | +0.0053 | [-0.0222, +0.0341] | 21 / 16 | point ok, lower < -eps (undetermined) |
| F_np_uncovered C1 | 38 | 0.6304 | 0.5896 | +0.0407 | [-0.0135, +0.0975] | 8 / 5 | PASS |
| F_np_uncovered C2 | 100 | 0.2333 | 0.2287 | +0.0045 | [-0.0310, +0.0381] | 15 / 10 | point ok, lower < -eps (undetermined) |
| G_tims_crosslib C1 | 100 | 0.5760 | 0.5997 | -0.0237 | [-0.0637, +0.0172] | 17 / 24 | FAIL |
| G_tims_crosslib C2 | 100 | 0.6386 | 0.6371 | +0.0014 | [-0.0308, +0.0329] | 15 / 10 | point ok, lower < -eps (undetermined) |

## wholeB: FE_B - M2x -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
