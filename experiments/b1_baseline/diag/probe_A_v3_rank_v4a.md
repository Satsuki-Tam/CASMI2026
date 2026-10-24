# learned-fusion probe: run_v3_eval/A_timstof/rank_v4a (w_ice 0.0; 23 features)

## view c1: 7 molecules, truth in shortlist 7 (strict MRR over 7; GL fallback molecules 0)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.600 | 0.429 |
| pipeline | 0.600 | 0.429 |
| fixed | 0.634 | 0.571 |
| lib | 0.786 | 0.714 |
| guard0.8 | 0.786 | 0.714 |
| guard0.9 | 0.600 | 0.429 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.633 | 0.571 |
| no_counts (lib_nref/in_train=0) | 0.600 | 0.429 |
| no_sim (lib_sim/same=0) | 0.633 | 0.571 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.729 | 0.571 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [6,20] | 7 | 0.600 | 0.634 | 0.786 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 2 | 0.500 | 0.526 | 0.250 |
| [0.60,0.80) | 2 | 0.750 | 1.000 | 1.000 |
| [0.80,0.90) | 3 | 0.567 | 0.462 | 1.000 |

learned loses (fixed top-1, learned not): 1; learned wins (learned top-1, fixed not): 0

lost molecules: learned top-1 has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 2.54; truth has in_train 1.00 / lib_nref mean 10.0 / lib_sim mean 0.678 / pop mean 1.04

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_fp | -1.185 | 0.976 | 1.537 |
| fp_rank_window | -1.110 | 2.773 | 0.693 |
| lib_same | -0.373 | 0.678 | 0.000 |
| ce_known | -0.203 | 1.000 | 1.000 |
| gl | -0.199 | 0.633 | 0.530 |
| fp | -0.176 | -12.778 | 12.087 |
| n_query | -0.129 | 4.000 | 4.000 |
| ppm_err | -0.129 | 0.800 | 0.800 |
| lib_sim | +0.271 | 0.678 | 0.000 |
| lsid | +0.297 | 0.693 | 2.197 |
| pop_public | +0.572 | 1.040 | 2.544 |
| lib_margin | +1.126 | 0.123 | -0.555 |

## view c2: 300 molecules, truth in shortlist 283 (strict MRR over 300; GL fallback molecules -566)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.808 | 0.743 |
| pipeline | 0.808 | 0.743 |
| fixed | 0.652 | 0.527 |
| lib | 0.000 | 0.000 |
| guard0.8 | 0.774 | 0.677 |
| guard0.9 | 0.791 | 0.710 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.757 | 0.660 |
| no_counts (lib_nref/in_train=0) | 0.808 | 0.743 |
| no_sim (lib_sim/same=0) | 0.757 | 0.660 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.679 | 0.553 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 283 | 0.857 | 0.692 | 0.000 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 283 | 0.857 | 0.692 | 0.000 |

learned loses (fixed top-1, learned not): 10; learned wins (learned top-1, fixed not): 75

lost molecules: learned top-1 has in_train 0.10 / lib_nref mean 0.1 / lib_sim mean 0.061 / pop mean 1.87; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 1.83

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| pop_public | -0.221 | 1.832 | 1.875 |
| lsynonyms | -0.184 | 0.688 | 1.075 |
| z_fp | -0.140 | 1.428 | 1.350 |
| lsid | -0.051 | 1.488 | 1.337 |
| lib_sim | -0.030 | 0.000 | 0.061 |
| ppm_err | -0.029 | 0.749 | 0.749 |
| fp_rank_window | -0.025 | 1.896 | 1.840 |
| fp | -0.023 | -5.329 | -6.599 |
| gl | +0.004 | 0.556 | 0.527 |
| lib_same | +0.009 | 0.000 | 0.061 |
| n_cands | +0.010 | 253.900 | 253.900 |
| z_gl | +0.183 | 3.781 | 3.491 |

