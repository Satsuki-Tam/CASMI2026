# W7 parity: experiments/b1_baseline/eval_test_panel250_pc/run_e132_c2/b1_candidates.parquet vs experiments/b1_baseline/run_panel_fe_pc (view c2)

**PARITY PASS**

molecules 250; query selection differs: 0

| metric | value |
|---|---:|
| identical candidate sets | 1.000 |
| Jaccard median / mean / min | 1.000 / 1.000 / 1.000 |
| candidates only in evaluator / only in pipeline (mean) | 0.00 / 0.00 |
| truth in evaluator shortlist / in pipeline shortlist | 1.000 / 1.000 (disagree 0) |
| fp abs diff: max / mean of means | 0.0000 / 0.00000 |
| library similarity abs diff max | 0.0000 |
| pop / in_tier / in_coconut / in_train equal share | 1.0000 / 1.0000 / 1.0000 / 1.0000 |
| ppm error abs diff max | 0.000 |

analog feature parity (pipeline dump ana_ap vs analog_probe ap): 56125 candidates, max abs diff 0.000000, share > 1e-6 0.0000

## output agreement on 250 molecules (model lambdarank.txt, w_ice 0, libpri(0.9,0.2), GL fallback < 0.5)

| output | top-1 identical | RR identical | top-25 identical as sets | ordered top-25 identical (official identities) |
|---|---:|---:|---:|---:|
| main (learned + fallback) | 250/250 | 250/250 | 250/250 (1.000) | 250/250 (1.000) |
| insurance (fixed + libpri) | 250/250 | 250/250 | 250/250 (1.000) | 250/250 (1.000) |
evaluator-side GL fallbacks: 34
forward-score noise gl: 48933 pairs, |diff| max 0.00e+00, mean 0.00e+00, p99 0.00e+00

## 132 E-lite agreement on 250 molecules (K 10, alpha 0.5, E keys 404,487)

| ordered top-25 identical | top-1 identical | RR identical | E membership mismatches / shared candidates | E-lite rank-1 changed vs P |
|---:|---:|---:|---:|---:|
| 250/250 | 250/250 | 250/250 | 0 / 56125 | 10 |

strata covered: E empty 0, truth outside E 0, negative-ion only 18, strong class-1 reference (c1, lib_max_c1 >= 0.9) 0, GL fallback 34

132 completeness: roster 250, compared 250 = expected 250 (True), empty view lists 0 (placeholders equal: True)

## by set

| set | n | identical sets | Jaccard mean | truth in F | truth in P |
|---|---:|---:|---:|---:|---:|
| P_np250 | 250 | 1.000 | 1.000 | 1.000 | 1.000 |

## largest candidate-set disagreements

| molecule | set | n_f | n_p | only_f | only_p | jaccard | truth_in_f | truth_in_p |
|---|---|---|---|---|---|---|---|---|
| AAWZDTNXLSGCEK | P_np250 | 231 | 231 | 0 | 0 | 1.000 | True | True |
| ACNHBCIZLNNLRS | P_np250 | 244 | 244 | 0 | 0 | 1.000 | True | True |
| ACWBQPMHZXGDFX | P_np250 | 244 | 244 | 0 | 0 | 1.000 | True | True |
| ADEBPBSSDYVVLD | P_np250 | 239 | 239 | 0 | 0 | 1.000 | True | True |
| AGOYDEPGAOXOCK | P_np250 | 204 | 204 | 0 | 0 | 1.000 | True | True |
| AIONOLUJZLIMTK | P_np250 | 217 | 217 | 0 | 0 | 1.000 | True | True |
| ALEXXDVDDISNDU | P_np250 | 232 | 232 | 0 | 0 | 1.000 | True | True |
| AMOGMTLMADGEOQ | P_np250 | 242 | 242 | 0 | 0 | 1.000 | True | True |
