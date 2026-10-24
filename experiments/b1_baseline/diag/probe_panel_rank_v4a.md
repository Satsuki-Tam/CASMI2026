# learned-fusion probe: run_panel_v2/P_np250/rank_v4a (w_ice 0.0; 23 features)

## view c1: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.688 | 0.548 |
| pipeline | 0.714 | 0.572 |
| fixed | 0.862 | 0.796 |
| lib | 0.908 | 0.852 |
| guard0.8 | 0.747 | 0.652 |
| guard0.9 | 0.698 | 0.568 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.782 | 0.676 |
| no_counts (lib_nref/in_train=0) | 0.688 | 0.548 |
| no_sim (lib_sim/same=0) | 0.782 | 0.676 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.839 | 0.752 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 6 | 0.406 | 0.382 | 0.488 | 1.00 |
| [6,20] | 15 | 0.628 | 0.750 | 0.827 | 1.00 |
| [21,100] | 229 | 0.699 | 0.882 | 0.925 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 23 | 0.597 | 0.715 | 0.604 |
| [0.60,0.80) | 77 | 0.579 | 0.823 | 0.893 |
| [0.80,0.90) | 125 | 0.739 | 0.908 | 0.955 |
| [0.90,0.95) | 24 | 0.840 | 0.885 | 1.000 |
| [0.95,1.00) | 1 | 1.000 | 1.000 | 1.000 |

learned loses (fixed top-1, learned not): 71; learned wins (learned top-1, fixed not): 9

lost molecules: learned top-1 has in_train 0.17 / lib_nref mean 2.2 / lib_sim mean 0.069 / pop mean 7.36; truth has in_train 1.00 / lib_nref mean 23.7 / lib_sim mean 0.775 / pop mean 18.88

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_fp | -0.675 | 1.432 | 1.477 |
| lib_same | -0.510 | 0.763 | 0.069 |
| fp_rank_window | -0.401 | 2.369 | 2.152 |
| gl | -0.316 | 0.354 | 0.329 |
| z_gl | -0.203 | 2.350 | 2.186 |
| fp | -0.147 | 19.935 | 22.146 |
| ce_known | -0.114 | 1.000 | 1.000 |
| pop_public | -0.101 | 18.885 | 7.359 |
| src_bit | +0.152 | 0.901 | 0.324 |
| lib_sim | +0.282 | 0.775 | 0.069 |
| lpmid | +0.392 | 6.936 | 1.089 |
| lib_margin | +0.939 | 0.244 | -0.463 |

## view c2: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.893 | 0.848 |
| pipeline | 0.885 | 0.828 |
| fixed | 0.862 | 0.796 |
| lib | 0.224 | 0.052 |
| guard0.8 | 0.873 | 0.808 |
| guard0.9 | 0.889 | 0.840 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.782 | 0.676 |
| no_counts (lib_nref/in_train=0) | 0.893 | 0.848 |
| no_sim (lib_sim/same=0) | 0.782 | 0.676 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.671 | 0.492 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 250 | 0.893 | 0.862 | 0.224 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 250 | 0.893 | 0.862 | 0.224 |

learned loses (fixed top-1, learned not): 14; learned wins (learned top-1, fixed not): 27

lost molecules: learned top-1 has in_train 0.21 / lib_nref mean 1.1 / lib_sim mean 0.047 / pop mean 6.87; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 18.02

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_fp | -0.883 | 0.277 | 1.188 |
| fp | -0.722 | -15.347 | 10.978 |
| fp_rank_window | -0.404 | 4.413 | 2.433 |
| z_gl | -0.224 | 1.164 | 1.361 |
| lib_margin | -0.175 | -0.342 | -0.295 |
| ppm_err | -0.129 | 0.915 | 0.842 |
| gl | -0.101 | -0.073 | -0.064 |
| lsid | -0.041 | 6.032 | 3.392 |
| np_bit | +0.128 | 1.000 | 0.714 |
| src_bit | +0.188 | 0.786 | 0.429 |
| lsynonyms | +0.332 | 4.444 | 2.220 |
| lpmid | +0.432 | 6.721 | 1.000 |

