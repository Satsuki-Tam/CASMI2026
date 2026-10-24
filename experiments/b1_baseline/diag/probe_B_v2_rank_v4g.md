# learned-fusion probe: run1_v2/B_nplib/rank_v4g (w_ice 1.0; 26 features)

## view c1: 72 molecules, truth in shortlist 71 (strict MRR over 72; GL fallback molecules -141)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.939 | 0.931 |
| pipeline | 0.939 | 0.931 |
| fixed | 0.580 | 0.472 |
| lib | 0.912 | 0.889 |
| guard0.6_0.1 | 0.932 | 0.917 |
| guard0.7_0.1 | 0.932 | 0.917 |
| guard0.8_0.1 | 0.939 | 0.931 |
| guard0.8_0.2 | 0.939 | 0.931 |
| guard0.9_0.2 | 0.939 | 0.931 |
| fguard0.6_0.1 | 0.854 | 0.833 |
| fguard0.7_0.1 | 0.854 | 0.833 |
| fguard0.8_0.1 | 0.814 | 0.778 |
| fguard0.8_0.2 | 0.779 | 0.736 |
| fguard0.9_0.2 | 0.710 | 0.653 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.740 | 0.667 |
| no_counts (lib_nref/in_train=0) | 0.939 | 0.931 |
| no_sim (lib_sim/same=0) | 0.740 | 0.667 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.922 | 0.889 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 13 | 1.000 | 0.378 | 0.821 | 1.00 |
| [6,20] | 50 | 0.952 | 0.678 | 0.960 | 1.00 |
| [21,100] | 8 | 0.881 | 0.367 | 0.875 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 12 | 0.837 | 0.558 | 0.660 |
| [0.60,0.80) | 6 | 1.000 | 0.441 | 1.000 |
| [0.80,0.90) | 20 | 0.929 | 0.660 | 0.963 |
| [0.90,0.95) | 13 | 1.000 | 0.635 | 0.962 |
| [0.95,1.00) | 20 | 1.000 | 0.547 | 1.000 |

learned loses (fixed top-1, learned not): 0; learned wins (learned top-1, fixed not): 33

## view c2: 300 molecules, truth in shortlist 159 (strict MRR over 300; GL fallback molecules -318)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.437 | 0.400 |
| pipeline | 0.437 | 0.400 |
| fixed | 0.373 | 0.327 |
| lib | 0.119 | 0.063 |
| guard0.6_0.1 | 0.411 | 0.350 |
| guard0.7_0.1 | 0.424 | 0.377 |
| guard0.8_0.1 | 0.429 | 0.387 |
| guard0.8_0.2 | 0.430 | 0.387 |
| guard0.9_0.2 | 0.432 | 0.390 |
| fguard0.6_0.1 | 0.347 | 0.277 |
| fguard0.7_0.1 | 0.357 | 0.297 |
| fguard0.8_0.1 | 0.363 | 0.307 |
| fguard0.8_0.2 | 0.364 | 0.310 |
| fguard0.9_0.2 | 0.368 | 0.317 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.430 | 0.393 |
| no_counts (lib_nref/in_train=0) | 0.437 | 0.400 |
| no_sim (lib_sim/same=0) | 0.430 | 0.393 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.306 | 0.220 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 159 | 0.824 | 0.704 | 0.225 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 159 | 0.824 | 0.704 | 0.225 |

learned loses (fixed top-1, learned not): 11; learned wins (learned top-1, fixed not): 33

lost molecules: learned top-1 has in_train 0.55 / lib_nref mean 6.5 / lib_sim mean 0.297 / pop mean 7.46; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 7.30

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -1.344 | -0.237 | 0.059 |
| lib_sim | -0.241 | 0.000 | 0.297 |
| ce_known | -0.064 | 0.091 | 0.091 |
| fp | -0.057 | 18.320 | 16.124 |
| lsid | -0.047 | 3.534 | 3.720 |
| lpmid | -0.029 | 1.532 | 1.674 |
| lib_same | -0.021 | 0.000 | 0.290 |
| lotus | -0.018 | 0.682 | 0.309 |
| ppm_err | +0.117 | 0.731 | 1.368 |
| pop_public | +0.168 | 7.305 | 7.459 |
| z_ice | +0.176 | 1.859 | 1.615 |
| z_gl | +0.447 | 2.149 | 1.338 |

