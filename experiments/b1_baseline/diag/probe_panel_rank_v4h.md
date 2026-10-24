# learned-fusion probe: run_panel_v2/P_np250/rank_v4h (w_ice 1.0; 26 features)

## view c1: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.831 | 0.764 |
| pipeline | 0.833 | 0.760 |
| fixed | 0.864 | 0.804 |
| lib | 0.908 | 0.852 |
| guard0.6_0.1 | 0.859 | 0.800 |
| guard0.7_0.1 | 0.858 | 0.800 |
| guard0.8_0.1 | 0.851 | 0.792 |
| guard0.8_0.2 | 0.838 | 0.776 |
| guard0.9_0.2 | 0.831 | 0.764 |
| fguard0.6_0.1 | 0.913 | 0.872 |
| fguard0.7_0.1 | 0.907 | 0.864 |
| fguard0.8_0.1 | 0.900 | 0.856 |
| fguard0.8_0.2 | 0.887 | 0.832 |
| fguard0.9_0.2 | 0.867 | 0.808 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.711 | 0.588 |
| no_counts (lib_nref/in_train=0) | 0.831 | 0.764 |
| no_sim (lib_sim/same=0) | 0.711 | 0.588 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.892 | 0.836 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 6 | 0.617 | 0.469 | 0.488 | 1.00 |
| [6,20] | 15 | 0.758 | 0.692 | 0.827 | 1.00 |
| [21,100] | 229 | 0.841 | 0.886 | 0.925 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 23 | 0.680 | 0.704 | 0.604 |
| [0.60,0.80) | 77 | 0.782 | 0.841 | 0.893 |
| [0.80,0.90) | 125 | 0.861 | 0.902 | 0.955 |
| [0.90,0.95) | 24 | 0.967 | 0.889 | 1.000 |
| [0.95,1.00) | 1 | 1.000 | 1.000 | 1.000 |

learned loses (fixed top-1, learned not): 31; learned wins (learned top-1, fixed not): 21

lost molecules: learned top-1 has in_train 0.77 / lib_nref mean 15.3 / lib_sim mean 0.452 / pop mean 10.62; truth has in_train 1.00 / lib_nref mean 23.3 / lib_sim mean 0.741 / pop mean 18.72

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lotus | -0.760 | 4.353 | 1.577 |
| fp | -0.257 | 24.677 | 28.633 |
| lsynonyms | -0.167 | 4.632 | 3.131 |
| z_fp | -0.133 | 1.360 | 1.501 |
| lsid | -0.130 | 6.209 | 4.383 |
| fp_rank_window | -0.121 | 2.521 | 2.187 |
| z_gl | -0.084 | 2.162 | 2.071 |
| ppm_err | -0.074 | 1.155 | 1.155 |
| z_ice | +0.105 | 2.035 | 1.901 |
| lib_sim | +0.237 | 0.741 | 0.452 |
| lpmid | +0.246 | 6.522 | 2.592 |
| lib_margin | +0.373 | 0.039 | -0.250 |

## view c2: 250 molecules, truth in shortlist 250 (strict MRR over 250; GL fallback molecules 34)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.678 | 0.548 |
| pipeline | 0.724 | 0.604 |
| fixed | 0.864 | 0.804 |
| lib | 0.224 | 0.052 |
| guard0.6_0.1 | 0.650 | 0.500 |
| guard0.7_0.1 | 0.663 | 0.520 |
| guard0.8_0.1 | 0.672 | 0.536 |
| guard0.8_0.2 | 0.672 | 0.536 |
| guard0.9_0.2 | 0.676 | 0.544 |
| fguard0.6_0.1 | 0.783 | 0.652 |
| fguard0.7_0.1 | 0.810 | 0.696 |
| fguard0.8_0.1 | 0.838 | 0.752 |
| fguard0.8_0.2 | 0.842 | 0.760 |
| fguard0.9_0.2 | 0.860 | 0.796 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.711 | 0.588 |
| no_counts (lib_nref/in_train=0) | 0.678 | 0.548 |
| no_sim (lib_sim/same=0) | 0.711 | 0.588 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.512 | 0.328 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 250 | 0.678 | 0.864 | 0.224 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 250 | 0.678 | 0.864 | 0.224 |

learned loses (fixed top-1, learned not): 71; learned wins (learned top-1, fixed not): 7

lost molecules: learned top-1 has in_train 0.69 / lib_nref mean 11.5 / lib_sim mean 0.416 / pop mean 9.86; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 18.40

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.848 | -0.403 | 0.014 |
| lotus | -0.673 | 3.763 | 1.416 |
| lib_sim | -0.311 | 0.000 | 0.416 |
| fp | -0.236 | 16.562 | 24.373 |
| z_fp | -0.125 | 1.058 | 1.332 |
| ppm_err | -0.094 | 1.182 | 1.167 |
| lib_same | -0.082 | 0.000 | 0.395 |
| n_cands | -0.034 | 220.127 | 220.127 |
| z_gl | +0.161 | 2.035 | 1.857 |
| pop_public | +0.161 | 18.397 | 9.857 |
| z_ice | +0.203 | 1.979 | 1.829 |
| lpmid | +0.376 | 6.638 | 2.271 |

