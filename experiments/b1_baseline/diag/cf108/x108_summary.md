# 108 reading: 107 data + C1 weight-share restoration (decision: CF_w - v8w7a; mechanism: CF_w - CF_unweighted)

## Checks

| tag | rows | v8w7a vs 102 diff | (cf0 check in 107) |
|---|---:|---:|---:|
| np053f1dev | 372 | 0 | 0 |
| np053f2dev | 389 | 0 | 0 |
| f1dev | 794 | 0 | 0 |
| f2dev | 795 | 0 | 0 |
| panel | 500 | 0 | 0 |
| p2dev | 792 | 0 | 0 |

## Decision

- **primary 1/2 A + 1/2 B_D: +0.0026 [-0.0030, +0.0079]**
- A 053 NP C2: +0.0088 [+0.0034, +0.0148]
- B_D f1/f2 D C2: -0.0037 [-0.0133, +0.0053]
- by side (point estimates; fold-A rows scored by cfB, fold-B rows by cfA): A-side +0.0029, B-side +0.0022; fit identity groups cfA 2911, cfB 2938, cfall 3589

## Mechanism (weighted - 107 unweighted, same rows and scoring direction; descriptive)
- A 053 NP C2: +0.0004 (row mean, n 520)
- B_D f1/f2 D C2: -0.0131 (row mean, n 200)
- G C1: -0.0023 (row mean, n 200)
- panel C1 clean: +0.0054 (row mean, n 202)
- 053 NP C1: +0.0010 (row mean, n 113)
- old B f1/f2 NP C2 (C-F): -0.0018 [-0.0063, +0.0027] (non-inferior)
- G C1 (f1/f2): -0.0017 [-0.0158, +0.0133] (undetermined)
- panel C1 clean (cfall): -0.0015 [-0.0159, +0.0126] (undetermined)
- 053 NP C1 (4 cells): +0.0078 [-0.0086, +0.0263] (non-inferior)
- dev2 NP C2 (cfall, stress): -0.0089 [-0.0182, -0.0003]
- **gate: NO**

## Diagnostics (row means; cfall on the development tables is in-fit and not shown)

| layer | n | v8w7a | CF | rescued / lost (CF vs v8w7a) |
|---|---:|---:|---:|---|
| A 053 NP C2 | 520 | 0.5808 | 0.5944 | 39 / 23 |
| B_D f1/f2 D C2 | 200 | 0.2782 | 0.2745 | 6 / 8 |
| old B f1/f2 NP C2 (C-F) | 800 | 0.4217 | 0.4199 | 19 / 26 |
| G C1 (f1/f2) | 200 | 0.8830 | 0.8813 | 5 / 6 |
| panel C1 clean (cfall) | 202 | 0.9251 | 0.9235 | 6 / 9 |
| 053 NP C1 (4 cells) | 113 | 0.8530 | 0.8638 | 7 / 4 |
