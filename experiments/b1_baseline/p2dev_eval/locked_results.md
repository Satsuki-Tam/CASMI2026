# B1 locked evaluation (official scorer replica, frozen ledger)

| set | view | candidate | output | official MRR@25 [95% CI] | no candidates | GL fallback |
|---|---|---|---|---|---|---|
| C_np_crosslib | c2 (n=100) | M1 | learned | 0.6223 [0.537, 0.708] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M1 | insurance | 0.5353 [0.447, 0.622] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M1 | fixed | 0.5353 [0.448, 0.622] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M1 | switch | 0.6223 [0.536, 0.707] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M1 | blend21 | 0.6150 [0.529, 0.700] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M1 | blend11 | 0.5949 [0.506, 0.682] | 2 | 1 |
| C_np_crosslib | c1 (n=95) | M1 | learned | 0.8739 [0.821, 0.922] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M1 | insurance | 0.7926 [0.718, 0.862] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M1 | fixed | 0.6537 [0.572, 0.735] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M1 | switch | 0.8897 [0.838, 0.936] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M1 | blend21 | 0.8665 [0.811, 0.918] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M1 | blend11 | 0.8222 [0.757, 0.884] | 0 | 0 |
| C_np_crosslib | c2 (n=100) | M2x | learned | 0.6100 [0.523, 0.694] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x | insurance | 0.5069 [0.423, 0.595] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x | fixed | 0.5069 [0.419, 0.592] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x | switch | 0.6100 [0.525, 0.695] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x | blend21 | 0.6120 [0.524, 0.699] | 2 | 1 |
| C_np_crosslib | c2 (n=100) | M2x | blend11 | 0.5911 [0.502, 0.679] | 2 | 1 |
| C_np_crosslib | c1 (n=95) | M2x | learned | 0.9157 [0.870, 0.956] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x | insurance | 0.7752 [0.699, 0.848] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x | fixed | 0.6226 [0.537, 0.708] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x | switch | 0.9262 [0.882, 0.966] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x | blend21 | 0.9117 [0.861, 0.957] | 0 | 0 |
| C_np_crosslib | c1 (n=95) | M2x | blend11 | 0.8642 [0.805, 0.918] | 0 | 0 |
| D_np_single | c2 (n=100) | M1 | learned | 0.2830 [0.201, 0.367] | 0 | 0 |
| D_np_single | c2 (n=100) | M1 | insurance | 0.2498 [0.173, 0.331] | 0 | 0 |
| D_np_single | c2 (n=100) | M1 | fixed | 0.2498 [0.173, 0.332] | 0 | 0 |
| D_np_single | c2 (n=100) | M1 | switch | 0.2830 [0.202, 0.368] | 0 | 0 |
| D_np_single | c2 (n=100) | M1 | blend21 | 0.2896 [0.207, 0.376] | 0 | 0 |
| D_np_single | c2 (n=100) | M1 | blend11 | 0.2764 [0.197, 0.360] | 0 | 0 |
| D_np_single | c1 (n=0) | M1 | - | no molecules in this view (not scored) | - | - |
| D_np_single | c2 (n=100) | M2x | learned | 0.2687 [0.190, 0.350] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | insurance | 0.2372 [0.163, 0.317] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | fixed | 0.2372 [0.164, 0.317] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | switch | 0.2687 [0.191, 0.350] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | blend21 | 0.2673 [0.189, 0.349] | 0 | 0 |
| D_np_single | c2 (n=100) | M2x | blend11 | 0.2658 [0.188, 0.348] | 0 | 0 |
| D_np_single | c1 (n=0) | M2x | - | no molecules in this view (not scored) | - | - |
| E_np_negonly | c2 (n=100) | M1 | learned | 0.2899 [0.219, 0.367] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M1 | insurance | 0.2899 [0.219, 0.363] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M1 | fixed | 0.2899 [0.220, 0.365] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M1 | switch | 0.2899 [0.218, 0.365] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M1 | blend21 | 0.2899 [0.219, 0.366] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M1 | blend11 | 0.2899 [0.219, 0.364] | 1 | 99 |
| E_np_negonly | c1 (n=59) | M1 | learned | 0.5945 [0.480, 0.707] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M1 | insurance | 0.5945 [0.481, 0.705] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M1 | fixed | 0.3036 [0.214, 0.402] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M1 | switch | 0.5945 [0.480, 0.706] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M1 | blend21 | 0.5945 [0.480, 0.706] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M1 | blend11 | 0.5945 [0.480, 0.706] | 0 | 59 |
| E_np_negonly | c2 (n=100) | M2x | learned | 0.2353 [0.169, 0.305] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x | insurance | 0.2353 [0.170, 0.308] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x | fixed | 0.2353 [0.168, 0.305] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x | switch | 0.2353 [0.167, 0.306] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x | blend21 | 0.2353 [0.168, 0.307] | 1 | 99 |
| E_np_negonly | c2 (n=100) | M2x | blend11 | 0.2353 [0.168, 0.307] | 1 | 99 |
| E_np_negonly | c1 (n=59) | M2x | learned | 0.5608 [0.443, 0.678] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x | insurance | 0.5608 [0.443, 0.675] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x | fixed | 0.2202 [0.143, 0.307] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x | switch | 0.5608 [0.444, 0.678] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x | blend21 | 0.5608 [0.444, 0.677] | 0 | 59 |
| E_np_negonly | c1 (n=59) | M2x | blend11 | 0.5608 [0.443, 0.677] | 0 | 59 |
| F_np_uncovered | c2 (n=100) | M1 | learned | 0.2476 [0.175, 0.325] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M1 | insurance | 0.2476 [0.175, 0.326] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M1 | fixed | 0.2476 [0.174, 0.326] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M1 | switch | 0.2476 [0.175, 0.325] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M1 | blend21 | 0.2476 [0.174, 0.327] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M1 | blend11 | 0.2476 [0.174, 0.325] | 0 | 100 |
| F_np_uncovered | c1 (n=38) | M1 | learned | 0.6178 [0.475, 0.758] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M1 | insurance | 0.6178 [0.476, 0.758] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M1 | fixed | 0.4480 [0.315, 0.589] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M1 | switch | 0.6178 [0.476, 0.756] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M1 | blend21 | 0.6178 [0.473, 0.754] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M1 | blend11 | 0.6178 [0.474, 0.757] | 0 | 38 |
| F_np_uncovered | c2 (n=100) | M2x | learned | 0.2287 [0.158, 0.304] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x | insurance | 0.2287 [0.158, 0.304] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x | fixed | 0.2287 [0.159, 0.304] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x | switch | 0.2287 [0.158, 0.305] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x | blend21 | 0.2287 [0.158, 0.305] | 0 | 100 |
| F_np_uncovered | c2 (n=100) | M2x | blend11 | 0.2287 [0.158, 0.305] | 0 | 100 |
| F_np_uncovered | c1 (n=38) | M2x | learned | 0.5896 [0.450, 0.727] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x | insurance | 0.5896 [0.448, 0.728] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x | fixed | 0.3960 [0.272, 0.525] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x | switch | 0.5896 [0.452, 0.728] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x | blend21 | 0.5896 [0.450, 0.724] | 0 | 38 |
| F_np_uncovered | c1 (n=38) | M2x | blend11 | 0.5896 [0.448, 0.729] | 0 | 38 |
| G_tims_crosslib | c2 (n=100) | M1 | learned | 0.6731 [0.591, 0.751] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M1 | insurance | 0.5858 [0.504, 0.666] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M1 | fixed | 0.5925 [0.510, 0.674] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M1 | switch | 0.6437 [0.561, 0.723] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M1 | blend21 | 0.6629 [0.581, 0.744] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M1 | blend11 | 0.6647 [0.581, 0.745] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M1 | learned | 0.6210 [0.551, 0.692] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M1 | insurance | 0.6589 [0.583, 0.733] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M1 | fixed | 0.6522 [0.577, 0.727] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M1 | switch | 0.6327 [0.561, 0.704] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M1 | blend21 | 0.6227 [0.553, 0.692] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M1 | blend11 | 0.6347 [0.562, 0.706] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x | learned | 0.6360 [0.553, 0.717] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x | insurance | 0.5373 [0.457, 0.619] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x | fixed | 0.5440 [0.461, 0.627] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x | switch | 0.6031 [0.523, 0.683] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x | blend21 | 0.6371 [0.554, 0.718] | 0 | 8 |
| G_tims_crosslib | c2 (n=100) | M2x | blend11 | 0.6266 [0.543, 0.709] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | learned | 0.5873 [0.515, 0.658] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | insurance | 0.5977 [0.520, 0.676] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | fixed | 0.5910 [0.514, 0.668] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | switch | 0.5989 [0.527, 0.670] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | blend21 | 0.5997 [0.527, 0.672] | 0 | 8 |
| G_tims_crosslib | c1 (n=100) | M2x | blend11 | 0.6150 [0.541, 0.687] | 0 | 8 |

## paired differences (molecule-level bootstrap, same ledger)

| set | view | comparison | mean Δ RR | 95% CI | n |
|---|---|---|---:|---|---:|
| C_np_crosslib | c2 | M1: learned − fixed | +0.0870 | [+0.038, +0.139] | 100 |
| C_np_crosslib | c2 | M1: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| C_np_crosslib | c2 | M1: switch − fixed | +0.0870 | [+0.037, +0.139] | 100 |
| C_np_crosslib | c2 | M1: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| C_np_crosslib | c2 | M1: blend21 − learned | -0.0073 | [-0.038, +0.021] | 100 |
| C_np_crosslib | c2 | M1: blend21 − fixed | +0.0797 | [+0.046, +0.116] | 100 |
| C_np_crosslib | c2 | M1: blend11 − learned | -0.0274 | [-0.066, +0.008] | 100 |
| C_np_crosslib | c2 | M1: blend11 − fixed | +0.0596 | [+0.032, +0.091] | 100 |
| C_np_crosslib | c2 | M2x: learned − fixed | +0.1030 | [+0.055, +0.153] | 100 |
| C_np_crosslib | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| C_np_crosslib | c2 | M2x: switch − fixed | +0.1030 | [+0.054, +0.153] | 100 |
| C_np_crosslib | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| C_np_crosslib | c2 | M2x: blend21 − learned | +0.0021 | [-0.027, +0.032] | 100 |
| C_np_crosslib | c2 | M2x: blend21 − fixed | +0.1051 | [+0.061, +0.153] | 100 |
| C_np_crosslib | c2 | M2x: blend11 − learned | -0.0188 | [-0.057, +0.018] | 100 |
| C_np_crosslib | c2 | M2x: blend11 − fixed | +0.0842 | [+0.046, +0.128] | 100 |
| C_np_crosslib | c2 | M2x − M1 (learned) | -0.0123 | [-0.049, +0.021] | 100 |
| C_np_crosslib | c2 | M2x − M1 (insurance) | -0.0284 | [-0.051, -0.009] | 100 |
| C_np_crosslib | c2 | M2x − M1 (switch) | -0.0123 | [-0.050, +0.022] | 100 |
| C_np_crosslib | c2 | M2x − M1 (blend21) | -0.0029 | [-0.036, +0.030] | 100 |
| C_np_crosslib | c2 | M2x learned − M1 insurance | +0.0747 | [+0.030, +0.121] | 100 |
| C_np_crosslib | c2 | REGISTERED M2x blend21 − M1 learned | -0.0102 | [-0.056, +0.034] | 100 |
| C_np_crosslib | c1 | M1: learned − fixed | +0.2201 | [+0.137, +0.305] | 95 |
| C_np_crosslib | c1 | M1: insurance − fixed | +0.1389 | [+0.078, +0.205] | 95 |
| C_np_crosslib | c1 | M1: switch − fixed | +0.2359 | [+0.153, +0.320] | 95 |
| C_np_crosslib | c1 | M1: switch − learned | +0.0158 | [+0.000, +0.037] | 95 |
| C_np_crosslib | c1 | M1: blend21 − learned | -0.0074 | [-0.042, +0.027] | 95 |
| C_np_crosslib | c1 | M1: blend21 − fixed | +0.2128 | [+0.141, +0.286] | 95 |
| C_np_crosslib | c1 | M1: blend11 − learned | -0.0517 | [-0.105, -0.002] | 95 |
| C_np_crosslib | c1 | M1: blend11 − fixed | +0.1685 | [+0.110, +0.230] | 95 |
| C_np_crosslib | c1 | M2x: learned − fixed | +0.2932 | [+0.210, +0.379] | 95 |
| C_np_crosslib | c1 | M2x: insurance − fixed | +0.1527 | [+0.090, +0.222] | 95 |
| C_np_crosslib | c1 | M2x: switch − fixed | +0.3037 | [+0.217, +0.391] | 95 |
| C_np_crosslib | c1 | M2x: switch − learned | +0.0105 | [+0.000, +0.026] | 95 |
| C_np_crosslib | c1 | M2x: blend21 − learned | -0.0040 | [-0.036, +0.027] | 95 |
| C_np_crosslib | c1 | M2x: blend21 − fixed | +0.2891 | [+0.215, +0.366] | 95 |
| C_np_crosslib | c1 | M2x: blend11 − learned | -0.0515 | [-0.097, -0.008] | 95 |
| C_np_crosslib | c1 | M2x: blend11 − fixed | +0.2417 | [+0.177, +0.310] | 95 |
| C_np_crosslib | c1 | M2x − M1 (learned) | +0.0418 | [+0.008, +0.080] | 95 |
| C_np_crosslib | c1 | M2x − M1 (insurance) | -0.0174 | [-0.036, -0.003] | 95 |
| C_np_crosslib | c1 | M2x − M1 (switch) | +0.0366 | [+0.004, +0.074] | 95 |
| C_np_crosslib | c1 | M2x − M1 (blend21) | +0.0452 | [+0.007, +0.089] | 95 |
| C_np_crosslib | c1 | M2x learned − M1 insurance | +0.1231 | [+0.055, +0.196] | 95 |
| C_np_crosslib | c1 | REGISTERED M2x blend21 − M1 learned | +0.0378 | [-0.000, +0.080] | 95 |
| D_np_single | c2 | M1: learned − fixed | +0.0331 | [+0.000, +0.071] | 100 |
| D_np_single | c2 | M1: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M1: switch − fixed | +0.0331 | [-0.001, +0.071] | 100 |
| D_np_single | c2 | M1: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M1: blend21 − learned | +0.0066 | [-0.003, +0.020] | 100 |
| D_np_single | c2 | M1: blend21 − fixed | +0.0397 | [+0.009, +0.075] | 100 |
| D_np_single | c2 | M1: blend11 − learned | -0.0066 | [-0.027, +0.012] | 100 |
| D_np_single | c2 | M1: blend11 − fixed | +0.0266 | [+0.003, +0.054] | 100 |
| D_np_single | c2 | M2x: learned − fixed | +0.0315 | [-0.012, +0.077] | 100 |
| D_np_single | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M2x: switch − fixed | +0.0315 | [-0.012, +0.078] | 100 |
| D_np_single | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| D_np_single | c2 | M2x: blend21 − learned | -0.0014 | [-0.030, +0.025] | 100 |
| D_np_single | c2 | M2x: blend21 − fixed | +0.0301 | [+0.001, +0.065] | 100 |
| D_np_single | c2 | M2x: blend11 − learned | -0.0029 | [-0.036, +0.029] | 100 |
| D_np_single | c2 | M2x: blend11 − fixed | +0.0286 | [+0.000, +0.062] | 100 |
| D_np_single | c2 | M2x − M1 (learned) | -0.0143 | [-0.043, +0.011] | 100 |
| D_np_single | c2 | M2x − M1 (insurance) | -0.0127 | [-0.046, +0.022] | 100 |
| D_np_single | c2 | M2x − M1 (switch) | -0.0143 | [-0.042, +0.010] | 100 |
| D_np_single | c2 | M2x − M1 (blend21) | -0.0223 | [-0.052, +0.009] | 100 |
| D_np_single | c2 | M2x learned − M1 insurance | +0.0189 | [-0.025, +0.065] | 100 |
| D_np_single | c2 | REGISTERED M2x blend21 − M1 learned | -0.0157 | [-0.048, +0.018] | 100 |
| E_np_negonly | c2 | M1: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M1: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M1: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M1: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M1: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M1: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M1: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M1: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| E_np_negonly | c2 | M2x − M1 (learned) | -0.0546 | [-0.095, -0.018] | 100 |
| E_np_negonly | c2 | M2x − M1 (insurance) | -0.0546 | [-0.095, -0.018] | 100 |
| E_np_negonly | c2 | M2x − M1 (switch) | -0.0546 | [-0.095, -0.018] | 100 |
| E_np_negonly | c2 | M2x − M1 (blend21) | -0.0546 | [-0.095, -0.018] | 100 |
| E_np_negonly | c2 | M2x learned − M1 insurance | -0.0546 | [-0.096, -0.018] | 100 |
| E_np_negonly | c2 | REGISTERED M2x blend21 − M1 learned | -0.0546 | [-0.095, -0.017] | 100 |
| E_np_negonly | c1 | M1: learned − fixed | +0.2909 | [+0.187, +0.401] | 59 |
| E_np_negonly | c1 | M1: insurance − fixed | +0.2909 | [+0.187, +0.397] | 59 |
| E_np_negonly | c1 | M1: switch − fixed | +0.2909 | [+0.187, +0.399] | 59 |
| E_np_negonly | c1 | M1: switch − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M1: blend21 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M1: blend21 − fixed | +0.2909 | [+0.187, +0.399] | 59 |
| E_np_negonly | c1 | M1: blend11 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M1: blend11 − fixed | +0.2909 | [+0.188, +0.400] | 59 |
| E_np_negonly | c1 | M2x: learned − fixed | +0.3406 | [+0.232, +0.453] | 59 |
| E_np_negonly | c1 | M2x: insurance − fixed | +0.3406 | [+0.232, +0.452] | 59 |
| E_np_negonly | c1 | M2x: switch − fixed | +0.3406 | [+0.231, +0.453] | 59 |
| E_np_negonly | c1 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x: blend21 − fixed | +0.3406 | [+0.232, +0.455] | 59 |
| E_np_negonly | c1 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 59 |
| E_np_negonly | c1 | M2x: blend11 − fixed | +0.3406 | [+0.232, +0.455] | 59 |
| E_np_negonly | c1 | M2x − M1 (learned) | -0.0337 | [-0.077, +0.005] | 59 |
| E_np_negonly | c1 | M2x − M1 (insurance) | -0.0337 | [-0.076, +0.005] | 59 |
| E_np_negonly | c1 | M2x − M1 (switch) | -0.0337 | [-0.077, +0.006] | 59 |
| E_np_negonly | c1 | M2x − M1 (blend21) | -0.0337 | [-0.078, +0.005] | 59 |
| E_np_negonly | c1 | M2x learned − M1 insurance | -0.0337 | [-0.077, +0.005] | 59 |
| E_np_negonly | c1 | REGISTERED M2x blend21 − M1 learned | -0.0337 | [-0.077, +0.004] | 59 |
| F_np_uncovered | c2 | M1: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M1: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M1: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M1: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M1: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M1: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M1: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M1: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: learned − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: insurance − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: switch − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend21 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x: blend11 − fixed | +0.0000 | [+0.000, +0.000] | 100 |
| F_np_uncovered | c2 | M2x − M1 (learned) | -0.0188 | [-0.043, +0.003] | 100 |
| F_np_uncovered | c2 | M2x − M1 (insurance) | -0.0188 | [-0.042, +0.003] | 100 |
| F_np_uncovered | c2 | M2x − M1 (switch) | -0.0188 | [-0.043, +0.003] | 100 |
| F_np_uncovered | c2 | M2x − M1 (blend21) | -0.0188 | [-0.042, +0.003] | 100 |
| F_np_uncovered | c2 | M2x learned − M1 insurance | -0.0188 | [-0.043, +0.003] | 100 |
| F_np_uncovered | c2 | REGISTERED M2x blend21 − M1 learned | -0.0188 | [-0.043, +0.003] | 100 |
| F_np_uncovered | c1 | M1: learned − fixed | +0.1698 | [+0.066, +0.286] | 38 |
| F_np_uncovered | c1 | M1: insurance − fixed | +0.1698 | [+0.070, +0.286] | 38 |
| F_np_uncovered | c1 | M1: switch − fixed | +0.1698 | [+0.069, +0.286] | 38 |
| F_np_uncovered | c1 | M1: switch − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M1: blend21 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M1: blend21 − fixed | +0.1698 | [+0.070, +0.285] | 38 |
| F_np_uncovered | c1 | M1: blend11 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M1: blend11 − fixed | +0.1698 | [+0.070, +0.284] | 38 |
| F_np_uncovered | c1 | M2x: learned − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x: insurance − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x: switch − fixed | +0.1936 | [+0.088, +0.315] | 38 |
| F_np_uncovered | c1 | M2x: switch − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x: blend21 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x: blend21 − fixed | +0.1936 | [+0.086, +0.312] | 38 |
| F_np_uncovered | c1 | M2x: blend11 − learned | +0.0000 | [+0.000, +0.000] | 38 |
| F_np_uncovered | c1 | M2x: blend11 − fixed | +0.1936 | [+0.086, +0.315] | 38 |
| F_np_uncovered | c1 | M2x − M1 (learned) | -0.0282 | [-0.072, +0.007] | 38 |
| F_np_uncovered | c1 | M2x − M1 (insurance) | -0.0282 | [-0.072, +0.008] | 38 |
| F_np_uncovered | c1 | M2x − M1 (switch) | -0.0282 | [-0.071, +0.007] | 38 |
| F_np_uncovered | c1 | M2x − M1 (blend21) | -0.0282 | [-0.072, +0.008] | 38 |
| F_np_uncovered | c1 | M2x learned − M1 insurance | -0.0282 | [-0.071, +0.007] | 38 |
| F_np_uncovered | c1 | REGISTERED M2x blend21 − M1 learned | -0.0282 | [-0.071, +0.007] | 38 |
| G_tims_crosslib | c2 | M1: learned − fixed | +0.0806 | [+0.033, +0.131] | 100 |
| G_tims_crosslib | c2 | M1: insurance − fixed | -0.0067 | [-0.018, +0.000] | 100 |
| G_tims_crosslib | c2 | M1: switch − fixed | +0.0512 | [+0.009, +0.096] | 100 |
| G_tims_crosslib | c2 | M1: switch − learned | -0.0294 | [-0.057, -0.007] | 100 |
| G_tims_crosslib | c2 | M1: blend21 − learned | -0.0102 | [-0.027, +0.003] | 100 |
| G_tims_crosslib | c2 | M1: blend21 − fixed | +0.0704 | [+0.028, +0.116] | 100 |
| G_tims_crosslib | c2 | M1: blend11 − learned | -0.0084 | [-0.031, +0.013] | 100 |
| G_tims_crosslib | c2 | M1: blend11 − fixed | +0.0722 | [+0.031, +0.117] | 100 |
| G_tims_crosslib | c2 | M2x: learned − fixed | +0.0920 | [+0.039, +0.148] | 100 |
| G_tims_crosslib | c2 | M2x: insurance − fixed | -0.0067 | [-0.018, +0.000] | 100 |
| G_tims_crosslib | c2 | M2x: switch − fixed | +0.0591 | [+0.014, +0.107] | 100 |
| G_tims_crosslib | c2 | M2x: switch − learned | -0.0329 | [-0.067, -0.004] | 100 |
| G_tims_crosslib | c2 | M2x: blend21 − learned | +0.0011 | [-0.019, +0.021] | 100 |
| G_tims_crosslib | c2 | M2x: blend21 − fixed | +0.0931 | [+0.044, +0.146] | 100 |
| G_tims_crosslib | c2 | M2x: blend11 − learned | -0.0094 | [-0.029, +0.009] | 100 |
| G_tims_crosslib | c2 | M2x: blend11 − fixed | +0.0826 | [+0.035, +0.132] | 100 |
| G_tims_crosslib | c2 | M2x − M1 (learned) | -0.0370 | [-0.073, -0.006] | 100 |
| G_tims_crosslib | c2 | M2x − M1 (insurance) | -0.0485 | [-0.090, -0.009] | 100 |
| G_tims_crosslib | c2 | M2x − M1 (switch) | -0.0405 | [-0.076, -0.010] | 100 |
| G_tims_crosslib | c2 | M2x − M1 (blend21) | -0.0258 | [-0.056, -0.003] | 100 |
| G_tims_crosslib | c2 | M2x learned − M1 insurance | +0.0502 | [-0.004, +0.106] | 100 |
| G_tims_crosslib | c2 | REGISTERED M2x blend21 − M1 learned | -0.0360 | [-0.068, -0.009] | 100 |
| G_tims_crosslib | c1 | M1: learned − fixed | -0.0312 | [-0.093, +0.030] | 100 |
| G_tims_crosslib | c1 | M1: insurance − fixed | +0.0067 | [+0.000, +0.020] | 100 |
| G_tims_crosslib | c1 | M1: switch − fixed | -0.0196 | [-0.080, +0.042] | 100 |
| G_tims_crosslib | c1 | M1: switch − learned | +0.0117 | [+0.000, +0.030] | 100 |
| G_tims_crosslib | c1 | M1: blend21 − learned | +0.0017 | [-0.020, +0.023] | 100 |
| G_tims_crosslib | c1 | M1: blend21 − fixed | -0.0296 | [-0.084, +0.024] | 100 |
| G_tims_crosslib | c1 | M1: blend11 − learned | +0.0137 | [-0.012, +0.041] | 100 |
| G_tims_crosslib | c1 | M1: blend11 − fixed | -0.0175 | [-0.069, +0.034] | 100 |
| G_tims_crosslib | c1 | M2x: learned − fixed | -0.0037 | [-0.074, +0.070] | 100 |
| G_tims_crosslib | c1 | M2x: insurance − fixed | +0.0067 | [+0.000, +0.020] | 100 |
| G_tims_crosslib | c1 | M2x: switch − fixed | +0.0080 | [-0.064, +0.080] | 100 |
| G_tims_crosslib | c1 | M2x: switch − learned | +0.0117 | [+0.000, +0.030] | 100 |
| G_tims_crosslib | c1 | M2x: blend21 − learned | +0.0124 | [-0.022, +0.047] | 100 |
| G_tims_crosslib | c1 | M2x: blend21 − fixed | +0.0087 | [-0.050, +0.066] | 100 |
| G_tims_crosslib | c1 | M2x: blend11 − learned | +0.0277 | [-0.015, +0.070] | 100 |
| G_tims_crosslib | c1 | M2x: blend11 − fixed | +0.0240 | [-0.027, +0.076] | 100 |
| G_tims_crosslib | c1 | M2x − M1 (learned) | -0.0337 | [-0.085, +0.015] | 100 |
| G_tims_crosslib | c1 | M2x − M1 (insurance) | -0.0612 | [-0.105, -0.021] | 100 |
| G_tims_crosslib | c1 | M2x − M1 (switch) | -0.0337 | [-0.084, +0.015] | 100 |
| G_tims_crosslib | c1 | M2x − M1 (blend21) | -0.0230 | [-0.062, +0.012] | 100 |
| G_tims_crosslib | c1 | M2x learned − M1 insurance | -0.0716 | [-0.142, -0.002] | 100 |
| G_tims_crosslib | c1 | REGISTERED M2x blend21 − M1 learned | -0.0213 | [-0.065, +0.020] | 100 |
