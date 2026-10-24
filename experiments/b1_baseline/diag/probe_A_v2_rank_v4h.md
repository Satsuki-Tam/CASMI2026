# learned-fusion probe: run1_v2/A_timstof/rank_v4h (w_ice 1.0; 26 features)

## view c1: 7 molecules, truth in shortlist 7 (strict MRR over 7; GL fallback molecules 0)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.864 | 0.857 |
| pipeline | 0.864 | 0.857 |
| fixed | 0.590 | 0.429 |
| lib | 0.786 | 0.714 |
| guard0.6_0.1 | 0.864 | 0.857 |
| guard0.7_0.1 | 0.864 | 0.857 |
| guard0.8_0.1 | 0.864 | 0.857 |
| guard0.8_0.2 | 0.864 | 0.857 |
| guard0.9_0.2 | 0.864 | 0.857 |
| fguard0.6_0.1 | 0.864 | 0.857 |
| fguard0.7_0.1 | 0.793 | 0.714 |
| fguard0.8_0.1 | 0.793 | 0.714 |
| fguard0.8_0.2 | 0.793 | 0.714 |
| fguard0.9_0.2 | 0.590 | 0.429 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.661 | 0.571 |
| no_counts (lib_nref/in_train=0) | 0.864 | 0.857 |
| no_sim (lib_sim/same=0) | 0.661 | 0.571 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.893 | 0.857 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [6,20] | 7 | 0.864 | 0.590 | 0.786 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 2 | 0.525 | 0.525 | 0.250 |
| [0.60,0.80) | 2 | 1.000 | 0.750 | 1.000 |
| [0.80,0.90) | 3 | 1.000 | 0.528 | 1.000 |

learned loses (fixed top-1, learned not): 0; learned wins (learned top-1, fixed not): 3

## view c2: 300 molecules, truth in shortlist 275 (strict MRR over 300; GL fallback molecules -550)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.737 | 0.640 |
| pipeline | 0.737 | 0.640 |
| fixed | 0.671 | 0.553 |
| lib | 0.010 | 0.000 |
| guard0.6_0.1 | 0.688 | 0.563 |
| guard0.7_0.1 | 0.701 | 0.577 |
| guard0.8_0.1 | 0.719 | 0.607 |
| guard0.8_0.2 | 0.725 | 0.617 |
| guard0.9_0.2 | 0.735 | 0.637 |
| fguard0.6_0.1 | 0.623 | 0.477 |
| fguard0.7_0.1 | 0.635 | 0.490 |
| fguard0.8_0.1 | 0.649 | 0.510 |
| fguard0.8_0.2 | 0.652 | 0.517 |
| fguard0.9_0.2 | 0.666 | 0.543 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.752 | 0.667 |
| no_counts (lib_nref/in_train=0) | 0.737 | 0.640 |
| no_sim (lib_sim/same=0) | 0.752 | 0.667 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.637 | 0.483 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 275 | 0.804 | 0.732 | 0.011 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 275 | 0.804 | 0.732 | 0.011 |

learned loses (fixed top-1, learned not): 14; learned wins (learned top-1, fixed not): 40

lost molecules: learned top-1 has in_train 0.50 / lib_nref mean 2.1 / lib_sim mean 0.400 / pop mean 2.00; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 2.28

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -0.970 | -0.410 | -0.009 |
| lib_sim | -0.438 | 0.000 | 0.400 |
| pop_public | -0.135 | 2.284 | 1.996 |
| lib_same | -0.123 | 0.000 | 0.400 |
| lsynonyms | -0.046 | 0.921 | 1.024 |
| lib_max_mol | -0.032 | 0.627 | 0.627 |
| z_ice | -0.030 | 2.809 | 2.734 |
| n_cands | -0.026 | 121.714 | 121.714 |
| gl | +0.104 | 0.536 | 0.515 |
| fp | +0.114 | 7.698 | 0.916 |
| z_fp | +0.238 | 2.049 | 1.650 |
| z_gl | +0.334 | 3.023 | 2.803 |

