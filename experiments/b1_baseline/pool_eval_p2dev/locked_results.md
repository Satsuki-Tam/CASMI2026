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
| C_np_crosslib | c2 (n=100) | M2x_pool | learned | 0.6095 [0.522, 0.696] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x_pool | insurance | 0.5069 [0.423, 0.594] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x_pool | fixed | 0.5069 [0.419, 0.592] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x_pool | switch | 0.6095 [0.523, 0.697] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x_pool | blend21 | 0.6075 [0.519, 0.695] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x_pool | blend11 | 0.5760 [0.488, 0.663] | 2 | 1 |
| C_np_crosslib | c1 (n=95) | M2x_pool | learned | 0.9074 [0.859, 0.950] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x_pool | insurance | 0.7752 [0.699, 0.847] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x_pool | fixed | 0.6225 [0.537, 0.708] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x_pool | switch | 0.9179 [0.871, 0.960] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x_pool | blend21 | 0.9070 [0.856, 0.953] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x_pool | blend11 | 0.8640 [0.805, 0.918] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | learned | 0.2687 [0.190, 0.349] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | insurance | 0.2372 [0.164, 0.316] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | fixed | 0.2372 [0.164, 0.316] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | switch | 0.2687 [0.192, 0.351] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | blend21 | 0.2673 [0.190, 0.350] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | blend11 | 0.2658 [0.188, 0.349] | 0 | 0 |
| D_np_single | c1 (n=0) | M2x | - | no molecules in this view (not scored) | - | - |
| D_np_single | c2 (n=100) | M2x_pool | learned | 0.2695 [0.190, 0.352] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x_pool | insurance | 0.2363 [0.162, 0.316] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x_pool | fixed | 0.2363 [0.163, 0.316] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x_pool | switch | 0.2695 [0.193, 0.350] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x_pool | blend21 | 0.2585 [0.183, 0.339] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x_pool | blend11 | 0.2626 [0.187, 0.344] | 0 | 0 |
| D_np_single | c1 (n=0) | M2x_pool | - | no molecules in this view (not scored) | - | - |
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
| E_np_negonly | c2 (n=100) | M2x_pool | learned | 0.2341 [0.168, 0.304] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x_pool | insurance | 0.2341 [0.169, 0.307] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x_pool | fixed | 0.2341 [0.167, 0.304] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x_pool | switch | 0.2341 [0.166, 0.305] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x_pool | blend21 | 0.2341 [0.167, 0.305] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x_pool | blend11 | 0.2341 [0.167, 0.306] | 1 | 99 |
| E_np_negonly | c1 (n=59) | M2x_pool | learned | 0.5600 [0.442, 0.677] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x_pool | insurance | 0.5600 [0.442, 0.675] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x_pool | fixed | 0.2180 [0.140, 0.305] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x_pool | switch | 0.5600 [0.443, 0.678] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x_pool | blend21 | 0.5600 [0.443, 0.676] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x_pool | blend11 | 0.5600 [0.442, 0.677] | 0 | 59 |
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
| F_np_uncovered | c2 (n=100) | M2x_pool | learned | 0.2271 [0.156, 0.302] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x_pool | insurance | 0.2271 [0.156, 0.302] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x_pool | fixed | 0.2271 [0.158, 0.302] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x_pool | switch | 0.2271 [0.157, 0.304] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x_pool | blend21 | 0.2271 [0.156, 0.303] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x_pool | blend11 | 0.2271 [0.157, 0.303] | 0 | 100 |
| F_np_uncovered | c1 (n=38) | M2x_pool | learned | 0.5857 [0.446, 0.723] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x_pool | insurance | 0.5857 [0.444, 0.724] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x_pool | fixed | 0.3921 [0.268, 0.522] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x_pool | switch | 0.5857 [0.448, 0.725] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x_pool | blend21 | 0.5857 [0.445, 0.721] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x_pool | blend11 | 0.5857 [0.444, 0.726] | 0 | 38 |
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
| G_tims_crosslib | c2 (n=100) | M2x_pool | learned | 0.6284 [0.545, 0.710] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x_pool | insurance | 0.5357 [0.454, 0.617] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x_pool | fixed | 0.5423 [0.459, 0.626] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x_pool | switch | 0.6009 [0.521, 0.682] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x_pool | blend21 | 0.6161 [0.533, 0.697] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x_pool | blend11 | 0.6120 [0.529, 0.693] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_pool | learned | 0.5462 [0.475, 0.617] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_pool | insurance | 0.5958 [0.518, 0.675] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_pool | fixed | 0.5892 [0.512, 0.667] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_pool | switch | 0.5587 [0.487, 0.630] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_pool | blend21 | 0.5601 [0.490, 0.630] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x_pool | blend11 | 0.5831 [0.510, 0.655] | 0 | 8 |

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
| C_np_crosslib | c2 | M2x_pool: learned − fixed | +0.1026 | [+0.051, +0.157] | 100 |
| C_np_crosslib | c2 | M2x_pool: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| C_np_crosslib | c2 | M2x_pool: switch − fixed | +0.1026 | [+0.051, +0.156] | 100 |
| C_np_crosslib | c2 | M2x_pool: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| C_np_crosslib | c2 | M2x_pool: blend21 − learned | -0.0019 | [-0.030, +0.027] | 100 |
| C_np_crosslib | c2 | M2x_pool: blend21 − fixed | +0.1007 | [+0.056, +0.148] | 100 |
| C_np_crosslib | c2 | M2x_pool: blend11 − learned | -0.0334 | [-0.071, +0.002] | 100 |
| C_np_crosslib | c2 | M2x_pool: blend11 − fixed | +0.0692 | [+0.031, +0.111] | 100 |
| C_np_crosslib | c2 | M2x_pool − M2x (learned) | -0.0005 | [-0.016, +0.017] | 100 |
| C_np_crosslib | c2 | M2x_pool − M2x (insurance) | -0.0001 | [-0.005, +0.005] | 100 |
| C_np_crosslib | c2 | M2x_pool − M2x (switch) | -0.0005 | [-0.016, +0.017] | 100 |
| C_np_crosslib | c2 | M2x_pool − M2x (blend21) | -0.0045 | [-0.020, +0.011] | 100 |
| C_np_crosslib | c2 | M2x_pool learned − M2x insurance | +0.1025 | [+0.051, +0.156] | 100 |
| C_np_crosslib | c2 | REGISTERED M2x_pool blend21 − M2x blend21 | -0.0045 | [-0.020, +0.011] | 100 |
| C_np_crosslib | c1 | M2x: learned − fixed | +0.2932 | [+0.209, +0.379] | 95 |
| C_np_crosslib | c1 | M2x: insurance − fixed | +0.1527 | [+0.090, +0.221] | 95 |
| C_np_crosslib | c1 | M2x: switch − fixed | +0.3037 | [+0.219, +0.392] | 95 |
| C_np_crosslib | c1 | M2x: switch − learned | +0.0105 | [+0.000, +0.026] | 95 |
| C_np_crosslib | c1 | M2x: blend21 − learned | -0.0040 | [-0.036, +0.027] | 95 |
| C_np_crosslib | c1 | M2x: blend21 − fixed | +0.2891 | [+0.215, +0.367] | 95 |
| C_np_crosslib | c1 | M2x: blend11 − learned | -0.0515 | [-0.096, -0.009] | 95 |
| C_np_crosslib | c1 | M2x: blend11 − fixed | +0.2417 | [+0.176, +0.309] | 95 |
| C_np_crosslib | c1 | M2x_pool: learned − fixed | +0.2849 | [+0.199, +0.373] | 95 |
| C_np_crosslib | c1 | M2x_pool: insurance − fixed | +0.1527 | [+0.090, +0.222] | 95 |
| C_np_crosslib | c1 | M2x_pool: switch − fixed | +0.2954 | [+0.206, +0.384] | 95 |
| C_np_crosslib | c1 | M2x_pool: switch − learned | +0.0105 | [+0.000, +0.026] | 95 |
| C_np_crosslib | c1 | M2x_pool: blend21 − learned | -0.0004 | [-0.036, +0.035] | 95 |
| C_np_crosslib | c1 | M2x_pool: blend21 − fixed | +0.2845 | [+0.211, +0.361] | 95 |
| C_np_crosslib | c1 | M2x_pool: blend11 − learned | -0.0433 | [-0.092, +0.003] | 95 |
| C_np_crosslib | c1 | M2x_pool: blend11 − fixed | +0.2416 | [+0.177, +0.310] | 95 |
| C_np_crosslib | c1 | M2x_pool − M2x (learned) | -0.0083 | [-0.022, +0.000] | 95 |
| C_np_crosslib | c1 | M2x_pool − M2x (insurance) | +0.0000 | [-0.005, +0.005] | 95 |
| C_np_crosslib | c1 | M2x_pool − M2x (switch) | -0.0083 | [-0.022, +0.000] | 95 |
| C_np_crosslib | c1 | M2x_pool − M2x (blend21) | -0.0047 | [-0.016, +0.002] | 95 |
| C_np_crosslib | c1 | M2x_pool learned − M2x insurance | +0.1322 | [+0.060, +0.209] | 95 |
| C_np_crosslib | c1 | REGISTERED M2x_pool blend21 − M2x blend21 | -0.0047 | [-0.016, +0.002] | 95 |
| D_np_single | c2 | M2x: learned − fixed | +0.0315 | [-0.012, +0.079] | 100 |
| D_np_single | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M2x: switch − fixed | +0.0315 | [-0.013, +0.079] | 100 |
| D_np_single | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M2x: blend21 − learned | -0.0014 | [-0.030, +0.025] | 100 |
| D_np_single | c2 | M2x: blend21 − fixed | +0.0301 | [+0.001, +0.065] | 100 |
| D_np_single | c2 | M2x: blend11 − learned | -0.0029 | [-0.036, +0.029] | 100 |
| D_np_single | c2 | M2x: blend11 − fixed | +0.0286 | [-0.000, +0.063] | 100 |
| D_np_single | c2 | M2x_pool: learned − fixed | +0.0331 | [-0.009, +0.078] | 100 |
| D_np_single | c2 | M2x_pool: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M2x_pool: switch − fixed | +0.0331 | [-0.009, +0.079] | 100 |
| D_np_single | c2 | M2x_pool: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M2x_pool: blend21 − learned | -0.0110 | [-0.038, +0.012] | 100 |
| D_np_single | c2 | M2x_pool: blend21 − fixed | +0.0222 | [-0.007, +0.055] | 100 |
| D_np_single | c2 | M2x_pool: blend11 − learned | -0.0068 | [-0.040, +0.024] | 100 |
| D_np_single | c2 | M2x_pool: blend11 − fixed | +0.0263 | [+0.000, +0.056] | 100 |
| D_np_single | c2 | M2x_pool − M2x (learned) | +0.0008 | [-0.014, +0.016] | 100 |
| D_np_single | c2 | M2x_pool − M2x (insurance) | -0.0008 | [-0.002, +0.000] | 100 |
| D_np_single | c2 | M2x_pool − M2x (switch) | +0.0008 | [-0.014, +0.016] | 100 |
| D_np_single | c2 | M2x_pool − M2x (blend21) | -0.0087 | [-0.025, +0.003] | 100 |
| D_np_single | c2 | M2x_pool learned − M2x insurance | +0.0323 | [-0.009, +0.077] | 100 |
| D_np_single | c2 | REGISTERED M2x_pool blend21 − M2x blend21 | -0.0087 | [-0.025, +0.003] | 100 |
| E_np_negonly | c2 | M2x: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool − M2x (learned) | -0.0012 | [-0.003, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool − M2x (insurance) | -0.0012 | [-0.003, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool − M2x (switch) | -0.0012 | [-0.003, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool − M2x (blend21) | -0.0012 | [-0.003, +0.000] | 100 |
| E_np_negonly | c2 | M2x_pool learned − M2x insurance | -0.0012 | [-0.003, +0.000] | 100 |
| E_np_negonly | c2 | REGISTERED M2x_pool blend21 − M2x blend21 | -0.0012 | [-0.003, +0.000] | 100 |
| E_np_negonly | c1 | M2x: learned − fixed | +0.3406 | [+0.230, +0.456] | 59 |
| E_np_negonly | c1 | M2x: insurance − fixed | +0.3406 | [+0.231, +0.452] | 59 |
| E_np_negonly | c1 | M2x: switch − fixed | +0.3406 | [+0.232, +0.454] | 59 |
| E_np_negonly | c1 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x: blend21 − fixed | +0.3406 | [+0.232, +0.454] | 59 |
| E_np_negonly | c1 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x: blend11 − fixed | +0.3406 | [+0.231, +0.454] | 59 |
| E_np_negonly | c1 | M2x_pool: learned − fixed | +0.3420 | [+0.233, +0.455] | 59 |
| E_np_negonly | c1 | M2x_pool: insurance − fixed | +0.3420 | [+0.233, +0.454] | 59 |
| E_np_negonly | c1 | M2x_pool: switch − fixed | +0.3420 | [+0.232, +0.456] | 59 |
| E_np_negonly | c1 | M2x_pool: switch − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x_pool: blend21 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x_pool: blend21 − fixed | +0.3420 | [+0.233, +0.457] | 59 |
| E_np_negonly | c1 | M2x_pool: blend11 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x_pool: blend11 − fixed | +0.3420 | [+0.233, +0.457] | 59 |
| E_np_negonly | c1 | M2x_pool − M2x (learned) | -0.0007 | [-0.002, +0.000] | 59 |
| E_np_negonly | c1 | M2x_pool − M2x (insurance) | -0.0007 | [-0.002, +0.000] | 59 |
| E_np_negonly | c1 | M2x_pool − M2x (switch) | -0.0007 | [-0.002, +0.000] | 59 |
| E_np_negonly | c1 | M2x_pool − M2x (blend21) | -0.0007 | [-0.002, +0.000] | 59 |
| E_np_negonly | c1 | M2x_pool learned − M2x insurance | -0.0007 | [-0.002, +0.000] | 59 |
| E_np_negonly | c1 | REGISTERED M2x_pool blend21 − M2x blend21 | -0.0007 | [-0.002, +0.000] | 59 |
| F_np_uncovered | c2 | M2x: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool − M2x (learned) | -0.0017 | [-0.005, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool − M2x (insurance) | -0.0017 | [-0.005, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool − M2x (switch) | -0.0017 | [-0.005, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool − M2x (blend21) | -0.0017 | [-0.005, +0.000] | 100 |
| F_np_uncovered | c2 | M2x_pool learned − M2x insurance | -0.0017 | [-0.005, +0.000] | 100 |
| F_np_uncovered | c2 | REGISTERED M2x_pool blend21 − M2x blend21 | -0.0017 | [-0.005, +0.000] | 100 |
| F_np_uncovered | c1 | M2x: learned − fixed | +0.1936 | [+0.086, +0.317] | 38 |
| F_np_uncovered | c1 | M2x: insurance − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x: switch − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x: blend21 − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x: blend11 − fixed | +0.1936 | [+0.086, +0.312] | 38 |
| F_np_uncovered | c1 | M2x_pool: learned − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x_pool: insurance − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x_pool: switch − fixed | +0.1936 | [+0.088, +0.315] | 38 |
| F_np_uncovered | c1 | M2x_pool: switch − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x_pool: blend21 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x_pool: blend21 − fixed | +0.1936 | [+0.086, +0.312] | 38 |
| F_np_uncovered | c1 | M2x_pool: blend11 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x_pool: blend11 − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x_pool − M2x (learned) | -0.0040 | [-0.013, +0.001] | 38 |
| F_np_uncovered | c1 | M2x_pool − M2x (insurance) | -0.0040 | [-0.013, +0.001] | 38 |
| F_np_uncovered | c1 | M2x_pool − M2x (switch) | -0.0040 | [-0.013, +0.001] | 38 |
| F_np_uncovered | c1 | M2x_pool − M2x (blend21) | -0.0040 | [-0.013, +0.001] | 38 |
| F_np_uncovered | c1 | M2x_pool learned − M2x insurance | -0.0040 | [-0.013, +0.001] | 38 |
| F_np_uncovered | c1 | REGISTERED M2x_pool blend21 − M2x blend21 | -0.0040 | [-0.013, +0.001] | 38 |
| G_tims_crosslib | c2 | M2x: learned − fixed | +0.0920 | [+0.039, +0.148] | 100 |
| G_tims_crosslib | c2 | M2x: insurance − fixed | -0.0067 | [-0.018, +0.000] | 100 |
| G_tims_crosslib | c2 | M2x: switch − fixed | +0.0591 | [+0.015, +0.107] | 100 |
| G_tims_crosslib | c2 | M2x: switch − learned | -0.0329 | [-0.066, -0.005] | 100 |
| G_tims_crosslib | c2 | M2x: blend21 − learned | +0.0011 | [-0.019, +0.022] | 100 |
| G_tims_crosslib | c2 | M2x: blend21 − fixed | +0.0931 | [+0.045, +0.145] | 100 |
| G_tims_crosslib | c2 | M2x: blend11 − learned | -0.0094 | [-0.028, +0.009] | 100 |
| G_tims_crosslib | c2 | M2x: blend11 − fixed | +0.0826 | [+0.036, +0.133] | 100 |
| G_tims_crosslib | c2 | M2x_pool: learned − fixed | +0.0861 | [+0.031, +0.144] | 100 |
| G_tims_crosslib | c2 | M2x_pool: insurance − fixed | -0.0067 | [-0.018, +0.000] | 100 |
| G_tims_crosslib | c2 | M2x_pool: switch − fixed | +0.0586 | [+0.009, +0.110] | 100 |
| G_tims_crosslib | c2 | M2x_pool: switch − learned | -0.0275 | [-0.058, -0.001] | 100 |
| G_tims_crosslib | c2 | M2x_pool: blend21 − learned | -0.0123 | [-0.039, +0.014] | 100 |
| G_tims_crosslib | c2 | M2x_pool: blend21 − fixed | +0.0738 | [+0.028, +0.121] | 100 |
| G_tims_crosslib | c2 | M2x_pool: blend11 − learned | -0.0164 | [-0.045, +0.012] | 100 |
| G_tims_crosslib | c2 | M2x_pool: blend11 − fixed | +0.0697 | [+0.025, +0.116] | 100 |
| G_tims_crosslib | c2 | M2x_pool − M2x (learned) | -0.0076 | [-0.036, +0.019] | 100 |
| G_tims_crosslib | c2 | M2x_pool − M2x (insurance) | -0.0017 | [-0.005, +0.000] | 100 |
| G_tims_crosslib | c2 | M2x_pool − M2x (switch) | -0.0022 | [-0.029, +0.024] | 100 |
| G_tims_crosslib | c2 | M2x_pool − M2x (blend21) | -0.0210 | [-0.045, +0.000] | 100 |
| G_tims_crosslib | c2 | M2x_pool learned − M2x insurance | +0.0911 | [+0.037, +0.148] | 100 |
| G_tims_crosslib | c2 | REGISTERED M2x_pool blend21 − M2x blend21 | -0.0210 | [-0.045, +0.000] | 100 |
| G_tims_crosslib | c1 | M2x: learned − fixed | -0.0037 | [-0.073, +0.068] | 100 |
| G_tims_crosslib | c1 | M2x: insurance − fixed | +0.0067 | [+0.000, +0.020] | 100 |
| G_tims_crosslib | c1 | M2x: switch − fixed | +0.0080 | [-0.064, +0.081] | 100 |
| G_tims_crosslib | c1 | M2x: switch − learned | +0.0117 | [+0.000, +0.030] | 100 |
| G_tims_crosslib | c1 | M2x: blend21 − learned | +0.0124 | [-0.022, +0.047] | 100 |
| G_tims_crosslib | c1 | M2x: blend21 − fixed | +0.0087 | [-0.049, +0.066] | 100 |
| G_tims_crosslib | c1 | M2x: blend11 − learned | +0.0277 | [-0.015, +0.071] | 100 |
| G_tims_crosslib | c1 | M2x: blend11 − fixed | +0.0240 | [-0.027, +0.077] | 100 |
| G_tims_crosslib | c1 | M2x_pool: learned − fixed | -0.0430 | [-0.116, +0.032] | 100 |
| G_tims_crosslib | c1 | M2x_pool: insurance − fixed | +0.0067 | [+0.000, +0.020] | 100 |
| G_tims_crosslib | c1 | M2x_pool: switch − fixed | -0.0305 | [-0.105, +0.043] | 100 |
| G_tims_crosslib | c1 | M2x_pool: switch − learned | +0.0125 | [+0.000, +0.033] | 100 |
| G_tims_crosslib | c1 | M2x_pool: blend21 − learned | +0.0139 | [-0.021, +0.049] | 100 |
| G_tims_crosslib | c1 | M2x_pool: blend21 − fixed | -0.0290 | [-0.089, +0.030] | 100 |
| G_tims_crosslib | c1 | M2x_pool: blend11 − learned | +0.0369 | [-0.009, +0.081] | 100 |
| G_tims_crosslib | c1 | M2x_pool: blend11 − fixed | -0.0061 | [-0.059, +0.046] | 100 |
| G_tims_crosslib | c1 | M2x_pool − M2x (learned) | -0.0411 | [-0.068, -0.016] | 100 |
| G_tims_crosslib | c1 | M2x_pool − M2x (insurance) | -0.0018 | [-0.005, +0.000] | 100 |
| G_tims_crosslib | c1 | M2x_pool − M2x (switch) | -0.0403 | [-0.068, -0.016] | 100 |
| G_tims_crosslib | c1 | M2x_pool − M2x (blend21) | -0.0395 | [-0.069, -0.013] | 100 |
| G_tims_crosslib | c1 | M2x_pool learned − M2x insurance | -0.0515 | [-0.125, +0.023] | 100 |
| G_tims_crosslib | c1 | REGISTERED M2x_pool blend21 − M2x blend21 | -0.0395 | [-0.069, -0.013] | 100 |
