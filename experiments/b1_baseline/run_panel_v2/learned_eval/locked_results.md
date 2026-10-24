# B1 locked evaluation (official scorer replica, frozen ledger)

| set | view | candidate | output | official MRR@25 [95% CI] | no candidates | GL fallback |
|---|---|---|---|---|---|---|
| P_np250 | c2 (n=250) | M1 | learned | 0.8997 [0.868, 0.929] | 0 | 34 |
| P_np250 | c2 (n=250) | M1 | insurance | 0.8599 [0.824, 0.895] | 0 | 34 |
| P_np250 | c2 (n=250) | M1 | fixed | 0.8639 [0.827, 0.898] | 0 | 34 |
| P_np250 | c1 (n=250) | M1 | learned | 0.5995 [0.553, 0.646] | 0 | 34 |
| P_np250 | c1 (n=250) | M1 | insurance | 0.8669 [0.831, 0.902] | 0 | 34 |
| P_np250 | c1 (n=250) | M1 | fixed | 0.8639 [0.828, 0.899] | 0 | 34 |

## paired differences (molecule-level bootstrap, same ledger)

| set | view | comparison | mean Δ RR | 95% CI | n |
|---|---|---|---:|---|---:|
| P_np250 | c2 | M1: learned − fixed | +0.0357 | [+0.016, +0.057] | 250 |
| P_np250 | c2 | M1: insurance − fixed | -0.0040 | [-0.010, +0.000] | 250 |
| P_np250 | c1 | M1: learned − fixed | -0.2644 | [-0.310, -0.220] | 250 |
| P_np250 | c1 | M1: insurance − fixed | +0.0030 | [+0.000, +0.009] | 250 |
