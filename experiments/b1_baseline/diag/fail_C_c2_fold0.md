# C2 failures: run_p2dev_v3 / C_np_crosslib / rank_v4b/lambdarank.txt (blend21 + GL fallback)

molecules 100 | scored 84 | MRR 0.6120 | truth rank 1: 55 | rank 2-25: 25 | >25: 4 | no truth in shortlist: 16 | parity mismatches vs evaluator top-25: 0

| top decoy group | n molecules | lost RR | decoy lib > truth lib | libpri fired | GL fallback | median truth lib | median decoy lib |
|---|---:|---:|---:|---:|---:|---:|---:|
| coconut_only | 6 | 4.86 | 0 | 0 | -12 | 0.000 | 0.000 |
| pc_only | 14 | 10.62 | 0 | 0 | -28 | 0.000 | 0.000 |
| train | 9 | 7.32 | 8 | 0 | -18 | 0.000 | 0.636 |

| truth library similarity | n | MRR | rank 1 share | molecules with a train decoy on top |
|---|---:|---:|---:|---:|
| [0, 0.5) | 84 | 0.729 | 0.65 | 9 |