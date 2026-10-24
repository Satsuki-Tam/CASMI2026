# learned-fusion probe: run_panel_v2/P_np250/rank_v4c (w_ice 0.0; 23 features)

## view c1: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.900 | 0.836 |
| pipeline | 0.894 | 0.820 |
| fixed | 0.862 | 0.796 |
| lib | 0.908 | 0.852 |
| guard0.6_0.1 | 0.914 | 0.860 |
| guard0.7_0.1 | 0.912 | 0.856 |
| guard0.7_0.2 | 0.903 | 0.840 |
| guard0.8_0.1 | 0.907 | 0.848 |
| guard0.8_0.2 | 0.900 | 0.836 |
| guard0.9_0.1 | 0.903 | 0.840 |
| guard0.9_0.2 | 0.900 | 0.836 |
| fguard0.6_0.1 | 0.907 | 0.856 |
| fguard0.7_0.1 | 0.903 | 0.852 |
| fguard0.7_0.2 | 0.893 | 0.836 |
| fguard0.8_0.1 | 0.895 | 0.844 |
| fguard0.8_0.2 | 0.884 | 0.824 |
| fguard0.9_0.1 | 0.870 | 0.808 |
| fguard0.9_0.2 | 0.865 | 0.800 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.732 | 0.604 |
| no_counts (lib_nref/in_train=0) | 0.900 | 0.836 |
| no_sim (lib_sim/same=0) | 0.732 | 0.604 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.913 | 0.856 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 6 | 0.690 | 0.382 | 0.488 | 1.00 |
| [6,20] | 15 | 0.808 | 0.750 | 0.827 | 1.00 |
| [21,100] | 229 | 0.911 | 0.882 | 0.925 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 23 | 0.729 | 0.715 | 0.604 |
| [0.60,0.80) | 77 | 0.843 | 0.823 | 0.893 |
| [0.80,0.90) | 125 | 0.952 | 0.908 | 0.955 |
| [0.90,0.95) | 24 | 0.969 | 0.885 | 1.000 |
| [0.95,1.00) | 1 | 1.000 | 1.000 | 1.000 |

learned loses (fixed top-1, learned not): 18; learned wins (learned top-1, fixed not): 28

lost molecules: learned top-1 has in_train 0.94 / lib_nref mean 19.9 / lib_sim mean 0.692 / pop mean 11.18; truth has in_train 1.00 / lib_nref mean 23.4 / lib_sim mean 0.708 / pop mean 18.27

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| z_fp | -0.599 | 1.413 | 1.726 |
| lib_margin | -0.459 | 0.043 | 0.027 |
| lotus | -0.298 | 3.528 | 1.616 |
| fp | -0.258 | 32.348 | 39.997 |
| fp_rank_window | -0.213 | 2.508 | 1.765 |
| lsid | -0.110 | 6.173 | 4.771 |
| ppm_err | -0.105 | 0.822 | 0.822 |
| np_bit | -0.077 | 1.000 | 1.000 |
| lib_sim | +0.103 | 0.708 | 0.692 |
| src_bit | +0.113 | 0.944 | 0.667 |
| lsynonyms | +0.191 | 4.572 | 3.372 |
| lpmid | +0.454 | 6.576 | 2.584 |

## view c2: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.640 | 0.464 |
| pipeline | 0.687 | 0.524 |
| fixed | 0.862 | 0.796 |
| lib | 0.224 | 0.052 |
| guard0.6_0.1 | 0.633 | 0.456 |
| guard0.7_0.1 | 0.640 | 0.464 |
| guard0.7_0.2 | 0.640 | 0.464 |
| guard0.8_0.1 | 0.640 | 0.464 |
| guard0.8_0.2 | 0.640 | 0.464 |
| guard0.9_0.1 | 0.640 | 0.464 |
| guard0.9_0.2 | 0.640 | 0.464 |
| fguard0.6_0.1 | 0.783 | 0.648 |
| fguard0.7_0.1 | 0.812 | 0.696 |
| fguard0.7_0.2 | 0.826 | 0.724 |
| fguard0.8_0.1 | 0.838 | 0.748 |
| fguard0.8_0.2 | 0.842 | 0.756 |
| fguard0.9_0.1 | 0.858 | 0.788 |
| fguard0.9_0.2 | 0.858 | 0.788 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.732 | 0.604 |
| no_counts (lib_nref/in_train=0) | 0.640 | 0.464 |
| no_sim (lib_sim/same=0) | 0.732 | 0.604 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.403 | 0.164 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 250 | 0.640 | 0.862 | 0.224 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 250 | 0.640 | 0.862 | 0.224 |

learned loses (fixed top-1, learned not): 86; learned wins (learned top-1, fixed not): 3

lost molecules: learned top-1 has in_train 0.92 / lib_nref mean 14.5 / lib_sim mean 0.609 / pop mean 10.29; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 17.96

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_sim | -2.086 | 0.000 | 0.609 |
| lib_margin | -1.906 | -0.441 | 0.168 |
| lib_same | -0.582 | 0.000 | 0.571 |
| lib_max_mol | -0.263 | 0.638 | 0.638 |
| fp | -0.242 | 13.520 | 19.765 |
| ppm_err | -0.097 | 1.218 | 1.206 |
| lotus | -0.066 | 3.376 | 1.604 |
| z_fp | -0.019 | 1.108 | 1.345 |
| pop_public | +0.312 | 17.960 | 10.291 |
| gl | +0.343 | 0.257 | 0.213 |
| lsynonyms | +0.556 | 4.534 | 3.143 |
| lpmid | +0.721 | 6.425 | 2.308 |

