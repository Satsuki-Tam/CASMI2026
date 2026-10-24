# learned-fusion probe: run1_v2/B_nplib/rank_v2 (w_ice 1.0; 28 features)

## view c1: 72 molecules, truth in shortlist 71 (strict MRR over 72; GL fallback molecules -141)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.917 | 0.889 |
| pipeline | 0.917 | 0.889 |
| fixed | 0.580 | 0.472 |
| lib | 0.912 | 0.889 |
| guard0.8 | 0.917 | 0.889 |
| guard0.9 | 0.917 | 0.889 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.664 | 0.542 |
| no_counts (lib_nref/in_train=0) | 0.874 | 0.806 |
| no_sim (lib_sim/same=0) | 0.738 | 0.653 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.933 | 0.917 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [1,5] | 13 | 0.962 | 0.378 | 0.821 | 1.00 |
| [6,20] | 50 | 0.930 | 0.678 | 0.960 | 1.00 |
| [21,100] | 8 | 0.875 | 0.367 | 0.875 | 1.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 12 | 0.756 | 0.558 | 0.660 |
| [0.60,0.80) | 6 | 1.000 | 0.441 | 1.000 |
| [0.80,0.90) | 20 | 0.933 | 0.660 | 0.963 |
| [0.90,0.95) | 13 | 1.000 | 0.635 | 0.962 |
| [0.95,1.00) | 20 | 0.963 | 0.547 | 1.000 |

learned loses (fixed top-1, learned not): 0; learned wins (learned top-1, fixed not): 30

## view c2: 300 molecules, truth in shortlist 159 (strict MRR over 300; GL fallback molecules -318)

| ranking | MRR (strict) | top-1 |
|---|---:|---:|
| learned | 0.430 | 0.393 |
| pipeline | 0.430 | 0.393 |
| fixed | 0.373 | 0.327 |
| lib | 0.119 | 0.063 |
| guard0.8 | 0.420 | 0.373 |
| guard0.9 | 0.423 | 0.380 |
| no_ref (lib_sim/same/nref/in_train=0) | 0.404 | 0.353 |
| no_counts (lib_nref/in_train=0) | 0.418 | 0.377 |
| no_sim (lib_sim/same=0) | 0.422 | 0.377 |
| no_prior (pop/lsid/lpmid/lsynonyms=0) | 0.303 | 0.220 |

| truth lib_nref bin | n | learned MRR | fixed MRR | lib-only MRR | truth in_train share |
|---|---:|---:|---:|---:|---:|
| [0,0] | 159 | 0.811 | 0.704 | 0.225 | 0.00 |

| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |
|---|---:|---:|---:|---:|
| [0.00,0.60) | 159 | 0.811 | 0.704 | 0.225 |

learned loses (fixed top-1, learned not): 7; learned wins (learned top-1, fixed not): 27

lost molecules: learned top-1 has in_train 0.57 / lib_nref mean 4.9 / lib_sim mean 0.222 / pop mean 3.50; truth has in_train 0.00 / lib_nref mean 0.0 / lib_sim mean 0.000 / pop mean 2.88

| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |
|---|---:|---:|---:|
| lib_margin | -1.331 | -0.151 | 0.070 |
| z_fp | -0.388 | 0.904 | 1.608 |
| fp_rank_window | -0.133 | 3.207 | 2.405 |
| fp | -0.104 | 10.345 | 19.304 |
| in_coconut | -0.087 | 0.000 | 0.143 |
| lib_nref | -0.078 | 0.000 | 4.857 |
| ce_known | -0.054 | 0.000 | 0.000 |
| np_bit | -0.038 | 0.000 | 0.143 |
| lsynonyms | +0.123 | 1.259 | 1.382 |
| ppm_err | +0.212 | 1.171 | 2.172 |
| z_ice | +0.563 | 3.448 | 2.670 |
| z_gl | +0.686 | 3.353 | 2.596 |

