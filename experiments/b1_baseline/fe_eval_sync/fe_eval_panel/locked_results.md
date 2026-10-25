# B1 locked evaluation (official scorer replica, frozen ledger)

| set | view | candidate | output | official MRR@25 [95% CI] | no candidates | GL fallback |
|---|---|---|---|---|---|---|
| P_np250 | c2 (n=250) | M2x | learned | 0.8896 [0.857, 0.920] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x | insurance | 0.8581 [0.822, 0.893] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x | fixed | 0.8621 [0.826, 0.896] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x | switch | 0.8856 [0.853, 0.917] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x | blend21 | 0.9045 [0.873, 0.934] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x | blend11 | 0.8980 [0.866, 0.928] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | learned | 0.7543 [0.714, 0.794] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | insurance | 0.8654 [0.830, 0.899] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | fixed | 0.8621 [0.826, 0.896] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | switch | 0.7623 [0.721, 0.803] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | blend21 | 0.8819 [0.848, 0.913] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x | blend11 | 0.8901 [0.857, 0.920] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x_fe | learned | 0.9467 [0.923, 0.968] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x_fe | insurance | 0.9157 [0.886, 0.943] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x_fe | fixed | 0.9197 [0.890, 0.947] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x_fe | switch | 0.9447 [0.921, 0.966] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x_fe | blend21 | 0.9521 [0.929, 0.973] | 0 | 34 |
| P_np250 | c2 (n=250) | M2x_fe | blend11 | 0.9474 [0.923, 0.970] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | learned | 0.7430 [0.701, 0.783] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | insurance | 0.9197 [0.890, 0.947] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | fixed | 0.9197 [0.890, 0.947] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | switch | 0.7530 [0.712, 0.793] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | blend21 | 0.9122 [0.882, 0.940] | 0 | 34 |
| P_np250 | c1 (n=250) | M2x_fe | blend11 | 0.9200 [0.891, 0.947] | 0 | 34 |

## paired differences (molecule-level bootstrap, same ledger)

| set | view | comparison | mean Δ RR | 95% CI | n |
|---|---|---|---:|---|---:|
| P_np250 | c2 | M2x: learned − fixed | +0.0275 | [+0.004, +0.051] | 250 |
| P_np250 | c2 | M2x: insurance − fixed | -0.0040 | [-0.010, +0.000] | 250 |
| P_np250 | c2 | M2x: switch − fixed | +0.0235 | [-0.000, +0.048] | 250 |
| P_np250 | c2 | M2x: switch − learned | -0.0040 | [-0.010, +0.000] | 250 |
| P_np250 | c2 | M2x: blend21 − learned | +0.0149 | [+0.003, +0.028] | 250 |
| P_np250 | c2 | M2x: blend21 − fixed | +0.0424 | [+0.023, +0.063] | 250 |
| P_np250 | c2 | M2x: blend11 − learned | +0.0084 | [-0.007, +0.024] | 250 |
| P_np250 | c2 | M2x: blend11 − fixed | +0.0359 | [+0.018, +0.055] | 250 |
| P_np250 | c2 | M2x_fe: learned − fixed | +0.0270 | [+0.006, +0.049] | 250 |
| P_np250 | c2 | M2x_fe: insurance − fixed | -0.0040 | [-0.010, +0.000] | 250 |
| P_np250 | c2 | M2x_fe: switch − fixed | +0.0250 | [+0.004, +0.048] | 250 |
| P_np250 | c2 | M2x_fe: switch − learned | -0.0020 | [-0.006, +0.000] | 250 |
| P_np250 | c2 | M2x_fe: blend21 − learned | +0.0054 | [-0.006, +0.017] | 250 |
| P_np250 | c2 | M2x_fe: blend21 − fixed | +0.0324 | [+0.016, +0.051] | 250 |
| P_np250 | c2 | M2x_fe: blend11 − learned | +0.0008 | [-0.013, +0.015] | 250 |
| P_np250 | c2 | M2x_fe: blend11 − fixed | +0.0277 | [+0.013, +0.044] | 250 |
| P_np250 | c2 | M2x_fe − M2x (learned) | +0.0571 | [+0.032, +0.085] | 250 |
| P_np250 | c2 | M2x_fe − M2x (insurance) | +0.0576 | [+0.035, +0.082] | 250 |
| P_np250 | c2 | M2x_fe − M2x (switch) | +0.0591 | [+0.034, +0.087] | 250 |
| P_np250 | c2 | M2x_fe − M2x (blend21) | +0.0476 | [+0.026, +0.071] | 250 |
| P_np250 | c2 | M2x_fe learned − M2x insurance | +0.0886 | [+0.060, +0.119] | 250 |
| P_np250 | c2 | REGISTERED M2x_fe blend21 − M2x blend21 | +0.0476 | [+0.026, +0.071] | 250 |
| P_np250 | c1 | M2x: learned − fixed | -0.1078 | [-0.148, -0.067] | 250 |
| P_np250 | c1 | M2x: insurance − fixed | +0.0033 | [+0.000, +0.010] | 250 |
| P_np250 | c1 | M2x: switch − fixed | -0.0998 | [-0.141, -0.059] | 250 |
| P_np250 | c1 | M2x: switch − learned | +0.0080 | [+0.002, +0.016] | 250 |
| P_np250 | c1 | M2x: blend21 − learned | +0.1276 | [+0.096, +0.161] | 250 |
| P_np250 | c1 | M2x: blend21 − fixed | +0.0198 | [-0.002, +0.042] | 250 |
| P_np250 | c1 | M2x: blend11 − learned | +0.1358 | [+0.101, +0.172] | 250 |
| P_np250 | c1 | M2x: blend11 − fixed | +0.0280 | [+0.008, +0.049] | 250 |
| P_np250 | c1 | M2x_fe: learned − fixed | -0.1767 | [-0.217, -0.138] | 250 |
| P_np250 | c1 | M2x_fe: insurance − fixed | +0.0000 | [+0.000, +0.000] | 250 |
| P_np250 | c1 | M2x_fe: switch − fixed | -0.1667 | [-0.207, -0.127] | 250 |
| P_np250 | c1 | M2x_fe: switch − learned | +0.0100 | [+0.002, +0.020] | 250 |
| P_np250 | c1 | M2x_fe: blend21 − learned | +0.1692 | [+0.135, +0.205] | 250 |
| P_np250 | c1 | M2x_fe: blend21 − fixed | -0.0075 | [-0.027, +0.012] | 250 |
| P_np250 | c1 | M2x_fe: blend11 − learned | +0.1770 | [+0.142, +0.214] | 250 |
| P_np250 | c1 | M2x_fe: blend11 − fixed | +0.0003 | [-0.015, +0.017] | 250 |
| P_np250 | c1 | M2x_fe − M2x (learned) | -0.0113 | [-0.041, +0.019] | 250 |
| P_np250 | c1 | M2x_fe − M2x (insurance) | +0.0543 | [+0.032, +0.078] | 250 |
| P_np250 | c1 | M2x_fe − M2x (switch) | -0.0093 | [-0.038, +0.020] | 250 |
| P_np250 | c1 | M2x_fe − M2x (blend21) | +0.0303 | [+0.008, +0.054] | 250 |
| P_np250 | c1 | M2x_fe learned − M2x insurance | -0.1224 | [-0.168, -0.076] | 250 |
| P_np250 | c1 | REGISTERED M2x_fe blend21 − M2x blend21 | +0.0303 | [+0.008, +0.054] | 250 |
