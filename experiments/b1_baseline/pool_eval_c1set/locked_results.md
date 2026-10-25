# B1 locked evaluation (official scorer replica, frozen ledger)

| set | view | candidate | output | official MRR@25 [95% CI] | no candidates | GL fallback |
|---|---|---|---|---|---|---|
| B_nplib | c2 (n=300) | M2x | learned | 0.5824 [0.532, 0.632] | 8 | 1 |
| B_nplib | c2 (n=300) | M2x | insurance | 0.4327 [0.385, 0.480] | 8 | 1 |
| B_nplib | c2 (n=300) | M2x | fixed | 0.4327 [0.385, 0.480] | 8 | 1 |
| B_nplib | c2 (n=300) | M2x | switch | 0.5824 [0.532, 0.632] | 8 | 1 |
| B_nplib | c2 (n=300) | M2x | blend21 | 0.5597 [0.510, 0.609] | 8 | 1 |
| B_nplib | c2 (n=300) | M2x | blend11 | 0.5420 [0.493, 0.591] | 8 | 1 |
| B_nplib | c1 (n=261) | M2x | learned | 0.9170 [0.888, 0.945] | 0 | 4 |
| B_nplib | c1 (n=261) | M2x | insurance | 0.6638 [0.615, 0.711] | 0 | 4 |
| B_nplib | c1 (n=261) | M2x | fixed | 0.5455 [0.497, 0.593] | 0 | 4 |
| B_nplib | c1 (n=261) | M2x | switch | 0.9196 [0.890, 0.947] | 0 | 4 |
| B_nplib | c1 (n=261) | M2x | blend21 | 0.9003 [0.870, 0.929] | 0 | 4 |
| B_nplib | c1 (n=261) | M2x | blend11 | 0.8576 [0.822, 0.891] | 0 | 4 |
| B_nplib | c2 (n=300) | M2x_pool | learned | 0.5768 [0.528, 0.626] | 8 | 1 |
| B_nplib | c2 (n=300) | M2x_pool | insurance | 0.4321 [0.384, 0.480] | 8 | 1 |
| B_nplib | c2 (n=300) | M2x_pool | fixed | 0.4321 [0.385, 0.481] | 8 | 1 |
| B_nplib | c2 (n=300) | M2x_pool | switch | 0.5768 [0.526, 0.626] | 8 | 1 |
| B_nplib | c2 (n=300) | M2x_pool | blend21 | 0.5566 [0.507, 0.606] | 8 | 1 |
| B_nplib | c2 (n=300) | M2x_pool | blend11 | 0.5350 [0.486, 0.584] | 8 | 1 |
| B_nplib | c1 (n=261) | M2x_pool | learned | 0.9174 [0.888, 0.944] | 0 | 4 |
| B_nplib | c1 (n=261) | M2x_pool | insurance | 0.6637 [0.615, 0.711] | 0 | 4 |
| B_nplib | c1 (n=261) | M2x_pool | fixed | 0.5455 [0.497, 0.594] | 0 | 4 |
| B_nplib | c1 (n=261) | M2x_pool | switch | 0.9199 [0.891, 0.947] | 0 | 4 |
| B_nplib | c1 (n=261) | M2x_pool | blend21 | 0.8959 [0.865, 0.925] | 0 | 4 |
| B_nplib | c1 (n=261) | M2x_pool | blend11 | 0.8521 [0.816, 0.887] | 0 | 4 |

## paired differences (molecule-level bootstrap, same ledger)

| set | view | comparison | mean Δ RR | 95% CI | n |
|---|---|---|---:|---|---:|
| B_nplib | c2 | M2x: learned − fixed | +0.1497 | [+0.111, +0.188] | 300 |
| B_nplib | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 300 |
| B_nplib | c2 | M2x: switch − fixed | +0.1497 | [+0.112, +0.189] | 300 |
| B_nplib | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 300 |
| B_nplib | c2 | M2x: blend21 − learned | -0.0226 | [-0.040, -0.006] | 300 |
| B_nplib | c2 | M2x: blend21 − fixed | +0.1270 | [+0.094, +0.161] | 300 |
| B_nplib | c2 | M2x: blend11 − learned | -0.0403 | [-0.063, -0.018] | 300 |
| B_nplib | c2 | M2x: blend11 − fixed | +0.1094 | [+0.080, +0.140] | 300 |
| B_nplib | c2 | M2x_pool: learned − fixed | +0.1446 | [+0.109, +0.182] | 300 |
| B_nplib | c2 | M2x_pool: insurance − fixed | +0.0000 | [+0.000, +0.000] | 300 |
| B_nplib | c2 | M2x_pool: switch − fixed | +0.1446 | [+0.110, +0.182] | 300 |
| B_nplib | c2 | M2x_pool: switch − learned | +0.0000 | [+0.000, +0.000] | 300 |
| B_nplib | c2 | M2x_pool: blend21 − learned | -0.0202 | [-0.039, -0.003] | 300 |
| B_nplib | c2 | M2x_pool: blend21 − fixed | +0.1245 | [+0.094, +0.156] | 300 |
| B_nplib | c2 | M2x_pool: blend11 − learned | -0.0418 | [-0.064, -0.020] | 300 |
| B_nplib | c2 | M2x_pool: blend11 − fixed | +0.1029 | [+0.076, +0.131] | 300 |
| B_nplib | c2 | M2x_pool − M2x (learned) | -0.0056 | [-0.020, +0.009] | 300 |
| B_nplib | c2 | M2x_pool − M2x (insurance) | -0.0006 | [-0.002, +0.000] | 300 |
| B_nplib | c2 | M2x_pool − M2x (switch) | -0.0056 | [-0.020, +0.008] | 300 |
| B_nplib | c2 | M2x_pool − M2x (blend21) | -0.0031 | [-0.017, +0.011] | 300 |
| B_nplib | c2 | M2x_pool learned − M2x insurance | +0.1441 | [+0.109, +0.181] | 300 |
| B_nplib | c2 | REGISTERED M2x_pool blend21 − M2x blend21 | -0.0031 | [-0.017, +0.010] | 300 |
| B_nplib | c1 | M2x: learned − fixed | +0.3716 | [+0.322, +0.422] | 261 |
| B_nplib | c1 | M2x: insurance − fixed | +0.1183 | [+0.084, +0.154] | 261 |
| B_nplib | c1 | M2x: switch − fixed | +0.3741 | [+0.324, +0.425] | 261 |
| B_nplib | c1 | M2x: switch − learned | +0.0026 | [+0.000, +0.008] | 261 |
| B_nplib | c1 | M2x: blend21 − learned | -0.0167 | [-0.035, +0.001] | 261 |
| B_nplib | c1 | M2x: blend21 − fixed | +0.3549 | [+0.308, +0.401] | 261 |
| B_nplib | c1 | M2x: blend11 − learned | -0.0594 | [-0.087, -0.033] | 261 |
| B_nplib | c1 | M2x: blend11 − fixed | +0.3122 | [+0.268, +0.357] | 261 |
| B_nplib | c1 | M2x_pool: learned − fixed | +0.3719 | [+0.321, +0.422] | 261 |
| B_nplib | c1 | M2x_pool: insurance − fixed | +0.1181 | [+0.084, +0.154] | 261 |
| B_nplib | c1 | M2x_pool: switch − fixed | +0.3744 | [+0.324, +0.424] | 261 |
| B_nplib | c1 | M2x_pool: switch − learned | +0.0026 | [+0.000, +0.008] | 261 |
| B_nplib | c1 | M2x_pool: blend21 − learned | -0.0215 | [-0.041, -0.003] | 261 |
| B_nplib | c1 | M2x_pool: blend21 − fixed | +0.3504 | [+0.305, +0.396] | 261 |
| B_nplib | c1 | M2x_pool: blend11 − learned | -0.0653 | [-0.093, -0.039] | 261 |
| B_nplib | c1 | M2x_pool: blend11 − fixed | +0.3066 | [+0.264, +0.350] | 261 |
| B_nplib | c1 | M2x_pool − M2x (learned) | +0.0003 | [-0.005, +0.006] | 261 |
| B_nplib | c1 | M2x_pool − M2x (insurance) | -0.0001 | [-0.001, +0.002] | 261 |
| B_nplib | c1 | M2x_pool − M2x (switch) | +0.0003 | [-0.005, +0.006] | 261 |
| B_nplib | c1 | M2x_pool − M2x (blend21) | -0.0044 | [-0.016, +0.006] | 261 |
| B_nplib | c1 | M2x_pool learned − M2x insurance | +0.2536 | [+0.206, +0.301] | 261 |
| B_nplib | c1 | REGISTERED M2x_pool blend21 − M2x blend21 | -0.0044 | [-0.016, +0.006] | 261 |
