# Structural relation of the truth and P's wrong rank-1 (C2 errors with the truth in the list, folds 1+2; descriptive)

rows 560 of 560 (both SMILES parsed)

| strata | errors | same formula | same Murcko scaffold (of same-formula) | Tanimoto q25/q50/q75 (same formula) | truth has a sugar ring | top-1 is train | FP prefers truth |
|---|---:|---:|---:|---|---:|---:|---:|
| NP (np053 NP_H/X/N, f1/f2 D) | 279 | 0.91 | 0.57 | 0.45 / 0.74 / 0.91 | 0.10 | 0.58 | 0.34 |
| other (C, E, F, G) | 281 | 0.93 | 0.38 | 0.37 / 0.61 / 0.80 | 0.10 | 0.52 | 0.35 |

| strata | same scaffold | n | Tanimoto median | top-1 is train | FP prefers truth | median FP gap |
|---|---|---:|---:|---:|---:|---:|
| NP | False | 109 | 0.45 | 0.55 | 0.34 | -6.1 |
| NP | True | 145 | 0.89 | 0.68 | 0.30 | -3.8 |
| other | False | 162 | 0.51 | 0.49 | 0.34 | -6.3 |
| other | True | 100 | 0.77 | 0.66 | 0.30 | -3.5 |
