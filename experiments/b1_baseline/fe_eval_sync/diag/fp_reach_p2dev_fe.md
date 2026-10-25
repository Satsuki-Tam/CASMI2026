# same-window FPNet comparison (fold0=experiments/b1_baseline/run_p2dev_v3, fold1_seen=experiments/b1_baseline/run_p2dev_fold1, full1=experiments/b1_baseline/run_p2dev_full1, full_eval=experiments/b1_baseline/run_p2dev_fe)

## C_np_crosslib: 100 molecules (windows identical across runs: n_unique equal for 100% ; truth in window 95)

| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |
|---|---|---:|---:|---:|---:|---:|
| FP only | fold0 | 0.650 | 0.750 | 0.780 | 0.840 | 0.227 |
| FP only | full_eval | 0.620 | 0.770 | 0.820 | 0.850 | 0.259 |
| FP + prior (shortlist lambda) | fold0 | 0.730 | 0.840 | 0.880 | 0.920 | 0.359 |
| FP + prior (shortlist lambda) | full_eval | 0.720 | 0.820 | 0.870 | 0.910 | 0.420 |
| FP + 0.5 prior | fold0 | 0.570 | 0.710 | 0.790 | 0.860 | 0.300 |
| FP + 0.5 prior | full_eval | 0.620 | 0.730 | 0.820 | 0.870 | 0.310 |
| prior only | fold0 | 0.410 | 0.450 | 0.490 | 0.520 | 0.231 |
| prior only | full_eval | 0.410 | 0.450 | 0.490 | 0.520 | 0.231 |

| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |
|---|---|---:|---|---:|---|---|
| FP only | full_eval − fold0 | +0.010 | [-0.030, +0.050] | +0.033 | [-0.010, +0.078] | 3 / 2 |
| FP + prior (shortlist lambda) | full_eval − fold0 | -0.010 | [-0.050, +0.020] | +0.061 | [+0.024, +0.103] | 1 / 2 |

| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |
|---|---:|---:|---:|
| fold0 | 0.950 | 0.949 | 1.000 |
| full_eval | 0.950 | 0.939 | 1.000 |

## D_np_single: 100 molecules (windows identical across runs: n_unique equal for 100% ; truth in window 91)

| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |
|---|---|---:|---:|---:|---:|---:|
| FP only | fold0 | 0.720 | 0.790 | 0.810 | 0.820 | 0.428 |
| FP only | fold1_seen | 0.850 | 0.880 | 0.890 | 0.910 | 0.568 |
| FP only | full1 | 0.850 | 0.870 | 0.880 | 0.900 | 0.665 |
| FP only | full_eval | 0.760 | 0.820 | 0.830 | 0.860 | 0.454 |
| FP + prior (shortlist lambda) | fold0 | 0.760 | 0.790 | 0.820 | 0.860 | 0.426 |
| FP + prior (shortlist lambda) | fold1_seen | 0.880 | 0.890 | 0.890 | 0.910 | 0.610 |
| FP + prior (shortlist lambda) | full1 | 0.850 | 0.880 | 0.880 | 0.880 | 0.594 |
| FP + prior (shortlist lambda) | full_eval | 0.820 | 0.850 | 0.860 | 0.860 | 0.454 |
| FP + 0.5 prior | fold0 | 0.600 | 0.700 | 0.760 | 0.810 | 0.222 |
| FP + 0.5 prior | fold1_seen | 0.620 | 0.780 | 0.810 | 0.870 | 0.272 |
| FP + 0.5 prior | full1 | 0.640 | 0.760 | 0.790 | 0.850 | 0.253 |
| FP + 0.5 prior | full_eval | 0.620 | 0.720 | 0.800 | 0.840 | 0.253 |
| prior only | fold0 | 0.160 | 0.230 | 0.280 | 0.320 | 0.082 |
| prior only | fold1_seen | 0.160 | 0.230 | 0.280 | 0.320 | 0.082 |
| prior only | full1 | 0.160 | 0.230 | 0.280 | 0.320 | 0.082 |
| prior only | full_eval | 0.160 | 0.230 | 0.280 | 0.320 | 0.082 |

| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |
|---|---|---:|---|---:|---|---|
| FP only | fold1_seen − fold0 | +0.090 | [+0.040, +0.150] | +0.140 | [+0.076, +0.204] | 9 / 0 |
| FP + prior (shortlist lambda) | fold1_seen − fold0 | +0.050 | [+0.010, +0.100] | +0.183 | [+0.124, +0.246] | 5 / 0 |
| FP only | full1 − fold0 | +0.080 | [+0.030, +0.140] | +0.236 | [+0.163, +0.309] | 8 / 0 |
| FP + prior (shortlist lambda) | full1 − fold0 | +0.020 | [+0.000, +0.050] | +0.167 | [+0.098, +0.239] | 2 / 0 |
| FP only | full_eval − fold0 | +0.040 | [+0.010, +0.080] | +0.025 | [-0.025, +0.077] | 4 / 0 |
| FP + prior (shortlist lambda) | full_eval − fold0 | +0.000 | [+0.000, +0.000] | +0.028 | [-0.028, +0.086] | 0 / 0 |

| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |
|---|---:|---:|---:|
| fold0 | 0.870 | 0.870 | nan |
| fold1_seen | 0.910 | 0.910 | nan |
| full1 | 0.900 | 0.900 | nan |
| full_eval | 0.870 | 0.870 | nan |

## E_np_negonly: 100 molecules (windows identical across runs: n_unique equal for 100% ; truth in window 90)

| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |
|---|---|---:|---:|---:|---:|---:|
| FP only | fold0 | 0.630 | 0.730 | 0.760 | 0.800 | 0.248 |
| FP only | fold1_seen | 0.830 | 0.870 | 0.900 | 0.900 | 0.570 |
| FP only | full1 | 0.880 | 0.890 | 0.900 | 0.900 | 0.583 |
| FP only | full_eval | 0.660 | 0.710 | 0.790 | 0.840 | 0.310 |
| FP + prior (shortlist lambda) | fold0 | 0.670 | 0.770 | 0.810 | 0.830 | 0.304 |
| FP + prior (shortlist lambda) | fold1_seen | 0.870 | 0.870 | 0.890 | 0.900 | 0.548 |
| FP + prior (shortlist lambda) | full1 | 0.860 | 0.890 | 0.900 | 0.900 | 0.502 |
| FP + prior (shortlist lambda) | full_eval | 0.740 | 0.780 | 0.820 | 0.850 | 0.341 |
| FP + 0.5 prior | fold0 | 0.620 | 0.700 | 0.760 | 0.780 | 0.234 |
| FP + 0.5 prior | fold1_seen | 0.740 | 0.820 | 0.850 | 0.860 | 0.320 |
| FP + 0.5 prior | full1 | 0.730 | 0.840 | 0.850 | 0.870 | 0.298 |
| FP + 0.5 prior | full_eval | 0.650 | 0.750 | 0.790 | 0.800 | 0.245 |
| prior only | fold0 | 0.360 | 0.460 | 0.500 | 0.540 | 0.123 |
| prior only | fold1_seen | 0.360 | 0.460 | 0.500 | 0.540 | 0.123 |
| prior only | full1 | 0.360 | 0.460 | 0.500 | 0.540 | 0.123 |
| prior only | full_eval | 0.360 | 0.460 | 0.500 | 0.540 | 0.123 |

| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |
|---|---|---:|---|---:|---|---|
| FP only | fold1_seen − fold0 | +0.100 | [+0.040, +0.160] | +0.322 | [+0.251, +0.399] | 10 / 0 |
| FP + prior (shortlist lambda) | fold1_seen − fold0 | +0.070 | [+0.030, +0.120] | +0.245 | [+0.186, +0.309] | 7 / 0 |
| FP only | full1 − fold0 | +0.100 | [+0.040, +0.160] | +0.335 | [+0.256, +0.414] | 10 / 0 |
| FP + prior (shortlist lambda) | full1 − fold0 | +0.070 | [+0.020, +0.120] | +0.198 | [+0.125, +0.273] | 7 / 0 |
| FP only | full_eval − fold0 | +0.040 | [+0.000, +0.090] | +0.062 | [+0.011, +0.116] | 5 / 1 |
| FP + prior (shortlist lambda) | full_eval − fold0 | +0.020 | [-0.020, +0.060] | +0.038 | [-0.008, +0.082] | 3 / 1 |

| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |
|---|---:|---:|---:|
| fold0 | 0.890 | 0.838 | 1.000 |
| fold1_seen | 0.900 | 0.909 | 1.000 |
| full1 | 0.900 | 0.909 | 1.000 |
| full_eval | 0.890 | 0.859 | 1.000 |

## F_np_uncovered: 100 molecules (windows identical across runs: n_unique equal for 100% ; truth in window 64)

| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |
|---|---|---:|---:|---:|---:|---:|
| FP only | fold0 | 0.370 | 0.390 | 0.440 | 0.460 | 0.156 |
| FP only | fold1_seen | 0.600 | 0.630 | 0.630 | 0.630 | 0.431 |
| FP only | full1 | 0.560 | 0.620 | 0.620 | 0.630 | 0.386 |
| FP only | full_eval | 0.350 | 0.400 | 0.430 | 0.490 | 0.152 |
| FP + prior (shortlist lambda) | fold0 | 0.400 | 0.450 | 0.500 | 0.550 | 0.240 |
| FP + prior (shortlist lambda) | fold1_seen | 0.620 | 0.630 | 0.630 | 0.630 | 0.405 |
| FP + prior (shortlist lambda) | full1 | 0.590 | 0.610 | 0.620 | 0.620 | 0.391 |
| FP + prior (shortlist lambda) | full_eval | 0.430 | 0.530 | 0.540 | 0.550 | 0.242 |
| FP + 0.5 prior | fold0 | 0.440 | 0.530 | 0.560 | 0.560 | 0.239 |
| FP + 0.5 prior | fold1_seen | 0.550 | 0.580 | 0.610 | 0.620 | 0.321 |
| FP + 0.5 prior | full1 | 0.530 | 0.590 | 0.590 | 0.600 | 0.269 |
| FP + 0.5 prior | full_eval | 0.450 | 0.550 | 0.550 | 0.580 | 0.236 |
| prior only | fold0 | 0.340 | 0.400 | 0.470 | 0.490 | 0.185 |
| prior only | fold1_seen | 0.340 | 0.400 | 0.470 | 0.490 | 0.185 |
| prior only | full1 | 0.340 | 0.400 | 0.470 | 0.490 | 0.185 |
| prior only | full_eval | 0.340 | 0.400 | 0.470 | 0.490 | 0.185 |

| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |
|---|---|---:|---|---:|---|---|
| FP only | fold1_seen − fold0 | +0.170 | [+0.100, +0.250] | +0.276 | [+0.203, +0.351] | 17 / 0 |
| FP + prior (shortlist lambda) | fold1_seen − fold0 | +0.080 | [+0.030, +0.140] | +0.165 | [+0.111, +0.224] | 8 / 0 |
| FP only | full1 − fold0 | +0.170 | [+0.100, +0.250] | +0.230 | [+0.164, +0.297] | 17 / 0 |
| FP + prior (shortlist lambda) | full1 − fold0 | +0.070 | [+0.030, +0.120] | +0.150 | [+0.093, +0.213] | 7 / 0 |
| FP only | full_eval − fold0 | +0.030 | [-0.020, +0.080] | -0.004 | [-0.039, +0.033] | 5 / 2 |
| FP + prior (shortlist lambda) | full_eval − fold0 | +0.000 | [-0.050, +0.050] | +0.002 | [-0.029, +0.033] | 3 / 3 |

| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |
|---|---:|---:|---:|
| fold0 | 0.600 | 0.570 | 1.000 |
| fold1_seen | 0.640 | 0.630 | 1.000 |
| full1 | 0.640 | 0.630 | 1.000 |
| full_eval | 0.610 | 0.580 | 1.000 |

## G_tims_crosslib: 100 molecules (windows identical across runs: n_unique equal for 100% ; truth in window 100)

| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |
|---|---|---:|---:|---:|---:|---:|
| FP only | fold0 | 0.850 | 0.950 | 0.960 | 0.960 | 0.452 |
| FP only | full_eval | 0.910 | 0.960 | 0.960 | 0.960 | 0.468 |
| FP + prior (shortlist lambda) | fold0 | 0.840 | 0.910 | 0.960 | 0.960 | 0.414 |
| FP + prior (shortlist lambda) | full_eval | 0.870 | 0.960 | 0.960 | 0.960 | 0.412 |
| FP + 0.5 prior | fold0 | 0.560 | 0.780 | 0.840 | 0.920 | 0.083 |
| FP + 0.5 prior | full_eval | 0.570 | 0.790 | 0.840 | 0.930 | 0.109 |
| prior only | fold0 | 0.010 | 0.010 | 0.010 | 0.010 | 0.001 |
| prior only | full_eval | 0.010 | 0.010 | 0.010 | 0.010 | 0.001 |

| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |
|---|---|---:|---|---:|---|---|
| FP only | full_eval − fold0 | +0.000 | [+0.000, +0.000] | +0.016 | [-0.038, +0.070] | 0 / 0 |
| FP + prior (shortlist lambda) | full_eval − fold0 | +0.000 | [+0.000, +0.000] | -0.002 | [-0.064, +0.058] | 0 / 0 |

| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |
|---|---:|---:|---:|
| fold0 | 0.980 | 0.960 | 0.980 |
| full_eval | 0.980 | 0.960 | 0.980 |

