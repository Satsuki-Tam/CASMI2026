# B1 locked evaluation (official scorer replica, frozen ledger)

| set | view | candidate | output | official MRR@25 [95% CI] | no candidates | GL fallback |
|---|---|---|---|---|---|---|
| P_np250 | c2 (n=250) | M2x_fe | learned | 0.9467 [0.923, 0.968] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x_fe | insurance | 0.9157 [0.886, 0.943] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x_fe | fixed | 0.9197 [0.890, 0.947] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x_fe | switch | 0.9447 [0.921, 0.966] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x_fe | blend21 | 0.9521 [0.929, 0.973] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x_fe | blend11 | 0.9474 [0.923, 0.969] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | learned | 0.7430 [0.701, 0.784] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | insurance | 0.9197 [0.890, 0.947] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | fixed | 0.9197 [0.890, 0.947] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | switch | 0.7530 [0.712, 0.794] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | blend21 | 0.9122 [0.882, 0.940] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | blend11 | 0.9200 [0.891, 0.946] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x | learned | 0.8896 [0.857, 0.920] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x | insurance | 0.8581 [0.821, 0.892] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x | fixed | 0.8621 [0.826, 0.897] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x | switch | 0.8856 [0.853, 0.916] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x | blend21 | 0.9045 [0.873, 0.934] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x | blend11 | 0.8980 [0.866, 0.928] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | learned | 0.7543 [0.713, 0.794] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | insurance | 0.8654 [0.829, 0.899] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | fixed | 0.8621 [0.826, 0.897] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | switch | 0.7623 [0.721, 0.802] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | blend21 | 0.8819 [0.849, 0.914] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | blend11 | 0.8901 [0.857, 0.921] | 0 | 34 |
| P_np250 | c2 (n=250) | ENS2 | learned | 0.9452 [0.922, 0.967] | 0 | 34 |
| P_np250 | c2 (n=250) | ENS2 | insurance | 0.9117 [0.881, 0.939] | 0 | 34 |
| P_np250 | c2 (n=250) | ENS2 | fixed | 0.9157 [0.886, 0.944] | 0 | 34 |
| P_np250 | c2 (n=250) | ENS2 | switch | 0.9432 [0.919, 0.965] | 0 | 34 |
| P_np250 | c2 (n=250) | ENS2 | blend21 | 0.9483 [0.924, 0.970] | 0 | 34 |
| P_np250 | c2 (n=250) | ENS2 | blend11 | 0.9435 [0.918, 0.967] | 0 | 34 |
| P_np250 | c1 (n=250) | ENS2 | learned | 0.7511 [0.710, 0.791] | 0 | 34 |
| P_np250 | c1 (n=250) | ENS2 | insurance | 0.9157 [0.886, 0.943] | 0 | 34 |
| P_np250 | c1 (n=250) | ENS2 | fixed | 0.9157 [0.886, 0.944] | 0 | 34 |
| P_np250 | c1 (n=250) | ENS2 | switch | 0.7611 [0.720, 0.801] | 0 | 34 |
| P_np250 | c1 (n=250) | ENS2 | blend21 | 0.9077 [0.878, 0.936] | 0 | 34 |
| P_np250 | c1 (n=250) | ENS2 | blend11 | 0.9160 [0.887, 0.943] | 0 | 34 |

## paired differences (molecule-level bootstrap, same ledger)

| set | view | comparison | mean Δ RR | 95% CI | n |
|---|---|---|---:|---|---:|
| P_np250 | c2 | M2x_fe: learned − fixed | +0.0270 | [+0.006, +0.049] | 250 |
| P_np250 | c2 | M2x_fe: insurance − fixed | -0.0040 | [-0.010, +0.000] | 250 |
| P_np250 | c2 | M2x_fe: switch − fixed | +0.0250 | [+0.004, +0.047] | 250 |
| P_np250 | c2 | M2x_fe: switch − learned | -0.0020 | [-0.006, +0.000] | 250 |
| P_np250 | c2 | M2x_fe: blend21 − learned | +0.0054 | [-0.005, +0.017] | 250 |
| P_np250 | c2 | M2x_fe: blend21 − fixed | +0.0324 | [+0.016, +0.051] | 250 |
| P_np250 | c2 | M2x_fe: blend11 − learned | +0.0008 | [-0.014, +0.015] | 250 |
| P_np250 | c2 | M2x_fe: blend11 − fixed | +0.0277 | [+0.013, +0.044] | 250 |
| P_np250 | c2 | M2x: learned − fixed | +0.0275 | [+0.005, +0.051] | 250 |
| P_np250 | c2 | M2x: insurance − fixed | -0.0040 | [-0.010, +0.000] | 250 |
| P_np250 | c2 | M2x: switch − fixed | +0.0235 | [-0.001, +0.047] | 250 |
| P_np250 | c2 | M2x: switch − learned | -0.0040 | [-0.010, +0.000] | 250 |
| P_np250 | c2 | M2x: blend21 − learned | +0.0149 | [+0.003, +0.028] | 250 |
| P_np250 | c2 | M2x: blend21 − fixed | +0.0424 | [+0.023, +0.063] | 250 |
| P_np250 | c2 | M2x: blend11 − learned | +0.0084 | [-0.007, +0.024] | 250 |
| P_np250 | c2 | M2x: blend11 − fixed | +0.0359 | [+0.018, +0.054] | 250 |
| P_np250 | c2 | M2x − M2x_fe (learned) | -0.0571 | [-0.085, -0.031] | 250 |
| P_np250 | c2 | M2x − M2x_fe (insurance) | -0.0576 | [-0.083, -0.035] | 250 |
| P_np250 | c2 | M2x − M2x_fe (switch) | -0.0591 | [-0.086, -0.034] | 250 |
| P_np250 | c2 | M2x − M2x_fe (blend21) | -0.0476 | [-0.071, -0.027] | 250 |
| P_np250 | c2 | M2x learned − M2x_fe insurance | -0.0261 | [-0.056, +0.002] | 250 |
| P_np250 | c2 | REGISTERED M2x blend21 − M2x_fe blend21 | -0.0476 | [-0.071, -0.026] | 250 |
| P_np250 | c2 | ENS2: learned − fixed | +0.0295 | [+0.009, +0.051] | 250 |
| P_np250 | c2 | ENS2: insurance − fixed | -0.0040 | [-0.010, +0.000] | 250 |
| P_np250 | c2 | ENS2: switch − fixed | +0.0275 | [+0.007, +0.049] | 250 |
| P_np250 | c2 | ENS2: switch − learned | -0.0020 | [-0.006, +0.000] | 250 |
| P_np250 | c2 | ENS2: blend21 − learned | +0.0031 | [-0.007, +0.014] | 250 |
| P_np250 | c2 | ENS2: blend21 − fixed | +0.0326 | [+0.016, +0.050] | 250 |
| P_np250 | c2 | ENS2: blend11 − learned | -0.0017 | [-0.016, +0.012] | 250 |
| P_np250 | c2 | ENS2: blend11 − fixed | +0.0278 | [+0.014, +0.044] | 250 |
| P_np250 | c2 | ENS2 − M2x_fe (learned) | -0.0014 | [-0.012, +0.009] | 250 |
| P_np250 | c2 | ENS2 − M2x_fe (insurance) | -0.0040 | [-0.010, +0.001] | 250 |
| P_np250 | c2 | ENS2 − M2x_fe (switch) | -0.0014 | [-0.012, +0.009] | 250 |
| P_np250 | c2 | ENS2 − M2x_fe (blend21) | -0.0038 | [-0.012, +0.004] | 250 |
| P_np250 | c2 | ENS2 learned − M2x_fe insurance | +0.0295 | [+0.010, +0.051] | 250 |
| P_np250 | c2 | REGISTERED ENS2 blend21 − M2x_fe blend21 | -0.0038 | [-0.012, +0.003] | 250 |
| P_np250 | c1 | M2x_fe: learned − fixed | -0.1767 | [-0.216, -0.137] | 250 |
| P_np250 | c1 | M2x_fe: insurance − fixed | +0.0000 | [+0.000, +0.000] | 250 |
| P_np250 | c1 | M2x_fe: switch − fixed | -0.1667 | [-0.207, -0.128] | 250 |
| P_np250 | c1 | M2x_fe: switch − learned | +0.0100 | [+0.002, +0.020] | 250 |
| P_np250 | c1 | M2x_fe: blend21 − learned | +0.1692 | [+0.135, +0.204] | 250 |
| P_np250 | c1 | M2x_fe: blend21 − fixed | -0.0075 | [-0.027, +0.012] | 250 |
| P_np250 | c1 | M2x_fe: blend11 − learned | +0.1770 | [+0.142, +0.213] | 250 |
| P_np250 | c1 | M2x_fe: blend11 − fixed | +0.0003 | [-0.016, +0.017] | 250 |
| P_np250 | c1 | M2x: learned − fixed | -0.1078 | [-0.148, -0.068] | 250 |
| P_np250 | c1 | M2x: insurance − fixed | +0.0033 | [+0.000, +0.010] | 250 |
| P_np250 | c1 | M2x: switch − fixed | -0.0998 | [-0.140, -0.060] | 250 |
| P_np250 | c1 | M2x: switch − learned | +0.0080 | [+0.002, +0.016] | 250 |
| P_np250 | c1 | M2x: blend21 − learned | +0.1276 | [+0.096, +0.160] | 250 |
| P_np250 | c1 | M2x: blend21 − fixed | +0.0198 | [-0.001, +0.042] | 250 |
| P_np250 | c1 | M2x: blend11 − learned | +0.1358 | [+0.101, +0.171] | 250 |
| P_np250 | c1 | M2x: blend11 − fixed | +0.0280 | [+0.008, +0.049] | 250 |
| P_np250 | c1 | M2x − M2x_fe (learned) | +0.0113 | [-0.018, +0.041] | 250 |
| P_np250 | c1 | M2x − M2x_fe (insurance) | -0.0543 | [-0.078, -0.032] | 250 |
| P_np250 | c1 | M2x − M2x_fe (switch) | +0.0093 | [-0.020, +0.039] | 250 |
| P_np250 | c1 | M2x − M2x_fe (blend21) | -0.0303 | [-0.054, -0.008] | 250 |
| P_np250 | c1 | M2x learned − M2x_fe insurance | -0.1654 | [-0.205, -0.127] | 250 |
| P_np250 | c1 | REGISTERED M2x blend21 − M2x_fe blend21 | -0.0303 | [-0.054, -0.008] | 250 |
| P_np250 | c1 | ENS2: learned − fixed | -0.1647 | [-0.205, -0.126] | 250 |
| P_np250 | c1 | ENS2: insurance − fixed | +0.0000 | [+0.000, +0.000] | 250 |
| P_np250 | c1 | ENS2: switch − fixed | -0.1547 | [-0.194, -0.116] | 250 |
| P_np250 | c1 | ENS2: switch − learned | +0.0100 | [+0.002, +0.020] | 250 |
| P_np250 | c1 | ENS2: blend21 − learned | +0.1566 | [+0.123, +0.192] | 250 |
| P_np250 | c1 | ENS2: blend21 − fixed | -0.0080 | [-0.027, +0.011] | 250 |
| P_np250 | c1 | ENS2: blend11 − learned | +0.1649 | [+0.129, +0.202] | 250 |
| P_np250 | c1 | ENS2: blend11 − fixed | +0.0003 | [-0.015, +0.016] | 250 |
| P_np250 | c1 | ENS2 − M2x_fe (learned) | +0.0081 | [-0.007, +0.024] | 250 |
| P_np250 | c1 | ENS2 − M2x_fe (insurance) | -0.0040 | [-0.011, +0.001] | 250 |
| P_np250 | c1 | ENS2 − M2x_fe (switch) | +0.0081 | [-0.007, +0.024] | 250 |
| P_np250 | c1 | ENS2 − M2x_fe (blend21) | -0.0045 | [-0.015, +0.005] | 250 |
| P_np250 | c1 | ENS2 learned − M2x_fe insurance | -0.1686 | [-0.208, -0.129] | 250 |
| P_np250 | c1 | REGISTERED ENS2 blend21 − M2x_fe blend21 | -0.0045 | [-0.015, +0.005] | 250 |
