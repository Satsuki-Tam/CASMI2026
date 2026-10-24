# learned-fusion probe: run_v3_eval/B_nplib/rank_v4d (w_ice 0.0; 23 features)

## view c1: 72 molecules, truth in shortlist 71 (strict MRR over 72; GL fallback molecules -141)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.945 | 0.931 |
| pipeline | 0.945 | 0.931 |
| fixed | 0.539 | 0.417 |
| lib | 0.901 | 0.875 |
| guard0.6_0.1 | 0.938 | 0.917 |
| guard0.7_0.1 | 0.938 | 0.917 |
| guard0.7_0.2 | 0.938 | 0.917 |
| guard0.8_0.1 | 0.945 | 0.931 |
| guard0.8_0.2 | 0.945 | 0.931 |
| guard0.9_0.1 | 0.945 | 0.931 |
| guard0.9_0.2 | 0.945 | 0.931 |
| fguard0.6_0.1 | 0.836 | 0.806 |
| fguard0.7_0.1 | 0.836 | 0.806 |
| fguard0.7_0.2 | 0.780 | 0.736 |
| fguard0.8_0.1 | 0.811 | 0.778 |
| fguard0.8_0.2 | 0.768 | 0.722 |
| fguard0.9_0.1 | 0.754 | 0.708 |
| fguard0.9_0.2 | 0.711 | 0.653 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.667 | 0.542 |
| no_counts (lib_nref/in_train=0) | 0.945 | 0.931 |
| no_sim (lib_sim/same=0) | 0.667 | 0.542 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.922 | 0.889 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 13 | 1.000 | 0.337 | 0.819 | 1.00 |
| [6,20] | 50 | 0.961 | 0.630 | 0.945 | 1.00 |
| [21,100] | 8 | 0.875 | 0.365 | 0.875 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 12 | 0.797 | 0.449 | 0.596 |
| [0.60,0.80) | 6 | 1.000 | 0.615 | 1.000 |
| [0.80,0.90) | 20 | 0.975 | 0.703 | 0.963 |
| [0.90,0.95) | 13 | 1.000 | 0.573 | 0.962 |
| [0.95,1.00) | 20 | 1.000 | 0.409 | 1.000 |

learned loses (fixed top-1, learned not): 0; learned wins (learned top-1, fixed not): 37

## view c2: 300 molecules, truth in shortlist 170 (strict MRR over 300; GL fallback molecules -340)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.417 | 0.357 |
| pipeline | 0.417 | 0.357 |
| fixed | 0.377 | 0.320 |
| lib | 0.070 | 0.027 |
| guard0.6_0.1 | 0.396 | 0.317 |
| guard0.7_0.1 | 0.406 | 0.337 |
| guard0.7_0.2 | 0.409 | 0.340 |
| guard0.8_0.1 | 0.412 | 0.347 |
| guard0.8_0.2 | 0.414 | 0.350 |
| guard0.9_0.1 | 0.414 | 0.350 |
| guard0.9_0.2 | 0.414 | 0.350 |
| fguard0.6_0.1 | 0.352 | 0.277 |
| fguard0.7_0.1 | 0.365 | 0.300 |
| fguard0.7_0.2 | 0.367 | 0.303 |
| fguard0.8_0.1 | 0.369 | 0.307 |
| fguard0.8_0.2 | 0.371 | 0.310 |
| fguard0.9_0.1 | 0.373 | 0.313 |
| fguard0.9_0.2 | 0.373 | 0.313 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.418 | 0.363 |
| no_counts (lib_nref/in_train=0) | 0.417 | 0.357 |
| no_sim (lib_sim/same=0) | 0.418 | 0.363 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.283 | 0.183 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 170 | 0.736 | 0.665 | 0.123 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 170 | 0.736 | 0.665 | 0.123 |

learned loses (fixed top-1, learned not): 12; learned wins (learned top-1, fixed not): 23

lost molecules: learned top-1 has in_train 0.75 / lib_nref mean 6.2 / lib_sim mean 0.366 / pop mean 6.45; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 6.30

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -1.423 | -0.281 | 0.084 |
| lib_sim | -0.597 | 0.000 | 0.366 |
| in_coconut | -0.141 | 0.417 | 0.583 |
| fp | -0.111 | 39.447 | 37.779 |
| lotus | -0.077 | 0.683 | 0.527 |
| ce_known | -0.070 | 0.000 | 0.000 |
| np_bit | -0.067 | 0.417 | 0.583 |
| src_bit | -0.064 | 0.083 | 0.250 |
| fp_rank_window | +0.112 | 2.702 | 2.811 |
| ppm_err | +0.137 | 1.751 | 2.299 |
| gl | +0.254 | 0.378 | 0.337 |
| z_gl | +0.897 | 2.293 | 1.631 |

