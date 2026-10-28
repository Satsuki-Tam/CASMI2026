# FP-collision audit of the v8w7a main's C2 errors with the truth in the list (rP > 1)

| tag set | errors | top-1 same formula | top-1 FP-identical to truth | truth FP-identical to any same-formula candidate | median Tanimoto top-1 vs truth | share Tanimoto >= 0.9 |
|---|---:|---:|---:|---:|---:|---:|
| f1dev C_np_crosslib | 24 | 1.000 | 0.000 | 0.000 | 0.517 | 0.000 |
| f1dev D_np_single | 16 | 0.750 | 0.000 | 0.000 | 0.699 | 0.188 |
| f1dev E_np_negonly | 54 | 0.907 | 0.000 | 0.000 | 0.599 | 0.093 |
| f1dev F_np_uncovered | 47 | 0.894 | 0.000 | 0.000 | 0.489 | 0.085 |
| f1dev G_tims_crosslib | 21 | 0.952 | 0.000 | 0.000 | 0.718 | 0.000 |
| np053f1dev NP_H | 62 | 0.871 | 0.000 | 0.000 | 0.510 | 0.065 |
| np053f1dev NP_N | 27 | 0.889 | 0.000 | 0.000 | 0.776 | 0.296 |
| np053f1dev NP_X | 28 | 1.000 | 0.000 | 0.000 | 0.926 | 0.714 |
| f2dev C_np_crosslib | 28 | 0.964 | 0.000 | 0.000 | 0.506 | 0.071 |
| f2dev D_np_single | 20 | 0.900 | 0.000 | 0.000 | 0.504 | 0.050 |
| f2dev E_np_negonly | 48 | 0.896 | 0.000 | 0.000 | 0.599 | 0.042 |
| f2dev F_np_uncovered | 39 | 0.949 | 0.000 | 0.000 | 0.451 | 0.103 |
| f2dev G_tims_crosslib | 20 | 1.000 | 0.000 | 0.000 | 0.736 | 0.000 |
| np053f2dev NP_H | 64 | 0.969 | 0.000 | 0.000 | 0.638 | 0.172 |
| np053f2dev NP_N | 32 | 0.875 | 0.000 | 0.000 | 0.684 | 0.156 |
| np053f2dev NP_X | 30 | 0.933 | 0.000 | 0.000 | 0.926 | 0.667 |
| **all** | 560 | 0.921 | 0.000 | 0.000 | 0.634 | 0.159 |
