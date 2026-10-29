# 115 stage 1: FP-only rank of the truth over the whole window (P0 / R / A rebuilt on the same system); C2-eligible truths only

- R final 233451aa9ee0af77, A final f121ee3dae81e364, P0 = fold-1 slot 1739d5683fa94fd7
- **dFP(A - R) = +0.00981, dFP(A - P0) = +0.01109 -> gate PASS (both > 0) -> stage 3**

| stratum | n | FP MRR@25 P0 / R / A | top-1 P0 / R / A | truth in M_all (resolved) / unresolved | truth simulated in A (n) | FP MRR A - R: truth simulated / not (resolved) |
|---|---:|---|---|---|---:|---|
| f1dev C_np_crosslib | 100 | 0.2275 / 0.2518 / 0.2395 | 0.130 / 0.160 / 0.150 | 0.32 / 0 | 32 | +0.0374 / -0.0357 |
| f1dev D_np_single | 100 | 0.0931 / 0.0923 / 0.0973 | 0.060 / 0.050 / 0.050 | 0.16 / 0 | 16 | +0.0132 / +0.0034 |
| f1dev E_np_negonly | 100 | 0.2248 / 0.2303 / 0.2489 | 0.120 / 0.120 / 0.150 | 0.41 / 0 | 41 | +0.0072 / +0.0266 |
| f1dev F_np_uncovered | 100 | 0.1526 / 0.1732 / 0.1813 | 0.070 / 0.100 / 0.110 | 0.48 / 0 | 48 | +0.0033 / +0.0125 |
| f1dev G_tims_crosslib | 100 | 0.5025 / 0.4764 / 0.4983 | 0.360 / 0.290 / 0.340 | 0.00 / 0 | 0 | +nan / +0.0219 |
| np053f1dev NP_H | 200 | 0.1376 / 0.1525 / 0.1728 | 0.060 / 0.075 / 0.090 | 0.95 / 0 | 191 | +0.0214 / -0.0028 |
| np053f1dev NP_X | 60 | 0.2820 / 0.2971 / 0.2773 | 0.167 / 0.167 / 0.150 | 1.00 / 0 | 60 | -0.0198 / +nan |
| np053f1dev NP_N | 60 | 0.2789 / 0.2707 / 0.2796 | 0.183 / 0.167 / 0.183 | 0.97 / 0 | 58 | +0.0092 / +0.0000 |
