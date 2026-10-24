# learned-fusion probe: run_panel_v2/P_np250/rank_v2 (w_ice 1.0; 28 features)

## view c1: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.588 | 0.420 |
| pipeline | 0.600 | 0.428 |
| fixed | 0.864 | 0.804 |
| lib | 0.908 | 0.852 |
| guard0.8 | 0.683 | 0.580 |
| guard0.9 | 0.607 | 0.452 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.849 | 0.776 |
| no_counts (lib_nref/in_train=0) | 0.822 | 0.736 |
| no_sim (lib_sim/same=0) | 0.631 | 0.472 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.833 | 0.748 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 6 | 0.472 | 0.469 | 0.488 | 1.00 |
| [6,20] | 15 | 0.677 | 0.692 | 0.827 | 1.00 |
| [21,100] | 229 | 0.585 | 0.886 | 0.925 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 23 | 0.636 | 0.704 | 0.604 |
| [0.60,0.80) | 77 | 0.515 | 0.841 | 0.893 |
| [0.80,0.90) | 125 | 0.594 | 0.902 | 0.955 |
| [0.90,0.95) | 24 | 0.759 | 0.889 | 1.000 |
| [0.95,1.00) | 1 | 0.250 | 1.000 | 1.000 |

learned loses (fixed top-1, learned not): 105; learned wins (learned top-1, fixed not): 9

lost molecules: learned top-1 has in_train 0.13 / lib_nref mean 1.0 / lib_sim mean 0.053 / pop mean 7.32; truth has in_train 1.00 / lib_nref mean 23.5 / lib_sim mean 0.791 / pop mean 18.76

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_nref | -0.618 | 23.533 | 1.048 |
| z_gl | -0.284 | 2.497 | 2.311 |
| z_fp | -0.280 | 1.287 | 1.282 |
| lsynonyms | -0.248 | 4.717 | 2.658 |
| z_ice | -0.231 | 2.497 | 2.232 |
| gl | -0.147 | 0.461 | 0.433 |
| ce_known | -0.140 | 1.000 | 1.000 |
| ice | -0.131 | 0.442 | 0.412 |
| src_bit | +0.119 | 0.914 | 0.210 |
| lib_sim | +0.169 | 0.791 | 0.053 |
| lpmid | +0.473 | 7.057 | 1.172 |
| lib_margin | +0.860 | 0.250 | -0.489 |

## view c2: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.914 | 0.872 |
| pipeline | 0.900 | 0.848 |
| fixed | 0.864 | 0.804 |
| lib | 0.224 | 0.052 |
| guard0.8 | 0.892 | 0.828 |
| guard0.9 | 0.910 | 0.864 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.849 | 0.776 |
| no_counts (lib_nref/in_train=0) | 0.903 | 0.860 |
| no_sim (lib_sim/same=0) | 0.919 | 0.884 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.607 | 0.408 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 250 | 0.914 | 0.864 | 0.224 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 250 | 0.914 | 0.864 | 0.224 |

learned loses (fixed top-1, learned not): 8; learned wins (learned top-1, fixed not): 25

lost molecules: learned top-1 has in_train 0.12 / lib_nref mean 1.5 / lib_sim mean 0.077 / pop mean 8.44; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 16.22

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| fp | -0.603 | -14.877 | 10.528 |
| z_fp | -0.471 | 0.062 | 0.947 |
| lib_margin | -0.268 | -0.269 | -0.192 |
| fp_rank_window | -0.172 | 5.022 | 3.028 |
| z_ice | -0.161 | 1.278 | 1.434 |
| ppm_err | -0.097 | 1.451 | 1.451 |
| gl | -0.063 | -0.122 | -0.118 |
| z_gl | -0.058 | 1.237 | 1.298 |
| lsid | +0.188 | 5.984 | 3.569 |
| lsynonyms | +0.269 | 3.843 | 2.442 |
| lpmid | +0.348 | 5.396 | 1.833 |
| pop_public | +0.405 | 16.215 | 8.444 |

