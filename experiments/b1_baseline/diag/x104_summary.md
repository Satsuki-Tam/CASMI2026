# 104 reading: t1E (main rank-1 fixed, E slots re-ordered by the 102 RRF score) (104_prereg_t1E.md)

## Checks (must pass before any number below)

| tag | rows | I1a p_e worsened an E-reached truth | I1b a variant improved a truth outside E | I2 alpha-1 kept a non-E rank-1 | I5 empty E changed | I3 main vs 087 (diff/rows) |
|---|---:|---:|---:|---:|---:|---|
| np053f1dev | 372 | 0 | 0 | 0 | 0 | 2/372 |
| np053f1dev | t1E checks | truth outside E changed 0 | rank-1 row sets differ 0 | empty E changed 0 | main vs 102 diff 0 |
| np053f2dev | 389 | 0 | 0 | 0 | 0 | 2/389 |
| np053f2dev | t1E checks | truth outside E changed 0 | rank-1 row sets differ 0 | empty E changed 0 | main vs 102 diff 0 |
| f1dev | 794 | 0 | 0 | 0 | 0 | 3/794 |
| f1dev | t1E checks | truth outside E changed 0 | rank-1 row sets differ 0 | empty E changed 0 | main vs 102 diff 0 |
| f2dev | 795 | 0 | 0 | 0 | 0 | 2/795 |
| f2dev | t1E checks | truth outside E changed 0 | rank-1 row sets differ 0 | empty E changed 0 | main vs 102 diff 0 |
| panel | 500 | 0 | 0 | 0 | 0 | 0/500 |
| panel | t1E checks | truth outside E changed 0 | rank-1 row sets differ 0 | empty E changed 0 | main vs 102 diff 0 |
| p2dev | 792 | 0 | 0 | 0 | 0 | 4/792 |
| p2dev | t1E checks | truth outside E changed 0 | rank-1 row sets differ 0 | empty E changed 0 | main vs 102 diff 0 |

## Decision table (one candidate)

| candidate | primary 1/2 A + 1/2 B_D | block A 053 NP C2 | block B_D f1/f2 D C2 | old B f1/f2 NP C2 (C-F) | G C1 (f1/f2) | panel C1 clean | 053 NP C1 (4 cells) | gate |
|---|---|---|---|---|---|---|---|---|
| t1E_rank_e1r_0.5 | **+0.0019 [-0.0007, +0.0048]** | +0.0037 [-0.0016, +0.0094] | +0.0002 [-0.0006, +0.0012] | +0.0026 [-0.0003, +0.0055] (non-inferior) | +0.0011 [+0.0000, +0.0025] (non-inferior) | -0.0055 [-0.0101, -0.0017] (undetermined) | -0.0006 [-0.0063, +0.0045] (non-inferior) | no |

- **Gate: NO**


## Diagnostics (row means, not the primary weights; not used for the decision)

| layer | n | main | p_e alone | e1b alone | e1r alone | oracle e1b | oracle e1r | truth in E source | truth reached in E subset |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A 053 NP C2 | 520 | 0.5808 | 0.6000 | 0.5368 | 0.5460 | 0.6292 | 0.6353 | 1.000 | 0.833 |
| B_D f1/f2 D C2 | 200 | 0.2782 | 0.1597 | 0.1448 | 0.1574 | 0.2921 | 0.2978 | 0.235 | 0.195 |
| old B f1/f2 NP C2 | 800 | 0.4217 | 0.2558 | 0.2255 | 0.2378 | 0.4573 | 0.4661 | 0.461 | 0.406 |
| G C1 | 200 | 0.8830 | 0.9267 | 0.9300 | 0.9342 | 0.9383 | 0.9483 | 1.000 | 0.985 |
| panel C1 clean | 202 | 0.9251 | 0.9298 | 0.7921 | 0.6858 | 0.9373 | 0.9348 | 1.000 | 1.000 |
| 053 NP C1 | 113 | 0.8530 | 0.8736 | 0.8714 | 0.8483 | 0.9098 | 0.9117 | 1.000 | 1.000 |
| panel C2 | 250 | 0.9535 | 0.9605 | 0.8598 | 0.8535 | 0.9774 | 0.9727 | 1.000 | 1.000 |

| variant | layer | rescued | lost | new rank-1 | lost rank-1 | d truth in E source | d truth outside | d truth reached in E | d COCONUT truth | d non-COCONUT | d GL path | d fallback |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t1E_rank_e1r_0.5 | A | 32 | 40 | 0 | 0 | -0.0005 (520) | n/a | -0.0007 (433) | -0.0005 (520) | n/a | -0.0043 (394) | +0.0111 (126) |
| t1E_rank_e1r_0.5 | B_D | 1 | 2 | 0 | 0 | +0.0008 (47) | +0.0000 (153) | +0.0009 (39) | +0.0012 (29) | +0.0000 (171) | +0.0002 (198) | +0.0000 (2) |
| t1E_rank_e1r_0.5 | old B | 45 | 40 | 0 | 0 | +0.0056 (369) | +0.0000 (431) | +0.0064 (325) | +0.0044 (275) | +0.0016 (525) | +0.0000 (386) | +0.0050 (414) |

| variant | C1 rank-1 lost (G / panel clean / 053) | dev2 NP C2 stress (C-F cells equal) |
|---|---|---|
| t1E_rank_e1r_0.5 | 0 / 0 / 0 | +0.0003 [-0.0023, +0.0028] |

## Sensitivity (descriptive): d = t1E - main by the truth's prior rank in the view list

| layer | absent | 1 | 2-3 | 4-10 | 11+ |
|---|---|---|---|---|---|
| A 053 NP C2 | +0.0000 (87) | -0.0053 (111) | -0.0084 (95) | -0.0012 (103) | +0.0098 (124) |
| B_D f1/f2 D C2 | +0.0000 (120) | +0.0000 (8) | +0.0000 (10) | +0.0000 (6) | +0.0006 (56) |
| old B f1/f2 NP C2 | +0.0000 (253) | -0.0063 (70) | -0.0151 (59) | +0.0146 (61) | +0.0070 (357) |
| G C1 | +0.0000 (3) | +0.0000 (1) | +0.0000 (2) | +0.0000 (1) | +0.0011 (193) |
| panel C1 clean | - | -0.0038 (133) | -0.0107 (46) | +0.0031 (14) | -0.0185 (9) |
| 053 NP C1 | - | +0.0000 (35) | +0.0093 (18) | -0.0124 (31) | +0.0067 (29) |
| panel C2 | - | +0.0000 (174) | +0.0032 (52) | -0.0178 (15) | +0.0185 (9) |

- panel C1 clean (prior strata = pop desc, ties fp desc, then fixed row order; not a pure popularity rank): measured prior-rank-1 share 0.66 (n1 133, n0 69), unweighted d -0.0055; re-weighted to FIXED assumed shares: share 0.66: -0.0055 (ESS 202), share 0.30: -0.0074 (ESS 129), share 0.10: -0.0084 (ESS 85)
