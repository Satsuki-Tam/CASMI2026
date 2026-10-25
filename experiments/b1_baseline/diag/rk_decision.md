# full_rk ranker pair: pre-registered decision table (023_decision section 4)

Main output = blend21 (+ GL-cover fallback, registered evaluator). Paired molecule-level bootstrap (10,000, seed 0). eps = 0.02.

## main: RK_new - RK_old -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9208 | 0.9128 | +0.0080 | [-0.0052, +0.0217] | 13 / 7 |
| panel C1 clean | 202 | 0.9044 | 0.8970 | +0.0074 | [-0.0084, +0.0235] | 12 / 7 |
| panel C1 uncertain | 48 | 0.9896 | 0.9792 | +0.0104 | [+0.0000, +0.0312] | 1 / 0 |
| panel C2 all | 250 | 0.9402 | 0.9492 | -0.0090 | [-0.0178, -0.0022] | 1 / 10 |
| panel C2 clean | 202 | 0.9260 | 0.9371 | -0.0111 | [-0.0218, -0.0026] | 1 / 10 |
| panel C2 uncertain | 48 | 1.0000 | 1.0000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |

## main: RK_new - RK_old -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse | protection |
|---|---:|---:|---:|---:|---|---|---|
| C_np_crosslib C1 | 95 | 0.9016 | 0.9027 | -0.0011 | [-0.0277, +0.0239] | 6 / 6 | point ok, lower < -eps (undetermined) |
| C_np_crosslib C2 | 100 | 0.5734 | 0.5921 | -0.0186 | [-0.0521, +0.0133] | 8 / 17 | point ok, lower < -eps (undetermined) |
| D_np_single C2 | 100 | 0.2623 | 0.2688 | -0.0065 | [-0.0267, +0.0118] | 8 / 7 | point ok, lower < -eps (undetermined) |
| E_np_negonly C1 | 59 | 0.5603 | 0.5603 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| E_np_negonly C2 | 100 | 0.2499 | 0.2499 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C1 | 38 | 0.6100 | 0.6100 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| F_np_uncovered C2 | 100 | 0.2318 | 0.2318 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 | PASS |
| G_tims_crosslib C1 | 100 | 0.6485 | 0.5676 | +0.0809 | [+0.0418, +0.1234] | 24 / 10 | PASS |
| G_tims_crosslib C2 | 100 | 0.6398 | 0.6326 | +0.0071 | [-0.0144, +0.0284] | 11 / 8 | PASS |

## main: RK_new - RK_old -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| W7 A_timstof C1 tune seen | 2 | 0.7500 | 1.0000 | -0.2500 | [-0.5000, +0.0000] | 0 / 1 |
| W7 A_timstof C1 eval seen | 3 | 0.2381 | 0.2525 | -0.0144 | [-0.1905, +0.1667] | 1 / 2 |
| W7 A_timstof C2 tune seen | 2 | 0.5000 | 0.5000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| W7 A_timstof C2 tune unseen | 98 | 0.7947 | 0.7785 | +0.0162 | [-0.0150, +0.0491] | 9 / 8 |
| W7 A_timstof C2 eval seen | 3 | 0.3333 | 0.3333 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| W7 A_timstof C2 eval unseen | 97 | 0.7057 | 0.7161 | -0.0103 | [-0.0383, +0.0158] | 5 / 12 |
| W7 B_nplib C1 tune seen | 20 | 0.8750 | 0.8625 | +0.0125 | [-0.0375, +0.0750] | 1 / 1 |
| W7 B_nplib C1 eval seen | 20 | 0.8938 | 0.8700 | +0.0238 | [+0.0000, +0.0600] | 3 / 0 |
| W7 B_nplib C1 eval unseen | 1 | 1.0000 | 0.3333 | +0.6667 | [+0.6667, +0.6667] | 1 / 0 |
| W7 B_nplib C2 tune seen | 23 | 0.5801 | 0.5973 | -0.0172 | [-0.0444, +0.0000] | 0 / 3 |
| W7 B_nplib C2 tune unseen | 77 | 0.3614 | 0.3653 | -0.0039 | [-0.0211, +0.0103] | 4 / 7 |
| W7 B_nplib C2 eval seen | 23 | 0.5738 | 0.5584 | +0.0154 | [-0.0215, +0.0690] | 3 / 3 |
| W7 B_nplib C2 eval unseen | 77 | 0.3394 | 0.3510 | -0.0115 | [-0.0325, +0.0005] | 1 / 5 |

## control: RK_new - RK_new0 -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9208 | 0.9194 | +0.0014 | [-0.0101, +0.0127] | 11 / 5 |
| panel C1 clean | 202 | 0.9044 | 0.9002 | +0.0042 | [-0.0091, +0.0175] | 11 / 4 |
| panel C1 uncertain | 48 | 0.9896 | 1.0000 | -0.0104 | [-0.0312, +0.0000] | 0 / 1 |
| panel C2 all | 250 | 0.9402 | 0.9452 | -0.0050 | [-0.0114, -0.0004] | 1 / 7 |
| panel C2 clean | 202 | 0.9260 | 0.9322 | -0.0062 | [-0.0139, -0.0005] | 1 / 7 |
| panel C2 uncertain | 48 | 1.0000 | 1.0000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |

## control: RK_new - RK_new0 -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| C_np_crosslib C1 | 95 | 0.9016 | 0.8815 | +0.0201 | [-0.0126, +0.0520] | 12 / 3 |
| C_np_crosslib C2 | 100 | 0.5734 | 0.5871 | -0.0137 | [-0.0321, +0.0038] | 4 / 13 |
| D_np_single C2 | 100 | 0.2623 | 0.2524 | +0.0099 | [-0.0029, +0.0267] | 7 / 6 |
| E_np_negonly C1 | 59 | 0.5603 | 0.5603 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| E_np_negonly C2 | 100 | 0.2499 | 0.2499 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| F_np_uncovered C1 | 38 | 0.6100 | 0.6100 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| F_np_uncovered C2 | 100 | 0.2318 | 0.2318 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| G_tims_crosslib C1 | 100 | 0.6485 | 0.6204 | +0.0281 | [+0.0029, +0.0567] | 11 / 8 |
| G_tims_crosslib C2 | 100 | 0.6398 | 0.6414 | -0.0016 | [-0.0273, +0.0235] | 7 / 11 |

## control: RK_new - RK_new0 -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| W7 A_timstof C1 tune seen | 2 | 0.7500 | 0.7500 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| W7 A_timstof C1 eval seen | 3 | 0.2381 | 0.4444 | -0.2063 | [-0.5000, +0.0714] | 1 / 2 |
| W7 A_timstof C2 tune seen | 2 | 0.5000 | 0.5000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| W7 A_timstof C2 tune unseen | 98 | 0.7947 | 0.7998 | -0.0052 | [-0.0342, +0.0225] | 5 / 7 |
| W7 A_timstof C2 eval seen | 3 | 0.3333 | 0.3333 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| W7 A_timstof C2 eval unseen | 97 | 0.7057 | 0.7109 | -0.0051 | [-0.0298, +0.0202] | 5 / 10 |
| W7 B_nplib C1 tune seen | 20 | 0.8750 | 0.8896 | -0.0146 | [-0.0417, +0.0000] | 0 / 2 |
| W7 B_nplib C1 eval seen | 20 | 0.8938 | 0.8794 | +0.0144 | [-0.0018, +0.0450] | 1 / 1 |
| W7 B_nplib C1 eval unseen | 1 | 1.0000 | 0.3333 | +0.6667 | [+0.6667, +0.6667] | 1 / 0 |
| W7 B_nplib C2 tune seen | 23 | 0.5801 | 0.5981 | -0.0180 | [-0.0433, -0.0019] | 0 / 5 |
| W7 B_nplib C2 tune unseen | 77 | 0.3614 | 0.3592 | +0.0022 | [-0.0044, +0.0089] | 4 / 3 |
| W7 B_nplib C2 eval seen | 23 | 0.5738 | 0.6290 | -0.0552 | [-0.1329, +0.0026] | 1 / 6 |
| W7 B_nplib C2 eval unseen | 77 | 0.3394 | 0.3361 | +0.0033 | [-0.0070, +0.0190] | 2 / 4 |

## adoption: RK_new - M2x -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9208 | 0.8819 | +0.0389 | [+0.0179, +0.0613] | 30 / 6 |
| panel C1 clean | 202 | 0.9044 | 0.8621 | +0.0423 | [+0.0170, +0.0691] | 27 / 6 |
| panel C1 uncertain | 48 | 0.9896 | 0.9653 | +0.0243 | [+0.0000, +0.0556] | 3 / 0 |
| panel C2 all | 250 | 0.9402 | 0.9045 | +0.0357 | [+0.0148, +0.0580] | 23 / 8 |
| panel C2 clean | 202 | 0.9260 | 0.8934 | +0.0327 | [+0.0096, +0.0588] | 19 / 8 |
| panel C2 uncertain | 48 | 1.0000 | 0.9514 | +0.0486 | [+0.0104, +0.1007] | 4 / 0 |

## adoption: RK_new - M2x -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| C_np_crosslib C1 | 95 | 0.9016 | 0.9117 | -0.0101 | [-0.0448, +0.0216] | 6 / 8 |
| C_np_crosslib C2 | 100 | 0.5734 | 0.6120 | -0.0386 | [-0.0857, +0.0064] | 13 / 19 |
| D_np_single C2 | 100 | 0.2623 | 0.2673 | -0.0050 | [-0.0357, +0.0237] | 7 / 10 |
| E_np_negonly C1 | 59 | 0.5603 | 0.5608 | -0.0005 | [-0.0263, +0.0257] | 6 / 8 |
| E_np_negonly C2 | 100 | 0.2499 | 0.2353 | +0.0146 | [-0.0046, +0.0350] | 20 / 15 |
| F_np_uncovered C1 | 38 | 0.6100 | 0.5896 | +0.0203 | [-0.0403, +0.0787] | 6 / 5 |
| F_np_uncovered C2 | 100 | 0.2318 | 0.2287 | +0.0030 | [-0.0254, +0.0302] | 13 / 10 |
| G_tims_crosslib C1 | 100 | 0.6485 | 0.5997 | +0.0488 | [+0.0031, +0.0965] | 25 / 15 |
| G_tims_crosslib C2 | 100 | 0.6398 | 0.6371 | +0.0027 | [-0.0249, +0.0303] | 15 / 7 |

## adoption: RK_new - M2x -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| W7 A_timstof C1 tune seen | 2 | 0.7500 | 0.7500 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| W7 A_timstof C1 eval seen | 3 | 0.2381 | 0.2492 | -0.0111 | [-0.0571, +0.0238] | 1 / 1 |
| W7 A_timstof C2 tune seen | 2 | 0.5000 | 0.5000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| W7 A_timstof C2 tune unseen | 98 | 0.7947 | 0.7747 | +0.0200 | [-0.0137, +0.0568] | 14 / 10 |
| W7 A_timstof C2 eval seen | 3 | 0.3333 | 0.3333 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| W7 A_timstof C2 eval unseen | 97 | 0.7057 | 0.7249 | -0.0192 | [-0.0606, +0.0211] | 11 / 13 |
| W7 B_nplib C1 tune seen | 20 | 0.8750 | 0.8167 | +0.0583 | [-0.0167, +0.1500] | 3 / 2 |
| W7 B_nplib C1 eval seen | 20 | 0.8938 | 0.8591 | +0.0347 | [+0.0000, +0.0841] | 3 / 0 |
| W7 B_nplib C1 eval unseen | 1 | 1.0000 | 0.3333 | +0.6667 | [+0.6667, +0.6667] | 1 / 0 |
| W7 B_nplib C2 tune seen | 23 | 0.5801 | 0.5359 | +0.0442 | [-0.0116, +0.1120] | 6 / 1 |
| W7 B_nplib C2 tune unseen | 77 | 0.3614 | 0.3902 | -0.0288 | [-0.0604, -0.0022] | 4 / 9 |
| W7 B_nplib C2 eval seen | 23 | 0.5738 | 0.4356 | +0.1382 | [+0.0386, +0.2611] | 9 / 0 |
| W7 B_nplib C2 eval unseen | 77 | 0.3394 | 0.3567 | -0.0173 | [-0.0425, +0.0013] | 2 / 6 |

## FPNet only: RK_old - M2x -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| panel C1 all | 250 | 0.9128 | 0.8819 | +0.0309 | [+0.0107, +0.0525] | 25 / 9 |
| panel C1 clean | 202 | 0.8970 | 0.8621 | +0.0349 | [+0.0121, +0.0604] | 22 / 8 |
| panel C1 uncertain | 48 | 0.9792 | 0.9653 | +0.0139 | [-0.0208, +0.0521] | 3 / 1 |
| panel C2 all | 250 | 0.9492 | 0.9045 | +0.0447 | [+0.0238, +0.0677] | 24 / 5 |
| panel C2 clean | 202 | 0.9371 | 0.8934 | +0.0438 | [+0.0204, +0.0690] | 20 / 5 |
| panel C2 uncertain | 48 | 1.0000 | 0.9514 | +0.0486 | [+0.0104, +0.1007] | 4 / 0 |

## FPNet only: RK_old - M2x -- dev2 (full_rk hold groups = unseen)

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| C_np_crosslib C1 | 95 | 0.9027 | 0.9117 | -0.0090 | [-0.0339, +0.0152] | 4 / 6 |
| C_np_crosslib C2 | 100 | 0.5921 | 0.6120 | -0.0200 | [-0.0631, +0.0236] | 11 / 17 |
| D_np_single C2 | 100 | 0.2688 | 0.2673 | +0.0015 | [-0.0235, +0.0238] | 7 / 5 |
| E_np_negonly C1 | 59 | 0.5603 | 0.5608 | -0.0005 | [-0.0258, +0.0253] | 6 / 8 |
| E_np_negonly C2 | 100 | 0.2499 | 0.2353 | +0.0146 | [-0.0046, +0.0347] | 20 / 15 |
| F_np_uncovered C1 | 38 | 0.6100 | 0.5896 | +0.0203 | [-0.0417, +0.0787] | 6 / 5 |
| F_np_uncovered C2 | 100 | 0.2318 | 0.2287 | +0.0030 | [-0.0252, +0.0302] | 13 / 10 |
| G_tims_crosslib C1 | 100 | 0.5676 | 0.5997 | -0.0320 | [-0.0707, +0.0068] | 16 / 21 |
| G_tims_crosslib C2 | 100 | 0.6326 | 0.6371 | -0.0045 | [-0.0303, +0.0204] | 11 / 10 |

## FPNet only: RK_old - M2x -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity

| stratum | n | cand | ref | Δ | 95% CI | better / worse |
|---|---:|---:|---:|---:|---|---|
| W7 A_timstof C1 tune seen | 2 | 1.0000 | 0.7500 | +0.2500 | [+0.0000, +0.5000] | 1 / 0 |
| W7 A_timstof C1 eval seen | 3 | 0.2525 | 0.2492 | +0.0033 | [-0.1667, +0.1333] | 2 / 1 |
| W7 A_timstof C2 tune seen | 2 | 0.5000 | 0.5000 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| W7 A_timstof C2 tune unseen | 98 | 0.7785 | 0.7747 | +0.0038 | [-0.0253, +0.0334] | 13 / 9 |
| W7 A_timstof C2 eval seen | 3 | 0.3333 | 0.3333 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| W7 A_timstof C2 eval unseen | 97 | 0.7161 | 0.7249 | -0.0089 | [-0.0404, +0.0213] | 12 / 8 |
| W7 B_nplib C1 tune seen | 20 | 0.8625 | 0.8167 | +0.0458 | [-0.0083, +0.1250] | 2 / 1 |
| W7 B_nplib C1 eval seen | 20 | 0.8700 | 0.8591 | +0.0109 | [+0.0000, +0.0297] | 2 / 0 |
| W7 B_nplib C1 eval unseen | 1 | 0.3333 | 0.3333 | +0.0000 | [+0.0000, +0.0000] | 0 / 0 |
| W7 B_nplib C2 tune seen | 23 | 0.5973 | 0.5359 | +0.0615 | [+0.0124, +0.1251] | 6 / 0 |
| W7 B_nplib C2 tune unseen | 77 | 0.3653 | 0.3902 | -0.0249 | [-0.0559, -0.0008] | 4 / 7 |
| W7 B_nplib C2 eval seen | 23 | 0.5584 | 0.4356 | +0.1228 | [+0.0347, +0.2322] | 8 / 0 |
| W7 B_nplib C2 eval unseen | 77 | 0.3510 | 0.3567 | -0.0057 | [-0.0231, +0.0095] | 2 / 6 |
