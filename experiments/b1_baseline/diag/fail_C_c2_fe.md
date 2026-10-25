# C2 failures: run_p2dev_fe / C_np_crosslib / rank_v4b/lambdarank.txt (blend21 + GL fallback)

molecules 100 | scored 83 | MRR 0.6013 | truth rank 1: 52 | rank 2-25: 28 | >25: 3 | no truth in shortlist: 17 | parity mismatches vs evaluator top-25: 0

| top decoy group | n molecules | lost RR | decoy lib > truth lib | libpri fired | GL fallback | median truth lib | median decoy lib |
|---|---:|---:|---:|---:|---:|---:|---:|
| coconut_only | 7 | 5.10 | 0 | 0 | -14 | 0.000 | 0.000 |
| pc_only | 10 | 7.48 | 0 | 0 | -20 | 0.000 | 0.000 |
| train | 14 | 10.29 | 14 | 0 | -28 | 0.000 | 0.656 |

| truth library similarity | n | MRR | rank 1 share | molecules with a train decoy on top |
|---|---:|---:|---:|---:|
| [0, 0.5) | 83 | 0.724 | 0.63 | 14 |