# same-window FPNet comparison (fold0=experiments/b1_baseline/run_panel_v3b, full1=experiments/b1_baseline/run_panel_full1, full_eval=experiments/b1_baseline/run_panel_fe)

## P_np250: 250 molecules (windows identical across runs: n_unique equal for 100% ; truth in window 250)

| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |
|---|---|---:|---:|---:|---:|---:|
| FP only | fold0 | 0.704 | 0.788 | 0.840 | 0.896 | 0.226 |
| FP only | full1 | 0.976 | 0.988 | 0.992 | 0.996 | 0.806 |
| FP only | full_eval | 0.944 | 0.960 | 0.972 | 0.988 | 0.628 |
| FP + prior (shortlist lambda) | fold0 | 0.976 | 0.988 | 0.992 | 0.992 | 0.792 |
| FP + prior (shortlist lambda) | full1 | 1.000 | 1.000 | 1.000 | 1.000 | 0.937 |
| FP + prior (shortlist lambda) | full_eval | 1.000 | 1.000 | 1.000 | 1.000 | 0.925 |
| FP + 0.5 prior | fold0 | 0.996 | 1.000 | 1.000 | 1.000 | 0.840 |
| FP + 0.5 prior | full1 | 1.000 | 1.000 | 1.000 | 1.000 | 0.888 |
| FP + 0.5 prior | full_eval | 1.000 | 1.000 | 1.000 | 1.000 | 0.890 |
| prior only | fold0 | 0.988 | 0.992 | 0.992 | 0.996 | 0.812 |
| prior only | full1 | 0.988 | 0.992 | 0.992 | 0.996 | 0.812 |
| prior only | full_eval | 0.988 | 0.992 | 0.992 | 0.996 | 0.812 |

| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |
|---|---|---:|---|---:|---|---|
| FP only | full1 − fold0 | +0.100 | [+0.064, +0.140] | +0.580 | [+0.533, +0.625] | 26 / 1 |
| FP + prior (shortlist lambda) | full1 − fold0 | +0.008 | [+0.000, +0.020] | +0.144 | [+0.112, +0.177] | 2 / 0 |
| FP only | full_eval − fold0 | +0.092 | [+0.056, +0.128] | +0.402 | [+0.356, +0.447] | 23 / 0 |
| FP + prior (shortlist lambda) | full_eval − fold0 | +0.008 | [+0.000, +0.020] | +0.132 | [+0.102, +0.164] | 2 / 0 |

| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |
|---|---:|---:|---:|
| fold0 | 1.000 | 1.000 | 1.000 |
| full1 | 1.000 | 1.000 | 1.000 |
| full_eval | 1.000 | 1.000 | 1.000 |

