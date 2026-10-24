# learned-fusion probe: run_c1_v2/B_nplib/rank_v4g (w_ice 1.0; 26 features)

## view c1: 257 molecules, truth in shortlist 257 (strict MRR over 257; GL fallback molecules 4)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.903 | 0.860 |
| pipeline | 0.901 | 0.856 |
| fixed | 0.561 | 0.428 |
| lib | 0.906 | 0.868 |
| guard0.6_0.1 | 0.922 | 0.891 |
| guard0.7_0.1 | 0.918 | 0.883 |
| guard0.8_0.1 | 0.913 | 0.875 |
| guard0.8_0.2 | 0.913 | 0.875 |
| guard0.9_0.2 | 0.906 | 0.864 |
| fguard0.6_0.1 | 0.824 | 0.767 |
| fguard0.7_0.1 | 0.791 | 0.720 |
| fguard0.8_0.1 | 0.762 | 0.681 |
| fguard0.8_0.2 | 0.740 | 0.654 |
| fguard0.9_0.2 | 0.665 | 0.553 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.686 | 0.556 |
| no_counts (lib_nref/in_train=0) | 0.903 | 0.860 |
| no_sim (lib_sim/same=0) | 0.686 | 0.556 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.905 | 0.860 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 72 | 0.860 | 0.507 | 0.821 | 1.00 |
| [6,20] | 161 | 0.914 | 0.584 | 0.943 | 1.00 |
| [21,100] | 24 | 0.958 | 0.573 | 0.912 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 68 | 0.797 | 0.566 | 0.713 |
| [0.60,0.80) | 49 | 0.904 | 0.563 | 0.952 |
| [0.80,0.90) | 55 | 0.921 | 0.565 | 0.982 |
| [0.90,0.95) | 39 | 0.964 | 0.613 | 0.966 |
| [0.95,1.00) | 46 | 0.986 | 0.504 | 1.000 |

learned loses (fixed top-1, learned not): 5; learned wins (learned top-1, fixed not): 116

lost molecules: learned top-1 has in_train 0.80 / lib_nref mean 7.4 / lib_sim mean 0.303 / pop mean 10.60; truth has in_train 1.00 / lib_nref mean 9.0 / lib_sim mean 0.186 / pop mean 11.11

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.712 | 0.093 | 0.210 |
| z_fp | -0.308 | 0.259 | 1.016 |
| lib_sim | -0.296 | 0.186 | 0.303 |
| src_bit | -0.108 | 0.600 | 0.800 |
| fp | -0.105 | 31.023 | 41.397 |
| ce_known | -0.089 | 0.400 | 0.400 |
| fp_rank_window | -0.052 | 3.048 | 2.219 |
| ppm_err | -0.040 | 0.295 | 0.295 |
| z_ice | +0.097 | 2.455 | 2.048 |
| pop_public | +0.124 | 11.110 | 10.599 |
| lpmid | +0.157 | 3.748 | 3.257 |
| z_gl | +0.506 | 3.127 | 2.086 |

## view c2: 300 molecules, truth in shortlist 216 (strict MRR over 300; GL fallback molecules -431)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.566 | 0.493 |
| pipeline | 0.565 | 0.490 |
| fixed | 0.425 | 0.323 |
| lib | 0.115 | 0.060 |
| guard0.6_0.1 | 0.549 | 0.463 |
| guard0.7_0.1 | 0.556 | 0.473 |
| guard0.8_0.1 | 0.561 | 0.483 |
| guard0.8_0.2 | 0.563 | 0.487 |
| guard0.9_0.2 | 0.566 | 0.493 |
| fguard0.6_0.1 | 0.415 | 0.307 |
| fguard0.7_0.1 | 0.420 | 0.313 |
| fguard0.8_0.1 | 0.423 | 0.320 |
| fguard0.8_0.2 | 0.424 | 0.320 |
| fguard0.9_0.2 | 0.425 | 0.323 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.543 | 0.453 |
| no_counts (lib_nref/in_train=0) | 0.566 | 0.493 |
| no_sim (lib_sim/same=0) | 0.543 | 0.453 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.408 | 0.270 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 216 | 0.787 | 0.591 | 0.160 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 216 | 0.787 | 0.591 | 0.160 |

learned loses (fixed top-1, learned not): 10; learned wins (learned top-1, fixed not): 61

lost molecules: learned top-1 has in_train 0.60 / lib_nref mean 5.6 / lib_sim mean 0.202 / pop mean 7.02; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 7.32

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.765 | -0.271 | -0.069 |
| z_fp | -0.328 | 0.343 | 1.006 |
| lib_sim | -0.180 | 0.000 | 0.202 |
| fp_rank_window | -0.145 | 3.189 | 2.386 |
| src_bit | -0.122 | 0.200 | 0.400 |
| fp | -0.109 | 33.185 | 40.730 |
| ppm_err | -0.037 | 0.485 | 0.485 |
| ce_known | -0.033 | 0.100 | 0.100 |
| gl | +0.096 | 0.460 | 0.390 |
| lsynonyms | +0.097 | 2.576 | 2.443 |
| z_ice | +0.160 | 2.175 | 1.752 |
| z_gl | +0.522 | 2.387 | 1.619 |

