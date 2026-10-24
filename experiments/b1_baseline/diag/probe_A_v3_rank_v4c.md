# learned-fusion probe: run_v3_eval/A_timstof/rank_v4c (w_ice 0.0; 23 features)

## view c1: 7 molecules, truth in shortlist 7 (strict MRR over 7; GL fallback molecules 0)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.905 | 0.857 |
| pipeline | 0.905 | 0.857 |
| fixed | 0.634 | 0.571 |
| lib | 0.786 | 0.714 |
| guard0.6_0.1 | 0.905 | 0.857 |
| guard0.7_0.1 | 0.905 | 0.857 |
| guard0.7_0.2 | 0.905 | 0.857 |
| guard0.8_0.1 | 0.905 | 0.857 |
| guard0.8_0.2 | 0.905 | 0.857 |
| guard0.9_0.1 | 0.905 | 0.857 |
| guard0.9_0.2 | 0.905 | 0.857 |
| fguard0.6_0.1 | 0.865 | 0.857 |
| fguard0.7_0.1 | 0.865 | 0.857 |
| fguard0.7_0.2 | 0.865 | 0.857 |
| fguard0.8_0.1 | 0.865 | 0.857 |
| fguard0.8_0.2 | 0.865 | 0.857 |
| fguard0.9_0.1 | 0.634 | 0.571 |
| fguard0.9_0.2 | 0.634 | 0.571 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.629 | 0.571 |
| no_counts (lib_nref/in_train=0) | 0.905 | 0.857 |
| no_sim (lib_sim/same=0) | 0.629 | 0.571 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.929 | 0.857 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [6,20] | 7 | 0.905 | 0.634 | 0.786 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 2 | 0.667 | 0.526 | 0.250 |
| [0.60,0.80) | 2 | 1.000 | 1.000 | 1.000 |
| [0.80,0.90) | 3 | 1.000 | 0.462 | 1.000 |

learned loses (fixed top-1, learned not): 0; learned wins (learned top-1, fixed not): 2

## view c2: 300 molecules, truth in shortlist 283 (strict MRR over 300; GL fallback molecules -566)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.675 | 0.523 |
| pipeline | 0.675 | 0.523 |
| fixed | 0.652 | 0.527 |
| lib | 0.000 | 0.000 |
| guard0.6_0.1 | 0.653 | 0.493 |
| guard0.7_0.1 | 0.660 | 0.497 |
| guard0.7_0.2 | 0.668 | 0.510 |
| guard0.8_0.1 | 0.670 | 0.513 |
| guard0.8_0.2 | 0.672 | 0.517 |
| guard0.9_0.1 | 0.673 | 0.520 |
| guard0.9_0.2 | 0.673 | 0.520 |
| fguard0.6_0.1 | 0.602 | 0.447 |
| fguard0.7_0.1 | 0.611 | 0.453 |
| fguard0.7_0.2 | 0.617 | 0.460 |
| fguard0.8_0.1 | 0.627 | 0.480 |
| fguard0.8_0.2 | 0.630 | 0.483 |
| fguard0.9_0.1 | 0.645 | 0.513 |
| fguard0.9_0.2 | 0.645 | 0.513 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.793 | 0.730 |
| no_counts (lib_nref/in_train=0) | 0.675 | 0.523 |
| no_sim (lib_sim/same=0) | 0.793 | 0.730 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.566 | 0.380 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 283 | 0.716 | 0.692 | 0.000 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 283 | 0.716 | 0.692 | 0.000 |

learned loses (fixed top-1, learned not): 41; learned wins (learned top-1, fixed not): 40

lost molecules: learned top-1 has in_train 0.78 / lib_nref mean 5.0 / lib_sim mean 0.584 / pop mean 2.06; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 2.27

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_sim | -2.299 | 0.000 | 0.584 |
| lib_margin | -2.191 | -0.450 | 0.134 |
| lib_same | -0.722 | 0.000 | 0.584 |
| lib_max_mol | -0.282 | 0.688 | 0.688 |
| ppm_err | -0.048 | 0.652 | 0.652 |
| pop_public | -0.019 | 2.269 | 2.061 |
| lsid | -0.014 | 1.641 | 1.443 |
| lsynonyms | -0.011 | 1.088 | 1.019 |
| fp_rank_window | +0.493 | 1.736 | 2.395 |
| z_gl | +0.544 | 3.807 | 3.179 |
| z_fp | +0.698 | 1.410 | 1.163 |
| gl | +0.950 | 0.585 | 0.519 |

