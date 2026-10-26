# 034 analog selection (rule fixed before the tables)

   variant  objective  min_c2_layer             worst  panel_c1_clean  passes
 anag0.5_1     0.0472       -0.0206 f0 panel C2 clean          0.0241   False
anag0.25_1     0.0464       -0.0195      f0 dev2 C C2          0.0223    True
 anag0.5_2     0.0435       -0.0261 f0 panel C2 clean          0.0253   False
anag0.25_2     0.0427       -0.0195      f0 dev2 C C2          0.0235    True
   anaw0.5     0.0365       -0.0166 f0 panel C2 clean          0.0224    True

**selected: anag0.25_1**

| layer | n | main | delta |
|---|---:|---:|---:|
| fe dev2 C C2 | 100 | 0.601 | +0.0098 |
| fe dev2 D C2 | 100 | 0.251 | -0.0116 |
| fe dev2 E C2 | 100 | 0.241 | +0.1809 |
| fe dev2 F C2 | 100 | 0.233 | +0.0674 |
| fe dev2 G C2 | 100 | 0.650 | +0.0598 |
| f0 dev2 C C2 | 100 | 0.612 | -0.0195 |
| f0 dev2 D C2 | 100 | 0.267 | -0.0063 |
| f0 dev2 E C2 | 100 | 0.235 | +0.1678 |
| f0 dev2 F C2 | 100 | 0.229 | +0.0844 |
| f0 dev2 G C2 | 100 | 0.637 | +0.0657 |
| f0 panel C2 clean | 202 | 0.893 | -0.0133 |
| f0 W7 A C2 | 300 | 0.790 | +0.0167 |
| f0 W7 B C2 | 300 | 0.443 | +0.0017 |
| fe panel C1 clean | 202 | 0.897 | +0.0223 |
| fe panel C1 uncertain | 48 | 0.976 | +0.0139 |
| f0 panel C1 clean (unseen) | 202 | 0.862 | +0.0406 |
| f0 W7 B C1 | 72 | 0.901 | +0.0316 |
| fe dev2 C C1 (unseen stress) | 95 | 0.899 | +0.0576 |
| fe dev2 E C1 (unseen stress) | 59 | 0.567 | +0.3644 |
| fe dev2 F C1 (unseen stress) | 38 | 0.630 | +0.1368 |
| fe dev2 G C1 (unseen stress) | 100 | 0.604 | +0.1455 |

## Confirmation (fresh sets, fold-0 tables): ['diag/gf6_conffit2_m2x.csv']

| layer | n | main | delta [95% paired bootstrap] |
|---|---:|---:|---|
| D_np_single C2 | 150 | 0.275 | +0.0135 [+0.0027, +0.0268] |
| E_np_negonly C1 | 118 | 0.599 | +0.3395 [+0.2638, +0.4177] |
| E_np_negonly C2 | 200 | 0.280 | +0.1060 [+0.0715, +0.1421] |
| D_np_single C2 (anag0.25_1 - anaw0.5) | 150 | | -0.0140 [-0.0257, -0.0044] |
| E_np_negonly C1 (anag0.25_1 - anaw0.5) | 118 | | +0.0557 [+0.0281, +0.0858] |
| E_np_negonly C2 (anag0.25_1 - anaw0.5) | 200 | | +0.0126 [-0.0036, +0.0284] |
| all C2 (pooled) | 350 | 0.278 | +0.0664 [+0.0454, +0.0883] |