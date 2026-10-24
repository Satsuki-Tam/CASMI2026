# learned-fusion probe: run_c1_v2/B_nplib/rank_v4h (w_ice 1.0; 26 features)

## view c1: 257 molecules, truth in shortlist 257 (strict MRR over 257; GL fallback molecules 4)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.919 | 0.887 |
| pipeline | 0.917 | 0.883 |
| fixed | 0.561 | 0.428 |
| lib | 0.906 | 0.868 |
| guard0.6_0.1 | 0.932 | 0.903 |
| guard0.7_0.1 | 0.932 | 0.903 |
| guard0.8_0.1 | 0.929 | 0.899 |
| guard0.8_0.2 | 0.926 | 0.895 |
| guard0.9_0.2 | 0.922 | 0.891 |
| fguard0.6_0.1 | 0.824 | 0.767 |
| fguard0.7_0.1 | 0.791 | 0.720 |
| fguard0.8_0.1 | 0.762 | 0.681 |
| fguard0.8_0.2 | 0.740 | 0.654 |
| fguard0.9_0.2 | 0.665 | 0.553 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.687 | 0.556 |
| no_counts (lib_nref/in_train=0) | 0.919 | 0.887 |
| no_sim (lib_sim/same=0) | 0.687 | 0.556 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.898 | 0.860 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 72 | 0.862 | 0.507 | 0.821 | 1.00 |
| [6,20] | 161 | 0.938 | 0.584 | 0.943 | 1.00 |
| [21,100] | 24 | 0.960 | 0.573 | 0.912 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 68 | 0.836 | 0.566 | 0.713 |
| [0.60,0.80) | 49 | 0.939 | 0.563 | 0.952 |
| [0.80,0.90) | 55 | 0.938 | 0.565 | 0.982 |
| [0.90,0.95) | 39 | 0.955 | 0.613 | 0.966 |
| [0.95,1.00) | 46 | 0.967 | 0.504 | 1.000 |

learned loses (fixed top-1, learned not): 0; learned wins (learned top-1, fixed not): 118

## view c2: 300 molecules, truth in shortlist 216 (strict MRR over 300; GL fallback molecules -431)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.530 | 0.433 |
| pipeline | 0.528 | 0.430 |
| fixed | 0.425 | 0.323 |
| lib | 0.115 | 0.060 |
| guard0.6_0.1 | 0.519 | 0.417 |
| guard0.7_0.1 | 0.523 | 0.420 |
| guard0.8_0.1 | 0.526 | 0.427 |
| guard0.8_0.2 | 0.528 | 0.430 |
| guard0.9_0.2 | 0.530 | 0.433 |
| fguard0.6_0.1 | 0.415 | 0.307 |
| fguard0.7_0.1 | 0.420 | 0.313 |
| fguard0.8_0.1 | 0.423 | 0.320 |
| fguard0.8_0.2 | 0.424 | 0.320 |
| fguard0.9_0.2 | 0.425 | 0.323 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.543 | 0.450 |
| no_counts (lib_nref/in_train=0) | 0.530 | 0.433 |
| no_sim (lib_sim/same=0) | 0.543 | 0.450 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.382 | 0.263 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 216 | 0.735 | 0.591 | 0.160 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 216 | 0.735 | 0.591 | 0.160 |

learned loses (fixed top-1, learned not): 12; learned wins (learned top-1, fixed not): 45

lost molecules: learned top-1 has in_train 0.67 / lib_nref mean 5.9 / lib_sim mean 0.314 / pop mean 4.50; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 6.47

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -1.055 | -0.288 | 0.026 |
| lib_sim | -0.244 | 0.000 | 0.314 |
| lotus | -0.239 | 1.019 | 0.612 |
| lib_same | -0.087 | 0.000 | 0.309 |
| fp_rank_window | -0.081 | 3.327 | 3.326 |
| lsynonyms | -0.080 | 2.027 | 1.836 |
| ppm_err | -0.035 | 0.527 | 0.527 |
| lsid | -0.033 | 2.737 | 2.419 |
| gl | +0.110 | 0.408 | 0.370 |
| lpmid | +0.126 | 1.664 | 0.356 |
| z_ice | +0.205 | 2.039 | 1.813 |
| z_gl | +0.464 | 2.766 | 2.345 |

