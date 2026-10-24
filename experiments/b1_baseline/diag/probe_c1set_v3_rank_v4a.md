# learned-fusion probe: run_v3_c1/B_nplib/rank_v4a (w_ice 0.0; 23 features)

## view c1: 257 molecules, truth in shortlist 257 (strict MRR over 257; GL fallback molecules 4)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.889 | 0.837 |
| pipeline | 0.889 | 0.837 |
| fixed | 0.546 | 0.401 |
| lib | 0.904 | 0.868 |
| guard0.8 | 0.907 | 0.864 |
| guard0.9 | 0.894 | 0.844 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.645 | 0.498 |
| no_counts (lib_nref/in_train=0) | 0.889 | 0.837 |
| no_sim (lib_sim/same=0) | 0.645 | 0.498 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.913 | 0.875 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 72 | 0.854 | 0.522 | 0.816 | 1.00 |
| [6,20] | 161 | 0.895 | 0.547 | 0.942 | 1.00 |
| [21,100] | 24 | 0.958 | 0.611 | 0.912 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 68 | 0.810 | 0.575 | 0.704 |
| [0.60,0.80) | 49 | 0.873 | 0.537 | 0.952 |
| [0.80,0.90) | 55 | 0.882 | 0.557 | 0.982 |
| [0.90,0.95) | 39 | 0.944 | 0.563 | 0.966 |
| [0.95,1.00) | 46 | 0.986 | 0.483 | 1.000 |

learned loses (fixed top-1, learned not): 5; learned wins (learned top-1, fixed not): 117

lost molecules: learned top-1 has in_train 0.60 / lib_nref mean 2.2 / lib_sim mean 0.138 / pop mean 7.16; truth has in_train 1.00 / lib_nref mean 8.6 / lib_sim mean 0.328 / pop mean 8.39

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_fp | -0.715 | 0.811 | 1.451 |
| fp_rank_window | -0.217 | 2.506 | 1.691 |
| fp | -0.212 | 17.765 | 28.842 |
| pop_public | -0.069 | 8.389 | 7.157 |
| z_gl | -0.065 | 3.248 | 2.691 |
| lsynonyms | -0.056 | 2.678 | 2.429 |
| lsid | -0.046 | 3.662 | 3.546 |
| ppm_err | -0.038 | 0.945 | 0.945 |
| np_bit | +0.097 | 0.600 | 0.400 |
| in_coconut | +0.130 | 0.600 | 0.400 |
| lib_sim | +0.159 | 0.328 | 0.138 |
| lib_margin | +0.342 | 0.113 | -0.077 |

## view c2: 300 molecules, truth in shortlist 233 (strict MRR over 300; GL fallback molecules -465)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.581 | 0.497 |
| pipeline | 0.581 | 0.497 |
| fixed | 0.433 | 0.323 |
| lib | 0.094 | 0.050 |
| guard0.8 | 0.576 | 0.487 |
| guard0.9 | 0.581 | 0.497 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.531 | 0.417 |
| no_counts (lib_nref/in_train=0) | 0.581 | 0.497 |
| no_sim (lib_sim/same=0) | 0.531 | 0.417 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.436 | 0.307 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 233 | 0.748 | 0.557 | 0.121 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 233 | 0.748 | 0.557 | 0.121 |

learned loses (fixed top-1, learned not): 9; learned wins (learned top-1, fixed not): 61

lost molecules: learned top-1 has in_train 0.56 / lib_nref mean 2.6 / lib_sim mean 0.181 / pop mean 5.05; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 5.34

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.761 | -0.206 | -0.026 |
| z_fp | -0.499 | 0.724 | 1.212 |
| fp | -0.266 | 11.135 | 21.784 |
| fp_rank_window | -0.230 | 3.047 | 2.007 |
| lsynonyms | -0.155 | 1.841 | 1.838 |
| lib_sim | -0.076 | 0.000 | 0.181 |
| ppm_err | -0.073 | 0.765 | 0.765 |
| ce_known | -0.039 | 0.111 | 0.111 |
| in_coconut | +0.086 | 0.333 | 0.222 |
| pop_public | +0.156 | 5.344 | 5.051 |
| gl | +0.376 | 0.493 | 0.411 |
| z_gl | +0.838 | 3.599 | 2.648 |

