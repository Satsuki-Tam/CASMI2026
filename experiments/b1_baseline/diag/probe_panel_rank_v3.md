# learned-fusion probe: run_panel_v2/P_np250/rank_v3 (w_ice 0.0; 25 features)

## view c1: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.430 | 0.244 |
| pipeline | 0.465 | 0.284 |
| fixed | 0.862 | 0.796 |
| lib | 0.908 | 0.852 |
| guard0.8 | 0.598 | 0.496 |
| guard0.9 | 0.466 | 0.300 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.859 | 0.796 |
| no_counts (lib_nref/in_train=0) | 0.825 | 0.736 |
| no_sim (lib_sim/same=0) | 0.512 | 0.320 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.868 | 0.792 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 6 | 0.454 | 0.382 | 0.488 | 1.00 |
| [6,20] | 15 | 0.657 | 0.750 | 0.827 | 1.00 |
| [21,100] | 229 | 0.414 | 0.882 | 0.925 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 23 | 0.427 | 0.715 | 0.604 |
| [0.60,0.80) | 77 | 0.389 | 0.823 | 0.893 |
| [0.80,0.90) | 125 | 0.431 | 0.908 | 0.955 |
| [0.90,0.95) | 24 | 0.567 | 0.885 | 1.000 |
| [0.95,1.00) | 1 | 0.200 | 1.000 | 1.000 |

learned loses (fixed top-1, learned not): 144; learned wins (learned top-1, fixed not): 6

lost molecules: learned top-1 has in_train 0.15 / lib_nref mean 0.8 / lib_sim mean 0.059 / pop mean 6.65; truth has in_train 1.00 / lib_nref mean 23.8 / lib_sim mean 0.797 / pop mean 18.72

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_nref | -0.865 | 23.785 | 0.833 |
| z_gl | -0.693 | 2.711 | 2.438 |
| z_fp | -0.499 | 1.256 | 1.288 |
| fp_rank_window | -0.462 | 2.599 | 2.352 |
| pop_public | -0.397 | 18.716 | 6.650 |
| gl | -0.299 | 0.427 | 0.394 |
| lib_same | -0.289 | 0.788 | 0.050 |
| ce_known | -0.212 | 1.000 | 1.000 |
| src_bit | +0.162 | 0.938 | 0.236 |
| lpmid | +0.447 | 7.094 | 0.969 |
| lib_sim | +0.468 | 0.797 | 0.059 |
| lib_margin | +1.232 | 0.306 | -0.432 |

## view c2: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.934 | 0.912 |
| pipeline | 0.921 | 0.888 |
| fixed | 0.862 | 0.796 |
| lib | 0.224 | 0.052 |
| guard0.8 | 0.912 | 0.868 |
| guard0.9 | 0.930 | 0.904 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.859 | 0.796 |
| no_counts (lib_nref/in_train=0) | 0.911 | 0.876 |
| no_sim (lib_sim/same=0) | 0.932 | 0.908 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.704 | 0.552 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 250 | 0.934 | 0.862 | 0.224 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 250 | 0.934 | 0.862 | 0.224 |

learned loses (fixed top-1, learned not): 6; learned wins (learned top-1, fixed not): 35

lost molecules: learned top-1 has in_train 0.33 / lib_nref mean 3.0 / lib_sim mean 0.142 / pop mean 7.20; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 16.14

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| fp | -0.986 | -31.812 | -0.529 |
| fp_rank_window | -0.656 | 5.909 | 3.710 |
| z_fp | -0.531 | -0.247 | 0.744 |
| lib_margin | -0.401 | -0.169 | -0.027 |
| z_gl | -0.306 | 1.165 | 1.530 |
| ppm_err | -0.131 | 1.081 | 1.081 |
| src_bit | -0.114 | 0.500 | 0.667 |
| gl | -0.078 | -0.306 | -0.280 |
| pop_public | +0.223 | 16.140 | 7.204 |
| lsynonyms | +0.237 | 3.695 | 2.238 |
| lsid | +0.324 | 5.737 | 3.281 |
| lpmid | +0.596 | 5.602 | 0.842 |

