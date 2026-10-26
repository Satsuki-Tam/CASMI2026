## on the v7a combination (base column anag0_1, model rank_v7a)

| variant | 11-layer objective (vs v7a combo) | min C2 layer | panel C1 clean | C C1 | G C1 | passes |
|---|---:|---:|---:|---:|---:|---|
| v7f_0.25 | +0.0048 | +0.0002 | -0.0007 | +0.0001 | +0.0000 | False |
| v7f_0.5 | +0.0040 | -0.0131 | -0.0027 | +0.0006 | -0.0063 | False |
| v7f_1 | +0.0039 | -0.0164 | -0.0038 | +0.0010 | -0.0163 | False |
| v7ffb_0.25 | +0.0036 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | False |
| v7ffb_0.5 | +0.0044 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | False |
| v7ffb_1 | +0.0073 | -0.0004 | +0.0000 | +0.0000 | +0.0000 | True |

## on the working baseline (model rank_v4b): frg_w vs FE main

| variant | 11-layer objective (vs FE) | min C2 layer | panel C1 clean | C C1 | G C1 |
|---|---:|---:|---:|---:|---:|
| frg_0.25 | +0.0088 | -0.0006 | -0.0000 | +0.0080 | +0.0028 |
| frg_0.5 | +0.0105 | -0.0115 | +0.0006 | +0.0119 | +0.0123 |
| frg_1 | +0.0117 | -0.0194 | -0.0015 | +0.0119 | +0.0121 |
| anaw0.5 | +0.0408 | -0.0166 | +0.0224 | +0.0769 | +0.1761 |

per-layer deltas (v7f_0.5 and v7ffb_0.5 vs v7a combo):
v7f_0.5 fe dev2 C C2 -0.013 | fe dev2 D C2 +0.001 | fe dev2 E C2 +0.015 | fe dev2 F C2 +0.001 | fe dev2 G C2 +0.001 | f0 dev2 C C2 +0.002 | f0 dev2 D C2 +0.003 | f0 dev2 E C2 +0.021 | f0 dev2 F C2 +0.006 | f0 dev2 G C2 +0.004 | f0 panel C2 clean +0.003
v7ffb_0.5 fe dev2 C C2 +0.000 | fe dev2 D C2 +0.000 | fe dev2 E C2 +0.015 | fe dev2 F C2 +0.001 | fe dev2 G C2 +0.001 | f0 dev2 C C2 +0.000 | f0 dev2 D C2 +0.000 | f0 dev2 E C2 +0.021 | f0 dev2 F C2 +0.006 | f0 dev2 G C2 +0.004 | f0 panel C2 clean +0.000
