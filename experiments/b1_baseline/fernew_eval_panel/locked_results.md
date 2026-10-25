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
| P_np250 | c2 (n=250) | FE_new | learned | 0.9493 [0.926, 0.971] | 0 | 34 |
| P_np250 | c2 (n=250) | FE_new | insurance | 0.9157 [0.886, 0.943] | 0 | 34 |
| P_np250 | c2 (n=250) | FE_new | fixed | 0.9197 [0.890, 0.947] | 0 | 34 |
| P_np250 | c2 (n=250) | FE_new | switch | 0.9453 [0.921, 0.967] | 0 | 34 |
| P_np250 | c2 (n=250) | FE_new | blend21 | 0.9447 [0.919, 0.967] | 0 | 34 |
| P_np250 | c2 (n=250) | FE_new | blend11 | 0.9422 [0.916, 0.966] | 0 | 34 |
| P_np250 | c1 (n=250) | FE_new | learned | 0.8410 [0.806, 0.874] | 0 | 34 |
| P_np250 | c1 (n=250) | FE_new | insurance | 0.9197 [0.890, 0.947] | 0 | 34 |
| P_np250 | c1 (n=250) | FE_new | fixed | 0.9197 [0.890, 0.947] | 0 | 34 |
| P_np250 | c1 (n=250) | FE_new | switch | 0.8490 [0.814, 0.882] | 0 | 34 |
| P_np250 | c1 (n=250) | FE_new | blend21 | 0.9308 [0.904, 0.956] | 0 | 34 |
| P_np250 | c1 (n=250) | FE_new | blend11 | 0.9357 [0.909, 0.960] | 0 | 34 |

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
| P_np250 | c2 | FE_new: learned − fixed | +0.0296 | [+0.012, +0.048] | 250 |
| P_np250 | c2 | FE_new: insurance − fixed | -0.0040 | [-0.010, +0.000] | 250 |
| P_np250 | c2 | FE_new: switch − fixed | +0.0256 | [+0.007, +0.045] | 250 |
| P_np250 | c2 | FE_new: switch − learned | -0.0040 | [-0.010, +0.000] | 250 |
| P_np250 | c2 | FE_new: blend21 − learned | -0.0046 | [-0.012, +0.002] | 250 |
| P_np250 | c2 | FE_new: blend21 − fixed | +0.0250 | [+0.009, +0.042] | 250 |
| P_np250 | c2 | FE_new: blend11 − learned | -0.0070 | [-0.019, +0.004] | 250 |
| P_np250 | c2 | FE_new: blend11 − fixed | +0.0225 | [+0.009, +0.037] | 250 |
| P_np250 | c2 | FE_new − M2x_fe (learned) | +0.0026 | [-0.009, +0.015] | 250 |
| P_np250 | c2 | FE_new − M2x_fe (insurance) | +0.0000 | [+0.000, +0.000] | 250 |
| P_np250 | c2 | FE_new − M2x_fe (switch) | +0.0006 | [-0.011, +0.012] | 250 |
| P_np250 | c2 | FE_new − M2x_fe (blend21) | -0.0074 | [-0.017, +0.001] | 250 |
| P_np250 | c2 | FE_new learned − M2x_fe insurance | +0.0336 | [+0.015, +0.053] | 250 |
| P_np250 | c2 | REGISTERED FE_new blend21 − M2x_fe blend21 | -0.0074 | [-0.017, +0.002] | 250 |
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
| P_np250 | c1 | FE_new: learned − fixed | -0.0787 | [-0.111, -0.047] | 250 |
| P_np250 | c1 | FE_new: insurance − fixed | +0.0000 | [+0.000, +0.000] | 250 |
| P_np250 | c1 | FE_new: switch − fixed | -0.0707 | [-0.102, -0.039] | 250 |
| P_np250 | c1 | FE_new: switch − learned | +0.0080 | [+0.002, +0.016] | 250 |
| P_np250 | c1 | FE_new: blend21 − learned | +0.0898 | [+0.064, +0.117] | 250 |
| P_np250 | c1 | FE_new: blend21 − fixed | +0.0111 | [-0.006, +0.030] | 250 |
| P_np250 | c1 | FE_new: blend11 − learned | +0.0948 | [+0.067, +0.124] | 250 |
| P_np250 | c1 | FE_new: blend11 − fixed | +0.0160 | [+0.004, +0.029] | 250 |
| P_np250 | c1 | FE_new − M2x_fe (learned) | +0.0979 | [+0.068, +0.129] | 250 |
| P_np250 | c1 | FE_new − M2x_fe (insurance) | +0.0000 | [+0.000, +0.000] | 250 |
| P_np250 | c1 | FE_new − M2x_fe (switch) | +0.0959 | [+0.066, +0.127] | 250 |
| P_np250 | c1 | FE_new − M2x_fe (blend21) | +0.0186 | [+0.004, +0.034] | 250 |
| P_np250 | c1 | FE_new learned − M2x_fe insurance | -0.0787 | [-0.111, -0.046] | 250 |
| P_np250 | c1 | REGISTERED FE_new blend21 − M2x_fe blend21 | +0.0186 | [+0.004, +0.034] | 250 |
