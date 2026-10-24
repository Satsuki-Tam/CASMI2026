# learned-fusion probe: run_v3_eval/A_timstof/rank_v4b (w_ice 0.0; 23 features)

## view c1: 7 molecules, truth in shortlist 7 (strict MRR over 7; GL fallback molecules 0)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.698 | 0.571 |
| pipeline | 0.698 | 0.571 |
| fixed | 0.634 | 0.571 |
| lib | 0.786 | 0.714 |
| guard0.8 | 0.793 | 0.714 |
| guard0.9 | 0.698 | 0.571 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.632 | 0.571 |
| no_counts (lib_nref/in_train=0) | 0.698 | 0.571 |
| no_sim (lib_sim/same=0) | 0.632 | 0.571 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.738 | 0.571 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [6,20] | 7 | 0.698 | 0.634 | 0.786 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 2 | 0.525 | 0.526 | 0.250 |
| [0.60,0.80) | 2 | 0.750 | 1.000 | 1.000 |
| [0.80,0.90) | 3 | 0.778 | 0.462 | 1.000 |

learned loses (fixed top-1, learned not): 1; learned wins (learned top-1, fixed not): 1

lost molecules: learned top-1 has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 2.54; truth has in_train 1.00 / lib_nref mean 10.0 / lib_sim mean 0.678 / pop mean 1.04

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| fp_rank_window | -1.127 | 2.773 | 0.693 |
| z_fp | -0.942 | 0.976 | 1.537 |
| ce_known | -0.330 | 1.000 | 1.000 |
| lib_same | -0.255 | 0.678 | 0.000 |
| n_query | -0.139 | 4.000 | 4.000 |
| ppm_err | -0.099 | 0.800 | 0.800 |
| fp | -0.086 | -12.778 | 12.087 |
| lib_max_mol | -0.024 | 0.678 | 0.678 |
| z_gl | +0.272 | 4.131 | 3.183 |
| lib_sim | +0.355 | 0.678 | 0.000 |
| pop_public | +0.496 | 1.040 | 2.544 |
| lib_margin | +0.518 | 0.123 | -0.555 |

## view c2: 300 molecules, truth in shortlist 283 (strict MRR over 300; GL fallback molecules -566)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.805 | 0.737 |
| pipeline | 0.805 | 0.737 |
| fixed | 0.652 | 0.527 |
| lib | 0.000 | 0.000 |
| guard0.8 | 0.773 | 0.677 |
| guard0.9 | 0.789 | 0.707 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.762 | 0.667 |
| no_counts (lib_nref/in_train=0) | 0.805 | 0.737 |
| no_sim (lib_sim/same=0) | 0.762 | 0.667 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.681 | 0.567 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 283 | 0.853 | 0.692 | 0.000 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 283 | 0.853 | 0.692 | 0.000 |

learned loses (fixed top-1, learned not): 12; learned wins (learned top-1, fixed not): 75

lost molecules: learned top-1 has in_train 0.08 / lib_nref mean 0.1 / lib_sim mean 0.051 / pop mean 1.81; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 1.84

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lsynonyms | -0.189 | 0.723 | 1.045 |
| pop_public | -0.148 | 1.843 | 1.810 |
| lib_margin | -0.092 | -0.355 | -0.304 |
| z_fp | -0.087 | 1.413 | 1.373 |
| fp_rank_window | -0.065 | 1.904 | 1.726 |
| fp | -0.051 | -7.410 | -7.581 |
| lsid | -0.050 | 1.481 | 1.288 |
| lib_sim | -0.046 | 0.000 | 0.051 |
| lib_max_mol | +0.008 | 0.495 | 0.495 |
| n_cands | +0.008 | 254.083 | 254.083 |
| z_gl | +0.039 | 3.949 | 3.587 |
| gl | +0.055 | 0.538 | 0.507 |

