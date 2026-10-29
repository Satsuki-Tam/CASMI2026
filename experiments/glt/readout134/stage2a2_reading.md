# 134 stage 2 reading (v2): GLACIER A2 (inten_encoder / inten_decoder / output_map, end-to-end intensity loss, timsTOF) - C0' (released), GL-only, view c2, full rosters

- **primary f1G rr_form: +0.0437 [-0.0132, +0.1023] (n 100)**

| cost / description | A2 - C0' | 95% | n |
|---|---:|---|---:|
| rr_form npH | -0.0205 | [-0.0478, +0.0049] | 200 |
| rr_form f1D | +0.0030 | [-0.0207, +0.0264] | 100 |
| rr_gl f1G | +0.0498 | [-0.0097, +0.1101] | 100 |
| rr_gl npH | -0.0183 | [-0.0464, +0.0088] | 200 |
| rr_gl f1D | +0.0083 | [-0.0165, +0.0336] | 100 |
| rr_gl panel | -0.0090 | [-0.0397, +0.0226] | 250 |
| rr_form panel | -0.0117 | [-0.0424, +0.0192] | 250 |

- **Gate: NO**

## per-cell tables (gl_only_eval.py v2)

# GL-only A vs B: run_f1dev G_tims_crosslib (c2), A = gl_f1G_c0prime.json, B = gl_f1G_A2.json

| view | n | metric | A | B | B - A [95%] |
|---|---:|---|---:|---:|---|
| c2 | 100 | rr_gl | 0.5787 | 0.6285 | +0.0498 [-0.0111, +0.1138] |
| c2 | 100 | rr_form | 0.5855 | 0.6292 | +0.0437 [-0.0144, +0.1035] |
| c2 | 100 | top1_form | 0.4800 | 0.5300 | +0.0500 [-0.0300, +0.1400] |
| c2 | 84 | margin_form | 0.0281 | 0.0409 | +0.0128 [+0.0045, +0.0215] |
| c2 | 100 | roster: empty 0, truth absent 10, truth covered A / B 84 / 84, >= 2 same-formula competitors 90, singletons 0, decoy GL coverage A / B 0.933 / 0.933 | | | |


# GL-only A vs B: run_np053_f1dev NP_H (c2), A = gl_npH_c0prime.json, B = gl_npH_A2.json

| view | n | metric | A | B | B - A [95%] |
|---|---:|---|---:|---:|---|
| c2 | 200 | rr_gl | 0.3199 | 0.3016 | -0.0183 [-0.0451, +0.0085] |
| c2 | 200 | rr_form | 0.3598 | 0.3393 | -0.0205 [-0.0463, +0.0047] |
| c2 | 200 | top1_form | 0.2850 | 0.2550 | -0.0300 [-0.0700, +0.0100] |
| c2 | 151 | margin_form | -0.0226 | -0.0202 | +0.0024 [-0.0030, +0.0076] |
| c2 | 200 | roster: empty 1, truth absent 41, truth covered A / B 158 / 158, >= 2 same-formula competitors 150, singletons 7, decoy GL coverage A / B 1.000 / 1.000 | | | |


# GL-only A vs B: run_f1dev D_np_single (c2), A = gl_f1D_c0prime.json, B = gl_f1D_A2.json

| view | n | metric | A | B | B - A [95%] |
|---|---:|---|---:|---:|---|
| c2 | 100 | rr_gl | 0.1564 | 0.1647 | +0.0083 [-0.0156, +0.0342] |
| c2 | 100 | rr_form | 0.1776 | 0.1807 | +0.0030 [-0.0194, +0.0276] |
| c2 | 100 | top1_form | 0.1200 | 0.1100 | -0.0100 [-0.0400, +0.0200] |
| c2 | 38 | margin_form | -0.0029 | -0.0085 | -0.0056 [-0.0131, +0.0018] |
| c2 | 100 | roster: empty 1, truth absent 61, truth covered A / B 38 / 38, >= 2 same-formula competitors 37, singletons 0, decoy GL coverage A / B 1.000 / 1.000 | | | |


# GL-only A vs B: run_panel_fe P_np250 (c2), A = gl_panel_c0prime.json, B = gl_panel_A2.json

| view | n | metric | A | B | B - A [95%] |
|---|---:|---|---:|---:|---|
| c2 | 250 | rr_gl | 0.4223 | 0.4133 | -0.0090 [-0.0406, +0.0228] |
| c2 | 250 | rr_form | 0.4290 | 0.4172 | -0.0117 [-0.0433, +0.0188] |
| c2 | 250 | top1_form | 0.2800 | 0.2760 | -0.0040 [-0.0560, +0.0440] |
| c2 | 216 | margin_form | -0.0261 | -0.0275 | -0.0015 [-0.0059, +0.0027] |
| c2 | 250 | roster: empty 0, truth absent 0, truth covered A / B 216 / 216, >= 2 same-formula competitors 250, singletons 0, decoy GL coverage A / B 0.864 / 0.864 | | | |

