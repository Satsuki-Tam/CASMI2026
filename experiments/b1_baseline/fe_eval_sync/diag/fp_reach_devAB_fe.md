# same-window FPNet comparison (fold0=experiments/b1_baseline/run_v3b_eval, fold1_seen=experiments/b1_baseline/run_v3b_eval_seen, full1=experiments/b1_baseline/run_v3b_eval_full1, full_eval=experiments/b1_baseline/run_v3b_eval_fe)

## A_timstof: 300 molecules (windows identical across runs: n_unique equal for 100% ; truth in window 300)

| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |
|---|---|---:|---:|---:|---:|---:|
| FP only | fold0 | 0.893 | 0.933 | 0.953 | 0.983 | 0.506 |
| FP only | fold1_seen | 0.967 | 0.980 | 0.997 | 0.997 | 0.710 |
| FP only | full1 | 0.977 | 0.987 | 0.993 | 0.997 | 0.749 |
| FP only | full_eval | 0.973 | 0.987 | 0.993 | 0.993 | 0.703 |
| FP + prior (shortlist lambda) | fold0 | 0.893 | 0.947 | 0.960 | 0.987 | 0.504 |
| FP + prior (shortlist lambda) | fold1_seen | 0.963 | 0.993 | 0.997 | 0.997 | 0.696 |
| FP + prior (shortlist lambda) | full1 | 0.980 | 0.990 | 0.997 | 0.997 | 0.731 |
| FP + prior (shortlist lambda) | full_eval | 0.963 | 0.987 | 0.993 | 0.997 | 0.707 |
| FP + 0.5 prior | fold0 | 0.707 | 0.853 | 0.900 | 0.953 | 0.189 |
| FP + 0.5 prior | fold1_seen | 0.797 | 0.937 | 0.970 | 0.997 | 0.248 |
| FP + 0.5 prior | full1 | 0.800 | 0.910 | 0.963 | 0.993 | 0.315 |
| FP + 0.5 prior | full_eval | 0.853 | 0.943 | 0.977 | 0.993 | 0.276 |
| prior only | fold0 | 0.000 | 0.007 | 0.013 | 0.040 | 0.000 |
| prior only | fold1_seen | 0.000 | 0.007 | 0.013 | 0.040 | 0.000 |
| prior only | full1 | 0.000 | 0.007 | 0.013 | 0.040 | 0.000 |
| prior only | full_eval | 0.000 | 0.007 | 0.013 | 0.040 | 0.000 |

| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |
|---|---|---:|---|---:|---|---|
| FP only | fold1_seen − fold0 | +0.013 | [+0.003, +0.027] | +0.204 | [+0.165, +0.243] | 4 / 0 |
| FP + prior (shortlist lambda) | fold1_seen − fold0 | +0.010 | [+0.000, +0.023] | +0.192 | [+0.154, +0.232] | 3 / 0 |
| FP only | full1 − fold0 | +0.013 | [+0.003, +0.027] | +0.242 | [+0.202, +0.283] | 4 / 0 |
| FP + prior (shortlist lambda) | full1 − fold0 | +0.010 | [+0.000, +0.023] | +0.227 | [+0.186, +0.269] | 3 / 0 |
| FP only | full_eval − fold0 | +0.010 | [-0.003, +0.027] | +0.197 | [+0.161, +0.234] | 4 / 1 |
| FP + prior (shortlist lambda) | full_eval − fold0 | +0.010 | [+0.000, +0.023] | +0.203 | [+0.165, +0.241] | 3 / 0 |

| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |
|---|---:|---:|---:|
| fold0 | 0.987 | 0.987 | 1.000 |
| fold1_seen | 0.997 | 0.997 | 1.000 |
| full1 | 0.997 | 0.997 | 1.000 |
| full_eval | 0.997 | 0.997 | 1.000 |

## B_nplib: 300 molecules (windows identical across runs: n_unique equal for 100% ; truth in window 277)

| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |
|---|---|---:|---:|---:|---:|---:|
| FP only | fold0 | 0.647 | 0.730 | 0.777 | 0.817 | 0.367 |
| FP only | fold1_seen | 0.823 | 0.870 | 0.883 | 0.897 | 0.570 |
| FP only | full1 | 0.847 | 0.877 | 0.900 | 0.910 | 0.636 |
| FP only | full_eval | 0.840 | 0.883 | 0.903 | 0.907 | 0.562 |
| FP + prior (shortlist lambda) | fold0 | 0.723 | 0.800 | 0.827 | 0.857 | 0.418 |
| FP + prior (shortlist lambda) | fold1_seen | 0.853 | 0.883 | 0.903 | 0.917 | 0.593 |
| FP + prior (shortlist lambda) | full1 | 0.863 | 0.897 | 0.903 | 0.917 | 0.634 |
| FP + prior (shortlist lambda) | full_eval | 0.867 | 0.880 | 0.900 | 0.920 | 0.613 |
| FP + 0.5 prior | fold0 | 0.657 | 0.730 | 0.777 | 0.827 | 0.289 |
| FP + 0.5 prior | fold1_seen | 0.737 | 0.810 | 0.843 | 0.883 | 0.350 |
| FP + 0.5 prior | full1 | 0.723 | 0.813 | 0.850 | 0.877 | 0.371 |
| FP + 0.5 prior | full_eval | 0.743 | 0.827 | 0.860 | 0.887 | 0.364 |
| prior only | fold0 | 0.273 | 0.313 | 0.353 | 0.407 | 0.121 |
| prior only | fold1_seen | 0.273 | 0.313 | 0.353 | 0.407 | 0.121 |
| prior only | full1 | 0.273 | 0.313 | 0.353 | 0.407 | 0.121 |
| prior only | full_eval | 0.273 | 0.313 | 0.353 | 0.407 | 0.121 |

| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |
|---|---|---:|---|---:|---|---|
| FP only | fold1_seen − fold0 | +0.080 | [+0.047, +0.113] | +0.203 | [+0.162, +0.245] | 26 / 2 |
| FP + prior (shortlist lambda) | fold1_seen − fold0 | +0.060 | [+0.033, +0.087] | +0.175 | [+0.137, +0.214] | 18 / 0 |
| FP only | full1 − fold0 | +0.093 | [+0.060, +0.127] | +0.269 | [+0.227, +0.312] | 28 / 0 |
| FP + prior (shortlist lambda) | full1 − fold0 | +0.060 | [+0.037, +0.087] | +0.216 | [+0.174, +0.259] | 18 / 0 |
| FP only | full_eval − fold0 | +0.090 | [+0.057, +0.127] | +0.195 | [+0.157, +0.234] | 29 / 2 |
| FP + prior (shortlist lambda) | full_eval − fold0 | +0.063 | [+0.037, +0.093] | +0.195 | [+0.159, +0.232] | 19 / 0 |

| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |
|---|---:|---:|---:|
| fold0 | 0.890 | 0.880 | 0.986 |
| fold1_seen | 0.917 | 0.920 | 1.000 |
| full1 | 0.920 | 0.920 | 1.000 |
| full_eval | 0.920 | 0.923 | 1.000 |

