# 033 pre-registration: readings fixed before the 10/26 Public results (written 09:10 JST, results expected ~12:15-12:30)

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

## 3. Addendum 09:18 JST: second calibration model with the community twin probe as an observation (before any result)
- Local twin tables (`group_filter_eval.py` + twin columns -> `diag/gf2_{m2x,fe}_{panel,p2dev,devAB}.csv`; main/train identical to the gf tables): twin = best library match among B1's candidates of the view.
  - fold-0 M2x: panel C1 main 0.882 / twin alone 0.852 / twin-first (any similarity) 0.910; **G timsTOF C1 main 0.612 / twin alone 0.816 / twin-first 0.867**; W7 B C1 0.913 / 0.887 / 0.925.
  - The C2 views lose heavily under twin-first: panel C2 0.904 -> 0.494 (t0) / 0.799 (t0.7) / 0.896 (t0.9); G C2 0.716 -> 0.389 / 0.619 / 0.673.
- Model B = calib_public2 `--tables gf2 --obs main=0.354 insurance=0.336 pc=0.046 pool=0.336 twin_only=0.275`, 4 seeds × 8M draws, 50 accepted (`diag/calib_twin1026_s{1..4}.md`):
  - weights: class-1 proxies 0.31 [0.28, 0.34], COCONUT 0.09, PubChem-only 0.06, zero 0.54.
  - **predicted P_T = 0.275 [0.26, 0.29], P_COCONUT = 0.078 [0.04, 0.11]**, P_26 = 0.003-0.006 (local types only).
  - twin-first on the M2x order: t0 ±0.00, **t0.5 +0.022, t0.7 +0.025 [+0.006, +0.042], t0.8 +0.019**, t0.9 +0.003.
- Model A (§1, no twin observation): P_T 0.209 [0.096, 0.296], P_COCONUT 0.149 [0.048, 0.272].
- **Fixed reading: the T and COCONUT probes decide between A and B.** If both land inside B's intervals (P_T 0.26-0.29 and P_COCONUT ≤ 0.11), model B is supported. The twin-first family then becomes the next candidate, prepared on the working baseline (full_eval) with its own local protection table, plus one Public comparison. If they land in A's region (P_T ≤ 0.24 or P_COCONUT ≥ 0.13), the twin probe's constraint does not transfer (a different twin definition, or our local C1 types misrepresent hidden class 1), and twin-first is not promoted on this calibration.
- Caveat fixed in advance: the calibration is valid only for changes inside the same FPNet and shortlist. Twin-first reorders within the list, so this applies. Its zero component cannot respond to the change.

## 4. Corrections after Codex 033 (09:45 JST, still before any result)
- band26 calibration prediction corrected: the absolute type-mixture value is w·s_band = **0.0016 [0.0006, 0.0026]** (model B draws). Adding the predicted difference to 0.354 mixed in main's fit error and produced the negative bound. **The reading "P_26 - 0.007 ≈ near-miss mass of the zero component" is withdrawn.** The 027 reading P_26 ≤ q_26-50 ≤ min(25·P_26, 1) stays.
- §2 readings corrected: P_T < 0.275 means only that B1's mean RR inside train candidates is below the external one-guess rule's hit rate (if both describe the same scoring set). It does not mean B1 dropped those molecules from its candidates. P_T ≥ 0.29 does not mean the external twin's molecules are recovered by B1. The comparison is a lead, not an observation of B1's twin.
- §3: model B is a sensitivity analysis, not the decision basis. A and B overlap (B = A + one constraint). Under B's constraints the hard-C1 weight can be anywhere in 0-0.36 and the hybrid twin prediction anywhere in −0.004 to +0.055 (linear programme, Codex 033). The "twin submission if T/B fall in B's interval, promotion at +0.015" rule is **withdrawn**.
