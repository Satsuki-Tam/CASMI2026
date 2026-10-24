# learned-fusion probe: run_v3_eval/B_nplib/rank_v4f (w_ice 0.0; 23 features)

## view c1: 72 molecules, truth in shortlist 71 (strict MRR over 72; GL fallback molecules -141)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.892 | 0.847 |
| pipeline | 0.892 | 0.847 |
| fixed | 0.539 | 0.417 |
| lib | 0.901 | 0.875 |
| guard0.6_0.1 | 0.899 | 0.861 |
| guard0.7_0.1 | 0.899 | 0.861 |
| guard0.7_0.2 | 0.885 | 0.833 |
| guard0.8_0.1 | 0.899 | 0.861 |
| guard0.8_0.2 | 0.892 | 0.847 |
| guard0.9_0.1 | 0.899 | 0.861 |
| guard0.9_0.2 | 0.892 | 0.847 |
| fguard0.6_0.1 | 0.836 | 0.806 |
| fguard0.7_0.1 | 0.836 | 0.806 |
| fguard0.7_0.2 | 0.780 | 0.736 |
| fguard0.8_0.1 | 0.811 | 0.778 |
| fguard0.8_0.2 | 0.768 | 0.722 |
| fguard0.9_0.1 | 0.754 | 0.708 |
| fguard0.9_0.2 | 0.711 | 0.653 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.641 | 0.514 |
| no_counts (lib_nref/in_train=0) | 0.892 | 0.847 |
| no_sim (lib_sim/same=0) | 0.641 | 0.514 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.894 | 0.861 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 13 | 0.885 | 0.337 | 0.819 | 1.00 |
| [6,20] | 50 | 0.913 | 0.630 | 0.945 | 1.00 |
| [21,100] | 8 | 0.880 | 0.365 | 0.875 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 12 | 0.748 | 0.449 | 0.596 |
| [0.60,0.80) | 6 | 0.917 | 0.615 | 1.000 |
| [0.80,0.90) | 20 | 0.929 | 0.703 | 0.963 |
| [0.90,0.95) | 13 | 0.962 | 0.573 | 0.962 |
| [0.95,1.00) | 20 | 0.932 | 0.409 | 1.000 |

learned loses (fixed top-1, learned not): 1; learned wins (learned top-1, fixed not): 32

lost molecules: learned top-1 has in_train 1.00 / lib_nref mean 2.0 / lib_sim mean 0.254 / pop mean 13.60; truth has in_train 1.00 / lib_nref mean 15.0 / lib_sim mean 0.953 / pop mean 18.52

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lotus | -1.248 | 4.511 | 2.079 |
| z_fp | -0.757 | 0.502 | 1.267 |
| lsynonyms | -0.387 | 4.613 | 4.008 |
| fp_rank_window | -0.365 | 4.043 | 2.485 |
| pop_public | -0.346 | 18.519 | 13.598 |
| in_coconut | -0.333 | 1.000 | 1.000 |
| src_bit | -0.315 | 1.000 | 1.000 |
| np_bit | -0.228 | 1.000 | 1.000 |
| lib_same | +0.309 | 0.953 | 0.254 |
| z_gl | +0.409 | 0.664 | -0.189 |
| lib_sim | +0.638 | 0.953 | 0.254 |
| lib_margin | +2.068 | 0.132 | -0.567 |

## view c2: 300 molecules, truth in shortlist 170 (strict MRR over 300; GL fallback molecules -340)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.419 | 0.367 |
| pipeline | 0.419 | 0.367 |
| fixed | 0.377 | 0.320 |
| lib | 0.070 | 0.027 |
| guard0.6_0.1 | 0.398 | 0.327 |
| guard0.7_0.1 | 0.407 | 0.343 |
| guard0.7_0.2 | 0.407 | 0.343 |
| guard0.8_0.1 | 0.412 | 0.353 |
| guard0.8_0.2 | 0.412 | 0.353 |
| guard0.9_0.1 | 0.414 | 0.357 |
| guard0.9_0.2 | 0.414 | 0.357 |
| fguard0.6_0.1 | 0.352 | 0.277 |
| fguard0.7_0.1 | 0.365 | 0.300 |
| fguard0.7_0.2 | 0.367 | 0.303 |
| fguard0.8_0.1 | 0.369 | 0.307 |
| fguard0.8_0.2 | 0.371 | 0.310 |
| fguard0.9_0.1 | 0.373 | 0.313 |
| fguard0.9_0.2 | 0.373 | 0.313 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.416 | 0.363 |
| no_counts (lib_nref/in_train=0) | 0.419 | 0.367 |
| no_sim (lib_sim/same=0) | 0.416 | 0.363 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.299 | 0.210 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 170 | 0.739 | 0.665 | 0.123 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 170 | 0.739 | 0.665 | 0.123 |

learned loses (fixed top-1, learned not): 10; learned wins (learned top-1, fixed not): 24

lost molecules: learned top-1 has in_train 0.50 / lib_nref mean 2.8 / lib_sim mean 0.337 / pop mean 5.98; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 7.36

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.643 | -0.420 | -0.082 |
| lib_sim | -0.174 | 0.000 | 0.337 |
| fp_rank_window | -0.167 | 3.002 | 2.454 |
| z_fp | -0.106 | 1.143 | 1.276 |
| lotus | -0.098 | 0.751 | 0.369 |
| lib_same | -0.092 | 0.000 | 0.337 |
| ppm_err | -0.054 | 1.015 | 0.875 |
| src_bit | -0.006 | 0.200 | 0.200 |
| lsynonyms | +0.041 | 2.365 | 2.266 |
| pop_public | +0.049 | 7.357 | 5.976 |
| gl | +0.156 | 0.436 | 0.426 |
| z_gl | +0.310 | 2.612 | 2.401 |

