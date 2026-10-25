# same-window FPNet comparison (fold0=experiments/b1_baseline/run_p2dev_v3, fold1_seen=experiments/b1_baseline/run_p2dev_fold1, full1=experiments/b1_baseline/run_p2dev_full1)

## D_np_single: 100 molecules (windows identical across runs: n_unique equal for 100% ; truth in window 91)

| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |
|---|---|---:|---:|---:|---:|---:|
| FP only | fold0 | 0.720 | 0.790 | 0.810 | 0.820 | 0.428 |
| FP only | fold1_seen | 0.850 | 0.880 | 0.890 | 0.910 | 0.568 |
| FP only | full1 | 0.850 | 0.870 | 0.880 | 0.900 | 0.665 |
| FP + prior (shortlist lambda) | fold0 | 0.760 | 0.790 | 0.820 | 0.860 | 0.426 |
| FP + prior (shortlist lambda) | fold1_seen | 0.880 | 0.890 | 0.890 | 0.910 | 0.610 |
| FP + prior (shortlist lambda) | full1 | 0.850 | 0.880 | 0.880 | 0.880 | 0.594 |
| FP + 0.5 prior | fold0 | 0.600 | 0.700 | 0.760 | 0.810 | 0.222 |
| FP + 0.5 prior | fold1_seen | 0.620 | 0.780 | 0.810 | 0.870 | 0.272 |
| FP + 0.5 prior | full1 | 0.640 | 0.760 | 0.790 | 0.850 | 0.253 |
| prior only | fold0 | 0.160 | 0.230 | 0.280 | 0.320 | 0.082 |
| prior only | fold1_seen | 0.160 | 0.230 | 0.280 | 0.320 | 0.082 |
| prior only | full1 | 0.160 | 0.230 | 0.280 | 0.320 | 0.082 |

| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |
|---|---|---:|---|---:|---|---|
| FP only | fold1_seen − fold0 | +0.090 | [+0.040, +0.150] | +0.140 | [+0.075, +0.203] | 9 / 0 |
| FP + prior (shortlist lambda) | fold1_seen − fold0 | +0.050 | [+0.010, +0.100] | +0.183 | [+0.125, +0.246] | 5 / 0 |
| FP only | full1 − fold0 | +0.080 | [+0.030, +0.140] | +0.236 | [+0.164, +0.312] | 8 / 0 |
| FP + prior (shortlist lambda) | full1 − fold0 | +0.020 | [+0.000, +0.050] | +0.167 | [+0.096, +0.237] | 2 / 0 |

| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |
|---|---:|---:|---:|
| fold0 | 0.870 | 0.870 | nan |
| fold1_seen | 0.910 | 0.910 | nan |
| full1 | 0.900 | 0.900 | nan |

## E_np_negonly: 100 molecules (windows identical across runs: n_unique equal for 100% ; truth in window 90)

| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |
|---|---|---:|---:|---:|---:|---:|
| FP only | fold0 | 0.630 | 0.730 | 0.760 | 0.800 | 0.248 |
| FP only | fold1_seen | 0.830 | 0.870 | 0.900 | 0.900 | 0.570 |
| FP only | full1 | 0.880 | 0.890 | 0.900 | 0.900 | 0.583 |
| FP + prior (shortlist lambda) | fold0 | 0.670 | 0.770 | 0.810 | 0.830 | 0.304 |
| FP + prior (shortlist lambda) | fold1_seen | 0.870 | 0.870 | 0.890 | 0.900 | 0.548 |
| FP + prior (shortlist lambda) | full1 | 0.860 | 0.890 | 0.900 | 0.900 | 0.502 |
| FP + 0.5 prior | fold0 | 0.620 | 0.700 | 0.760 | 0.780 | 0.234 |
| FP + 0.5 prior | fold1_seen | 0.740 | 0.820 | 0.850 | 0.860 | 0.320 |
| FP + 0.5 prior | full1 | 0.730 | 0.840 | 0.850 | 0.870 | 0.298 |
| prior only | fold0 | 0.360 | 0.460 | 0.500 | 0.540 | 0.123 |
| prior only | fold1_seen | 0.360 | 0.460 | 0.500 | 0.540 | 0.123 |
| prior only | full1 | 0.360 | 0.460 | 0.500 | 0.540 | 0.123 |

| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |
|---|---|---:|---|---:|---|---|
| FP only | fold1_seen − fold0 | +0.100 | [+0.050, +0.160] | +0.322 | [+0.250, +0.397] | 10 / 0 |
| FP + prior (shortlist lambda) | fold1_seen − fold0 | +0.070 | [+0.020, +0.120] | +0.245 | [+0.182, +0.306] | 7 / 0 |
| FP only | full1 − fold0 | +0.100 | [+0.050, +0.160] | +0.335 | [+0.256, +0.415] | 10 / 0 |
| FP + prior (shortlist lambda) | full1 − fold0 | +0.070 | [+0.030, +0.120] | +0.198 | [+0.127, +0.272] | 7 / 0 |

| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |
|---|---:|---:|---:|
| fold0 | 0.890 | 0.838 | 1.000 |
| fold1_seen | 0.900 | 0.909 | 1.000 |
| full1 | 0.900 | 0.909 | 1.000 |

## F_np_uncovered: 100 molecules (windows identical across runs: n_unique equal for 100% ; truth in window 64)

| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |
|---|---|---:|---:|---:|---:|---:|
| FP only | fold0 | 0.370 | 0.390 | 0.440 | 0.460 | 0.156 |
| FP only | fold1_seen | 0.600 | 0.630 | 0.630 | 0.630 | 0.431 |
| FP only | full1 | 0.560 | 0.620 | 0.620 | 0.630 | 0.386 |
| FP + prior (shortlist lambda) | fold0 | 0.400 | 0.450 | 0.500 | 0.550 | 0.240 |
| FP + prior (shortlist lambda) | fold1_seen | 0.620 | 0.630 | 0.630 | 0.630 | 0.405 |
| FP + prior (shortlist lambda) | full1 | 0.590 | 0.610 | 0.620 | 0.620 | 0.391 |
| FP + 0.5 prior | fold0 | 0.440 | 0.530 | 0.560 | 0.560 | 0.239 |
| FP + 0.5 prior | fold1_seen | 0.550 | 0.580 | 0.610 | 0.620 | 0.321 |
| FP + 0.5 prior | full1 | 0.530 | 0.590 | 0.590 | 0.600 | 0.269 |
| prior only | fold0 | 0.340 | 0.400 | 0.470 | 0.490 | 0.185 |
| prior only | fold1_seen | 0.340 | 0.400 | 0.470 | 0.490 | 0.185 |
| prior only | full1 | 0.340 | 0.400 | 0.470 | 0.490 | 0.185 |

| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |
|---|---|---:|---|---:|---|---|
| FP only | fold1_seen − fold0 | +0.170 | [+0.100, +0.250] | +0.276 | [+0.202, +0.352] | 17 / 0 |
| FP + prior (shortlist lambda) | fold1_seen − fold0 | +0.080 | [+0.030, +0.140] | +0.165 | [+0.112, +0.225] | 8 / 0 |
| FP only | full1 − fold0 | +0.170 | [+0.100, +0.250] | +0.230 | [+0.164, +0.300] | 17 / 0 |
| FP + prior (shortlist lambda) | full1 − fold0 | +0.070 | [+0.020, +0.120] | +0.150 | [+0.095, +0.210] | 7 / 0 |

| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |
|---|---:|---:|---:|
| fold0 | 0.600 | 0.570 | 1.000 |
| fold1_seen | 0.640 | 0.630 | 1.000 |
| full1 | 0.640 | 0.630 | 1.000 |

