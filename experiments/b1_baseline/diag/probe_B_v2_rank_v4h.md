# learned-fusion probe: run1_v2/B_nplib/rank_v4h (w_ice 1.0; 26 features)

## view c1: 72 molecules, truth in shortlist 71 (strict MRR over 72; GL fallback molecules -141)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.939 | 0.917 |
| pipeline | 0.939 | 0.917 |
| fixed | 0.580 | 0.472 |
| lib | 0.912 | 0.889 |
| guard0.6_0.1 | 0.939 | 0.917 |
| guard0.7_0.1 | 0.939 | 0.917 |
| guard0.8_0.1 | 0.946 | 0.931 |
| guard0.8_0.2 | 0.939 | 0.917 |
| guard0.9_0.2 | 0.939 | 0.917 |
| fguard0.6_0.1 | 0.854 | 0.833 |
| fguard0.7_0.1 | 0.854 | 0.833 |
| fguard0.8_0.1 | 0.814 | 0.778 |
| fguard0.8_0.2 | 0.779 | 0.736 |
| fguard0.9_0.2 | 0.710 | 0.653 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.701 | 0.597 |
| no_counts (lib_nref/in_train=0) | 0.939 | 0.917 |
| no_sim (lib_sim/same=0) | 0.701 | 0.597 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.913 | 0.889 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 13 | 0.962 | 0.378 | 0.821 | 1.00 |
| [6,20] | 50 | 0.961 | 0.678 | 0.960 | 1.00 |
| [21,100] | 8 | 0.884 | 0.367 | 0.875 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 12 | 0.803 | 0.558 | 0.660 |
| [0.60,0.80) | 6 | 1.000 | 0.441 | 1.000 |
| [0.80,0.90) | 20 | 0.975 | 0.660 | 0.963 |
| [0.90,0.95) | 13 | 1.000 | 0.635 | 0.962 |
| [0.95,1.00) | 20 | 0.975 | 0.547 | 1.000 |

learned loses (fixed top-1, learned not): 1; learned wins (learned top-1, fixed not): 33

lost molecules: learned top-1 has in_train 1.00 / lib_nref mean 2.0 / lib_sim mean 0.254 / pop mean 13.60; truth has in_train 1.00 / lib_nref mean 15.0 / lib_sim mean 0.953 / pop mean 18.52

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lotus | -1.926 | 4.511 | 2.079 |
| z_fp | -0.936 | 0.037 | 1.356 |
| lsid | -0.581 | 5.582 | 4.996 |
| lsynonyms | -0.455 | 4.613 | 4.008 |
| pop_public | -0.410 | 18.519 | 13.598 |
| fp | -0.310 | -13.875 | -8.961 |
| in_coconut | -0.275 | 1.000 | 1.000 |
| src_bit | -0.214 | 1.000 | 1.000 |
| z_gl | +0.466 | 0.574 | -0.354 |
| lib_same | +0.494 | 0.953 | 0.254 |
| lib_sim | +1.541 | 0.953 | 0.254 |
| lib_margin | +1.700 | 0.132 | -0.567 |

## view c2: 300 molecules, truth in shortlist 159 (strict MRR over 300; GL fallback molecules -318)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.404 | 0.343 |
| pipeline | 0.404 | 0.343 |
| fixed | 0.373 | 0.327 |
| lib | 0.119 | 0.063 |
| guard0.6_0.1 | 0.390 | 0.317 |
| guard0.7_0.1 | 0.398 | 0.333 |
| guard0.8_0.1 | 0.402 | 0.340 |
| guard0.8_0.2 | 0.402 | 0.340 |
| guard0.9_0.2 | 0.402 | 0.340 |
| fguard0.6_0.1 | 0.347 | 0.277 |
| fguard0.7_0.1 | 0.357 | 0.297 |
| fguard0.8_0.1 | 0.363 | 0.307 |
| fguard0.8_0.2 | 0.364 | 0.310 |
| fguard0.9_0.2 | 0.368 | 0.317 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.418 | 0.370 |
| no_counts (lib_nref/in_train=0) | 0.404 | 0.343 |
| no_sim (lib_sim/same=0) | 0.418 | 0.370 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.297 | 0.220 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 159 | 0.761 | 0.704 | 0.225 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 159 | 0.761 | 0.704 | 0.225 |

learned loses (fixed top-1, learned not): 18; learned wins (learned top-1, fixed not): 23

lost molecules: learned top-1 has in_train 0.67 / lib_nref mean 4.7 / lib_sim mean 0.385 / pop mean 5.70; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 6.24

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -1.373 | -0.230 | 0.155 |
| lib_sim | -0.342 | 0.000 | 0.385 |
| lib_same | -0.105 | 0.000 | 0.381 |
| lotus | -0.101 | 0.417 | 0.343 |
| lpmid | -0.071 | 1.255 | 1.108 |
| lsid | -0.038 | 3.214 | 2.989 |
| in_coconut | -0.037 | 0.333 | 0.333 |
| src_bit | -0.028 | 0.167 | 0.167 |
| ppm_err | +0.122 | 1.112 | 1.501 |
| lsynonyms | +0.133 | 2.294 | 2.024 |
| z_ice | +0.136 | 2.289 | 2.100 |
| z_gl | +0.600 | 2.584 | 1.977 |

