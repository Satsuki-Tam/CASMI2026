# learned-fusion probe: run_v3_eval/B_nplib/rank_v4b (w_ice 0.0; 23 features)

## view c1: 72 molecules, truth in shortlist 71 (strict MRR over 72; GL fallback molecules -141)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.933 | 0.917 |
| pipeline | 0.933 | 0.917 |
| fixed | 0.539 | 0.417 |
| lib | 0.901 | 0.875 |
| guard0.6_0.1 | 0.926 | 0.903 |
| guard0.7_0.1 | 0.926 | 0.903 |
| guard0.7_0.2 | 0.926 | 0.903 |
| guard0.8_0.1 | 0.933 | 0.917 |
| guard0.8_0.2 | 0.933 | 0.917 |
| guard0.9_0.1 | 0.933 | 0.917 |
| guard0.9_0.2 | 0.933 | 0.917 |
| fguard0.6_0.1 | 0.836 | 0.806 |
| fguard0.7_0.1 | 0.836 | 0.806 |
| fguard0.7_0.2 | 0.780 | 0.736 |
| fguard0.8_0.1 | 0.811 | 0.778 |
| fguard0.8_0.2 | 0.768 | 0.722 |
| fguard0.9_0.1 | 0.754 | 0.708 |
| fguard0.9_0.2 | 0.711 | 0.653 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.699 | 0.556 |
| no_counts (lib_nref/in_train=0) | 0.933 | 0.917 |
| no_sim (lib_sim/same=0) | 0.699 | 0.556 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.922 | 0.889 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 13 | 1.000 | 0.337 | 0.819 | 1.00 |
| [6,20] | 50 | 0.943 | 0.630 | 0.945 | 1.00 |
| [21,100] | 8 | 0.875 | 0.365 | 0.875 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 12 | 0.833 | 0.449 | 0.596 |
| [0.60,0.80) | 6 | 1.000 | 0.615 | 1.000 |
| [0.80,0.90) | 20 | 0.908 | 0.703 | 0.963 |
| [0.90,0.95) | 13 | 1.000 | 0.573 | 0.962 |
| [0.95,1.00) | 20 | 1.000 | 0.409 | 1.000 |

learned loses (fixed top-1, learned not): 1; learned wins (learned top-1, fixed not): 37

lost molecules: learned top-1 has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 13.94; truth has in_train 1.00 / lib_nref mean 15.0 / lib_sim mean 0.836 / pop mean 21.24

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| pop_public | -0.691 | 21.241 | 13.937 |
| lsid | -0.557 | 7.770 | 5.402 |
| z_gl | -0.485 | 2.269 | 1.888 |
| lib_same | -0.219 | 0.836 | 0.000 |
| z_fp | -0.199 | 1.318 | 0.845 |
| np_bit | -0.133 | 1.000 | 1.000 |
| fp | -0.122 | 4.965 | -3.745 |
| in_coconut | -0.090 | 1.000 | 1.000 |
| lotus | +0.246 | 3.091 | 0.000 |
| src_bit | +0.441 | 1.000 | 0.000 |
| lib_sim | +0.664 | 0.836 | 0.000 |
| lib_margin | +0.826 | 0.062 | -0.774 |

## view c2: 300 molecules, truth in shortlist 170 (strict MRR over 300; GL fallback molecules -340)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.453 | 0.407 |
| pipeline | 0.453 | 0.407 |
| fixed | 0.377 | 0.320 |
| lib | 0.070 | 0.027 |
| guard0.6_0.1 | 0.427 | 0.357 |
| guard0.7_0.1 | 0.440 | 0.383 |
| guard0.7_0.2 | 0.441 | 0.383 |
| guard0.8_0.1 | 0.446 | 0.393 |
| guard0.8_0.2 | 0.446 | 0.393 |
| guard0.9_0.1 | 0.448 | 0.397 |
| guard0.9_0.2 | 0.448 | 0.397 |
| fguard0.6_0.1 | 0.352 | 0.277 |
| fguard0.7_0.1 | 0.365 | 0.300 |
| fguard0.7_0.2 | 0.367 | 0.303 |
| fguard0.8_0.1 | 0.369 | 0.307 |
| fguard0.8_0.2 | 0.371 | 0.310 |
| fguard0.9_0.1 | 0.373 | 0.313 |
| fguard0.9_0.2 | 0.373 | 0.313 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.439 | 0.383 |
| no_counts (lib_nref/in_train=0) | 0.453 | 0.407 |
| no_sim (lib_sim/same=0) | 0.439 | 0.383 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.302 | 0.203 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 170 | 0.799 | 0.665 | 0.123 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 170 | 0.799 | 0.665 | 0.123 |

learned loses (fixed top-1, learned not): 11; learned wins (learned top-1, fixed not): 37

lost molecules: learned top-1 has in_train 0.36 / lib_nref mean 2.9 / lib_sim mean 0.210 / pop mean 5.25; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 5.42

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.455 | -0.324 | -0.114 |
| lib_sim | -0.249 | 0.000 | 0.210 |
| fp | -0.156 | 23.975 | 26.977 |
| np_bit | -0.119 | 0.364 | 0.455 |
| fp_rank_window | -0.095 | 2.632 | 2.361 |
| in_coconut | -0.085 | 0.364 | 0.455 |
| lotus | -0.067 | 0.335 | 0.449 |
| src_bit | -0.046 | 0.091 | 0.182 |
| pop_public | +0.068 | 5.420 | 5.249 |
| ppm_err | +0.096 | 1.305 | 1.902 |
| gl | +0.147 | 0.439 | 0.410 |
| z_gl | +0.558 | 2.795 | 2.290 |

