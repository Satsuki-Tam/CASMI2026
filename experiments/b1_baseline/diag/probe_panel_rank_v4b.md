# learned-fusion probe: run_panel_v2/P_np250/rank_v4b (w_ice 0.0; 23 features)

## view c1: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.737 | 0.604 |
| pipeline | 0.754 | 0.620 |
| fixed | 0.862 | 0.796 |
| lib | 0.908 | 0.852 |
| guard0.6_0.1 | 0.840 | 0.776 |
| guard0.7_0.1 | 0.819 | 0.744 |
| guard0.7_0.2 | 0.799 | 0.708 |
| guard0.8_0.1 | 0.784 | 0.692 |
| guard0.8_0.2 | 0.770 | 0.664 |
| guard0.9_0.1 | 0.747 | 0.624 |
| guard0.9_0.2 | 0.745 | 0.620 |
| fguard0.6_0.1 | 0.907 | 0.856 |
| fguard0.7_0.1 | 0.903 | 0.852 |
| fguard0.7_0.2 | 0.893 | 0.836 |
| fguard0.8_0.1 | 0.895 | 0.844 |
| fguard0.8_0.2 | 0.884 | 0.824 |
| fguard0.9_0.1 | 0.870 | 0.808 |
| fguard0.9_0.2 | 0.865 | 0.800 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.781 | 0.680 |
| no_counts (lib_nref/in_train=0) | 0.737 | 0.604 |
| no_sim (lib_sim/same=0) | 0.781 | 0.680 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.861 | 0.788 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 6 | 0.449 | 0.382 | 0.488 | 1.00 |
| [6,20] | 15 | 0.707 | 0.750 | 0.827 | 1.00 |
| [21,100] | 229 | 0.746 | 0.882 | 0.925 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 23 | 0.617 | 0.715 | 0.604 |
| [0.60,0.80) | 77 | 0.583 | 0.823 | 0.893 |
| [0.80,0.90) | 125 | 0.827 | 0.908 | 0.955 |
| [0.90,0.95) | 24 | 0.865 | 0.885 | 1.000 |
| [0.95,1.00) | 1 | 1.000 | 1.000 | 1.000 |

learned loses (fixed top-1, learned not): 67; learned wins (learned top-1, fixed not): 19

lost molecules: learned top-1 has in_train 0.19 / lib_nref mean 2.4 / lib_sim mean 0.082 / pop mean 7.33; truth has in_train 1.00 / lib_nref mean 23.5 / lib_sim mean 0.764 / pop mean 18.65

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_fp | -0.593 | 1.421 | 1.504 |
| z_gl | -0.443 | 2.375 | 2.251 |
| fp_rank_window | -0.408 | 2.441 | 2.104 |
| gl | -0.313 | 0.360 | 0.343 |
| lib_same | -0.297 | 0.746 | 0.077 |
| ce_known | -0.214 | 1.000 | 1.000 |
| fp | -0.089 | 19.432 | 22.899 |
| ppm_err | -0.084 | 1.341 | 1.341 |
| src_bit | +0.064 | 0.896 | 0.313 |
| lpmid | +0.345 | 6.807 | 1.138 |
| lib_sim | +0.485 | 0.764 | 0.082 |
| lib_margin | +1.017 | 0.221 | -0.461 |

## view c2: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.882 | 0.828 |
| pipeline | 0.890 | 0.832 |
| fixed | 0.862 | 0.796 |
| lib | 0.224 | 0.052 |
| guard0.6_0.1 | 0.791 | 0.668 |
| guard0.7_0.1 | 0.818 | 0.712 |
| guard0.7_0.2 | 0.842 | 0.752 |
| guard0.8_0.1 | 0.854 | 0.776 |
| guard0.8_0.2 | 0.861 | 0.788 |
| guard0.9_0.1 | 0.874 | 0.812 |
| guard0.9_0.2 | 0.878 | 0.820 |
| fguard0.6_0.1 | 0.783 | 0.648 |
| fguard0.7_0.1 | 0.812 | 0.696 |
| fguard0.7_0.2 | 0.826 | 0.724 |
| fguard0.8_0.1 | 0.838 | 0.748 |
| fguard0.8_0.2 | 0.842 | 0.756 |
| fguard0.9_0.1 | 0.858 | 0.788 |
| fguard0.9_0.2 | 0.858 | 0.788 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.781 | 0.680 |
| no_counts (lib_nref/in_train=0) | 0.882 | 0.828 |
| no_sim (lib_sim/same=0) | 0.781 | 0.680 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.624 | 0.424 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 250 | 0.882 | 0.862 | 0.224 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 250 | 0.882 | 0.862 | 0.224 |

learned loses (fixed top-1, learned not): 16; learned wins (learned top-1, fixed not): 24

lost molecules: learned top-1 has in_train 0.38 / lib_nref mean 3.2 / lib_sim mean 0.149 / pop mean 7.39; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 17.91

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_fp | -0.739 | 0.375 | 1.417 |
| lib_margin | -0.543 | -0.348 | -0.199 |
| fp_rank_window | -0.506 | 4.252 | 1.842 |
| fp | -0.466 | -20.010 | 8.171 |
| gl | -0.112 | -0.279 | -0.274 |
| z_gl | -0.074 | 0.967 | 1.006 |
| ppm_err | -0.072 | 1.008 | 0.943 |
| lib_sim | -0.033 | 0.000 | 0.149 |
| src_bit | +0.221 | 0.812 | 0.250 |
| pop_public | +0.245 | 17.912 | 7.388 |
| lsynonyms | +0.328 | 4.441 | 2.337 |
| lpmid | +0.342 | 6.512 | 1.282 |

