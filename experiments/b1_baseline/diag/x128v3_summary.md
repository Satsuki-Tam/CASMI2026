# 128 v3 reading (fold 1): within-formula rerank of P (128_prereg_wf.md v2 + v3)

- coverage-free upper bound primary(wf_ub - main) = +0.1635 [+0.1298, +0.1993] -> not excluded by this bound
- coverage-aware bound gl: +0.0911 [+0.0681, +0.1163] (descriptive)
- coverage-aware bound mist: +0.0911 [+0.0681, +0.1163] (descriptive)

| variant | primary | block A | block D | old B f1dev C-F C2 | G C1 f1dev | NP C1 np053f1dev H/N | c1dev C1 pooled | c1dev positive-ion C1 | gate |
|---|---|---|---|---|---|---|---|---|---|
| wf_gl_0.5 | **-0.0202 [-0.0315, -0.0104]** | -0.0233 [-0.0346, -0.0133] | -0.0171 [-0.0375, -0.0013] | -0.0270 [-0.0399, -0.0151] | -0.0214 [-0.0497, +0.0020] | -0.0598 [-0.0991, -0.0250] | -0.0942 [-0.1158, -0.0736] (n 391) | -0.1116 [-0.1368, -0.0868] (n 330) | no |
| wf_gl_2.0 | **-0.0704 [-0.0961, -0.0457]** | -0.0720 [-0.0933, -0.0514] | -0.0689 [-0.1173, -0.0239] | -0.0670 [-0.0885, -0.0463] | -0.1642 [-0.2218, -0.1096] | -0.1560 [-0.2194, -0.0941] | -0.2742 [-0.3091, -0.2388] (n 391) | -0.3249 [-0.3646, -0.2865] (n 330) | no |
| wf_mist_0.5 | **-0.0207 [-0.0353, -0.0070]** | -0.0255 [-0.0387, -0.0130] | -0.0159 [-0.0417, +0.0079] | -0.0161 [-0.0277, -0.0051] | -0.1627 [-0.2178, -0.1105] | -0.0767 [-0.1211, -0.0321] | -0.1244 [-0.1473, -0.1015] (n 391) | -0.1473 [-0.1751, -0.1208] (n 330) | no |
| wf_mist_2.0 | **-0.0742 [-0.1000, -0.0495]** | -0.0786 [-0.1015, -0.0552] | -0.0697 [-0.1158, -0.0256] | -0.0914 [-0.1140, -0.0695] | -0.4075 [-0.4884, -0.3253] | -0.2009 [-0.2707, -0.1314] | -0.4275 [-0.4675, -0.3860] (n 391) | -0.5065 [-0.5497, -0.4636] (n 330) | no |

- **Selection (fold 1): none**

## Diagnostics (not used for the decision)

| tag | set | view | n | main | wf_ub | up / down (gl_0.5, gl_2.0, mist_0.5, mist_2.0) | movable truths (gl / mist) | reorderable groups (mean) | truth rank in the finite subset P / X (median, movable rows) |
|---|---|---|---:|---:|---:|---|---|---|---|
| f1dev | C_np_crosslib | c1 | 91 | 0.9353 | 0.9890 | gl_0.5: 1/24 ; gl_2.0: 0/49 ; mist_0.5: 5/21 ; mist_2.0: 5/64 | 86 / 87 | 7.60 / 7.33 | gl 1/3 (n 86, any-truth 86); mist 1/7 (n 87, any-truth 87) |
| f1dev | C_np_crosslib | c2 | 100 | 0.6388 | 0.8200 | gl_0.5: 8/24 ; gl_2.0: 10/41 ; mist_0.5: 9/20 ; mist_2.0: 8/52 | 80 / 81 | 7.93 / 7.64 | gl 1/3 (n 80, any-truth 80); mist 1/6 (n 81, any-truth 81) |
| f1dev | D_np_single | c2 | 100 | 0.2753 | 0.3558 | gl_0.5: 2/6 ; gl_2.0: 4/17 ; mist_0.5: 3/10 ; mist_2.0: 4/20 | 38 / 38 | 9.68 / 9.18 | gl 1/3 (n 38, any-truth 38); mist 1/4 (n 38, any-truth 38) |
| f1dev | E_np_negonly | c1 | 60 | 0.8312 | 0.9550 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.00 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| f1dev | E_np_negonly | c2 | 100 | 0.4559 | 0.8263 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.00 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| f1dev | F_np_uncovered | c1 | 43 | 0.8103 | 0.9767 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.00 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| f1dev | F_np_uncovered | c2 | 100 | 0.3023 | 0.6399 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.00 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| f1dev | G_tims_crosslib | c1 | 100 | 0.8801 | 0.9750 | gl_0.5: 1/7 ; gl_2.0: 2/33 ; mist_0.5: 2/36 ; mist_2.0: 3/60 | 90 / 90 | 5.31 / 5.31 | gl 1/1 (n 90, any-truth 90); mist 1/7 (n 90, any-truth 90) |
| f1dev | G_tims_crosslib | c2 | 100 | 0.7775 | 0.8950 | gl_0.5: 1/8 ; gl_2.0: 5/29 ; mist_0.5: 4/32 ; mist_2.0: 6/54 | 84 / 84 | 5.31 / 5.31 | gl 1/1 (n 84, any-truth 84); mist 1/7 (n 84, any-truth 84) |
| np053f1dev | NP_H | c1 | 36 | 0.7831 | 0.9815 | gl_0.5: 1/10 ; gl_2.0: 1/16 ; mist_0.5: 1/15 ; mist_2.0: 2/24 | 34 / 34 | 9.94 / 9.83 | gl 1/16 (n 34, any-truth 34); mist 1/8 (n 34, any-truth 34) |
| np053f1dev | NP_H | c2 | 200 | 0.5588 | 0.7623 | gl_0.5: 6/42 ; gl_2.0: 10/72 ; mist_0.5: 14/44 ; mist_2.0: 13/78 | 151 / 151 | 12.70 / 12.34 | gl 1/4 (n 151, any-truth 151); mist 1/4 (n 151, any-truth 151) |
| np053f1dev | NP_N | c1 | 15 | 0.8667 | 0.9467 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.00 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| np053f1dev | NP_N | c2 | 60 | 0.5567 | 0.8464 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.15 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| np053f1dev | NP_X | c1 | 1 | 1.0000 | 1.0000 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.00 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| np053f1dev | NP_X | c2 | 60 | 0.6605 | 1.0000 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.00 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| c1bankdev | C1_neg_few | c1 | 48 | 0.9253 | 1.0000 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.00 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| c1bankdev | C1_neg_few | c2 | 52 | 0.5019 | 0.8615 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.00 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| c1bankdev | C1_neg_many | c1 | 13 | 0.9231 | 0.9308 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.00 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| c1bankdev | C1_neg_many | c2 | 13 | 0.5641 | 0.6923 | gl_0.5: 0/0 ; gl_2.0: 0/0 ; mist_0.5: 0/0 ; mist_2.0: 0/0 | 0 / 0 | 0.00 / 0.00 | gl nan/nan (n 0, any-truth 0); mist nan/nan (n 0, any-truth 0) |
| c1bankdev | C1_pos_few | c1 | 329 | 0.9606 | 0.9970 | gl_0.5: 1/73 ; gl_2.0: 3/162 ; mist_0.5: 5/101 ; mist_2.0: 4/222 | 326 / 326 | 6.41 / 6.41 | gl 1/2 (n 326, any-truth 326); mist 1/8 (n 326, any-truth 326) |
| c1bankdev | C1_pos_few | c2 | 366 | 0.6169 | 0.7766 | gl_0.5: 14/61 ; gl_2.0: 19/121 ; mist_0.5: 24/80 ; mist_2.0: 23/174 | 284 / 284 | 6.84 / 6.82 | gl 1/2 (n 284, any-truth 284); mist 1/8 (n 284, any-truth 284) |
| c1bankdev | C1_pos_many | c1 | 1 | 0.3333 | 1.0000 | gl_0.5: 0/0 ; gl_2.0: 0/1 ; mist_0.5: 0/1 ; mist_2.0: 0/1 | 1 / 1 | 22.00 / 22.00 | gl 3/5 (n 1, any-truth 1); mist 3/8 (n 1, any-truth 1) |
| c1bankdev | C1_pos_many | c2 | 1 | 0.2500 | 1.0000 | gl_0.5: 0/0 ; gl_2.0: 0/1 ; mist_0.5: 0/1 ; mist_2.0: 0/1 | 1 / 1 | 22.00 / 22.00 | gl 3/5 (n 1, any-truth 1); mist 3/8 (n 1, any-truth 1) |
