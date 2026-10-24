# P1 baseline results (class-2 proxy, [M+H]+, fold-0 FPNet, label-free retrieval)

## A_timstof (N=300; libs {'enveda-180': 300}; CE known for 300 molecules)

| stage | molecules | share |
|---|---:|---:|
| db_present_external | 296 | 0.987 |
| window_external | 296 | 0.987 |
| truth_in_window_raw | 300 | 1.000 |
| truth_in_shortlist | 292 | 0.973 |
| top-25 (fp) | 274 | 0.913 |
| top-1 (fp) | 92 | 0.307 |

drop stage (fp): rank_2_25 180, rank_1 90, rank_gt_25 18, not_in_shortlist 8, not_in_external_db 4

window: median 10184 unique structures (median 10092 not in train libraries); median FP rank of truth in window 3; funnel 3.5 s/molecule

| variant | MRR@25 | 95% CI | top-1 | hit@25 | Δ vs fp | Δ vs fp+gl |
|---|---:|---:|---:|---:|---:|---:|
| prior | 0.001 | [0.000,0.002] | 0.000 | 0.010 | -0.464 [-0.507,-0.421] |  |
| fp | 0.465 | [0.422,0.508] | 0.307 | 0.913 |  |  |
| fp+0.15prior | 0.486 | [0.442,0.530] | 0.340 | 0.927 | +0.021 [+0.010,+0.034] |  |
| fp+0.5prior | 0.471 | [0.428,0.516] | 0.323 | 0.917 | +0.007 [-0.019,+0.033] |  |

by group (MRR@25): eval: fp 0.483, fp+0.15prior 0.514 (n=100); fit: fp 0.460, fp+0.15prior 0.473 (n=100); tune: fp 0.451, fp+0.15prior 0.470 (n=100)
