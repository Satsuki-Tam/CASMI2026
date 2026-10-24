# learned-fusion probe: run_panel_v2/P_np250/rank_v4e (w_ice 0.0; 23 features)

## view c1: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.857 | 0.776 |
| pipeline | 0.854 | 0.768 |
| fixed | 0.862 | 0.796 |
| lib | 0.908 | 0.852 |
| guard0.6_0.1 | 0.884 | 0.820 |
| guard0.7_0.1 | 0.883 | 0.820 |
| guard0.7_0.2 | 0.870 | 0.800 |
| guard0.8_0.1 | 0.876 | 0.808 |
| guard0.8_0.2 | 0.866 | 0.792 |
| guard0.9_0.1 | 0.859 | 0.780 |
| guard0.9_0.2 | 0.857 | 0.776 |
| fguard0.6_0.1 | 0.907 | 0.856 |
| fguard0.7_0.1 | 0.903 | 0.852 |
| fguard0.7_0.2 | 0.893 | 0.836 |
| fguard0.8_0.1 | 0.895 | 0.844 |
| fguard0.8_0.2 | 0.884 | 0.824 |
| fguard0.9_0.1 | 0.870 | 0.808 |
| fguard0.9_0.2 | 0.865 | 0.800 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.718 | 0.592 |
| no_counts (lib_nref/in_train=0) | 0.857 | 0.776 |
| no_sim (lib_sim/same=0) | 0.718 | 0.592 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.892 | 0.820 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 6 | 0.648 | 0.382 | 0.488 | 1.00 |
| [6,20] | 15 | 0.782 | 0.750 | 0.827 | 1.00 |
| [21,100] | 229 | 0.867 | 0.882 | 0.925 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 23 | 0.683 | 0.715 | 0.604 |
| [0.60,0.80) | 77 | 0.821 | 0.823 | 0.893 |
| [0.80,0.90) | 125 | 0.887 | 0.908 | 0.955 |
| [0.90,0.95) | 24 | 0.972 | 0.885 | 1.000 |
| [0.95,1.00) | 1 | 1.000 | 1.000 | 1.000 |

learned loses (fixed top-1, learned not): 24; learned wins (learned top-1, fixed not): 19

lost molecules: learned top-1 has in_train 0.88 / lib_nref mean 18.4 / lib_sim mean 0.570 / pop mean 11.07; truth has in_train 1.00 / lib_nref mean 23.5 / lib_sim mean 0.741 / pop mean 18.19

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lotus | -0.310 | 3.736 | 1.709 |
| z_fp | -0.273 | 1.154 | 1.471 |
| fp_rank_window | -0.182 | 3.002 | 2.139 |
| fp | -0.143 | 15.831 | 23.736 |
| lsynonyms | -0.134 | 4.683 | 3.326 |
| z_gl | -0.103 | 1.986 | 1.999 |
| lsid | -0.068 | 6.108 | 4.584 |
| ppm_err | -0.055 | 1.061 | 1.061 |
| pop_public | +0.063 | 18.191 | 11.072 |
| lib_margin | +0.121 | 0.051 | -0.120 |
| lpmid | +0.239 | 6.373 | 2.700 |
| lib_sim | +0.246 | 0.741 | 0.570 |

## view c2: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.674 | 0.520 |
| pipeline | 0.715 | 0.572 |
| fixed | 0.862 | 0.796 |
| lib | 0.224 | 0.052 |
| guard0.6_0.1 | 0.655 | 0.488 |
| guard0.7_0.1 | 0.666 | 0.504 |
| guard0.7_0.2 | 0.668 | 0.508 |
| guard0.8_0.1 | 0.674 | 0.520 |
| guard0.8_0.2 | 0.674 | 0.520 |
| guard0.9_0.1 | 0.674 | 0.520 |
| guard0.9_0.2 | 0.674 | 0.520 |
| fguard0.6_0.1 | 0.783 | 0.648 |
| fguard0.7_0.1 | 0.812 | 0.696 |
| fguard0.7_0.2 | 0.826 | 0.724 |
| fguard0.8_0.1 | 0.838 | 0.748 |
| fguard0.8_0.2 | 0.842 | 0.756 |
| fguard0.9_0.1 | 0.858 | 0.788 |
| fguard0.9_0.2 | 0.858 | 0.788 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.718 | 0.592 |
| no_counts (lib_nref/in_train=0) | 0.674 | 0.520 |
| no_sim (lib_sim/same=0) | 0.718 | 0.592 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.511 | 0.312 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 250 | 0.674 | 0.862 | 0.224 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 250 | 0.674 | 0.862 | 0.224 |

learned loses (fixed top-1, learned not): 75; learned wins (learned top-1, fixed not): 6

lost molecules: learned top-1 has in_train 0.83 / lib_nref mean 13.4 / lib_sim mean 0.524 / pop mean 10.20; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 18.18

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -1.158 | -0.420 | 0.105 |
| lib_sim | -0.666 | 0.000 | 0.524 |
| lotus | -0.261 | 3.467 | 1.445 |
| lib_same | -0.214 | 0.000 | 0.490 |
| z_fp | -0.135 | 0.976 | 1.292 |
| fp | -0.048 | 8.373 | 16.061 |
| ppm_err | -0.045 | 1.159 | 1.145 |
| fp_rank_window | -0.033 | 3.176 | 2.438 |
| gl | +0.112 | 0.215 | 0.196 |
| pop_public | +0.211 | 18.177 | 10.204 |
| lpmid | +0.343 | 6.565 | 2.401 |
| z_gl | +0.395 | 2.020 | 1.838 |

