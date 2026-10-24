# learned-fusion probe: run_v3_c1/B_nplib/rank_v4f (w_ice 0.0; 23 features)

## view c1: 257 molecules, truth in shortlist 257 (strict MRR over 257; GL fallback molecules 4)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.882 | 0.813 |
| pipeline | 0.882 | 0.813 |
| fixed | 0.546 | 0.401 |
| lib | 0.904 | 0.868 |
| guard0.6_0.1 | 0.912 | 0.868 |
| guard0.7_0.1 | 0.909 | 0.860 |
| guard0.7_0.2 | 0.905 | 0.852 |
| guard0.8_0.1 | 0.901 | 0.848 |
| guard0.8_0.2 | 0.899 | 0.844 |
| guard0.9_0.1 | 0.893 | 0.833 |
| guard0.9_0.2 | 0.891 | 0.829 |
| fguard0.6_0.1 | 0.827 | 0.770 |
| fguard0.7_0.1 | 0.790 | 0.724 |
| fguard0.7_0.2 | 0.760 | 0.685 |
| fguard0.8_0.1 | 0.761 | 0.685 |
| fguard0.8_0.2 | 0.734 | 0.650 |
| fguard0.9_0.1 | 0.680 | 0.572 |
| fguard0.9_0.2 | 0.658 | 0.545 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.643 | 0.514 |
| no_counts (lib_nref/in_train=0) | 0.882 | 0.813 |
| no_sim (lib_sim/same=0) | 0.643 | 0.514 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.903 | 0.864 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 72 | 0.837 | 0.522 | 0.816 | 1.00 |
| [6,20] | 161 | 0.893 | 0.547 | 0.942 | 1.00 |
| [21,100] | 24 | 0.940 | 0.611 | 0.912 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 68 | 0.798 | 0.575 | 0.704 |
| [0.60,0.80) | 49 | 0.888 | 0.537 | 0.952 |
| [0.80,0.90) | 55 | 0.915 | 0.557 | 0.982 |
| [0.90,0.95) | 39 | 0.908 | 0.563 | 0.966 |
| [0.95,1.00) | 46 | 0.937 | 0.483 | 1.000 |

learned loses (fixed top-1, learned not): 3; learned wins (learned top-1, fixed not): 109

lost molecules: learned top-1 has in_train 0.67 / lib_nref mean 2.7 / lib_sim mean 0.230 / pop mean 5.04; truth has in_train 1.00 / lib_nref mean 7.3 / lib_sim mean 0.298 / pop mean 6.12

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_fp | -0.276 | 0.776 | 1.384 |
| lsynonyms | -0.235 | 2.199 | 2.058 |
| fp_rank_window | -0.203 | 1.927 | 1.342 |
| z_gl | -0.187 | 3.788 | 3.413 |
| fp | -0.067 | -1.080 | 8.521 |
| lib_margin | -0.062 | 0.094 | 0.026 |
| ppm_err | -0.050 | 1.454 | 1.454 |
| n_query | -0.008 | 3.667 | 3.667 |
| lib_sim | +0.050 | 0.298 | 0.230 |
| lpmid | +0.087 | 1.887 | 1.238 |
| in_coconut | +0.139 | 0.333 | 0.000 |
| np_bit | +0.169 | 0.333 | 0.000 |

## view c2: 300 molecules, truth in shortlist 233 (strict MRR over 300; GL fallback molecules -465)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.508 | 0.400 |
| pipeline | 0.508 | 0.400 |
| fixed | 0.433 | 0.323 |
| lib | 0.094 | 0.050 |
| guard0.6_0.1 | 0.500 | 0.387 |
| guard0.7_0.1 | 0.505 | 0.393 |
| guard0.7_0.2 | 0.505 | 0.393 |
| guard0.8_0.1 | 0.508 | 0.400 |
| guard0.8_0.2 | 0.508 | 0.400 |
| guard0.9_0.1 | 0.508 | 0.400 |
| guard0.9_0.2 | 0.508 | 0.400 |
| fguard0.6_0.1 | 0.423 | 0.310 |
| fguard0.7_0.1 | 0.428 | 0.317 |
| fguard0.7_0.2 | 0.429 | 0.317 |
| fguard0.8_0.1 | 0.432 | 0.323 |
| fguard0.8_0.2 | 0.433 | 0.323 |
| fguard0.9_0.1 | 0.432 | 0.323 |
| fguard0.9_0.2 | 0.433 | 0.323 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.527 | 0.433 |
| no_counts (lib_nref/in_train=0) | 0.508 | 0.400 |
| no_sim (lib_sim/same=0) | 0.527 | 0.433 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.402 | 0.283 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 233 | 0.655 | 0.557 | 0.121 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 233 | 0.655 | 0.557 | 0.121 |

learned loses (fixed top-1, learned not): 12; learned wins (learned top-1, fixed not): 35

lost molecules: learned top-1 has in_train 0.75 / lib_nref mean 5.8 / lib_sim mean 0.292 / pop mean 5.29; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 7.87

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -1.218 | -0.199 | 0.093 |
| fp_rank_window | -0.144 | 3.063 | 2.384 |
| lib_sim | -0.114 | 0.000 | 0.292 |
| z_fp | -0.113 | 0.671 | 0.890 |
| lotus | -0.066 | 0.995 | 0.334 |
| lib_same | -0.050 | 0.000 | 0.287 |
| ppm_err | -0.048 | 1.006 | 1.006 |
| lsynonyms | -0.026 | 2.292 | 2.101 |
| np_bit | +0.112 | 0.500 | 0.250 |
| lpmid | +0.124 | 2.443 | 0.839 |
| gl | +0.232 | 0.372 | 0.344 |
| z_gl | +0.406 | 2.608 | 2.301 |

