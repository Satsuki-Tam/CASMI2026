# 106 ICEBERG pilot (exploratory; fixed before the run)

## (1) truth's rank inside its formula group (rows with >= 2 ICE-scored group members)

| layer | rows | group size (median) | within-group MRR main / GL / ICE | ICE beats main (rows) | main beats ICE |
|---|---:|---:|---|---:|---:|
| C2 NP_H/NP_N (053) | 67 | 114 | 0.716 / 0.458 / 0.367 | 3 | 47 |
| C2 C/D (f1/f2) | 69 | 195 | 0.742 / 0.514 / 0.488 | 7 | 36 |
| C1 G (f1/f2) | 53 | 227 | 0.898 / 0.702 / 0.664 | 5 | 24 |
| C1 panel | 35 | 127 | 0.944 / 0.563 / 0.568 | 1 | 18 |

## (2) main top 25 with formula groups re-ordered by z(main) + 0.5 z(ICE) inside their own slots

| layer | rows | main | delta | rescued / lost |
|---|---:|---:|---|---|
| C2 NP_H/NP_N (053) | 118 | 0.5790 | -0.0127 [-0.0379, +0.0111] | 9 / 11 |
| C2 C/D (f1/f2) | 118 | 0.4499 | -0.0091 [-0.0342, +0.0147] | 7 / 13 |
| C1 G (f1/f2) | 60 | 0.8482 | -0.0278 [-0.0667, +0.0083] | 2 / 5 |
| C1 panel | 40 | 0.9388 | -0.0238 [-0.0625, +0.0024] | 1 / 2 |
