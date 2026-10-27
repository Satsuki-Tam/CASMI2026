# 077 / 078 development, registered reading

| role | comparison | primary NP_H C2 (f1,f2) | blocks | panel C1 clean (state) | f1/f2 NP C2 C-F (state) | non-COCO C2 (f1/f2 C+D) | NP_H C2 GL&pos | G C1 / G C2 | dev2 NP C2 | NP_H C1 | NP_X/N max abs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 078 MAIN | rank_v8w_cmp - rank_v8w_pc | +0.0033 [-0.0051, +0.0119] | +0.0127 / -0.0061 | -0.0018 [-0.0135, +0.0105] (undetermined) | +0.0040 [-0.0002, +0.0086] (non-inferior) | +0.0043 [-0.0043, +0.0128] | +0.0043 [-0.0061, +0.0149] | +0.0187 [+0.0079, +0.0317] (non-inferior) / +0.0066 | +0.0048 [-0.0009, +0.0111] | -0.0228 | 0.0000 |
| 078 PUB | rank_v8w_cmp - rank_v4b | +0.0334 [+0.0191, +0.0481] | +0.0311 / +0.0358 | +0.0038 [-0.0151, +0.0232] (undetermined) | +0.0170 [+0.0092, +0.0247] (non-inferior) | +0.0174 [+0.0026, +0.0333] | +0.0415 [+0.0233, +0.0590] | +0.1086 [+0.0786, +0.1401] (non-inferior) / -0.0044 | +0.0028 [-0.0080, +0.0129] | -0.0056 | 0.0000 |
| 077 C1w same data | rank_v9b_w - rank_v9b | +0.0008 [-0.0040, +0.0064] | +0.0002 / +0.0015 | +0.0080 [-0.0021, +0.0201] (non-inferior) | +0.0007 [-0.0018, +0.0032] (non-inferior) | +0.0014 [-0.0064, +0.0087] | +0.0010 [-0.0053, +0.0079] | +0.0027 [-0.0047, +0.0117] (non-inferior) / -0.0023 | -0.0018 [-0.0050, +0.0005] | -0.0069 | 0.0000 |
| 077 COCO at matched C1 | rank_v9b_w - rank_v9a | +0.0172 [+0.0074, +0.0278] | +0.0198 / +0.0145 | -0.0032 [-0.0144, +0.0077] (undetermined) | -0.0024 [-0.0064, +0.0014] (non-inferior) | -0.0095 [-0.0201, +0.0001] | +0.0214 [+0.0096, +0.0353] | +0.0106 [-0.0017, +0.0248] (non-inferior) / -0.0014 | -0.0005 [-0.0044, +0.0036] | +0.0004 | 0.0000 |
| 077 PUB | rank_v9b_w - rank_v4b | +0.0424 [+0.0285, +0.0575] | +0.0387 / +0.0460 | +0.0115 [-0.0043, +0.0286] (non-inferior) | +0.0116 [+0.0050, +0.0184] (non-inferior) | +0.0059 [-0.0061, +0.0176] | +0.0526 [+0.0350, +0.0709] | +0.0929 [+0.0648, +0.1237] (non-inferior) / -0.0064 | +0.0021 [-0.0064, +0.0110] | +0.0137 | 0.0000 |
| ref v9b-v9a | rank_v9b - rank_v9a | +0.0163 [+0.0068, +0.0267] | +0.0196 / +0.0130 | -0.0112 [-0.0238, +0.0001] (undetermined) | -0.0031 [-0.0069, +0.0003] (non-inferior) | -0.0110 [-0.0202, -0.0032] | +0.0204 [+0.0080, +0.0334] | +0.0079 [-0.0046, +0.0221] (non-inferior) / +0.0009 | +0.0013 [-0.0032, +0.0063] | +0.0073 | 0.0000 |
| ref v8w-v4b | rank_v8w_pc - rank_v4b | +0.0301 [+0.0159, +0.0447] | +0.0184 / +0.0419 | +0.0056 [-0.0117, +0.0242] (undetermined) | +0.0130 [+0.0065, +0.0199] (non-inferior) | +0.0132 [+0.0002, +0.0259] | +0.0372 [+0.0199, +0.0556] | +0.0898 [+0.0624, +0.1207] (non-inferior) / -0.0110 | -0.0021 [-0.0126, +0.0080] | +0.0172 | 0.0000 |

## per layer (stress / detail)

| role | cmp | block | set | view | n | d | up | down |
|---|---|---|---|---|---|---|---|---|
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f1dev | C_np_crosslib | c1 | 91 | 0.006 | 2 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f1dev | C_np_crosslib | c2 | 100 | 0.0162 | 11 | 3 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f1dev | D_np_single | c2 | 100 | 0.0153 | 6 | 3 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f1dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f1dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f1dev | F_np_uncovered | c1 | 43 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f1dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f1dev | G_tims_crosslib | c1 | 100 | 0.015 | 5 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f1dev | G_tims_crosslib | c2 | 100 | 0.0061 | 3 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f2dev | C_np_crosslib | c1 | 96 | -0.0023 | 1 | 1 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f2dev | C_np_crosslib | c2 | 100 | 0.0046 | 5 | 5 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f2dev | D_np_single | c1 | 1 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f2dev | D_np_single | c2 | 100 | -0.004 | 4 | 2 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f2dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f2dev | G_tims_crosslib | c1 | 100 | 0.0225 | 7 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | f2dev | G_tims_crosslib | c2 | 100 | 0.0072 | 4 | 3 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f1dev | NP_H | c1 | 36 | -0.0302 | 0 | 5 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f1dev | NP_H | c2 | 200 | 0.0127 | 16 | 10 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f1dev | NP_N | c1 | 15 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f1dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f1dev | NP_X | c1 | 1 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f1dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f2dev | NP_H | c1 | 40 | -0.0154 | 2 | 2 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f2dev | NP_H | c2 | 200 | -0.0061 | 14 | 9 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f2dev | NP_N | c1 | 22 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f2dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f2dev | NP_X | c1 | 7 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | np053f2dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | p2dev | C_np_crosslib | c1 | 95 | 0.0035 | 1 | 2 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | p2dev | C_np_crosslib | c2 | 100 | 0.0144 | 9 | 4 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | p2dev | D_np_single | c2 | 100 | 0.0049 | 4 | 2 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | p2dev | E_np_negonly | c1 | 59 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | p2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | p2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | p2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | p2dev | G_tims_crosslib | c1 | 100 | 0.045 | 9 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | p2dev | G_tims_crosslib | c2 | 100 | 0.0067 | 3 | 0 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | panel | P_np250 | c1 | 250 | 0.0006 | 4 | 8 |
| 078 MAIN | rank_v8w_cmp-rank_v8w_pc | panel | P_np250 | c2 | 250 | 0.0075 | 8 | 2 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f1dev | C_np_crosslib | c1 | 91 | 0.012 | 4 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f1dev | C_np_crosslib | c2 | 100 | 0.0506 | 21 | 3 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f1dev | D_np_single | c2 | 100 | 0.0312 | 10 | 4 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f1dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f1dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f1dev | F_np_uncovered | c1 | 43 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f1dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f1dev | G_tims_crosslib | c1 | 100 | 0.0912 | 19 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f1dev | G_tims_crosslib | c2 | 100 | -0.0027 | 9 | 6 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f2dev | C_np_crosslib | c1 | 96 | -0.0095 | 1 | 1 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f2dev | C_np_crosslib | c2 | 100 | 0.0461 | 18 | 8 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f2dev | D_np_single | c1 | 1 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f2dev | D_np_single | c2 | 100 | 0.0078 | 6 | 4 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f2dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f2dev | G_tims_crosslib | c1 | 100 | 0.1259 | 24 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | f2dev | G_tims_crosslib | c2 | 100 | -0.0061 | 8 | 11 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f1dev | NP_H | c1 | 36 | -0.0279 | 2 | 7 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f1dev | NP_H | c2 | 200 | 0.0311 | 37 | 14 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f1dev | NP_N | c1 | 15 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f1dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f1dev | NP_X | c1 | 1 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f1dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f2dev | NP_H | c1 | 40 | 0.0167 | 2 | 1 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f2dev | NP_H | c2 | 200 | 0.0358 | 37 | 7 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f2dev | NP_N | c1 | 22 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f2dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f2dev | NP_X | c1 | 7 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | np053f2dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | p2dev | C_np_crosslib | c1 | 95 | -0.0056 | 2 | 4 |
| 078 PUB | rank_v8w_cmp-rank_v4b | p2dev | C_np_crosslib | c2 | 100 | 0.0039 | 13 | 7 |
| 078 PUB | rank_v8w_cmp-rank_v4b | p2dev | D_np_single | c2 | 100 | 0.0072 | 5 | 5 |
| 078 PUB | rank_v8w_cmp-rank_v4b | p2dev | E_np_negonly | c1 | 59 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | p2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | p2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | p2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 078 PUB | rank_v8w_cmp-rank_v4b | p2dev | G_tims_crosslib | c1 | 100 | 0.1324 | 28 | 1 |
| 078 PUB | rank_v8w_cmp-rank_v4b | p2dev | G_tims_crosslib | c2 | 100 | -0.0316 | 15 | 13 |
| 078 PUB | rank_v8w_cmp-rank_v4b | panel | P_np250 | c1 | 250 | 0.0051 | 10 | 10 |
| 078 PUB | rank_v8w_cmp-rank_v4b | panel | P_np250 | c2 | 250 | 0.0135 | 12 | 4 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f1dev | C_np_crosslib | c1 | 91 | 0.0 | 1 | 1 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f1dev | C_np_crosslib | c2 | 100 | -0.0074 | 7 | 8 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f1dev | D_np_single | c2 | 100 | 0.0008 | 2 | 3 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f1dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f1dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f1dev | F_np_uncovered | c1 | 43 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f1dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f1dev | G_tims_crosslib | c1 | 100 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f1dev | G_tims_crosslib | c2 | 100 | 0.0002 | 1 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f2dev | C_np_crosslib | c1 | 96 | 0.0057 | 4 | 1 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f2dev | C_np_crosslib | c2 | 100 | 0.0115 | 4 | 3 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f2dev | D_np_single | c1 | 1 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f2dev | D_np_single | c2 | 100 | 0.0005 | 2 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f2dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f2dev | G_tims_crosslib | c1 | 100 | 0.0053 | 3 | 3 |
| 077 C1w same data | rank_v9b_w-rank_v9b | f2dev | G_tims_crosslib | c2 | 100 | -0.0048 | 1 | 1 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f1dev | NP_H | c1 | 36 | -0.0139 | 0 | 1 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f1dev | NP_H | c2 | 200 | 0.0002 | 9 | 10 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f1dev | NP_N | c1 | 15 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f1dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f1dev | NP_X | c1 | 1 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f1dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f2dev | NP_H | c1 | 40 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f2dev | NP_H | c2 | 200 | 0.0015 | 7 | 7 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f2dev | NP_N | c1 | 22 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f2dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f2dev | NP_X | c1 | 7 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | np053f2dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | p2dev | C_np_crosslib | c1 | 95 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | p2dev | C_np_crosslib | c2 | 100 | -0.0059 | 1 | 8 |
| 077 C1w same data | rank_v9b_w-rank_v9b | p2dev | D_np_single | c2 | 100 | -0.0013 | 3 | 2 |
| 077 C1w same data | rank_v9b_w-rank_v9b | p2dev | E_np_negonly | c1 | 59 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | p2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | p2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | p2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 077 C1w same data | rank_v9b_w-rank_v9b | p2dev | G_tims_crosslib | c1 | 100 | 0.0008 | 1 | 1 |
| 077 C1w same data | rank_v9b_w-rank_v9b | p2dev | G_tims_crosslib | c2 | 100 | -0.0141 | 1 | 4 |
| 077 C1w same data | rank_v9b_w-rank_v9b | panel | P_np250 | c1 | 250 | 0.0065 | 6 | 2 |
| 077 C1w same data | rank_v9b_w-rank_v9b | panel | P_np250 | c2 | 250 | -0.0013 | 3 | 3 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f1dev | C_np_crosslib | c1 | 91 | -0.0055 | 1 | 2 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f1dev | C_np_crosslib | c2 | 100 | -0.008 | 5 | 9 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f1dev | D_np_single | c2 | 100 | -0.0003 | 4 | 2 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f1dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f1dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f1dev | F_np_uncovered | c1 | 43 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f1dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f1dev | G_tims_crosslib | c1 | 100 | 0.0117 | 2 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f1dev | G_tims_crosslib | c2 | 100 | 0.0003 | 1 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f2dev | C_np_crosslib | c1 | 96 | -0.0057 | 0 | 2 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f2dev | C_np_crosslib | c2 | 100 | -0.0106 | 8 | 12 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f2dev | D_np_single | c1 | 1 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f2dev | D_np_single | c2 | 100 | -0.0002 | 3 | 3 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f2dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f2dev | G_tims_crosslib | c1 | 100 | 0.0095 | 6 | 5 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | f2dev | G_tims_crosslib | c2 | 100 | -0.0031 | 3 | 1 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f1dev | NP_H | c1 | 36 | 0.0029 | 3 | 2 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f1dev | NP_H | c2 | 200 | 0.0198 | 25 | 8 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f1dev | NP_N | c1 | 15 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f1dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f1dev | NP_X | c1 | 1 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f1dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f2dev | NP_H | c1 | 40 | -0.0021 | 0 | 1 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f2dev | NP_H | c2 | 200 | 0.0145 | 19 | 6 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f2dev | NP_N | c1 | 22 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f2dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f2dev | NP_X | c1 | 7 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | np053f2dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | p2dev | C_np_crosslib | c1 | 95 | -0.0091 | 1 | 2 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | p2dev | C_np_crosslib | c2 | 100 | -0.0021 | 3 | 8 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | p2dev | D_np_single | c2 | 100 | 0.0001 | 5 | 4 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | p2dev | E_np_negonly | c1 | 59 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | p2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | p2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | p2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | p2dev | G_tims_crosslib | c1 | 100 | -0.0192 | 1 | 5 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | p2dev | G_tims_crosslib | c2 | 100 | -0.0223 | 2 | 8 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | panel | P_np250 | c1 | 250 | -0.0026 | 3 | 5 |
| 077 COCO at matched C1 | rank_v9b_w-rank_v9a | panel | P_np250 | c2 | 250 | 0.0053 | 8 | 2 |
| 077 PUB | rank_v9b_w-rank_v4b | f1dev | C_np_crosslib | c1 | 91 | 0.0065 | 4 | 2 |
| 077 PUB | rank_v9b_w-rank_v4b | f1dev | C_np_crosslib | c2 | 100 | 0.0264 | 16 | 5 |
| 077 PUB | rank_v9b_w-rank_v4b | f1dev | D_np_single | c2 | 100 | 0.0182 | 11 | 1 |
| 077 PUB | rank_v9b_w-rank_v4b | f1dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | f1dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | f1dev | F_np_uncovered | c1 | 43 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | f1dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | f1dev | G_tims_crosslib | c1 | 100 | 0.0812 | 17 | 1 |
| 077 PUB | rank_v9b_w-rank_v4b | f1dev | G_tims_crosslib | c2 | 100 | 0.0062 | 10 | 5 |
| 077 PUB | rank_v9b_w-rank_v4b | f2dev | C_np_crosslib | c1 | 96 | -0.0134 | 1 | 2 |
| 077 PUB | rank_v9b_w-rank_v4b | f2dev | C_np_crosslib | c2 | 100 | 0.041 | 19 | 7 |
| 077 PUB | rank_v9b_w-rank_v4b | f2dev | D_np_single | c1 | 1 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | f2dev | D_np_single | c2 | 100 | 0.0074 | 6 | 5 |
| 077 PUB | rank_v9b_w-rank_v4b | f2dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | f2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | f2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | f2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | f2dev | G_tims_crosslib | c1 | 100 | 0.1046 | 23 | 3 |
| 077 PUB | rank_v9b_w-rank_v4b | f2dev | G_tims_crosslib | c2 | 100 | -0.0189 | 6 | 11 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f1dev | NP_H | c1 | 36 | 0.01 | 3 | 4 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f1dev | NP_H | c2 | 200 | 0.0387 | 42 | 11 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f1dev | NP_N | c1 | 15 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f1dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f1dev | NP_X | c1 | 1 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f1dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f2dev | NP_H | c1 | 40 | 0.0175 | 2 | 2 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f2dev | NP_H | c2 | 200 | 0.046 | 38 | 8 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f2dev | NP_N | c1 | 22 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f2dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f2dev | NP_X | c1 | 7 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | np053f2dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | p2dev | C_np_crosslib | c1 | 95 | -0.0074 | 2 | 5 |
| 077 PUB | rank_v9b_w-rank_v4b | p2dev | C_np_crosslib | c2 | 100 | 0.0056 | 11 | 6 |
| 077 PUB | rank_v9b_w-rank_v4b | p2dev | D_np_single | c2 | 100 | 0.003 | 8 | 7 |
| 077 PUB | rank_v9b_w-rank_v4b | p2dev | E_np_negonly | c1 | 59 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | p2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | p2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | p2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| 077 PUB | rank_v9b_w-rank_v4b | p2dev | G_tims_crosslib | c1 | 100 | 0.1066 | 26 | 2 |
| 077 PUB | rank_v9b_w-rank_v4b | p2dev | G_tims_crosslib | c2 | 100 | -0.0417 | 13 | 13 |
| 077 PUB | rank_v9b_w-rank_v4b | panel | P_np250 | c1 | 250 | 0.0093 | 11 | 6 |
| 077 PUB | rank_v9b_w-rank_v4b | panel | P_np250 | c2 | 250 | 0.0128 | 11 | 2 |
| ref v9b-v9a | rank_v9b-rank_v9a | f1dev | C_np_crosslib | c1 | 91 | -0.0055 | 0 | 1 |
| ref v9b-v9a | rank_v9b-rank_v9a | f1dev | C_np_crosslib | c2 | 100 | -0.0006 | 4 | 7 |
| ref v9b-v9a | rank_v9b-rank_v9a | f1dev | D_np_single | c2 | 100 | -0.0011 | 5 | 2 |
| ref v9b-v9a | rank_v9b-rank_v9a | f1dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | f1dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | f1dev | F_np_uncovered | c1 | 43 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | f1dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | f1dev | G_tims_crosslib | c1 | 100 | 0.0117 | 2 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | f1dev | G_tims_crosslib | c2 | 100 | 0.0002 | 1 | 1 |
| ref v9b-v9a | rank_v9b-rank_v9a | f2dev | C_np_crosslib | c1 | 96 | -0.0115 | 0 | 4 |
| ref v9b-v9a | rank_v9b-rank_v9a | f2dev | C_np_crosslib | c2 | 100 | -0.0221 | 7 | 11 |
| ref v9b-v9a | rank_v9b-rank_v9a | f2dev | D_np_single | c1 | 1 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | f2dev | D_np_single | c2 | 100 | -0.0008 | 3 | 3 |
| ref v9b-v9a | rank_v9b-rank_v9a | f2dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | f2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | f2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | f2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | f2dev | G_tims_crosslib | c1 | 100 | 0.0042 | 6 | 5 |
| ref v9b-v9a | rank_v9b-rank_v9a | f2dev | G_tims_crosslib | c2 | 100 | 0.0017 | 3 | 1 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f1dev | NP_H | c1 | 36 | 0.0168 | 3 | 2 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f1dev | NP_H | c2 | 200 | 0.0196 | 27 | 10 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f1dev | NP_N | c1 | 15 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f1dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f1dev | NP_X | c1 | 1 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f1dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f2dev | NP_H | c1 | 40 | -0.0021 | 0 | 1 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f2dev | NP_H | c2 | 200 | 0.013 | 19 | 5 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f2dev | NP_N | c1 | 22 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f2dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f2dev | NP_X | c1 | 7 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | np053f2dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | p2dev | C_np_crosslib | c1 | 95 | -0.0091 | 1 | 2 |
| ref v9b-v9a | rank_v9b-rank_v9a | p2dev | C_np_crosslib | c2 | 100 | 0.0039 | 4 | 4 |
| ref v9b-v9a | rank_v9b-rank_v9a | p2dev | D_np_single | c2 | 100 | 0.0015 | 5 | 5 |
| ref v9b-v9a | rank_v9b-rank_v9a | p2dev | E_np_negonly | c1 | 59 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | p2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | p2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | p2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| ref v9b-v9a | rank_v9b-rank_v9a | p2dev | G_tims_crosslib | c1 | 100 | -0.02 | 0 | 4 |
| ref v9b-v9a | rank_v9b-rank_v9a | p2dev | G_tims_crosslib | c2 | 100 | -0.0082 | 3 | 6 |
| ref v9b-v9a | rank_v9b-rank_v9a | panel | P_np250 | c1 | 250 | -0.0091 | 3 | 8 |
| ref v9b-v9a | rank_v9b-rank_v9a | panel | P_np250 | c2 | 250 | 0.0065 | 7 | 2 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f1dev | C_np_crosslib | c1 | 91 | 0.0059 | 3 | 1 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f1dev | C_np_crosslib | c2 | 100 | 0.0345 | 16 | 7 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f1dev | D_np_single | c2 | 100 | 0.0159 | 11 | 4 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f1dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f1dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f1dev | F_np_uncovered | c1 | 43 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f1dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f1dev | G_tims_crosslib | c1 | 100 | 0.0762 | 17 | 1 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f1dev | G_tims_crosslib | c2 | 100 | -0.0088 | 8 | 6 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f2dev | C_np_crosslib | c1 | 96 | -0.0071 | 1 | 2 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f2dev | C_np_crosslib | c2 | 100 | 0.0415 | 16 | 7 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f2dev | D_np_single | c1 | 1 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f2dev | D_np_single | c2 | 100 | 0.0118 | 6 | 5 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f2dev | E_np_negonly | c1 | 60 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f2dev | G_tims_crosslib | c1 | 100 | 0.1034 | 21 | 2 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | f2dev | G_tims_crosslib | c2 | 100 | -0.0132 | 8 | 13 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f1dev | NP_H | c1 | 36 | 0.0023 | 3 | 5 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f1dev | NP_H | c2 | 200 | 0.0184 | 33 | 16 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f1dev | NP_N | c1 | 15 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f1dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f1dev | NP_X | c1 | 1 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f1dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f2dev | NP_H | c1 | 40 | 0.0321 | 3 | 2 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f2dev | NP_H | c2 | 200 | 0.0419 | 35 | 7 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f2dev | NP_N | c1 | 22 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f2dev | NP_N | c2 | 60 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f2dev | NP_X | c1 | 7 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | np053f2dev | NP_X | c2 | 60 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | p2dev | C_np_crosslib | c1 | 95 | -0.0091 | 1 | 4 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | p2dev | C_np_crosslib | c2 | 100 | -0.0105 | 11 | 10 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | p2dev | D_np_single | c2 | 100 | 0.0022 | 4 | 7 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | p2dev | E_np_negonly | c1 | 59 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | p2dev | E_np_negonly | c2 | 100 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | p2dev | F_np_uncovered | c1 | 38 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | p2dev | F_np_uncovered | c2 | 100 | 0.0 | 0 | 0 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | p2dev | G_tims_crosslib | c1 | 100 | 0.0874 | 24 | 3 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | p2dev | G_tims_crosslib | c2 | 100 | -0.0383 | 14 | 14 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | panel | P_np250 | c1 | 250 | 0.0045 | 10 | 6 |
| ref v8w-v4b | rank_v8w_pc-rank_v4b | panel | P_np250 | c2 | 250 | 0.006 | 11 | 5 |
