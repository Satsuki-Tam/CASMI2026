# learned-fusion probe: run_v3_c1/B_nplib/rank_v4b (w_ice 0.0; 23 features)

## view c1: 257 molecules, truth in shortlist 257 (strict MRR over 257; GL fallback molecules 4)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.918 | 0.883 |
| pipeline | 0.918 | 0.883 |
| fixed | 0.546 | 0.401 |
| lib | 0.904 | 0.868 |
| guard0.6_0.1 | 0.929 | 0.903 |
| guard0.7_0.1 | 0.927 | 0.899 |
| guard0.7_0.2 | 0.927 | 0.899 |
| guard0.8_0.1 | 0.923 | 0.891 |
| guard0.8_0.2 | 0.923 | 0.891 |
| guard0.9_0.1 | 0.921 | 0.887 |
| guard0.9_0.2 | 0.921 | 0.887 |
| fguard0.6_0.1 | 0.827 | 0.770 |
| fguard0.7_0.1 | 0.790 | 0.724 |
| fguard0.7_0.2 | 0.760 | 0.685 |
| fguard0.8_0.1 | 0.761 | 0.685 |
| fguard0.8_0.2 | 0.734 | 0.650 |
| fguard0.9_0.1 | 0.680 | 0.572 |
| fguard0.9_0.2 | 0.658 | 0.545 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.658 | 0.521 |
| no_counts (lib_nref/in_train=0) | 0.918 | 0.883 |
| no_sim (lib_sim/same=0) | 0.658 | 0.521 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.917 | 0.879 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 72 | 0.870 | 0.522 | 0.816 | 1.00 |
| [6,20] | 161 | 0.939 | 0.547 | 0.942 | 1.00 |
| [21,100] | 24 | 0.924 | 0.611 | 0.912 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 68 | 0.799 | 0.575 | 0.704 |
| [0.60,0.80) | 49 | 0.936 | 0.537 | 0.952 |
| [0.80,0.90) | 55 | 0.943 | 0.557 | 0.982 |
| [0.90,0.95) | 39 | 0.970 | 0.563 | 0.966 |
| [0.95,1.00) | 46 | 1.000 | 0.483 | 1.000 |

learned loses (fixed top-1, learned not): 5; learned wins (learned top-1, fixed not): 129

lost molecules: learned top-1 has in_train 0.80 / lib_nref mean 3.0 / lib_sim mean 0.282 / pop mean 5.80; truth has in_train 1.00 / lib_nref mean 10.4 / lib_sim mean 0.252 / pop mean 9.84

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.436 | 0.078 | 0.108 |
| lib_sim | -0.310 | 0.252 | 0.282 |
| src_bit | -0.198 | 0.400 | 0.600 |
| ce_known | -0.092 | 0.200 | 0.200 |
| z_fp | -0.078 | 0.807 | 0.705 |
| fp | -0.068 | 0.258 | -0.406 |
| lotus | -0.065 | 1.121 | 0.220 |
| ppm_err | -0.062 | 0.771 | 0.771 |
| np_bit | +0.076 | 0.400 | 0.200 |
| lpmid | +0.096 | 3.473 | 0.743 |
| pop_public | +0.183 | 9.842 | 5.799 |
| gl | +0.240 | 0.424 | 0.350 |

## view c2: 300 molecules, truth in shortlist 233 (strict MRR over 300; GL fallback molecules -465)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.582 | 0.497 |
| pipeline | 0.582 | 0.497 |
| fixed | 0.433 | 0.323 |
| lib | 0.094 | 0.050 |
| guard0.6_0.1 | 0.565 | 0.467 |
| guard0.7_0.1 | 0.574 | 0.480 |
| guard0.7_0.2 | 0.576 | 0.483 |
| guard0.8_0.1 | 0.581 | 0.493 |
| guard0.8_0.2 | 0.581 | 0.493 |
| guard0.9_0.1 | 0.582 | 0.497 |
| guard0.9_0.2 | 0.582 | 0.497 |
| fguard0.6_0.1 | 0.423 | 0.310 |
| fguard0.7_0.1 | 0.428 | 0.317 |
| fguard0.7_0.2 | 0.429 | 0.317 |
| fguard0.8_0.1 | 0.432 | 0.323 |
| fguard0.8_0.2 | 0.433 | 0.323 |
| fguard0.9_0.1 | 0.432 | 0.323 |
| fguard0.9_0.2 | 0.433 | 0.323 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.551 | 0.453 |
| no_counts (lib_nref/in_train=0) | 0.582 | 0.497 |
| no_sim (lib_sim/same=0) | 0.551 | 0.453 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.424 | 0.297 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 233 | 0.750 | 0.557 | 0.121 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 233 | 0.750 | 0.557 | 0.121 |

learned loses (fixed top-1, learned not): 10; learned wins (learned top-1, fixed not): 62

lost molecules: learned top-1 has in_train 0.40 / lib_nref mean 2.7 / lib_sim mean 0.123 / pop mean 3.30; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 4.94

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.601 | -0.215 | -0.092 |
| fp_rank_window | -0.227 | 2.906 | 2.445 |
| z_fp | -0.221 | 0.735 | 0.871 |
| lib_sim | -0.125 | 0.000 | 0.123 |
| fp | -0.094 | 4.591 | 10.134 |
| src_bit | -0.087 | 0.100 | 0.200 |
| lsynonyms | -0.027 | 1.633 | 1.397 |
| ce_known | -0.026 | 0.000 | 0.000 |
| np_bit | +0.060 | 0.200 | 0.100 |
| pop_public | +0.153 | 4.938 | 3.295 |
| gl | +0.201 | 0.470 | 0.421 |
| z_gl | +0.202 | 3.099 | 2.579 |

