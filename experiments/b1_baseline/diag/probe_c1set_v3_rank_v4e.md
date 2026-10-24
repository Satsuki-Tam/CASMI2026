# learned-fusion probe: run_v3_c1/B_nplib/rank_v4e (w_ice 0.0; 23 features)

## view c1: 257 molecules, truth in shortlist 257 (strict MRR over 257; GL fallback molecules 4)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.924 | 0.887 |
| pipeline | 0.924 | 0.887 |
| fixed | 0.546 | 0.401 |
| lib | 0.904 | 0.868 |
| guard0.6_0.1 | 0.930 | 0.899 |
| guard0.7_0.1 | 0.931 | 0.899 |
| guard0.7_0.2 | 0.926 | 0.891 |
| guard0.8_0.1 | 0.931 | 0.899 |
| guard0.8_0.2 | 0.926 | 0.891 |
| guard0.9_0.1 | 0.929 | 0.895 |
| guard0.9_0.2 | 0.926 | 0.891 |
| fguard0.6_0.1 | 0.827 | 0.770 |
| fguard0.7_0.1 | 0.790 | 0.724 |
| fguard0.7_0.2 | 0.760 | 0.685 |
| fguard0.8_0.1 | 0.761 | 0.685 |
| fguard0.8_0.2 | 0.734 | 0.650 |
| fguard0.9_0.1 | 0.680 | 0.572 |
| fguard0.9_0.2 | 0.658 | 0.545 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.647 | 0.521 |
| no_counts (lib_nref/in_train=0) | 0.924 | 0.887 |
| no_sim (lib_sim/same=0) | 0.647 | 0.521 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.904 | 0.864 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 72 | 0.877 | 0.522 | 0.816 | 1.00 |
| [6,20] | 161 | 0.939 | 0.547 | 0.942 | 1.00 |
| [21,100] | 24 | 0.962 | 0.611 | 0.912 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 68 | 0.821 | 0.575 | 0.704 |
| [0.60,0.80) | 49 | 0.970 | 0.537 | 0.952 |
| [0.80,0.90) | 55 | 0.949 | 0.557 | 0.982 |
| [0.90,0.95) | 39 | 0.970 | 0.563 | 0.966 |
| [0.95,1.00) | 46 | 0.955 | 0.483 | 1.000 |

learned loses (fixed top-1, learned not): 3; learned wins (learned top-1, fixed not): 128

lost molecules: learned top-1 has in_train 1.00 / lib_nref mean 4.7 / lib_sim mean 0.467 / pop mean 5.53; truth has in_train 1.00 / lib_nref mean 7.0 / lib_sim mean 0.154 / pop mean 6.12

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -1.712 | -0.130 | 0.182 |
| lib_sim | -0.463 | 0.154 | 0.467 |
| lsynonyms | -0.277 | 2.199 | 2.193 |
| lib_same | -0.196 | 0.154 | 0.467 |
| fp | -0.174 | -5.957 | -2.685 |
| z_fp | -0.122 | 0.530 | 1.013 |
| ppm_err | -0.033 | 0.960 | 0.960 |
| lib_max_mol | -0.022 | 0.472 | 0.472 |
| np_bit | +0.162 | 0.333 | 0.000 |
| pop_public | +0.299 | 6.124 | 5.528 |
| gl | +0.458 | 0.456 | 0.345 |
| z_gl | +0.931 | 3.778 | 2.398 |

## view c2: 300 molecules, truth in shortlist 233 (strict MRR over 300; GL fallback molecules -465)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.499 | 0.383 |
| pipeline | 0.499 | 0.383 |
| fixed | 0.433 | 0.323 |
| lib | 0.094 | 0.050 |
| guard0.6_0.1 | 0.494 | 0.377 |
| guard0.7_0.1 | 0.499 | 0.383 |
| guard0.7_0.2 | 0.499 | 0.383 |
| guard0.8_0.1 | 0.499 | 0.383 |
| guard0.8_0.2 | 0.499 | 0.383 |
| guard0.9_0.1 | 0.499 | 0.383 |
| guard0.9_0.2 | 0.499 | 0.383 |
| fguard0.6_0.1 | 0.423 | 0.310 |
| fguard0.7_0.1 | 0.428 | 0.317 |
| fguard0.7_0.2 | 0.429 | 0.317 |
| fguard0.8_0.1 | 0.432 | 0.323 |
| fguard0.8_0.2 | 0.433 | 0.323 |
| fguard0.9_0.1 | 0.432 | 0.323 |
| fguard0.9_0.2 | 0.433 | 0.323 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.533 | 0.440 |
| no_counts (lib_nref/in_train=0) | 0.499 | 0.383 |
| no_sim (lib_sim/same=0) | 0.533 | 0.440 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.367 | 0.233 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 233 | 0.642 | 0.557 | 0.121 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 233 | 0.642 | 0.557 | 0.121 |

learned loses (fixed top-1, learned not): 14; learned wins (learned top-1, fixed not): 32

lost molecules: learned top-1 has in_train 0.86 / lib_nref mean 7.6 / lib_sim mean 0.378 / pop mean 5.36; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 7.35

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -1.254 | -0.257 | 0.121 |
| lib_sim | -0.513 | 0.000 | 0.378 |
| lib_same | -0.219 | 0.000 | 0.373 |
| fp_rank_window | -0.159 | 3.049 | 2.328 |
| z_fp | -0.122 | 0.720 | 0.942 |
| src_bit | -0.037 | 0.214 | 0.286 |
| ppm_err | -0.024 | 0.953 | 0.953 |
| lotus | -0.014 | 0.939 | 0.393 |
| lpmid | +0.133 | 2.107 | 0.783 |
| pop_public | +0.296 | 7.349 | 5.359 |
| gl | +0.339 | 0.411 | 0.362 |
| z_gl | +0.554 | 2.856 | 2.288 |

