# 033 pre-registration: readings fixed before the 10/26 Public results (written 09:15 JST, results expected ~12:15-12:30)

Submissions (09:02 JST): T probe 57645888, COCONUT-only probe 57645901, band26 probe 57645908, DUP diagnostic 57645926.
The readings of 027_decision §2, 030_decision §1 and 032_decision §2 stay as fixed. This file only adds two predictions and one external comparison.

## 1. Calibration predictions (calib_public2.py, stage 1 = main 0.354 / insurance 0.336 / pc 0.046 / pool 0.336, 4,000,000 draws, 51 accepted; `diag/calib_pre_probes1026.md` on the Spark)
| probe | predicted Public, mean [5%, 95%] |
|---|---|
| T (train-structure candidates only, M2x order) | 0.209 [0.096, 0.296] |
| COCONUT-only (non-train) | 0.149 [0.048, 0.272] |
| band26 (ranks 26-50 lifted to 1-25) | 0.007 [-0.011, 0.028] |
- The calibration gives the "zero under every configuration" component (posterior weight 0.55) a band26 value of 0 by construction. So the band26 prediction covers only the local proxy types. **Reading: P_26 - 0.007 ≈ the near-miss mass inside the zero component.**
- A T or COCONUT result outside the interval is evidence against the proxy-type mixture (as full_eval was on 10/25), not against the probe.

## 2. External comparison for the T probe: community "library twin at rank 1" probe
- Topic 742088 (2026-09-19, analog-propagation fork; pool = train + COCONUT + ChEBI/LIPID MAPS, ±8.5 ppm): **only the nearest library spectrum's structure at rank 1 = 0.275 on Public** (twin correct for ~27.5% of molecules). The full list of the same pipeline scored 0.324. Its ranks 3-25 alone scored 0.059.
- A correct twin is a train structure, so 0.275 is a lower bound on the class-1 share that a one-guess twin rule recovers. Caveats: the scorer identity changed on 10/07 (RemoveStereochemistry); their similarity function and window are not ours; it is a single submission (noise ~±0.016).
- Reading of P_T (B1's M2x order restricted to train structures; P_T ≥ B1's class-1 contribution M_T):
  - **P_T ≤ 0.25**: B1's ordering among train candidates loses molecules that a one-guess twin rule gets. Class-1 handling becomes the primary suspect for the gap to E0 (0.464). Next: the twin-first variants (local, being computed now in `group_filter_eval.py`: twin_only / twin1_t{0,0.5,0.7,0.8,0.9}), together with the DUP result.
  - **P_T ≥ 0.29**: B1 already recovers the twin cases. The gap lies in non-train truths (COCONUT ordering, PubChem) or in the zero component.
  - In between: undecided. Use the DUP diagnostic and the local twin tables before acting.
