# learned-fusion probe: run_v3_c1/B_nplib/rank_v4d (w_ice 0.0; 23 features)

## view c1: 257 molecules, truth in shortlist 257 (strict MRR over 257; GL fallback molecules 4)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.924 | 0.887 |
| pipeline | 0.924 | 0.887 |
| fixed | 0.546 | 0.401 |
| lib | 0.904 | 0.868 |
| guard0.6_0.1 | 0.931 | 0.903 |
| guard0.7_0.1 | 0.930 | 0.899 |
| guard0.7_0.2 | 0.928 | 0.895 |
| guard0.8_0.1 | 0.928 | 0.895 |
| guard0.8_0.2 | 0.926 | 0.891 |
| guard0.9_0.1 | 0.926 | 0.891 |
| guard0.9_0.2 | 0.926 | 0.891 |
| fguard0.6_0.1 | 0.827 | 0.770 |
| fguard0.7_0.1 | 0.790 | 0.724 |
| fguard0.7_0.2 | 0.760 | 0.685 |
| fguard0.8_0.1 | 0.761 | 0.685 |
| fguard0.8_0.2 | 0.734 | 0.650 |
| fguard0.9_0.1 | 0.680 | 0.572 |
| fguard0.9_0.2 | 0.658 | 0.545 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.642 | 0.502 |
| no_counts (lib_nref/in_train=0) | 0.924 | 0.887 |
| no_sim (lib_sim/same=0) | 0.642 | 0.502 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.920 | 0.879 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 72 | 0.889 | 0.522 | 0.816 | 1.00 |
| [6,20] | 161 | 0.939 | 0.547 | 0.942 | 1.00 |
| [21,100] | 24 | 0.924 | 0.611 | 0.912 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 68 | 0.812 | 0.575 | 0.704 |
| [0.60,0.80) | 49 | 0.961 | 0.537 | 0.952 |
| [0.80,0.90) | 55 | 0.953 | 0.557 | 0.982 |
| [0.90,0.95) | 39 | 0.962 | 0.563 | 0.966 |
| [0.95,1.00) | 46 | 0.983 | 0.483 | 1.000 |

learned loses (fixed top-1, learned not): 4; learned wins (learned top-1, fixed not): 129

lost molecules: learned top-1 has in_train 1.00 / lib_nref mean 4.2 / lib_sim mean 0.354 / pop mean 7.53; truth has in_train 1.00 / lib_nref mean 11.2 / lib_sim mean 0.199 / pop mean 9.51

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.860 | -0.019 | 0.137 |
| lib_sim | -0.434 | 0.199 | 0.354 |
| fp | -0.283 | -0.404 | 0.358 |
| lsynonyms | -0.196 | 2.565 | 2.554 |
| lib_same | -0.189 | 0.199 | 0.350 |
| src_bit | -0.174 | 0.250 | 0.500 |
| lotus | -0.079 | 1.401 | 0.973 |
| ppm_err | -0.074 | 0.963 | 0.963 |
| in_coconut | +0.045 | 0.500 | 0.250 |
| fp_rank_window | +0.081 | 2.911 | 2.826 |
| gl | +0.365 | 0.343 | 0.259 |
| z_gl | +0.607 | 2.992 | 1.852 |

## view c2: 300 molecules, truth in shortlist 233 (strict MRR over 300; GL fallback molecules -465)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.535 | 0.430 |
| pipeline | 0.535 | 0.430 |
| fixed | 0.433 | 0.323 |
| lib | 0.094 | 0.050 |
| guard0.6_0.1 | 0.524 | 0.413 |
| guard0.7_0.1 | 0.530 | 0.420 |
| guard0.7_0.2 | 0.533 | 0.427 |
| guard0.8_0.1 | 0.533 | 0.427 |
| guard0.8_0.2 | 0.535 | 0.430 |
| guard0.9_0.1 | 0.535 | 0.430 |
| guard0.9_0.2 | 0.535 | 0.430 |
| fguard0.6_0.1 | 0.423 | 0.310 |
| fguard0.7_0.1 | 0.428 | 0.317 |
| fguard0.7_0.2 | 0.429 | 0.317 |
| fguard0.8_0.1 | 0.432 | 0.323 |
| fguard0.8_0.2 | 0.433 | 0.323 |
| fguard0.9_0.1 | 0.432 | 0.323 |
| fguard0.9_0.2 | 0.433 | 0.323 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.530 | 0.423 |
| no_counts (lib_nref/in_train=0) | 0.535 | 0.430 |
| no_sim (lib_sim/same=0) | 0.530 | 0.423 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.392 | 0.247 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 233 | 0.689 | 0.557 | 0.121 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 233 | 0.689 | 0.557 | 0.121 |

learned loses (fixed top-1, learned not): 13; learned wins (learned top-1, fixed not): 45

lost molecules: learned top-1 has in_train 0.62 / lib_nref mean 5.8 / lib_sim mean 0.281 / pop mean 4.73; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 5.82

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -1.227 | -0.277 | 0.004 |
| lib_sim | -0.331 | 0.000 | 0.281 |
| src_bit | -0.114 | 0.077 | 0.231 |
| fp_rank_window | -0.113 | 2.669 | 2.244 |
| fp | -0.065 | 23.198 | 28.389 |
| z_fp | -0.053 | 0.848 | 0.979 |
| ce_known | -0.048 | 0.000 | 0.000 |
| ppm_err | -0.042 | 1.030 | 1.030 |
| pop_public | +0.082 | 5.816 | 4.728 |
| in_coconut | +0.105 | 0.308 | 0.154 |
| gl | +0.273 | 0.450 | 0.402 |
| z_gl | +0.392 | 2.926 | 2.335 |

