# learned-fusion probe: run_panel_v2/P_np250/rank_v4g (w_ice 1.0; 26 features)

## view c1: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.699 | 0.560 |
| pipeline | 0.708 | 0.560 |
| fixed | 0.864 | 0.804 |
| lib | 0.908 | 0.852 |
| guard0.6_0.1 | 0.829 | 0.764 |
| guard0.7_0.1 | 0.806 | 0.732 |
| guard0.8_0.1 | 0.765 | 0.668 |
| guard0.8_0.2 | 0.750 | 0.644 |
| guard0.9_0.2 | 0.717 | 0.592 |
| fguard0.6_0.1 | 0.913 | 0.872 |
| fguard0.7_0.1 | 0.907 | 0.864 |
| fguard0.8_0.1 | 0.900 | 0.856 |
| fguard0.8_0.2 | 0.887 | 0.832 |
| fguard0.9_0.2 | 0.867 | 0.808 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.810 | 0.724 |
| no_counts (lib_nref/in_train=0) | 0.699 | 0.560 |
| no_sim (lib_sim/same=0) | 0.810 | 0.724 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.839 | 0.776 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 6 | 0.433 | 0.469 | 0.488 | 1.00 |
| [6,20] | 15 | 0.653 | 0.692 | 0.827 | 1.00 |
| [21,100] | 229 | 0.709 | 0.886 | 0.925 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 23 | 0.662 | 0.704 | 0.604 |
| [0.60,0.80) | 77 | 0.539 | 0.841 | 0.893 |
| [0.80,0.90) | 125 | 0.793 | 0.902 | 0.955 |
| [0.90,0.95) | 24 | 0.773 | 0.889 | 1.000 |
| [0.95,1.00) | 1 | 0.500 | 1.000 | 1.000 |

learned loses (fixed top-1, learned not): 76; learned wins (learned top-1, fixed not): 15

lost molecules: learned top-1 has in_train 0.21 / lib_nref mean 3.3 / lib_sim mean 0.090 / pop mean 7.87; truth has in_train 1.00 / lib_nref mean 23.4 / lib_sim mean 0.766 / pop mean 18.44

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_fp | -0.315 | 1.357 | 1.413 |
| z_gl | -0.312 | 2.557 | 2.331 |
| z_ice | -0.268 | 2.481 | 2.210 |
| ce_known | -0.253 | 1.000 | 1.000 |
| lib_same | -0.249 | 0.749 | 0.083 |
| fp_rank_window | -0.182 | 2.447 | 2.226 |
| gl | -0.133 | 0.437 | 0.402 |
| lotus | -0.102 | 3.304 | 0.733 |
| src_bit | +0.097 | 0.947 | 0.342 |
| lib_sim | +0.180 | 0.766 | 0.090 |
| lpmid | +0.385 | 6.741 | 1.538 |
| lib_margin | +0.692 | 0.229 | -0.446 |

## view c2: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.886 | 0.840 |
| pipeline | 0.896 | 0.852 |
| fixed | 0.864 | 0.804 |
| lib | 0.224 | 0.052 |
| guard0.6_0.1 | 0.798 | 0.684 |
| guard0.7_0.1 | 0.825 | 0.728 |
| guard0.8_0.1 | 0.859 | 0.788 |
| guard0.8_0.2 | 0.866 | 0.800 |
| guard0.9_0.2 | 0.882 | 0.832 |
| fguard0.6_0.1 | 0.783 | 0.652 |
| fguard0.7_0.1 | 0.810 | 0.696 |
| fguard0.8_0.1 | 0.838 | 0.752 |
| fguard0.8_0.2 | 0.842 | 0.760 |
| fguard0.9_0.2 | 0.860 | 0.796 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.810 | 0.724 |
| no_counts (lib_nref/in_train=0) | 0.886 | 0.840 |
| no_sim (lib_sim/same=0) | 0.810 | 0.724 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.611 | 0.432 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 250 | 0.886 | 0.864 | 0.224 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 250 | 0.886 | 0.864 | 0.224 |

learned loses (fixed top-1, learned not): 14; learned wins (learned top-1, fixed not): 23

lost molecules: learned top-1 has in_train 0.50 / lib_nref mean 6.6 / lib_sim mean 0.182 / pop mean 9.32; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 17.89

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.449 | -0.285 | -0.103 |
| fp | -0.437 | -11.362 | 7.871 |
| z_fp | -0.263 | 0.398 | 0.965 |
| lotus | -0.241 | 4.111 | 1.152 |
| fp_rank_window | -0.124 | 4.203 | 3.173 |
| z_ice | -0.122 | 0.630 | 0.697 |
| z_gl | -0.101 | 0.703 | 0.748 |
| ice | -0.096 | -0.566 | -0.561 |
| src_bit | +0.082 | 0.857 | 0.571 |
| lsynonyms | +0.204 | 4.278 | 2.850 |
| pop_public | +0.279 | 17.885 | 9.320 |
| lpmid | +0.348 | 6.170 | 2.059 |

