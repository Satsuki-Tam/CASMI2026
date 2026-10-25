# C1 failures: run_rk_panel / P_np250 / rank_v4b/lambdarank.txt (blend21 + GL fallback)

molecules 250 | scored 250 | MRR 0.9128 | truth rank 1: 216 | rank 2-25: 34 | >25: 0 | no truth in shortlist: 0 | parity mismatches vs evaluator top-25: 0

| top decoy group | n molecules | lost RR | decoy lib > truth lib | libpri fired | GL fallback | median truth lib | median decoy lib |
|---|---:|---:|---:|---:|---:|---:|---:|
| coconut_only | 8 | 4.30 | 0 | 0 | 1 | 0.794 | 0.000 |
| pc_only | 2 | 1.58 | 0 | 0 | 0 | 0.532 | 0.000 |
| train | 24 | 15.92 | 12 | 0 | 5 | 0.704 | 0.742 |

| truth library similarity | n | MRR | rank 1 share | molecules with a train decoy on top |
|---|---:|---:|---:|---:|
| [0, 0.5) | 12 | 0.731 | 0.67 | 3 |
| [0.5, 0.7) | 36 | 0.799 | 0.69 | 8 |
| [0.7, 0.8) | 52 | 0.898 | 0.85 | 6 |
| [0.8, 0.9) | 125 | 0.956 | 0.92 | 6 |
| [0.9, 1.0) | 25 | 0.980 | 0.96 | 1 |