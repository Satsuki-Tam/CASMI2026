# learned-fusion probe: run_v3_eval/B_nplib/rank_v4c (w_ice 0.0; 23 features)

## view c1: 72 molecules, truth in shortlist 71 (strict MRR over 72; GL fallback molecules -141)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.935 | 0.917 |
| pipeline | 0.935 | 0.917 |
| fixed | 0.539 | 0.417 |
| lib | 0.901 | 0.875 |
| guard0.6_0.1 | 0.935 | 0.917 |
| guard0.7_0.1 | 0.935 | 0.917 |
| guard0.7_0.2 | 0.935 | 0.917 |
| guard0.8_0.1 | 0.935 | 0.917 |
| guard0.8_0.2 | 0.935 | 0.917 |
| guard0.9_0.1 | 0.935 | 0.917 |
| guard0.9_0.2 | 0.935 | 0.917 |
| fguard0.6_0.1 | 0.836 | 0.806 |
| fguard0.7_0.1 | 0.836 | 0.806 |
| fguard0.7_0.2 | 0.780 | 0.736 |
| fguard0.8_0.1 | 0.811 | 0.778 |
| fguard0.8_0.2 | 0.768 | 0.722 |
| fguard0.9_0.1 | 0.754 | 0.708 |
| fguard0.9_0.2 | 0.711 | 0.653 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.751 | 0.653 |
| no_counts (lib_nref/in_train=0) | 0.935 | 0.917 |
| no_sim (lib_sim/same=0) | 0.751 | 0.653 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.923 | 0.889 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 13 | 0.900 | 0.337 | 0.819 | 1.00 |
| [6,20] | 50 | 0.972 | 0.630 | 0.945 | 1.00 |
| [21,100] | 8 | 0.880 | 0.365 | 0.875 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 12 | 0.738 | 0.449 | 0.596 |
| [0.60,0.80) | 6 | 1.000 | 0.615 | 1.000 |
| [0.80,0.90) | 20 | 0.975 | 0.703 | 0.963 |
| [0.90,0.95) | 13 | 1.000 | 0.573 | 0.962 |
| [0.95,1.00) | 20 | 1.000 | 0.409 | 1.000 |

learned loses (fixed top-1, learned not): 1; learned wins (learned top-1, fixed not): 37

lost molecules: learned top-1 has in_train 1.00 / lib_nref mean 4.0 / lib_sim mean 0.763 / pop mean 9.07; truth has in_train 1.00 / lib_nref mean 5.0 / lib_sim mean 0.000 / pop mean 13.55

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -2.170 | -0.553 | 0.210 |
| lib_sim | -2.162 | 0.000 | 0.763 |
| lib_same | -0.527 | 0.000 | 0.763 |
| fp_rank_window | -0.391 | 1.609 | 0.693 |
| lib_max_mol | -0.373 | 0.763 | 0.763 |
| z_gl | -0.153 | 4.682 | 4.244 |
| z_fp | -0.044 | 1.464 | 1.915 |
| in_tier | +0.000 | 1.000 | 1.000 |
| pop_public | +0.407 | 13.554 | 9.071 |
| ppm_err | +0.438 | 5.153 | 5.153 |
| lsid | +0.442 | 6.414 | 5.641 |
| lpmid | +0.673 | 3.664 | 1.099 |

## view c2: 300 molecules, truth in shortlist 170 (strict MRR over 300; GL fallback molecules -340)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.412 | 0.350 |
| pipeline | 0.412 | 0.350 |
| fixed | 0.377 | 0.320 |
| lib | 0.070 | 0.027 |
| guard0.6_0.1 | 0.401 | 0.330 |
| guard0.7_0.1 | 0.410 | 0.347 |
| guard0.7_0.2 | 0.410 | 0.347 |
| guard0.8_0.1 | 0.410 | 0.347 |
| guard0.8_0.2 | 0.410 | 0.347 |
| guard0.9_0.1 | 0.410 | 0.347 |
| guard0.9_0.2 | 0.410 | 0.347 |
| fguard0.6_0.1 | 0.352 | 0.277 |
| fguard0.7_0.1 | 0.365 | 0.300 |
| fguard0.7_0.2 | 0.367 | 0.303 |
| fguard0.8_0.1 | 0.369 | 0.307 |
| fguard0.8_0.2 | 0.371 | 0.310 |
| fguard0.9_0.1 | 0.373 | 0.313 |
| fguard0.9_0.2 | 0.373 | 0.313 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.463 | 0.423 |
| no_counts (lib_nref/in_train=0) | 0.412 | 0.350 |
| no_sim (lib_sim/same=0) | 0.463 | 0.423 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.271 | 0.177 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 170 | 0.727 | 0.665 | 0.123 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 170 | 0.727 | 0.665 | 0.123 |

learned loses (fixed top-1, learned not): 20; learned wins (learned top-1, fixed not): 29

lost molecules: learned top-1 has in_train 0.85 / lib_nref mean 9.1 / lib_sim mean 0.504 / pop mean 5.56; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 6.54

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -2.323 | -0.284 | 0.220 |
| lib_sim | -2.197 | 0.000 | 0.504 |
| lib_same | -0.767 | 0.000 | 0.499 |
| lib_max_mol | -0.234 | 0.511 | 0.511 |
| src_bit | -0.054 | 0.250 | 0.350 |
| lotus | -0.037 | 0.599 | 0.443 |
| in_coconut | -0.028 | 0.400 | 0.350 |
| n_cands | -0.028 | 235.250 | 235.250 |
| fp | +0.319 | 23.977 | 15.705 |
| z_fp | +0.557 | 1.393 | 1.051 |
| gl | +0.575 | 0.454 | 0.403 |
| z_gl | +0.701 | 2.956 | 2.220 |

