# 035 addendum (10:50 JST, after the request was queued; for Q1 and the implementation check)

## Q1 sensitivity: analogs from the query's own library removed in the C2 view (same-depositor siblings), anaw0.5 − main
| table | layer | n | C2 standard | C2 without same-library analogs |
|---|---|---:|---|---|
| fresh (fold-0) | C C2 | 21 | +0.090 [−0.030, +0.208] | +0.098 [−0.012, +0.215] |
| fresh (fold-0) | D C2 | 80 | +0.014 [−0.009, +0.041] | **−0.013 [−0.036, −0.000]** |
| fresh (fold-0) | E C2 | 100 | +0.103 [+0.050, +0.157] | +0.106 [+0.056, +0.159] |
| fresh (fold-0) | F C2 | 63 | +0.047 [−0.023, +0.119] | +0.028 [−0.036, +0.089] |
| fresh (fold-0) | G C2 | 72 | +0.038 [−0.007, +0.092] | +0.037 [−0.005, +0.089] |
| fresh (fold-0) | all C2 | 336 | **+0.057 [+0.032, +0.082]** | **+0.048 [+0.024, +0.072]** |
| dev2 (full_eval) | all C2 | 500 | +0.049 [+0.030, +0.068] | +0.036 [+0.020, +0.053] |
- Reading: removing every analog from the query's library (an upper bound on the same-study sibling effect, since it also removes legitimate analogs) shrinks the pooled C2 gain by about 20-25%. The rest survives on both table families. D (single-library NP, no references) turns slightly negative on the fresh set.

## Frozen kernel sources (experiments/b1_ana035: pipeline ef8f8f96, b1_analog 4f471bd1) with --analog_w 0.5 --analog_feat ap
- parity16: **PASS in both views** (main and insurance top-25 identical 16/16; analog features identical for 3,782 candidates; GL-learned 12 + fallback 4 molecules).
