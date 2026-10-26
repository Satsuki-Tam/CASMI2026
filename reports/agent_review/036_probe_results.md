# 10/26 Public probe results (12:12 JST) and the pre-registered readings

| submission | Public |
|---|---:|
| T probe (train-structure candidates only, M2x order) 57645888 | **0.160** |
| COCONUT-only (non-train) probe 57645901 | **0.202** |
| DUP diagnostic (full_eval, entropy duplicate rule off) 57645926 | **0.370** (working baseline 0.370: **±0.000**) |
| band26 57645908 | pending |
| FE + analog anaw0.5 57650023 | pending |

## Algebra (`experiments/b1_probe027/probe_algebra.py`; M 0.354, P_K 0.336, P_P 0.046)
- P_T + P_B − P_K = **+0.026** (choosing train vs COCONUT membership inside the pool: between the 0.01 and 0.03 guides).
- P_T + P_B + P_P = **0.408** (three-group membership oracle with fixed internal orders; M + 0.054).
- **M_T (class-1 = train-truth contribution of M2x) ∈ [0.106, 0.160]; M_B (COCONUT-only truths) ∈ [0.148, 0.202]**; M_P ∈ [0.018, 0.046]. → The largest part of B1's score comes from truths that are COCONUT structures not in train (class-2 NP), not from class 1.
- Calibration: model A's marginal intervals contain both (P_T 0.209 [0.096, 0.296], P_B 0.149 [0.048, 0.272]); model B (community twin constraint) is far off (predicted P_T 0.275, P_B 0.078) → the community twin probe does not describe this scoring set the way model B assumed (as Codex 033 warned).
- Reading 027 §2: T/B membership recovery 0.026 → in between ("undecided"); internal orders and reach remain the main levers, cross-group confusion is a secondary +0.026 (pool) / +0.054 (three groups).

## DUP (032 §2)
- Δ = ±0.000 → "small positive / tie → no promotion". The entropy near-duplicate rule is not a lever on Public; closed. (The analog submission keeps dup_sim 0.98 as registered.)

## Consequence for the analog channel (pending 57650023)
- The hidden-relevant C2 type is COCONUT-truth NP. Local anaw0.5 − main by truth group (C2): COCONUT-only +0.017 [−0.002, +0.036] (full_eval dev2 + panel), +0.013 [−0.005, +0.031] (fold-0 incl. W7), +0.071 [+0.032, +0.112] (fresh sets); PubChem-only +0.063 / +0.033 / +0.100. Positive for both groups, smaller for COCONUT truths.

## band26 (12:17 JST): **0.005**
- P_26 = 0.005 → the share of molecules with the truth at ranks 26-50 satisfies 0.005 ≤ q ≤ 0.125; main + band oracle = 0.359. Reading 027 §2 (≤ 0.01): the band's lift score is small; ranks 51+ and unreached truths cannot be told apart from this probe.

## Corrections after Codex 036
- Wording: M_T is the **train-truth** contribution, M_B the non-train COCONUT-truth contribution (candidate-derived groups, not the official classes; a non-train COCONUT structure can still be class 1 if another public library references it). Firm: **non-train truths together (M_B + M_P = 0.194-0.248) contribute more than train truths (0.106-0.160)**. Not firm: COCONUT-only being the single largest (M_T and M_B intervals overlap), the class shares (P_T = share × in-group MRR), and where E0's lead lies (≥ 0.056 of it is not explained by group selection).
- The "full_eval dev2 + panel COCONUT +0.017" line above mixed the identity-seen full_eval panel C2 (excluded condition). Valid full_eval dev2 only: reached COCONUT-only truths (119) anaw0.5 − main = **+0.083**.
- v7a combination − anaw0.5 on the confirmation C2 by group: reached COCONUT-only +0.011 [−0.012, +0.034], reached PubChem-only +0.046 [+0.029, +0.065], truth absent 0 (truth_group is shortlist-based; absent molecules can also be COCONUT truths).
