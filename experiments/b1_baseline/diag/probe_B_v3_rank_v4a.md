# learned-fusion probe: run_v3_eval/B_nplib/rank_v4a (w_ice 0.0; 23 features)

## view c1: 72 molecules, truth in shortlist 71 (strict MRR over 72; GL fallback molecules -141)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.913 | 0.875 |
| pipeline | 0.913 | 0.875 |
| fixed | 0.539 | 0.417 |
| lib | 0.901 | 0.875 |
| guard0.8 | 0.913 | 0.875 |
| guard0.9 | 0.913 | 0.875 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.715 | 0.583 |
| no_counts (lib_nref/in_train=0) | 0.913 | 0.875 |
| no_sim (lib_sim/same=0) | 0.715 | 0.583 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.928 | 0.917 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 13 | 0.962 | 0.337 | 0.819 | 1.00 |
| [6,20] | 50 | 0.923 | 0.630 | 0.945 | 1.00 |
| [21,100] | 8 | 0.882 | 0.365 | 0.875 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 12 | 0.740 | 0.449 | 0.596 |
| [0.60,0.80) | 6 | 0.917 | 0.615 | 1.000 |
| [0.80,0.90) | 20 | 0.917 | 0.703 | 0.963 |
| [0.90,0.95) | 13 | 1.000 | 0.573 | 0.962 |
| [0.95,1.00) | 20 | 1.000 | 0.409 | 1.000 |

learned loses (fixed top-1, learned not): 1; learned wins (learned top-1, fixed not): 34

lost molecules: learned top-1 has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 13.94; truth has in_train 1.00 / lib_nref mean 15.0 / lib_sim mean 0.836 / pop mean 21.24

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| pop_public | -0.633 | 21.241 | 13.937 |
| lsid | -0.471 | 7.770 | 5.402 |
| lib_same | -0.467 | 0.836 | 0.000 |
| fp | -0.271 | 4.965 | -3.745 |
| in_coconut | -0.172 | 1.000 | 1.000 |
| lsynonyms | -0.164 | 4.633 | 2.834 |
| np_bit | -0.128 | 1.000 | 1.000 |
| z_fp | -0.126 | 1.318 | 0.845 |
| lotus | +0.133 | 3.091 | 0.000 |
| lib_sim | +0.391 | 0.836 | 0.000 |
| src_bit | +0.620 | 1.000 | 0.000 |
| lib_margin | +0.818 | 0.062 | -0.774 |

## view c2: 300 molecules, truth in shortlist 170 (strict MRR over 300; GL fallback molecules -340)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.469 | 0.437 |
| pipeline | 0.469 | 0.437 |
| fixed | 0.377 | 0.320 |
| lib | 0.070 | 0.027 |
| guard0.8 | 0.458 | 0.413 |
| guard0.9 | 0.461 | 0.420 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.445 | 0.393 |
| no_counts (lib_nref/in_train=0) | 0.469 | 0.437 |
| no_sim (lib_sim/same=0) | 0.445 | 0.393 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.325 | 0.230 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 170 | 0.828 | 0.665 | 0.123 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 170 | 0.828 | 0.665 | 0.123 |

learned loses (fixed top-1, learned not): 4; learned wins (learned top-1, fixed not): 39

lost molecules: learned top-1 has in_train 0.25 / lib_nref mean 3.2 / lib_sim mean 0.000 / pop mean 3.81; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 4.20

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| fp_rank_window | -0.442 | 3.116 | 2.032 |
| fp | -0.440 | 19.755 | 32.395 |
| z_fp | -0.314 | 1.253 | 1.565 |
| lotus | -0.277 | 0.000 | 0.486 |
| in_coconut | -0.255 | 0.000 | 0.250 |
| np_bit | -0.233 | 0.000 | 0.250 |
| lsid | -0.142 | 2.498 | 2.037 |
| src_bit | -0.133 | 0.000 | 0.250 |
| lsynonyms | +0.199 | 1.616 | 1.334 |
| pop_public | +0.300 | 4.202 | 3.809 |
| ppm_err | +0.381 | 1.762 | 3.404 |
| z_gl | +0.521 | 3.425 | 2.985 |

