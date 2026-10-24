# learned-fusion probe: run_panel_v2/P_np250/rank_v4d (w_ice 0.0; 23 features)

## view c1: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.740 | 0.628 |
| pipeline | 0.740 | 0.620 |
| fixed | 0.862 | 0.796 |
| lib | 0.908 | 0.852 |
| guard0.6_0.1 | 0.840 | 0.784 |
| guard0.7_0.1 | 0.829 | 0.768 |
| guard0.7_0.2 | 0.791 | 0.712 |
| guard0.8_0.1 | 0.805 | 0.736 |
| guard0.8_0.2 | 0.774 | 0.688 |
| guard0.9_0.1 | 0.744 | 0.636 |
| guard0.9_0.2 | 0.742 | 0.632 |
| fguard0.6_0.1 | 0.907 | 0.856 |
| fguard0.7_0.1 | 0.903 | 0.852 |
| fguard0.7_0.2 | 0.893 | 0.836 |
| fguard0.8_0.1 | 0.895 | 0.844 |
| fguard0.8_0.2 | 0.884 | 0.824 |
| fguard0.9_0.1 | 0.870 | 0.808 |
| fguard0.9_0.2 | 0.865 | 0.800 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.810 | 0.724 |
| no_counts (lib_nref/in_train=0) | 0.740 | 0.628 |
| no_sim (lib_sim/same=0) | 0.810 | 0.724 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.894 | 0.844 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 6 | 0.450 | 0.382 | 0.488 | 1.00 |
| [6,20] | 15 | 0.660 | 0.750 | 0.827 | 1.00 |
| [21,100] | 229 | 0.753 | 0.882 | 0.925 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 23 | 0.586 | 0.715 | 0.604 |
| [0.60,0.80) | 77 | 0.646 | 0.823 | 0.893 |
| [0.80,0.90) | 125 | 0.782 | 0.908 | 0.955 |
| [0.90,0.95) | 24 | 0.958 | 0.885 | 1.000 |
| [0.95,1.00) | 1 | 1.000 | 1.000 | 1.000 |

learned loses (fixed top-1, learned not): 63; learned wins (learned top-1, fixed not): 21

lost molecules: learned top-1 has in_train 0.19 / lib_nref mean 2.3 / lib_sim mean 0.076 / pop mean 7.05; truth has in_train 1.00 / lib_nref mean 23.6 / lib_sim mean 0.767 / pop mean 18.61

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_gl | -0.709 | 2.542 | 2.271 |
| z_fp | -0.548 | 1.263 | 1.447 |
| fp_rank_window | -0.540 | 2.678 | 2.098 |
| gl | -0.404 | 0.454 | 0.422 |
| ce_known | -0.382 | 1.000 | 1.000 |
| lib_same | -0.371 | 0.749 | 0.065 |
| lsynonyms | -0.127 | 4.745 | 2.548 |
| ppm_err | -0.118 | 1.299 | 1.299 |
| src_bit | +0.146 | 0.937 | 0.270 |
| lpmid | +0.511 | 6.868 | 1.152 |
| lib_sim | +0.604 | 0.767 | 0.076 |
| lib_margin | +1.044 | 0.172 | -0.519 |

## view c2: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.877 | 0.816 |
| pipeline | 0.882 | 0.820 |
| fixed | 0.862 | 0.796 |
| lib | 0.224 | 0.052 |
| guard0.6_0.1 | 0.795 | 0.672 |
| guard0.7_0.1 | 0.816 | 0.700 |
| guard0.7_0.2 | 0.840 | 0.744 |
| guard0.8_0.1 | 0.850 | 0.764 |
| guard0.8_0.2 | 0.858 | 0.780 |
| guard0.9_0.1 | 0.869 | 0.800 |
| guard0.9_0.2 | 0.873 | 0.808 |
| fguard0.6_0.1 | 0.783 | 0.648 |
| fguard0.7_0.1 | 0.812 | 0.696 |
| fguard0.7_0.2 | 0.826 | 0.724 |
| fguard0.8_0.1 | 0.838 | 0.748 |
| fguard0.8_0.2 | 0.842 | 0.756 |
| fguard0.9_0.1 | 0.858 | 0.788 |
| fguard0.9_0.2 | 0.858 | 0.788 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.810 | 0.724 |
| no_counts (lib_nref/in_train=0) | 0.877 | 0.816 |
| no_sim (lib_sim/same=0) | 0.810 | 0.724 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.575 | 0.356 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 250 | 0.877 | 0.862 | 0.224 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 250 | 0.877 | 0.862 | 0.224 |

learned loses (fixed top-1, learned not): 18; learned wins (learned top-1, fixed not): 23

lost molecules: learned top-1 has in_train 0.39 / lib_nref mean 3.9 / lib_sim mean 0.204 / pop mean 7.10; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 17.00

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.702 | -0.306 | -0.102 |
| fp | -0.377 | -3.766 | 14.352 |
| z_fp | -0.370 | 0.653 | 1.300 |
| z_gl | -0.347 | 1.499 | 1.574 |
| fp_rank_window | -0.338 | 3.953 | 2.327 |
| lib_sim | -0.120 | 0.000 | 0.204 |
| ppm_err | -0.114 | 1.079 | 1.079 |
| lotus | -0.073 | 3.389 | 1.218 |
| pop_public | +0.260 | 17.003 | 7.096 |
| lsynonyms | +0.287 | 4.254 | 2.405 |
| src_bit | +0.325 | 0.722 | 0.278 |
| lpmid | +0.540 | 5.867 | 0.709 |

