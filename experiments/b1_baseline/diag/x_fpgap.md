# FP score of the truth vs the main's wrong rank-1 (C2 errors with the truth in the list; table fp = merged-logit f.z)

| tag set | errors | FP prefers truth (gap > 0) | median gap | truth FP rank 1 in list | truth FP rank 2-5 | truth prior below top-1 | FP prefers truth AND prior below | top-1 is a train structure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| f1dev C_np_crosslib | 24 | 0.292 | -8.06 | 0.000 | 0.083 | 0.750 | 0.292 | 0.417 |
| f1dev D_np_single | 16 | 0.188 | -3.99 | 0.000 | 0.188 | 0.625 | 0.125 | 0.438 |
| f1dev E_np_negonly | 54 | 0.389 | -3.52 | 0.111 | 0.222 | 0.667 | 0.278 | 0.667 |
| f1dev F_np_uncovered | 47 | 0.426 | -2.92 | 0.064 | 0.255 | 0.681 | 0.277 | 0.511 |
| f1dev G_tims_crosslib | 21 | 0.333 | -3.46 | 0.095 | 0.381 | 0.476 | 0.143 | 0.429 |
| np053f1dev NP_H | 62 | 0.242 | -8.78 | 0.016 | 0.113 | 0.694 | 0.210 | 0.548 |
| np053f1dev NP_N | 27 | 0.444 | -3.24 | 0.111 | 0.148 | 0.556 | 0.148 | 0.556 |
| np053f1dev NP_X | 28 | 0.321 | -2.20 | 0.036 | 0.286 | 0.643 | 0.250 | 0.786 |
| f2dev C_np_crosslib | 28 | 0.321 | -5.66 | 0.071 | 0.143 | 0.607 | 0.286 | 0.321 |
| f2dev D_np_single | 20 | 0.550 | +2.14 | 0.100 | 0.100 | 0.650 | 0.450 | 0.300 |
| f2dev E_np_negonly | 48 | 0.396 | -1.34 | 0.104 | 0.292 | 0.583 | 0.229 | 0.562 |
| f2dev F_np_uncovered | 39 | 0.256 | -5.54 | 0.026 | 0.026 | 0.744 | 0.154 | 0.667 |
| f2dev G_tims_crosslib | 20 | 0.300 | -2.71 | 0.200 | 0.500 | 0.350 | 0.100 | 0.250 |
| np053f2dev NP_H | 64 | 0.328 | -4.08 | 0.016 | 0.203 | 0.688 | 0.250 | 0.453 |
| np053f2dev NP_N | 32 | 0.469 | -2.51 | 0.094 | 0.375 | 0.719 | 0.406 | 0.844 |
| np053f2dev NP_X | 30 | 0.300 | -3.57 | 0.000 | 0.167 | 0.700 | 0.167 | 0.733 |
| **all** | 560 | 0.346 | -4.01 | 0.061 | 0.209 | 0.650 | 0.239 | 0.550 |
