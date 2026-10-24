# library-priority rule: per-molecule dRR vs base S(2,1,0.5)

fired ~ lib_max >= tau (margin condition not recoverable from the CSV); 'changed' = truth rank differs.

## P_np250 / view c2 (n=250; base MRR 0.864; lib-only MRR 0.095)

| lib_max bin | n | best-match-is-truth | base MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 154 | 0.097 | 0.911 | 0.115 |
| [0.60,0.80) | 65 | 0.000 | 0.801 | 0.070 |
| [0.80,0.90) | 26 | 0.000 | 0.775 | 0.045 |
| [0.90,0.95) | 5 | 0.000 | 0.695 | 0.037 |

| rule | MRR | dRR mean | rescued (sum dRR) | hurt (sum dRR) | changed | lib_max>=tau | of which truth is best match | mis-promotion (truth_lib < lib_max) : n / hurt / dRR sum | hurt among base top-1 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| libpri(tau=0.9,m=0.2)>S(2,1,0.5) | 0.860 | -0.0040 | 0 (+0.00) | 2 (-1.00) | 2 | 5 | 0 (dRR +0.00) | 5 / 2 / -1.00 | 2 |
|  ↳ by lib_max bin | [0.00,0.60) n=154 dRR=+0.000; [0.60,0.80) n=65 dRR=+0.000; [0.80,0.90) n=26 dRR=+0.000; [0.90,0.95) n=5 dRR=-0.200 | | | | | | | | |
| libpri(tau=0.8,m=0.2)>S(2,1,0.5) | 0.842 | -0.0220 | 0 (+0.00) | 11 (-5.50) | 11 | 31 | 0 (dRR +0.00) | 31 / 11 / -5.50 | 11 |
|  ↳ by lib_max bin | [0.00,0.60) n=154 dRR=+0.000; [0.60,0.80) n=65 dRR=+0.000; [0.80,0.90) n=26 dRR=-0.173; [0.90,0.95) n=5 dRR=-0.200 | | | | | | | | |

## P_np250 / view c1 (n=250; base MRR 0.864; lib-only MRR 0.909)

| lib_max bin | n | best-match-is-truth | base MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 16 | 0.625 | 0.706 | 0.736 |
| [0.60,0.80) | 82 | 0.768 | 0.844 | 0.858 |
| [0.80,0.90) | 122 | 0.943 | 0.899 | 0.965 |
| [0.90,0.95) | 29 | 0.828 | 0.856 | 0.908 |
| [0.95,1.00) | 1 | 1.000 | 1.000 | 1.000 |

| rule | MRR | dRR mean | rescued (sum dRR) | hurt (sum dRR) | changed | lib_max>=tau | of which truth is best match | mis-promotion (truth_lib < lib_max) : n / hurt / dRR sum | hurt among base top-1 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| libpri(tau=0.9,m=0.2)>S(2,1,0.5) | 0.867 | +0.0030 | 1 (+0.75) | 0 (+0.00) | 1 | 30 | 25 (dRR +0.75) | 5 / 0 / +0.00 | 0 |
|  ↳ by lib_max bin | [0.00,0.60) n=16 dRR=+0.000; [0.60,0.80) n=82 dRR=+0.000; [0.80,0.90) n=122 dRR=+0.000; [0.90,0.95) n=29 dRR=+0.026; [0.95,1.00) n=1 dRR=+0.000 | | | | | | | | |
| libpri(tau=0.8,m=0.2)>S(2,1,0.5) | 0.887 | +0.0226 | 7 (+5.66) | 0 (+0.00) | 7 | 152 | 140 (dRR +5.66) | 12 / 0 / +0.00 | 0 |
|  ↳ by lib_max bin | [0.00,0.60) n=16 dRR=+0.000; [0.60,0.80) n=82 dRR=+0.000; [0.80,0.90) n=122 dRR=+0.040; [0.90,0.95) n=29 dRR=+0.026; [0.95,1.00) n=1 dRR=+0.000 | | | | | | | | |

## summary

| label | view | rule | n | base | rule | dRR | rescued | hurt | fired | mis-promotions (hurt) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P_np250 | c2 | libpri(tau=0.9,m=0.2)>S(2,1,0.5) | 250 | 0.864 | 0.860 | -0.0040 | 0 | 2 | 5 | 5 (2) |
| P_np250 | c2 | libpri(tau=0.8,m=0.2)>S(2,1,0.5) | 250 | 0.864 | 0.842 | -0.0220 | 0 | 11 | 31 | 31 (11) |
| P_np250 | c1 | libpri(tau=0.9,m=0.2)>S(2,1,0.5) | 250 | 0.864 | 0.867 | +0.0030 | 1 | 0 | 30 | 5 (0) |
| P_np250 | c1 | libpri(tau=0.8,m=0.2)>S(2,1,0.5) | 250 | 0.864 | 0.887 | +0.0226 | 7 | 0 | 152 | 12 (0) |
