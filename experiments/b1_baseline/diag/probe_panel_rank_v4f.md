# learned-fusion probe: run_panel_v2/P_np250/rank_v4f (w_ice 0.0; 23 features)

## view c1: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.798 | 0.704 |
| pipeline | 0.812 | 0.716 |
| fixed | 0.862 | 0.796 |
| lib | 0.908 | 0.852 |
| guard0.6_0.1 | 0.850 | 0.780 |
| guard0.7_0.1 | 0.847 | 0.776 |
| guard0.7_0.2 | 0.826 | 0.744 |
| guard0.8_0.1 | 0.835 | 0.760 |
| guard0.8_0.2 | 0.817 | 0.732 |
| guard0.9_0.1 | 0.801 | 0.708 |
| guard0.9_0.2 | 0.798 | 0.704 |
| fguard0.6_0.1 | 0.907 | 0.856 |
| fguard0.7_0.1 | 0.903 | 0.852 |
| fguard0.7_0.2 | 0.893 | 0.836 |
| fguard0.8_0.1 | 0.895 | 0.844 |
| fguard0.8_0.2 | 0.884 | 0.824 |
| fguard0.9_0.1 | 0.870 | 0.808 |
| fguard0.9_0.2 | 0.865 | 0.800 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.706 | 0.572 |
| no_counts (lib_nref/in_train=0) | 0.798 | 0.704 |
| no_sim (lib_sim/same=0) | 0.706 | 0.572 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.880 | 0.812 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 6 | 0.625 | 0.382 | 0.488 | 1.00 |
| [6,20] | 15 | 0.741 | 0.750 | 0.827 | 1.00 |
| [21,100] | 229 | 0.807 | 0.882 | 0.925 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 23 | 0.638 | 0.715 | 0.604 |
| [0.60,0.80) | 77 | 0.763 | 0.823 | 0.893 |
| [0.80,0.90) | 125 | 0.815 | 0.908 | 0.955 |
| [0.90,0.95) | 24 | 0.967 | 0.885 | 1.000 |
| [0.95,1.00) | 1 | 1.000 | 1.000 | 1.000 |

learned loses (fixed top-1, learned not): 40; learned wins (learned top-1, fixed not): 17

lost molecules: learned top-1 has in_train 0.80 / lib_nref mean 15.9 / lib_sim mean 0.522 / pop mean 10.82; truth has in_train 1.00 / lib_nref mean 23.7 / lib_sim mean 0.762 / pop mean 19.05

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lotus | -0.420 | 4.081 | 1.780 |
| fp_rank_window | -0.392 | 2.746 | 1.618 |
| z_fp | -0.348 | 1.212 | 1.655 |
| fp | -0.228 | 12.412 | 23.563 |
| lsynonyms | -0.129 | 4.717 | 3.288 |
| in_coconut | -0.109 | 1.000 | 0.950 |
| pop_public | -0.080 | 19.054 | 10.818 |
| np_bit | -0.065 | 1.000 | 0.950 |
| gl | +0.068 | 0.268 | 0.252 |
| lib_sim | +0.142 | 0.762 | 0.522 |
| lpmid | +0.222 | 6.898 | 2.473 |
| lib_margin | +0.648 | 0.097 | -0.142 |

## view c2: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.685 | 0.540 |
| pipeline | 0.726 | 0.588 |
| fixed | 0.862 | 0.796 |
| lib | 0.224 | 0.052 |
| guard0.6_0.1 | 0.658 | 0.492 |
| guard0.7_0.1 | 0.672 | 0.516 |
| guard0.7_0.2 | 0.675 | 0.520 |
| guard0.8_0.1 | 0.679 | 0.528 |
| guard0.8_0.2 | 0.679 | 0.528 |
| guard0.9_0.1 | 0.683 | 0.536 |
| guard0.9_0.2 | 0.683 | 0.536 |
| fguard0.6_0.1 | 0.783 | 0.648 |
| fguard0.7_0.1 | 0.812 | 0.696 |
| fguard0.7_0.2 | 0.826 | 0.724 |
| fguard0.8_0.1 | 0.838 | 0.748 |
| fguard0.8_0.2 | 0.842 | 0.756 |
| fguard0.9_0.1 | 0.858 | 0.788 |
| fguard0.9_0.2 | 0.858 | 0.788 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.706 | 0.572 |
| no_counts (lib_nref/in_train=0) | 0.685 | 0.540 |
| no_sim (lib_sim/same=0) | 0.706 | 0.572 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.542 | 0.340 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 250 | 0.685 | 0.862 | 0.224 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 250 | 0.685 | 0.862 | 0.224 |

learned loses (fixed top-1, learned not): 70; learned wins (learned top-1, fixed not): 6

lost molecules: learned top-1 has in_train 0.70 / lib_nref mean 11.9 / lib_sim mean 0.441 / pop mean 9.99; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 18.63

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.653 | -0.428 | 0.013 |
| lotus | -0.307 | 3.534 | 1.320 |
| z_fp | -0.192 | 1.017 | 1.405 |
| lib_sim | -0.173 | 0.000 | 0.441 |
| fp_rank_window | -0.170 | 3.140 | 2.149 |
| fp | -0.127 | 7.308 | 17.218 |
| lib_same | -0.080 | 0.000 | 0.413 |
| ppm_err | -0.058 | 1.131 | 1.116 |
| src_bit | +0.080 | 0.929 | 0.571 |
| gl | +0.101 | 0.223 | 0.207 |
| z_gl | +0.197 | 2.029 | 1.885 |
| lpmid | +0.307 | 6.823 | 2.219 |

