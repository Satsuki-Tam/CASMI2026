# B1 locked evaluation (official scorer replica, frozen ledger)

| set | view | candidate | output | official MRR@25 [95% CI] | no candidates | GL fallback |
|---|---|---|---|---|---|---|
| C_np_crosslib | c2 (n=100) | M2x | learned | 0.6100 [0.524, 0.695] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x | insurance | 0.5069 [0.420, 0.593] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x | fixed | 0.5069 [0.420, 0.594] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x | switch | 0.6100 [0.525, 0.694] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x | blend21 | 0.6120 [0.525, 0.698] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x | blend11 | 0.5911 [0.502, 0.679] | 2 | 1 |
| C_np_crosslib | c1 (n=95) | M2x | learned | 0.9157 [0.869, 0.956] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x | insurance | 0.7752 [0.698, 0.847] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x | fixed | 0.6226 [0.539, 0.705] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x | switch | 0.9262 [0.881, 0.966] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x | blend21 | 0.9117 [0.861, 0.956] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x | blend11 | 0.8642 [0.805, 0.919] | 0 | 0 |
| C_np_crosslib | c2 (n=100) | M2x_fe | learned | 0.6205 [0.533, 0.705] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x_fe | insurance | 0.5216 [0.436, 0.609] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x_fe | fixed | 0.5216 [0.433, 0.607] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x_fe | switch | 0.6205 [0.534, 0.707] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x_fe | blend21 | 0.6013 [0.515, 0.687] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x_fe | blend11 | 0.5749 [0.486, 0.661] | 2 | 1 |
| C_np_crosslib | c1 (n=95) | M2x_fe | learned | 0.9175 [0.872, 0.957] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x_fe | insurance | 0.7757 [0.701, 0.849] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x_fe | fixed | 0.6245 [0.538, 0.709] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x_fe | switch | 0.9227 [0.879, 0.962] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x_fe | blend21 | 0.8989 [0.848, 0.946] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x_fe | blend11 | 0.8849 [0.829, 0.935] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | learned | 0.2687 [0.190, 0.349] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | insurance | 0.2372 [0.164, 0.316] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | fixed | 0.2372 [0.164, 0.316] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | switch | 0.2687 [0.192, 0.351] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | blend21 | 0.2673 [0.190, 0.350] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | blend11 | 0.2658 [0.188, 0.349] | 0 | 0 |
| D_np_single | c1 (n=0) | M2x | - | no molecules in this view (not scored) | - | - |
| D_np_single | c2 (n=100) | M2x_fe | learned | 0.2498 [0.177, 0.327] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x_fe | insurance | 0.2330 [0.160, 0.311] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x_fe | fixed | 0.2330 [0.161, 0.310] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x_fe | switch | 0.2498 [0.178, 0.326] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x_fe | blend21 | 0.2514 [0.179, 0.329] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x_fe | blend11 | 0.2597 [0.184, 0.340] | 0 | 0 |
| D_np_single | c1 (n=0) | M2x_fe | - | no molecules in this view (not scored) | - | - |
| E_np_negonly | c2 (n=100) | M2x | learned | 0.2353 [0.169, 0.308] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x | insurance | 0.2353 [0.169, 0.307] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x | fixed | 0.2353 [0.169, 0.307] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x | switch | 0.2353 [0.169, 0.307] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x | blend21 | 0.2353 [0.169, 0.307] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x | blend11 | 0.2353 [0.169, 0.308] | 1 | 99 |
| E_np_negonly | c1 (n=59) | M2x | learned | 0.5608 [0.441, 0.677] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x | insurance | 0.5608 [0.445, 0.677] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x | fixed | 0.2202 [0.143, 0.306] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x | switch | 0.5608 [0.443, 0.676] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x | blend21 | 0.5608 [0.444, 0.677] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x | blend11 | 0.5608 [0.443, 0.676] | 0 | 59 |
| E_np_negonly | c2 (n=100) | M2x_fe | learned | 0.2406 [0.177, 0.309] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x_fe | insurance | 0.2406 [0.177, 0.309] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x_fe | fixed | 0.2406 [0.177, 0.308] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x_fe | switch | 0.2406 [0.176, 0.309] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x_fe | blend21 | 0.2406 [0.177, 0.308] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x_fe | blend11 | 0.2406 [0.176, 0.310] | 1 | 99 |
| E_np_negonly | c1 (n=59) | M2x_fe | learned | 0.5669 [0.450, 0.684] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x_fe | insurance | 0.5669 [0.451, 0.679] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x_fe | fixed | 0.2209 [0.147, 0.304] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x_fe | switch | 0.5669 [0.451, 0.682] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x_fe | blend21 | 0.5669 [0.450, 0.682] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x_fe | blend11 | 0.5669 [0.450, 0.683] | 0 | 59 |
| F_np_uncovered | c2 (n=100) | M2x | learned | 0.2287 [0.159, 0.304] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x | insurance | 0.2287 [0.159, 0.306] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x | fixed | 0.2287 [0.158, 0.305] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x | switch | 0.2287 [0.159, 0.303] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x | blend21 | 0.2287 [0.158, 0.305] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x | blend11 | 0.2287 [0.159, 0.304] | 0 | 100 |
| F_np_uncovered | c1 (n=38) | M2x | learned | 0.5896 [0.449, 0.730] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x | insurance | 0.5896 [0.452, 0.729] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x | fixed | 0.3960 [0.272, 0.527] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x | switch | 0.5896 [0.451, 0.725] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x | blend21 | 0.5896 [0.448, 0.725] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x | blend11 | 0.5896 [0.450, 0.727] | 0 | 38 |
| F_np_uncovered | c2 (n=100) | M2x_fe | learned | 0.2333 [0.161, 0.310] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x_fe | insurance | 0.2333 [0.162, 0.309] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x_fe | fixed | 0.2333 [0.161, 0.308] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x_fe | switch | 0.2333 [0.161, 0.311] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x_fe | blend21 | 0.2333 [0.161, 0.309] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x_fe | blend11 | 0.2333 [0.162, 0.311] | 0 | 100 |
| F_np_uncovered | c1 (n=38) | M2x_fe | learned | 0.6304 [0.486, 0.769] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x_fe | insurance | 0.6304 [0.484, 0.769] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x_fe | fixed | 0.4317 [0.301, 0.566] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x_fe | switch | 0.6304 [0.491, 0.772] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x_fe | blend21 | 0.6304 [0.488, 0.768] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x_fe | blend11 | 0.6304 [0.487, 0.770] | 0 | 38 |
| G_tims_crosslib | c2 (n=100) | M2x | learned | 0.6360 [0.553, 0.716] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x | insurance | 0.5373 [0.457, 0.618] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x | fixed | 0.5440 [0.463, 0.626] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x | switch | 0.6031 [0.521, 0.683] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x | blend21 | 0.6371 [0.554, 0.719] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x | blend11 | 0.6266 [0.543, 0.709] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | learned | 0.5873 [0.515, 0.659] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | insurance | 0.5977 [0.518, 0.676] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | fixed | 0.5910 [0.514, 0.669] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | switch | 0.5989 [0.525, 0.671] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | blend21 | 0.5997 [0.528, 0.672] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | blend11 | 0.6150 [0.541, 0.688] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x_fe | learned | 0.6373 [0.555, 0.717] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x_fe | insurance | 0.5129 [0.433, 0.593] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x_fe | fixed | 0.5179 [0.437, 0.598] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x_fe | switch | 0.6161 [0.536, 0.696] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x_fe | blend21 | 0.6495 [0.566, 0.730] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x_fe | blend11 | 0.6302 [0.546, 0.712] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_fe | learned | 0.6043 [0.532, 0.676] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_fe | insurance | 0.5685 [0.491, 0.645] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_fe | fixed | 0.5618 [0.486, 0.638] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_fe | switch | 0.6093 [0.538, 0.681] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_fe | blend21 | 0.6035 [0.532, 0.675] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_fe | blend11 | 0.6001 [0.527, 0.672] | 0 | 8 |

## paired differences (molecule-level bootstrap, same ledger)

| set | view | comparison | mean Δ RR | 95% CI | n |
|---|---|---|---:|---|---:|
| C_np_crosslib | c2 | M2x: learned − fixed | +0.1030 | [+0.055, +0.154] | 100 |
| C_np_crosslib | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| C_np_crosslib | c2 | M2x: switch − fixed | +0.1030 | [+0.056, +0.154] | 100 |
| C_np_crosslib | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| C_np_crosslib | c2 | M2x: blend21 − learned | +0.0021 | [-0.028, +0.032] | 100 |
| C_np_crosslib | c2 | M2x: blend21 − fixed | +0.1051 | [+0.061, +0.153] | 100 |
| C_np_crosslib | c2 | M2x: blend11 − learned | -0.0188 | [-0.056, +0.019] | 100 |
| C_np_crosslib | c2 | M2x: blend11 − fixed | +0.0842 | [+0.045, +0.128] | 100 |
| C_np_crosslib | c2 | M2x_fe: learned − fixed | +0.0988 | [+0.048, +0.153] | 100 |
| C_np_crosslib | c2 | M2x_fe: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| C_np_crosslib | c2 | M2x_fe: switch − fixed | +0.0988 | [+0.047, +0.153] | 100 |
| C_np_crosslib | c2 | M2x_fe: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| C_np_crosslib | c2 | M2x_fe: blend21 − learned | -0.0192 | [-0.048, +0.007] | 100 |
| C_np_crosslib | c2 | M2x_fe: blend21 − fixed | +0.0796 | [+0.038, +0.124] | 100 |
| C_np_crosslib | c2 | M2x_fe: blend11 − learned | -0.0455 | [-0.081, -0.015] | 100 |
| C_np_crosslib | c2 | M2x_fe: blend11 − fixed | +0.0533 | [+0.018, +0.092] | 100 |
| C_np_crosslib | c2 | M2x_fe − M2x (learned) | +0.0105 | [-0.028, +0.052] | 100 |
| C_np_crosslib | c2 | M2x_fe − M2x (insurance) | +0.0147 | [-0.009, +0.044] | 100 |
| C_np_crosslib | c2 | M2x_fe − M2x (switch) | +0.0105 | [-0.027, +0.051] | 100 |
| C_np_crosslib | c2 | M2x_fe − M2x (blend21) | -0.0108 | [-0.046, +0.026] | 100 |
| C_np_crosslib | c2 | M2x_fe learned − M2x insurance | +0.1135 | [+0.060, +0.169] | 100 |
| C_np_crosslib | c2 | REGISTERED M2x_fe blend21 − M2x blend21 | -0.0108 | [-0.047, +0.026] | 100 |
| C_np_crosslib | c1 | M2x: learned − fixed | +0.2932 | [+0.209, +0.379] | 95 |
| C_np_crosslib | c1 | M2x: insurance − fixed | +0.1527 | [+0.090, +0.221] | 95 |
| C_np_crosslib | c1 | M2x: switch − fixed | +0.3037 | [+0.219, +0.392] | 95 |
| C_np_crosslib | c1 | M2x: switch − learned | +0.0105 | [+0.000, +0.026] | 95 |
| C_np_crosslib | c1 | M2x: blend21 − learned | -0.0040 | [-0.036, +0.027] | 95 |
| C_np_crosslib | c1 | M2x: blend21 − fixed | +0.2891 | [+0.215, +0.367] | 95 |
| C_np_crosslib | c1 | M2x: blend11 − learned | -0.0515 | [-0.096, -0.009] | 95 |
| C_np_crosslib | c1 | M2x: blend11 − fixed | +0.2417 | [+0.176, +0.309] | 95 |
| C_np_crosslib | c1 | M2x_fe: learned − fixed | +0.2930 | [+0.205, +0.381] | 95 |
| C_np_crosslib | c1 | M2x_fe: insurance − fixed | +0.1512 | [+0.089, +0.220] | 95 |
| C_np_crosslib | c1 | M2x_fe: switch − fixed | +0.2982 | [+0.210, +0.387] | 95 |
| C_np_crosslib | c1 | M2x_fe: switch − learned | +0.0053 | [+0.000, +0.016] | 95 |
| C_np_crosslib | c1 | M2x_fe: blend21 − learned | -0.0186 | [-0.053, +0.015] | 95 |
| C_np_crosslib | c1 | M2x_fe: blend21 − fixed | +0.2744 | [+0.198, +0.353] | 95 |
| C_np_crosslib | c1 | M2x_fe: blend11 − learned | -0.0325 | [-0.076, +0.010] | 95 |
| C_np_crosslib | c1 | M2x_fe: blend11 − fixed | +0.2605 | [+0.189, +0.336] | 95 |
| C_np_crosslib | c1 | M2x_fe − M2x (learned) | +0.0017 | [-0.024, +0.025] | 95 |
| C_np_crosslib | c1 | M2x_fe − M2x (insurance) | +0.0005 | [-0.018, +0.021] | 95 |
| C_np_crosslib | c1 | M2x_fe − M2x (switch) | -0.0035 | [-0.027, +0.017] | 95 |
| C_np_crosslib | c1 | M2x_fe − M2x (blend21) | -0.0128 | [-0.039, +0.009] | 95 |
| C_np_crosslib | c1 | M2x_fe learned − M2x insurance | +0.1423 | [+0.073, +0.216] | 95 |
| C_np_crosslib | c1 | REGISTERED M2x_fe blend21 − M2x blend21 | -0.0128 | [-0.039, +0.010] | 95 |
| D_np_single | c2 | M2x: learned − fixed | +0.0315 | [-0.012, +0.079] | 100 |
| D_np_single | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M2x: switch − fixed | +0.0315 | [-0.013, +0.079] | 100 |
| D_np_single | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M2x: blend21 − learned | -0.0014 | [-0.030, +0.025] | 100 |
| D_np_single | c2 | M2x: blend21 − fixed | +0.0301 | [+0.001, +0.065] | 100 |
| D_np_single | c2 | M2x: blend11 − learned | -0.0029 | [-0.036, +0.029] | 100 |
| D_np_single | c2 | M2x: blend11 − fixed | +0.0286 | [-0.000, +0.063] | 100 |
| D_np_single | c2 | M2x_fe: learned − fixed | +0.0168 | [-0.026, +0.060] | 100 |
| D_np_single | c2 | M2x_fe: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M2x_fe: switch − fixed | +0.0168 | [-0.026, +0.061] | 100 |
| D_np_single | c2 | M2x_fe: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M2x_fe: blend21 − learned | +0.0016 | [-0.026, +0.027] | 100 |
| D_np_single | c2 | M2x_fe: blend21 − fixed | +0.0183 | [-0.011, +0.049] | 100 |
| D_np_single | c2 | M2x_fe: blend11 − learned | +0.0099 | [-0.025, +0.045] | 100 |
| D_np_single | c2 | M2x_fe: blend11 − fixed | +0.0266 | [+0.004, +0.052] | 100 |
| D_np_single | c2 | M2x_fe − M2x (learned) | -0.0189 | [-0.055, +0.014] | 100 |
| D_np_single | c2 | M2x_fe − M2x (insurance) | -0.0041 | [-0.021, +0.008] | 100 |
| D_np_single | c2 | M2x_fe − M2x (switch) | -0.0189 | [-0.056, +0.014] | 100 |
| D_np_single | c2 | M2x_fe − M2x (blend21) | -0.0159 | [-0.049, +0.014] | 100 |
| D_np_single | c2 | M2x_fe learned − M2x insurance | +0.0127 | [-0.035, +0.062] | 100 |
| D_np_single | c2 | REGISTERED M2x_fe blend21 − M2x blend21 | -0.0159 | [-0.049, +0.014] | 100 |
| E_np_negonly | c2 | M2x: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_fe: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_fe: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_fe: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_fe: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_fe: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_fe: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_fe: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_fe: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_fe − M2x (learned) | +0.0053 | [-0.023, +0.034] | 100 |
| E_np_negonly | c2 | M2x_fe − M2x (insurance) | +0.0053 | [-0.023, +0.033] | 100 |
| E_np_negonly | c2 | M2x_fe − M2x (switch) | +0.0053 | [-0.023, +0.033] | 100 |
| E_np_negonly | c2 | M2x_fe − M2x (blend21) | +0.0053 | [-0.023, +0.033] | 100 |
| E_np_negonly | c2 | M2x_fe learned − M2x insurance | +0.0053 | [-0.024, +0.033] | 100 |
| E_np_negonly | c2 | REGISTERED M2x_fe blend21 − M2x blend21 | +0.0053 | [-0.023, +0.033] | 100 |
| E_np_negonly | c1 | M2x: learned − fixed | +0.3406 | [+0.230, +0.456] | 59 |
| E_np_negonly | c1 | M2x: insurance − fixed | +0.3406 | [+0.231, +0.452] | 59 |
| E_np_negonly | c1 | M2x: switch − fixed | +0.3406 | [+0.232, +0.454] | 59 |
| E_np_negonly | c1 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x: blend21 − fixed | +0.3406 | [+0.232, +0.454] | 59 |
| E_np_negonly | c1 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x: blend11 − fixed | +0.3406 | [+0.231, +0.454] | 59 |
| E_np_negonly | c1 | M2x_fe: learned − fixed | +0.3459 | [+0.238, +0.458] | 59 |
| E_np_negonly | c1 | M2x_fe: insurance − fixed | +0.3459 | [+0.238, +0.457] | 59 |
| E_np_negonly | c1 | M2x_fe: switch − fixed | +0.3459 | [+0.237, +0.459] | 59 |
| E_np_negonly | c1 | M2x_fe: switch − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x_fe: blend21 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x_fe: blend21 − fixed | +0.3459 | [+0.239, +0.459] | 59 |
| E_np_negonly | c1 | M2x_fe: blend11 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x_fe: blend11 − fixed | +0.3459 | [+0.238, +0.459] | 59 |
| E_np_negonly | c1 | M2x_fe − M2x (learned) | +0.0061 | [-0.030, +0.044] | 59 |
| E_np_negonly | c1 | M2x_fe − M2x (insurance) | +0.0061 | [-0.030, +0.045] | 59 |
| E_np_negonly | c1 | M2x_fe − M2x (switch) | +0.0061 | [-0.031, +0.044] | 59 |
| E_np_negonly | c1 | M2x_fe − M2x (blend21) | +0.0061 | [-0.031, +0.045] | 59 |
| E_np_negonly | c1 | M2x_fe learned − M2x insurance | +0.0061 | [-0.030, +0.044] | 59 |
| E_np_negonly | c1 | REGISTERED M2x_fe blend21 − M2x blend21 | +0.0061 | [-0.030, +0.044] | 59 |
| F_np_uncovered | c2 | M2x: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_fe: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_fe: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_fe: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_fe: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_fe: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_fe: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_fe: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_fe: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_fe − M2x (learned) | +0.0045 | [-0.031, +0.038] | 100 |
| F_np_uncovered | c2 | M2x_fe − M2x (insurance) | +0.0045 | [-0.031, +0.037] | 100 |
| F_np_uncovered | c2 | M2x_fe − M2x (switch) | +0.0045 | [-0.032, +0.038] | 100 |
| F_np_uncovered | c2 | M2x_fe − M2x (blend21) | +0.0045 | [-0.031, +0.038] | 100 |
| F_np_uncovered | c2 | M2x_fe learned − M2x insurance | +0.0045 | [-0.031, +0.038] | 100 |
| F_np_uncovered | c2 | REGISTERED M2x_fe blend21 − M2x blend21 | +0.0045 | [-0.031, +0.037] | 100 |
| F_np_uncovered | c1 | M2x: learned − fixed | +0.1936 | [+0.086, +0.317] | 38 |
| F_np_uncovered | c1 | M2x: insurance − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x: switch − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x: blend21 − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x: blend11 − fixed | +0.1936 | [+0.086, +0.312] | 38 |
| F_np_uncovered | c1 | M2x_fe: learned − fixed | +0.1986 | [+0.093, +0.315] | 38 |
| F_np_uncovered | c1 | M2x_fe: insurance − fixed | +0.1986 | [+0.092, +0.317] | 38 |
| F_np_uncovered | c1 | M2x_fe: switch − fixed | +0.1986 | [+0.095, +0.317] | 38 |
| F_np_uncovered | c1 | M2x_fe: switch − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x_fe: blend21 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x_fe: blend21 − fixed | +0.1986 | [+0.092, +0.314] | 38 |
| F_np_uncovered | c1 | M2x_fe: blend11 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x_fe: blend11 − fixed | +0.1986 | [+0.092, +0.318] | 38 |
| F_np_uncovered | c1 | M2x_fe − M2x (learned) | +0.0407 | [-0.014, +0.098] | 38 |
| F_np_uncovered | c1 | M2x_fe − M2x (insurance) | +0.0407 | [-0.013, +0.100] | 38 |
| F_np_uncovered | c1 | M2x_fe − M2x (switch) | +0.0407 | [-0.013, +0.099] | 38 |
| F_np_uncovered | c1 | M2x_fe − M2x (blend21) | +0.0407 | [-0.013, +0.098] | 38 |
| F_np_uncovered | c1 | M2x_fe learned − M2x insurance | +0.0407 | [-0.013, +0.099] | 38 |
| F_np_uncovered | c1 | REGISTERED M2x_fe blend21 − M2x blend21 | +0.0407 | [-0.013, +0.098] | 38 |
| G_tims_crosslib | c2 | M2x: learned − fixed | +0.0920 | [+0.039, +0.148] | 100 |
| G_tims_crosslib | c2 | M2x: insurance − fixed | -0.0067 | [-0.018, +0.000] | 100 |
| G_tims_crosslib | c2 | M2x: switch − fixed | +0.0591 | [+0.015, +0.107] | 100 |
| G_tims_crosslib | c2 | M2x: switch − learned | -0.0329 | [-0.066, -0.005] | 100 |
| G_tims_crosslib | c2 | M2x: blend21 − learned | +0.0011 | [-0.019, +0.022] | 100 |
| G_tims_crosslib | c2 | M2x: blend21 − fixed | +0.0931 | [+0.045, +0.145] | 100 |
| G_tims_crosslib | c2 | M2x: blend11 − learned | -0.0094 | [-0.028, +0.009] | 100 |
| G_tims_crosslib | c2 | M2x: blend11 − fixed | +0.0826 | [+0.036, +0.133] | 100 |
| G_tims_crosslib | c2 | M2x_fe: learned − fixed | +0.1195 | [+0.063, +0.178] | 100 |
| G_tims_crosslib | c2 | M2x_fe: insurance − fixed | -0.0050 | [-0.015, +0.000] | 100 |
| G_tims_crosslib | c2 | M2x_fe: switch − fixed | +0.0982 | [+0.047, +0.153] | 100 |
| G_tims_crosslib | c2 | M2x_fe: switch − learned | -0.0212 | [-0.049, +0.003] | 100 |
| G_tims_crosslib | c2 | M2x_fe: blend21 − learned | +0.0122 | [-0.007, +0.034] | 100 |
| G_tims_crosslib | c2 | M2x_fe: blend21 − fixed | +0.1316 | [+0.081, +0.186] | 100 |
| G_tims_crosslib | c2 | M2x_fe: blend11 − learned | -0.0072 | [-0.036, +0.020] | 100 |
| G_tims_crosslib | c2 | M2x_fe: blend11 − fixed | +0.1123 | [+0.065, +0.163] | 100 |
| G_tims_crosslib | c2 | M2x_fe − M2x (learned) | +0.0013 | [-0.038, +0.041] | 100 |
| G_tims_crosslib | c2 | M2x_fe − M2x (insurance) | -0.0244 | [-0.060, +0.009] | 100 |
| G_tims_crosslib | c2 | M2x_fe − M2x (switch) | +0.0130 | [-0.024, +0.050] | 100 |
| G_tims_crosslib | c2 | M2x_fe − M2x (blend21) | +0.0124 | [-0.018, +0.043] | 100 |
| G_tims_crosslib | c2 | M2x_fe learned − M2x insurance | +0.1000 | [+0.049, +0.153] | 100 |
| G_tims_crosslib | c2 | REGISTERED M2x_fe blend21 − M2x blend21 | +0.0124 | [-0.018, +0.043] | 100 |
| G_tims_crosslib | c1 | M2x: learned − fixed | -0.0037 | [-0.073, +0.068] | 100 |
| G_tims_crosslib | c1 | M2x: insurance − fixed | +0.0067 | [+0.000, +0.020] | 100 |
| G_tims_crosslib | c1 | M2x: switch − fixed | +0.0080 | [-0.064, +0.081] | 100 |
| G_tims_crosslib | c1 | M2x: switch − learned | +0.0117 | [+0.000, +0.030] | 100 |
| G_tims_crosslib | c1 | M2x: blend21 − learned | +0.0124 | [-0.022, +0.047] | 100 |
| G_tims_crosslib | c1 | M2x: blend21 − fixed | +0.0087 | [-0.049, +0.066] | 100 |
| G_tims_crosslib | c1 | M2x: blend11 − learned | +0.0277 | [-0.015, +0.071] | 100 |
| G_tims_crosslib | c1 | M2x: blend11 − fixed | +0.0240 | [-0.027, +0.077] | 100 |
| G_tims_crosslib | c1 | M2x_fe: learned − fixed | +0.0424 | [-0.029, +0.118] | 100 |
| G_tims_crosslib | c1 | M2x_fe: insurance − fixed | +0.0067 | [+0.000, +0.020] | 100 |
| G_tims_crosslib | c1 | M2x_fe: switch − fixed | +0.0474 | [-0.027, +0.121] | 100 |
| G_tims_crosslib | c1 | M2x_fe: switch − learned | +0.0050 | [+0.000, +0.015] | 100 |
| G_tims_crosslib | c1 | M2x_fe: blend21 − learned | -0.0007 | [-0.037, +0.034] | 100 |
| G_tims_crosslib | c1 | M2x_fe: blend21 − fixed | +0.0417 | [-0.016, +0.100] | 100 |
| G_tims_crosslib | c1 | M2x_fe: blend11 − learned | -0.0041 | [-0.049, +0.038] | 100 |
| G_tims_crosslib | c1 | M2x_fe: blend11 − fixed | +0.0383 | [-0.014, +0.092] | 100 |
| G_tims_crosslib | c1 | M2x_fe − M2x (learned) | +0.0170 | [-0.027, +0.062] | 100 |
| G_tims_crosslib | c1 | M2x_fe − M2x (insurance) | -0.0292 | [-0.068, +0.007] | 100 |
| G_tims_crosslib | c1 | M2x_fe − M2x (switch) | +0.0103 | [-0.033, +0.054] | 100 |
| G_tims_crosslib | c1 | M2x_fe − M2x (blend21) | +0.0039 | [-0.033, +0.041] | 100 |
| G_tims_crosslib | c1 | M2x_fe learned − M2x insurance | +0.0066 | [-0.070, +0.085] | 100 |
| G_tims_crosslib | c1 | REGISTERED M2x_fe blend21 − M2x blend21 | +0.0039 | [-0.032, +0.040] | 100 |
