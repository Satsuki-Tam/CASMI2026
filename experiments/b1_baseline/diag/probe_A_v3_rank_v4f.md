# learned-fusion probe: run_v3_eval/A_timstof/rank_v4f (w_ice 0.0; 23 features)

## view c1: 7 molecules, truth in shortlist 7 (strict MRR over 7; GL fallback molecules 0)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.867 | 0.857 |
| pipeline | 0.867 | 0.857 |
| fixed | 0.634 | 0.571 |
| lib | 0.786 | 0.714 |
| guard0.6_0.1 | 0.867 | 0.857 |
| guard0.7_0.1 | 0.867 | 0.857 |
| guard0.7_0.2 | 0.867 | 0.857 |
| guard0.8_0.1 | 0.867 | 0.857 |
| guard0.8_0.2 | 0.867 | 0.857 |
| guard0.9_0.1 | 0.867 | 0.857 |
| guard0.9_0.2 | 0.867 | 0.857 |
| fguard0.6_0.1 | 0.865 | 0.857 |
| fguard0.7_0.1 | 0.865 | 0.857 |
| fguard0.7_0.2 | 0.865 | 0.857 |
| fguard0.8_0.1 | 0.865 | 0.857 |
| fguard0.8_0.2 | 0.865 | 0.857 |
| fguard0.9_0.1 | 0.634 | 0.571 |
| fguard0.9_0.2 | 0.634 | 0.571 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.637 | 0.571 |
| no_counts (lib_nref/in_train=0) | 0.867 | 0.857 |
| no_sim (lib_sim/same=0) | 0.637 | 0.571 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.886 | 0.857 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [6,20] | 7 | 0.867 | 0.634 | 0.786 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 2 | 0.536 | 0.526 | 0.250 |
| [0.60,0.80) | 2 | 1.000 | 1.000 | 1.000 |
| [0.80,0.90) | 3 | 1.000 | 0.462 | 1.000 |

learned loses (fixed top-1, learned not): 0; learned wins (learned top-1, fixed not): 2

## view c2: 300 molecules, truth in shortlist 283 (strict MRR over 300; GL fallback molecules -566)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.730 | 0.617 |
| pipeline | 0.730 | 0.617 |
| fixed | 0.652 | 0.527 |
| lib | 0.000 | 0.000 |
| guard0.6_0.1 | 0.677 | 0.533 |
| guard0.7_0.1 | 0.691 | 0.547 |
| guard0.7_0.2 | 0.704 | 0.567 |
| guard0.8_0.1 | 0.709 | 0.577 |
| guard0.8_0.2 | 0.714 | 0.587 |
| guard0.9_0.1 | 0.725 | 0.607 |
| guard0.9_0.2 | 0.727 | 0.610 |
| fguard0.6_0.1 | 0.602 | 0.447 |
| fguard0.7_0.1 | 0.611 | 0.453 |
| fguard0.7_0.2 | 0.617 | 0.460 |
| fguard0.8_0.1 | 0.627 | 0.480 |
| fguard0.8_0.2 | 0.630 | 0.483 |
| fguard0.9_0.1 | 0.645 | 0.513 |
| fguard0.9_0.2 | 0.645 | 0.513 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.738 | 0.630 |
| no_counts (lib_nref/in_train=0) | 0.730 | 0.617 |
| no_sim (lib_sim/same=0) | 0.738 | 0.630 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.624 | 0.460 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 283 | 0.774 | 0.692 | 0.000 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 283 | 0.774 | 0.692 | 0.000 |

learned loses (fixed top-1, learned not): 19; learned wins (learned top-1, fixed not): 46

lost molecules: learned top-1 has in_train 0.26 / lib_nref mean 1.4 / lib_sim mean 0.205 / pop mean 1.81; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 2.03

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.269 | -0.375 | -0.169 |
| lsynonyms | -0.102 | 0.902 | 0.986 |
| lib_sim | -0.095 | 0.000 | 0.205 |
| fp_rank_window | -0.093 | 1.765 | 1.349 |
| pop_public | -0.072 | 2.027 | 1.807 |
| lib_same | -0.047 | 0.000 | 0.205 |
| z_fp | -0.044 | 1.514 | 1.559 |
| fp | -0.043 | -5.613 | -3.447 |
| ce_known | +0.003 | 1.000 | 1.000 |
| n_cands | +0.004 | 254.526 | 254.526 |
| gl | +0.202 | 0.558 | 0.525 |
| z_gl | +0.202 | 4.084 | 3.704 |

