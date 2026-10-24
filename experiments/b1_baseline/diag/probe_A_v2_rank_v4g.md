# learned-fusion probe: run1_v2/A_timstof/rank_v4g (w_ice 1.0; 26 features)

## view c1: 7 molecules, truth in shortlist 7 (strict MRR over 7; GL fallback molecules 0)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.643 | 0.429 |
| pipeline | 0.643 | 0.429 |
| fixed | 0.590 | 0.429 |
| lib | 0.786 | 0.714 |
| guard0.6_0.1 | 0.857 | 0.857 |
| guard0.7_0.1 | 0.786 | 0.714 |
| guard0.8_0.1 | 0.786 | 0.714 |
| guard0.8_0.2 | 0.786 | 0.714 |
| guard0.9_0.2 | 0.643 | 0.429 |
| fguard0.6_0.1 | 0.864 | 0.857 |
| fguard0.7_0.1 | 0.793 | 0.714 |
| fguard0.8_0.1 | 0.793 | 0.714 |
| fguard0.8_0.2 | 0.793 | 0.714 |
| fguard0.9_0.2 | 0.590 | 0.429 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.643 | 0.571 |
| no_counts (lib_nref/in_train=0) | 0.643 | 0.429 |
| no_sim (lib_sim/same=0) | 0.643 | 0.571 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.727 | 0.571 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [6,20] | 7 | 0.643 | 0.590 | 0.786 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 2 | 0.500 | 0.525 | 0.250 |
| [0.60,0.80) | 2 | 0.750 | 0.750 | 1.000 |
| [0.80,0.90) | 3 | 0.667 | 0.528 | 1.000 |

learned loses (fixed top-1, learned not): 0; learned wins (learned top-1, fixed not): 0

## view c2: 300 molecules, truth in shortlist 275 (strict MRR over 300; GL fallback molecules -550)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.792 | 0.733 |
| pipeline | 0.792 | 0.733 |
| fixed | 0.671 | 0.553 |
| lib | 0.010 | 0.000 |
| guard0.6_0.1 | 0.711 | 0.597 |
| guard0.7_0.1 | 0.727 | 0.613 |
| guard0.8_0.1 | 0.753 | 0.660 |
| guard0.8_0.2 | 0.762 | 0.677 |
| guard0.9_0.2 | 0.778 | 0.707 |
| fguard0.6_0.1 | 0.623 | 0.477 |
| fguard0.7_0.1 | 0.635 | 0.490 |
| fguard0.8_0.1 | 0.649 | 0.510 |
| fguard0.8_0.2 | 0.652 | 0.517 |
| fguard0.9_0.2 | 0.666 | 0.543 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.761 | 0.683 |
| no_counts (lib_nref/in_train=0) | 0.792 | 0.733 |
| no_sim (lib_sim/same=0) | 0.761 | 0.683 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.698 | 0.583 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 275 | 0.863 | 0.732 | 0.011 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 275 | 0.863 | 0.732 | 0.011 |

learned loses (fixed top-1, learned not): 7; learned wins (learned top-1, fixed not): 61

lost molecules: learned top-1 has in_train 0.14 / lib_nref mean 0.1 / lib_sim mean 0.087 / pop mean 1.50; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 1.47

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lsynonyms | -0.321 | 0.355 | 0.908 |
| z_ice | -0.303 | 2.307 | 2.509 |
| pop_public | -0.297 | 1.467 | 1.503 |
| ice | -0.099 | 0.401 | 0.426 |
| lib_margin | -0.078 | -0.345 | -0.258 |
| fp_rank_window | -0.058 | 1.694 | 1.551 |
| n_query | -0.049 | 3.143 | 3.143 |
| z_fp | -0.048 | 2.271 | 1.832 |
| ce_known | +0.020 | 1.000 | 1.000 |
| gl | +0.055 | 0.506 | 0.476 |
| src_bit | +0.059 | 0.143 | 0.000 |
| z_gl | +0.202 | 3.009 | 2.701 |

