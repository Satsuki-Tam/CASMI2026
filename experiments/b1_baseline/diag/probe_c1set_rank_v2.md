# learned-fusion probe: run_c1_v2/B_nplib/rank_v2 (w_ice 1.0; 28 features)

## view c1: 257 molecules, truth in shortlist 257 (strict MRR over 257; GL fallback molecules 4)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.886 | 0.817 |
| pipeline | 0.884 | 0.813 |
| fixed | 0.561 | 0.428 |
| lib | 0.906 | 0.868 |
| guard0.8 | 0.912 | 0.864 |
| guard0.9 | 0.893 | 0.829 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.650 | 0.510 |
| no_counts (lib_nref/in_train=0) | 0.864 | 0.790 |
| no_sim (lib_sim/same=0) | 0.696 | 0.576 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.905 | 0.864 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 72 | 0.891 | 0.507 | 0.821 | 1.00 |
| [6,20] | 161 | 0.882 | 0.584 | 0.943 | 1.00 |
| [21,100] | 24 | 0.896 | 0.573 | 0.912 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 68 | 0.840 | 0.566 | 0.713 |
| [0.60,0.80) | 49 | 0.851 | 0.563 | 0.952 |
| [0.80,0.90) | 55 | 0.866 | 0.565 | 0.982 |
| [0.90,0.95) | 39 | 0.941 | 0.613 | 0.966 |
| [0.95,1.00) | 46 | 0.969 | 0.504 | 1.000 |

learned loses (fixed top-1, learned not): 8; learned wins (learned top-1, fixed not): 108

lost molecules: learned top-1 has in_train 0.12 / lib_nref mean 3.0 / lib_sim mean 0.100 / pop mean 6.49; truth has in_train 1.00 / lib_nref mean 13.9 / lib_sim mean 0.628 / pop mean 7.57

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_gl | -0.459 | 2.819 | 2.697 |
| lsynonyms | -0.340 | 2.186 | 2.538 |
| z_ice | -0.332 | 2.454 | 2.259 |
| pop_public | -0.228 | 7.573 | 6.485 |
| z_fp | -0.153 | 1.515 | 0.904 |
| gl | -0.117 | 0.418 | 0.405 |
| fp_rank_window | -0.105 | 1.861 | 2.195 |
| ice | -0.062 | 0.359 | 0.343 |
| ce_known | +0.064 | 0.125 | 0.125 |
| lpmid | +0.101 | 2.532 | 1.266 |
| lib_sim | +0.190 | 0.628 | 0.100 |
| lib_margin | +0.902 | 0.320 | -0.207 |

## view c2: 300 molecules, truth in shortlist 216 (strict MRR over 300; GL fallback molecules -431)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.566 | 0.487 |
| pipeline | 0.564 | 0.483 |
| fixed | 0.425 | 0.323 |
| lib | 0.115 | 0.060 |
| guard0.8 | 0.562 | 0.480 |
| guard0.9 | 0.566 | 0.487 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.518 | 0.420 |
| no_counts (lib_nref/in_train=0) | 0.548 | 0.460 |
| no_sim (lib_sim/same=0) | 0.559 | 0.477 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.393 | 0.267 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 216 | 0.785 | 0.591 | 0.160 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 216 | 0.785 | 0.591 | 0.160 |

learned loses (fixed top-1, learned not): 9; learned wins (learned top-1, fixed not): 58

lost molecules: learned top-1 has in_train 0.44 / lib_nref mean 3.7 / lib_sim mean 0.251 / pop mean 3.43; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 3.54

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.949 | -0.357 | -0.107 |
| lsynonyms | -0.084 | 1.279 | 1.496 |
| ce_known | -0.062 | 0.000 | 0.000 |
| lib_sim | -0.051 | 0.000 | 0.251 |
| fp | -0.049 | 20.346 | 15.373 |
| in_coconut | -0.048 | 0.222 | 0.222 |
| lib_nref | -0.042 | 0.000 | 3.667 |
| n_query | -0.035 | 2.667 | 2.667 |
| pop_public | +0.040 | 3.538 | 3.432 |
| gl | +0.094 | 0.503 | 0.461 |
| z_ice | +0.353 | 2.232 | 1.956 |
| z_gl | +0.391 | 2.941 | 2.451 |

