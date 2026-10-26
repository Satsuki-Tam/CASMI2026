# 033 decision (09:35 JST)

Adopted from Codex 033 (all points):
1. The community twin probe (0.275) is a lead, not an observation of B1's twin. Model B stays as a sensitivity analysis only. The twin-promotion rule of 033_request is withdrawn (033_prereg §4).
2. The hybrid calibration (C1 from full_eval tables, C2 from fold-0 tables) substitutes conditions. Under full_eval, dev2 identities are held out (hold = dev2, lock = locked2), so dev2 C1 there is identity-unseen; W7 under full_eval is query-trained; only panel C1 (clean 202 as the main table) is "identity seen, query unseen" = hidden class 1 for the working baseline. Class-2 costs for full_eval come from its own dev2 C2 tables.
   - Consequence I draw: on the panel (the seen regime) twin-first adds only ~+0.001-0.01 because the full-train FPNet already ranks the truth well; the large G gain (+0.17-0.25) is an unseen-identity effect. For the working baseline the class-1 benefit is therefore likely small while the dev2 C2 cost is real (G −0.065, C/D/F −0.007-0.010 on full denominators).
3. twin1m_t0.7_m0.1 is recorded as a post-hoc selected development candidate; fixed from now on. Not promoted; no Public submission today for it. The kernel `casmi26-b1-fpnet-twin` v1 stays staged (smoke only).
4. DUP comparison base fixed (A = 0.370 baseline, B = 57645926 dup off, C = twin alone, D = combination); a combination is a new registered candidate, never a silent switch.
5. band26: absolute prediction w·s_band = 0.0016 [0.0006, 0.0026]; the near-miss-mass reading is withdrawn; 027's reading stays.

Next (local, Spark): the joint table Codex asked for (same molecules: B1 wrong & twin right vs B1 right & twin wrong, by sim / margin / twin rank / reference coverage), split by regime (panel clean 202 seen; panel uncertain; dev2 G unseen), to decide whether any twin form can help the working baseline. Today's last slot: decided after the DUP result.

## Joint audit result (09:40, `experiments/b1_baseline/twin_joint_audit.py` -> `diag/twin_joint_audit.md`, rule twin1m_t0.7_m0.1 fixed)
| regime | n | main | rule | main@1 & twin right | main wrong & twin right | main@1 & twin wrong | both wrong |
|---|---:|---:|---:|---:|---:|---:|---:|
| panel C1 clean, full_eval (identity seen, query unseen = hidden class 1 of the working baseline) | 202 | 0.897 | 0.907 | 153 | 16 | 18 | 15 |
| same, fold-0 (identity unseen) | 202 | 0.862 | 0.891 | 145 | 24 | 15 | 18 |
| dev2 G C1, full_eval (identity unseen) | 100 | 0.604 | 0.787 | 40 | 40 | 2 | 18 |
| dev2 C2 layers, full_eval (full denominators) | 100 each | | | | | | G −0.065, C −0.010, D −0.007, F −0.010, E 0 |
- In the seen regime the main list and the twin are about equally good and complementary (16 vs 18 disagreements); the fixed rule adds +0.010 there. The large twin gains exist only where the FPNet has not seen the identity.
- Per twin-similarity bin (full_eval): panel C1 clean [0.8, 0.9) holds 51% of molecules, rule +0.022 per molecule; all C2 views [0.8, 0.9) hold 6% of molecules, rule −0.144 per molecule. With any class weights near the calibrations (class 1 ~0.3, class 2 ~0.15) the expected Public change is about +0.002-0.003.
- **Conclusion: the twin-first rule is not a lever for the working baseline (closed).** Still open, small: a selector between the main top-1 and the twin in the seen regime. The oracle choice on panel clean gives 187/202 at rank 1 vs 171. Expected value is small, so it is not pursued now.
- Implication for the gap to E0: if hidden class 1 resembles the panel (Enveda timsTOF NP queries, references in public NP libraries), the working baseline already ranks it at ~0.9. The remaining 0.09 then sits mostly in class 2 or in molecules we score 0 on, which today's T / COCONUT / band26 probes help to locate.
