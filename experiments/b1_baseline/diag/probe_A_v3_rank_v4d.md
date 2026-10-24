# learned-fusion probe: run_v3_eval/A_timstof/rank_v4d (w_ice 0.0; 23 features)

## view c1: 7 molecules, truth in shortlist 7 (strict MRR over 7; GL fallback molecules 0)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.776 | 0.714 |
| pipeline | 0.776 | 0.714 |
| fixed | 0.634 | 0.571 |
| lib | 0.786 | 0.714 |
| guard0.6_0.1 | 0.871 | 0.857 |
| guard0.7_0.1 | 0.776 | 0.714 |
| guard0.7_0.2 | 0.776 | 0.714 |
| guard0.8_0.1 | 0.776 | 0.714 |
| guard0.8_0.2 | 0.776 | 0.714 |
| guard0.9_0.1 | 0.776 | 0.714 |
| guard0.9_0.2 | 0.776 | 0.714 |
| fguard0.6_0.1 | 0.865 | 0.857 |
| fguard0.7_0.1 | 0.865 | 0.857 |
| fguard0.7_0.2 | 0.865 | 0.857 |
| fguard0.8_0.1 | 0.865 | 0.857 |
| fguard0.8_0.2 | 0.865 | 0.857 |
| fguard0.9_0.1 | 0.634 | 0.571 |
| fguard0.9_0.2 | 0.634 | 0.571 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.632 | 0.571 |
| no_counts (lib_nref/in_train=0) | 0.776 | 0.714 |
| no_sim (lib_sim/same=0) | 0.632 | 0.571 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.893 | 0.857 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [6,20] | 7 | 0.776 | 0.634 | 0.786 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 2 | 0.550 | 0.526 | 0.250 |
| [0.60,0.80) | 2 | 0.667 | 1.000 | 1.000 |
| [0.80,0.90) | 3 | 1.000 | 0.462 | 1.000 |

learned loses (fixed top-1, learned not): 1; learned wins (learned top-1, fixed not): 2

lost molecules: learned top-1 has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 2.54; truth has in_train 1.00 / lib_nref mean 10.0 / lib_sim mean 0.678 / pop mean 1.04

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| fp_rank_window | -1.390 | 2.773 | 0.693 |
| z_fp | -0.943 | 0.976 | 1.537 |
| ce_known | -0.476 | 1.000 | 1.000 |
| z_gl | -0.131 | 4.131 | 3.183 |
| lib_same | -0.111 | 0.678 | 0.000 |
| n_query | -0.102 | 4.000 | 4.000 |
| ppm_err | -0.052 | 0.800 | 0.800 |
| lib_max_mol | -0.051 | 0.678 | 0.678 |
| lsid | +0.194 | 0.693 | 2.197 |
| pop_public | +0.453 | 1.040 | 2.544 |
| lib_sim | +0.536 | 0.678 | 0.000 |
| lib_margin | +1.313 | 0.123 | -0.555 |

## view c2: 300 molecules, truth in shortlist 283 (strict MRR over 300; GL fallback molecules -566)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.769 | 0.683 |
| pipeline | 0.769 | 0.683 |
| fixed | 0.652 | 0.527 |
| lib | 0.000 | 0.000 |
| guard0.6_0.1 | 0.694 | 0.557 |
| guard0.7_0.1 | 0.711 | 0.577 |
| guard0.7_0.2 | 0.730 | 0.607 |
| guard0.8_0.1 | 0.733 | 0.613 |
| guard0.8_0.2 | 0.742 | 0.630 |
| guard0.9_0.1 | 0.752 | 0.650 |
| guard0.9_0.2 | 0.756 | 0.657 |
| fguard0.6_0.1 | 0.602 | 0.447 |
| fguard0.7_0.1 | 0.611 | 0.453 |
| fguard0.7_0.2 | 0.617 | 0.460 |
| fguard0.8_0.1 | 0.627 | 0.480 |
| fguard0.8_0.2 | 0.630 | 0.483 |
| fguard0.9_0.1 | 0.645 | 0.513 |
| fguard0.9_0.2 | 0.645 | 0.513 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.744 | 0.643 |
| no_counts (lib_nref/in_train=0) | 0.769 | 0.683 |
| no_sim (lib_sim/same=0) | 0.744 | 0.643 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.623 | 0.463 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 283 | 0.815 | 0.692 | 0.000 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 283 | 0.815 | 0.692 | 0.000 |

learned loses (fixed top-1, learned not): 16; learned wins (learned top-1, fixed not): 63

lost molecules: learned top-1 has in_train 0.19 / lib_nref mean 0.9 / lib_sim mean 0.149 / pop mean 1.73; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 1.78

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.444 | -0.335 | -0.186 |
| lib_sim | -0.189 | 0.000 | 0.149 |
| pop_public | -0.151 | 1.783 | 1.729 |
| lsynonyms | -0.110 | 0.766 | 1.015 |
| fp | -0.082 | -3.700 | -5.258 |
| lsid | -0.030 | 1.400 | 1.222 |
| ppm_err | -0.029 | 0.701 | 0.701 |
| z_fp | -0.027 | 1.474 | 1.401 |
| fp_rank_window | +0.019 | 1.811 | 1.668 |
| ce_known | +0.089 | 1.000 | 1.000 |
| gl | +0.120 | 0.544 | 0.517 |
| z_gl | +0.311 | 3.873 | 3.587 |

