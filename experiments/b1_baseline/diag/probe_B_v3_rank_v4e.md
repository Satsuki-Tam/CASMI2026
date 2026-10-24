# learned-fusion probe: run_v3_eval/B_nplib/rank_v4e (w_ice 0.0; 23 features)

## view c1: 72 molecules, truth in shortlist 71 (strict MRR over 72; GL fallback molecules -141)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.944 | 0.931 |
| pipeline | 0.944 | 0.931 |
| fixed | 0.539 | 0.417 |
| lib | 0.901 | 0.875 |
| guard0.6_0.1 | 0.938 | 0.917 |
| guard0.7_0.1 | 0.938 | 0.917 |
| guard0.7_0.2 | 0.938 | 0.917 |
| guard0.8_0.1 | 0.944 | 0.931 |
| guard0.8_0.2 | 0.944 | 0.931 |
| guard0.9_0.1 | 0.944 | 0.931 |
| guard0.9_0.2 | 0.944 | 0.931 |
| fguard0.6_0.1 | 0.836 | 0.806 |
| fguard0.7_0.1 | 0.836 | 0.806 |
| fguard0.7_0.2 | 0.780 | 0.736 |
| fguard0.8_0.1 | 0.811 | 0.778 |
| fguard0.8_0.2 | 0.768 | 0.722 |
| fguard0.9_0.1 | 0.754 | 0.708 |
| fguard0.9_0.2 | 0.711 | 0.653 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.657 | 0.528 |
| no_counts (lib_nref/in_train=0) | 0.944 | 0.931 |
| no_sim (lib_sim/same=0) | 0.657 | 0.528 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.908 | 0.875 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 13 | 0.949 | 0.337 | 0.819 | 1.00 |
| [6,20] | 50 | 0.973 | 0.630 | 0.945 | 1.00 |
| [21,100] | 8 | 0.875 | 0.365 | 0.875 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 12 | 0.750 | 0.449 | 0.596 |
| [0.60,0.80) | 6 | 1.000 | 0.615 | 1.000 |
| [0.80,0.90) | 20 | 1.000 | 0.703 | 0.963 |
| [0.90,0.95) | 13 | 1.000 | 0.573 | 0.962 |
| [0.95,1.00) | 20 | 1.000 | 0.409 | 1.000 |

learned loses (fixed top-1, learned not): 0; learned wins (learned top-1, fixed not): 37

## view c2: 300 molecules, truth in shortlist 170 (strict MRR over 300; GL fallback molecules -340)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.395 | 0.330 |
| pipeline | 0.395 | 0.330 |
| fixed | 0.377 | 0.320 |
| lib | 0.070 | 0.027 |
| guard0.6_0.1 | 0.383 | 0.307 |
| guard0.7_0.1 | 0.389 | 0.320 |
| guard0.7_0.2 | 0.390 | 0.320 |
| guard0.8_0.1 | 0.394 | 0.327 |
| guard0.8_0.2 | 0.394 | 0.327 |
| guard0.9_0.1 | 0.394 | 0.327 |
| guard0.9_0.2 | 0.394 | 0.327 |
| fguard0.6_0.1 | 0.352 | 0.277 |
| fguard0.7_0.1 | 0.365 | 0.300 |
| fguard0.7_0.2 | 0.367 | 0.303 |
| fguard0.8_0.1 | 0.369 | 0.307 |
| fguard0.8_0.2 | 0.371 | 0.310 |
| fguard0.9_0.1 | 0.373 | 0.313 |
| fguard0.9_0.2 | 0.373 | 0.313 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.420 | 0.370 |
| no_counts (lib_nref/in_train=0) | 0.395 | 0.330 |
| no_sim (lib_sim/same=0) | 0.420 | 0.370 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.283 | 0.187 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 170 | 0.698 | 0.665 | 0.123 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 170 | 0.698 | 0.665 | 0.123 |

learned loses (fixed top-1, learned not): 15; learned wins (learned top-1, fixed not): 18

lost molecules: learned top-1 has in_train 0.67 / lib_nref mean 5.9 / lib_sim mean 0.446 / pop mean 6.23; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 7.07

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -1.219 | -0.295 | 0.151 |
| lib_sim | -0.699 | 0.000 | 0.446 |
| lib_same | -0.238 | 0.000 | 0.446 |
| lotus | -0.084 | 0.753 | 0.246 |
| ppm_err | -0.040 | 1.356 | 1.264 |
| pop_public | -0.027 | 7.071 | 6.228 |
| src_bit | -0.012 | 0.200 | 0.200 |
| ce_known | -0.012 | 0.133 | 0.133 |
| lsynonyms | +0.115 | 2.183 | 2.186 |
| z_fp | +0.136 | 1.321 | 1.196 |
| gl | +0.280 | 0.438 | 0.405 |
| z_gl | +0.640 | 2.900 | 2.408 |

