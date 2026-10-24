# learned-fusion probe: run_v3_c1/B_nplib/rank_v4c (w_ice 0.0; 23 features)

## view c1: 257 molecules, truth in shortlist 257 (strict MRR over 257; GL fallback molecules 4)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.926 | 0.891 |
| pipeline | 0.926 | 0.891 |
| fixed | 0.546 | 0.401 |
| lib | 0.904 | 0.868 |
| guard0.6_0.1 | 0.931 | 0.899 |
| guard0.7_0.1 | 0.932 | 0.899 |
| guard0.7_0.2 | 0.926 | 0.891 |
| guard0.8_0.1 | 0.931 | 0.899 |
| guard0.8_0.2 | 0.926 | 0.891 |
| guard0.9_0.1 | 0.931 | 0.899 |
| guard0.9_0.2 | 0.926 | 0.891 |
| fguard0.6_0.1 | 0.827 | 0.770 |
| fguard0.7_0.1 | 0.790 | 0.724 |
| fguard0.7_0.2 | 0.760 | 0.685 |
| fguard0.8_0.1 | 0.761 | 0.685 |
| fguard0.8_0.2 | 0.734 | 0.650 |
| fguard0.9_0.1 | 0.680 | 0.572 |
| fguard0.9_0.2 | 0.658 | 0.545 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.675 | 0.568 |
| no_counts (lib_nref/in_train=0) | 0.926 | 0.891 |
| no_sim (lib_sim/same=0) | 0.675 | 0.568 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.907 | 0.860 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 72 | 0.865 | 0.522 | 0.816 | 1.00 |
| [6,20] | 161 | 0.952 | 0.547 | 0.942 | 1.00 |
| [21,100] | 24 | 0.929 | 0.611 | 0.912 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 68 | 0.801 | 0.575 | 0.704 |
| [0.60,0.80) | 49 | 0.976 | 0.537 | 0.952 |
| [0.80,0.90) | 55 | 0.979 | 0.557 | 0.982 |
| [0.90,0.95) | 39 | 0.970 | 0.563 | 0.966 |
| [0.95,1.00) | 46 | 0.955 | 0.483 | 1.000 |

learned loses (fixed top-1, learned not): 3; learned wins (learned top-1, fixed not): 129

lost molecules: learned top-1 has in_train 1.00 / lib_nref mean 3.0 / lib_sim mean 0.233 / pop mean 6.51; truth has in_train 1.00 / lib_nref mean 11.0 / lib_sim mean 0.111 / pop mean 12.33

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_gl | -1.213 | 1.930 | 2.260 |
| lib_sim | -0.628 | 0.111 | 0.233 |
| src_bit | -0.495 | 0.333 | 0.667 |
| lib_margin | -0.467 | -0.025 | 0.097 |
| ppm_err | -0.349 | 1.275 | 1.275 |
| fp | -0.302 | 3.479 | 0.298 |
| fp_rank_window | -0.232 | 2.565 | 2.815 |
| lib_same | -0.101 | 0.111 | 0.230 |
| lib_max_mol | +0.080 | 0.346 | 0.346 |
| pop_public | +0.180 | 12.333 | 6.513 |
| lpmid | +0.259 | 4.665 | 1.238 |
| gl | +0.298 | 0.238 | 0.219 |

## view c2: 300 molecules, truth in shortlist 233 (strict MRR over 300; GL fallback molecules -465)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.497 | 0.387 |
| pipeline | 0.497 | 0.387 |
| fixed | 0.433 | 0.323 |
| lib | 0.094 | 0.050 |
| guard0.6_0.1 | 0.492 | 0.377 |
| guard0.7_0.1 | 0.494 | 0.380 |
| guard0.7_0.2 | 0.494 | 0.380 |
| guard0.8_0.1 | 0.496 | 0.383 |
| guard0.8_0.2 | 0.496 | 0.383 |
| guard0.9_0.1 | 0.497 | 0.387 |
| guard0.9_0.2 | 0.497 | 0.387 |
| fguard0.6_0.1 | 0.423 | 0.310 |
| fguard0.7_0.1 | 0.428 | 0.317 |
| fguard0.7_0.2 | 0.429 | 0.317 |
| fguard0.8_0.1 | 0.432 | 0.323 |
| fguard0.8_0.2 | 0.433 | 0.323 |
| fguard0.9_0.1 | 0.432 | 0.323 |
| fguard0.9_0.2 | 0.433 | 0.323 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.562 | 0.487 |
| no_counts (lib_nref/in_train=0) | 0.497 | 0.387 |
| no_sim (lib_sim/same=0) | 0.562 | 0.487 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.356 | 0.223 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 233 | 0.640 | 0.557 | 0.121 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 233 | 0.640 | 0.557 | 0.121 |

learned loses (fixed top-1, learned not): 23; learned wins (learned top-1, fixed not): 42

lost molecules: learned top-1 has in_train 0.91 / lib_nref mean 7.4 / lib_sim mean 0.357 / pop mean 4.73; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 5.65

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -2.585 | -0.279 | 0.078 |
| lib_sim | -1.940 | 0.000 | 0.357 |
| lib_same | -0.695 | 0.000 | 0.356 |
| lib_max_mol | -0.121 | 0.402 | 0.402 |
| ppm_err | -0.028 | 0.939 | 0.939 |
| ce_known | -0.003 | 0.043 | 0.043 |
| gl_missing | +0.000 | 0.000 | 0.000 |
| in_tier | +0.000 | 0.913 | 0.913 |
| z_fp | +0.351 | 0.824 | 0.532 |
| fp | +0.397 | 21.378 | 12.378 |
| z_gl | +0.708 | 3.071 | 2.022 |
| gl | +0.716 | 0.413 | 0.338 |

