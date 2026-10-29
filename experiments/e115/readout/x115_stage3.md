# 115 stage 3: v8w7a main on P0 / R / A tables (fold 1)

- GLACIER: shared (molecule, SMILES) values checked across the three arms: 347081

## Reproduction of the existing main by P0 (P0 - existing)

| cell | rows | rows differing | signed mean | mean abs | max abs |
|---|---:|---:|---:|---:|---:|
| f1dev C_np_crosslib c1 | 91 | 0 | +0.00000 | 0.00000 | 0.0000 |
| f1dev C_np_crosslib c2 | 100 | 0 | +0.00000 | 0.00000 | 0.0000 |
| f1dev D_np_single c2 | 100 | 0 | +0.00000 | 0.00000 | 0.0000 |
| f1dev E_np_negonly c1 | 60 | 0 | +0.00000 | 0.00000 | 0.0000 |
| f1dev E_np_negonly c2 | 100 | 0 | +0.00000 | 0.00000 | 0.0000 |
| f1dev F_np_uncovered c1 | 43 | 0 | +0.00000 | 0.00000 | 0.0000 |
| f1dev F_np_uncovered c2 | 100 | 0 | +0.00000 | 0.00000 | 0.0000 |
| f1dev G_tims_crosslib c1 | 100 | 0 | +0.00000 | 0.00000 | 0.0000 |
| f1dev G_tims_crosslib c2 | 100 | 0 | +0.00000 | 0.00000 | 0.0000 |
| np053f1dev NP_H c1 | 36 | 0 | +0.00000 | 0.00000 | 0.0000 |
| np053f1dev NP_H c2 | 200 | 0 | +0.00000 | 0.00000 | 0.0000 |
| np053f1dev NP_N c1 | 15 | 0 | +0.00000 | 0.00000 | 0.0000 |
| np053f1dev NP_N c2 | 60 | 0 | +0.00000 | 0.00000 | 0.0000 |
| np053f1dev NP_X c1 | 1 | 0 | +0.00000 | 0.00000 | 0.0000 |
| np053f1dev NP_X c2 | 60 | 0 | +0.00000 | 0.00000 | 0.0000 |
| c1bankdev C1_neg_few c1 | 48 | 0 | +0.00000 | 0.00000 | 0.0000 |
| c1bankdev C1_neg_few c2 | 52 | 0 | +0.00000 | 0.00000 | 0.0000 |
| c1bankdev C1_neg_many c1 | 13 | 0 | +0.00000 | 0.00000 | 0.0000 |
| c1bankdev C1_neg_many c2 | 13 | 0 | +0.00000 | 0.00000 | 0.0000 |
| c1bankdev C1_pos_few c1 | 329 | 0 | +0.00000 | 0.00000 | 0.0000 |
| c1bankdev C1_pos_few c2 | 366 | 0 | +0.00000 | 0.00000 | 0.0000 |
| c1bankdev C1_pos_many c1 | 1 | 0 | +0.00000 | 0.00000 | 0.0000 |
| c1bankdev C1_pos_many c2 | 1 | 0 | +0.00000 | 0.00000 | 0.0000 |

## Decision (both comparisons must pass)

| comparison | primary | block A | block D | old B f1dev C-F C2 | G C1 f1dev | NP C1 np053f1dev H/N | C1 bank c1dev pooled | pass |
|---|---|---|---|---|---|---|---|---|
| A - R | **-0.0070 [-0.0177, +0.0027]** | -0.0051 [-0.0167, +0.0039] | -0.0090 [-0.0274, +0.0081] | -0.0049 [-0.0140, +0.0042] | -0.0313 [-0.0583, -0.0083] | -0.0095 [-0.0251, -0.0001] | +0.0013 [-0.0033, +0.0060] | no |
| A - P0 | **-0.0025 [-0.0126, +0.0072]** | -0.0011 [-0.0145, +0.0111] | -0.0040 [-0.0196, +0.0110] | -0.0074 [-0.0168, +0.0013] | -0.0317 [-0.0617, -0.0050] | -0.0003 [-0.0018, +0.0009] | -0.0012 [-0.0082, +0.0057] | no |

**Gate: NO**

## Diagnostics (row means; not used for the decision)

| cell | n | main P0 | main R | main A | A - R rescued / lost | A - P0 rescued / lost |
|---|---:|---:|---:|---:|---|---|
| f1dev C_np_crosslib c1 | 91 | 0.9353 | 0.9418 | 0.9331 | 0 / 3 | 1 / 4 |
| f1dev C_np_crosslib c2 | 100 | 0.6388 | 0.6290 | 0.6210 | 8 / 8 | 9 / 7 |
| f1dev D_np_single c2 | 100 | 0.2753 | 0.2803 | 0.2714 | 1 / 6 | 2 / 5 |
| f1dev E_np_negonly c1 | 60 | 0.8312 | 0.8382 | 0.8388 | 2 / 1 | 3 / 2 |
| f1dev E_np_negonly c2 | 100 | 0.4559 | 0.4485 | 0.4515 | 9 / 6 | 9 / 6 |
| f1dev F_np_uncovered c1 | 43 | 0.8103 | 0.8111 | 0.8227 | 1 / 0 | 2 / 0 |
| f1dev F_np_uncovered c2 | 100 | 0.3023 | 0.3046 | 0.2991 | 4 / 11 | 6 / 11 |
| f1dev G_tims_crosslib c1 | 100 | 0.8801 | 0.8798 | 0.8484 | 1 / 7 | 1 / 7 |
| f1dev G_tims_crosslib c2 | 100 | 0.7775 | 0.7746 | 0.7610 | 2 / 7 | 3 / 7 |
| np053f1dev NP_H c1 | 36 | 0.7831 | 0.7988 | 0.7825 | 0 / 3 | 1 / 2 |
| np053f1dev NP_H c2 | 200 | 0.5588 | 0.5569 | 0.5566 | 10 / 19 | 9 / 20 |
| np053f1dev NP_N c1 | 15 | 0.8667 | 0.8694 | 0.8667 | 0 / 1 | 0 / 0 |
| np053f1dev NP_N c2 | 60 | 0.5567 | 0.5667 | 0.5566 | 2 / 5 | 2 / 2 |
| np053f1dev NP_X c1 | 1 | 1.0000 | 1.0000 | 1.0000 | 0 / 0 | 0 / 0 |
| np053f1dev NP_X c2 | 60 | 0.6605 | 0.6426 | 0.6604 | 8 / 4 | 7 / 6 |
| c1bankdev C1_neg_few c1 | 48 | 0.9253 | 0.9253 | 0.9219 | 0 / 1 | 0 / 1 |
| c1bankdev C1_neg_few c2 | 52 | 0.5019 | 0.4920 | 0.5032 | 5 / 2 | 5 / 4 |
| c1bankdev C1_neg_many c1 | 13 | 0.9231 | 0.9231 | 0.9231 | 0 / 0 | 0 / 0 |
| c1bankdev C1_neg_many c2 | 13 | 0.5641 | 0.5641 | 0.5641 | 0 / 0 | 0 / 0 |
| c1bankdev C1_pos_few c1 | 329 | 0.9606 | 0.9576 | 0.9597 | 6 / 3 | 6 / 7 |
| c1bankdev C1_pos_few c2 | 366 | 0.6169 | 0.6033 | 0.6174 | 41 / 24 | 28 / 29 |
| c1bankdev C1_pos_many c1 | 1 | 0.3333 | 0.3333 | 0.3333 | 0 / 0 | 0 / 0 |
| c1bankdev C1_pos_many c2 | 1 | 0.2500 | 0.1667 | 0.1429 | 0 / 1 | 0 / 1 |
