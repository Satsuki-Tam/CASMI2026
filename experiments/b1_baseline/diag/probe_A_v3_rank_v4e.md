# learned-fusion probe: run_v3_eval/A_timstof/rank_v4e (w_ice 0.0; 23 features)

## view c1: 7 molecules, truth in shortlist 7 (strict MRR over 7; GL fallback molecules 0)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.875 | 0.857 |
| pipeline | 0.875 | 0.857 |
| fixed | 0.634 | 0.571 |
| lib | 0.786 | 0.714 |
| guard0.6_0.1 | 0.875 | 0.857 |
| guard0.7_0.1 | 0.875 | 0.857 |
| guard0.7_0.2 | 0.875 | 0.857 |
| guard0.8_0.1 | 0.875 | 0.857 |
| guard0.8_0.2 | 0.875 | 0.857 |
| guard0.9_0.1 | 0.875 | 0.857 |
| guard0.9_0.2 | 0.875 | 0.857 |
| fguard0.6_0.1 | 0.865 | 0.857 |
| fguard0.7_0.1 | 0.865 | 0.857 |
| fguard0.7_0.2 | 0.865 | 0.857 |
| fguard0.8_0.1 | 0.865 | 0.857 |
| fguard0.8_0.2 | 0.865 | 0.857 |
| fguard0.9_0.1 | 0.634 | 0.571 |
| fguard0.9_0.2 | 0.634 | 0.571 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.633 | 0.571 |
| no_counts (lib_nref/in_train=0) | 0.875 | 0.857 |
| no_sim (lib_sim/same=0) | 0.633 | 0.571 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.929 | 0.857 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [6,20] | 7 | 0.875 | 0.634 | 0.786 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 2 | 0.562 | 0.526 | 0.250 |
| [0.60,0.80) | 2 | 1.000 | 1.000 | 1.000 |
| [0.80,0.90) | 3 | 1.000 | 0.462 | 1.000 |

learned loses (fixed top-1, learned not): 0; learned wins (learned top-1, fixed not): 2

## view c2: 300 molecules, truth in shortlist 283 (strict MRR over 300; GL fallback molecules -566)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.703 | 0.577 |
| pipeline | 0.703 | 0.577 |
| fixed | 0.652 | 0.527 |
| lib | 0.000 | 0.000 |
| guard0.6_0.1 | 0.663 | 0.517 |
| guard0.7_0.1 | 0.676 | 0.527 |
| guard0.7_0.2 | 0.685 | 0.540 |
| guard0.8_0.1 | 0.691 | 0.553 |
| guard0.8_0.2 | 0.693 | 0.557 |
| guard0.9_0.1 | 0.701 | 0.573 |
| guard0.9_0.2 | 0.701 | 0.573 |
| fguard0.6_0.1 | 0.602 | 0.447 |
| fguard0.7_0.1 | 0.611 | 0.453 |
| fguard0.7_0.2 | 0.617 | 0.460 |
| fguard0.8_0.1 | 0.627 | 0.480 |
| fguard0.8_0.2 | 0.630 | 0.483 |
| fguard0.9_0.1 | 0.645 | 0.513 |
| fguard0.9_0.2 | 0.645 | 0.513 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.731 | 0.617 |
| no_counts (lib_nref/in_train=0) | 0.703 | 0.577 |
| no_sim (lib_sim/same=0) | 0.731 | 0.617 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.596 | 0.423 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 283 | 0.745 | 0.692 | 0.000 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 283 | 0.745 | 0.692 | 0.000 |

learned loses (fixed top-1, learned not): 26; learned wins (learned top-1, fixed not): 41

lost molecules: learned top-1 has in_train 0.50 / lib_nref mean 2.9 / lib_sim mean 0.403 / pop mean 1.90; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 1.91

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.885 | -0.396 | 0.008 |
| lib_sim | -0.581 | 0.000 | 0.403 |
| lib_same | -0.179 | 0.000 | 0.403 |
| pop_public | -0.077 | 1.914 | 1.897 |
| lsynonyms | -0.041 | 0.850 | 0.954 |
| lsid | -0.019 | 1.469 | 1.345 |
| ppm_err | -0.014 | 0.658 | 0.658 |
| lib_max_mol | -0.010 | 0.632 | 0.632 |
| z_fp | +0.116 | 1.560 | 1.490 |
| fp_rank_window | +0.136 | 1.565 | 1.589 |
| gl | +0.219 | 0.579 | 0.542 |
| z_gl | +0.603 | 3.967 | 3.594 |

