# 107 reading: ranker data scaling with cross-fitting (CF - v8w7a)

## Checks

| tag | rows | v8w7a vs 102 diff | cf0 vs v8w7a diff |
|---|---:|---:|---:|
| np053f1dev | 372 | 0 | 0 |
| np053f2dev | 389 | 0 | 0 |
| f1dev | 794 | 0 | 0 |
| f2dev | 795 | 0 | 0 |
| panel | 500 | 0 | 0 |
| p2dev | 792 | 0 | 0 |

## Decision

- **primary 1/2 A + 1/2 B_D: +0.0090 [+0.0036, +0.0151]**
- A 053 NP C2: +0.0085 [+0.0034, +0.0144]
- B_D f1/f2 D C2: +0.0094 [+0.0003, +0.0207]
- by side (point estimates; fold-A rows scored by cfB, fold-B rows by cfA): A-side +0.0099, B-side +0.0076; fit identity groups cfA 2911, cfB 2938, cfall 3589
- old B f1/f2 NP C2 (C-F): +0.0039 [-0.0010, +0.0089] (non-inferior)
- G C1 (f1/f2): +0.0007 [-0.0158, +0.0167] (undetermined)
- panel C1 clean (cfall): -0.0070 [-0.0194, +0.0049] (undetermined)
- 053 NP C1 (4 cells): +0.0074 [-0.0092, +0.0259] (non-inferior)
- dev2 NP C2 (cfall, stress): -0.0071 [-0.0173, +0.0025]
- **gate: NO**

## Diagnostics (row means; cfall on the development tables is in-fit and not shown)

| layer | n | v8w7a | CF | rescued / lost (CF vs v8w7a) |
|---|---:|---:|---:|---|
| A 053 NP C2 | 520 | 0.5808 | 0.5940 | 39 / 26 |
| B_D f1/f2 D C2 | 200 | 0.2782 | 0.2876 | 9 / 4 |
| old B f1/f2 NP C2 (C-F) | 800 | 0.4217 | 0.4256 | 24 / 22 |
| G C1 (f1/f2) | 200 | 0.8830 | 0.8836 | 9 / 7 |
| panel C1 clean (cfall) | 202 | 0.9251 | 0.9181 | 5 / 10 |
| 053 NP C1 (4 cells) | 113 | 0.8530 | 0.8628 | 6 / 5 |
