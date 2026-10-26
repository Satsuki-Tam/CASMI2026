# 034 pre-registration: analog channel probe (written 09:47 JST, before any analog result)

Motivation: B1 uses the library only as references of the candidate's own structure. The public lineage's starting point (analog propagation,
0.254 alone on Public) also uses library analogs (similar spectra of other structures, mass shift allowed) as a neighbourhood. B1 has no such
channel. `analog_probe.py` (own implementation): representatives up to 3 per (key, polarity), shifted entropy similarity within ±200 Da, top 80
analog keys per view with the evaluator's masks (C2: truth key + its identity group removed; C1: the truth's own-library spectra removed),
candidate features from Morgan Tanimoto to the analogs (ap = max tan·sim³, mean_tan = Σ tan·sim³ / Σ sim³).

Variants (fixed now): ana_only (rank by ap, diagnostic); anaw{0.25,0.5,1,2} = registered score + w·z(ap); anamt{0.25,0.5,1,2} = + w·z(mean_tan).

Regimes (Codex 033, no substitution), working baseline tables (full_eval):
- class 2 = dev2 C2 layers C/D/E/F/G (identity unseen by full_eval), full denominators;
- class 1 = panel C1 clean 202 (identity seen, query unseen); panel C1 uncertain as a side table; dev2 C1 = unseen stress table;
- panel C2 under full_eval is identity-seen -> not a class-2 measurement (reported only as a side table).

Reading (fixed now):
- Signal check: ana_only on dev2 C2 vs main. If ana_only alone is far below main everywhere and no blend gains, close the channel.
- Selection: one variant chosen by the equal-weight mean Δ over the five dev2 C2 layers, subject to panel C1 clean Δ ≥ −0.01 and no dev2 C2 layer below −0.02 (point). The chosen variant is a development candidate only.
- Before any Public use: confirm the chosen variant on molecules not used for the choice (fold-0 tables of the same sets for a regime check + a fresh confirmation set), and send the bundle to Codex. A dev2-C2 mean gain below +0.01 is treated as no evidence.

## Result 1 (10:05 JST): selection on the full_eval tables, then the regime check on the fold-0 tables
- full_eval tables (selection): anaw1 = dev2 C2 mean +0.0625 (C +0.022, D +0.000, E +0.181, F +0.067, G +0.042), panel C1 clean +0.023 → the pre-registered rule selects **anaw1**. The gain is not driven by near-aliases: 86% of the summed RR change comes from molecules whose truth has best Tanimoto < 0.9 to any analog.
- **Regime check (fold-0 = identity unseen) FAILS for anaw1**: panel C2 clean (easy NP class 2) **−0.048**, W7 A timsTOF C2 **−0.024**, W7 B NP C2 +0.004, dev2 C/D −0.002/−0.004, E +0.168, F +0.084, G +0.050; panel C1 clean +0.043, W7 B C1 +0.055. → anaw1 is **not** a candidate.
- Mechanism (read from the table, to be tested): a decoy that is itself a library compound with a similar spectrum gets Tanimoto 1 to itself (ap = sim³), i.e. the analog channel re-counts the library self-match that lib_sim already carries. That promotes library decoys in C2, the same failure as twin-first. mean_tan (anamt1) did not show it (fold-0: no layer below −0.003), but choosing it now would be post-hoc.
- Next (fixed before computing): add self-excluded features (the candidate's own key removed from its analog set: ap_x, mean_tan_x). One selection rule over BOTH table families: maximise the mean over all class-2 layers (fe dev2 C2 ×5 + fold-0 dev2 C2 ×5 + fold-0 panel C2 clean + W7 A/B C2), subject to no class-2 layer < −0.02 in either family and panel C1 clean (fe) ≥ −0.01. Candidates: anaw{0.5,1}, anamt{0.5,1,2}, anaxw{0.5,1} (ap_x), anamtx{0.5,1,2} (mean_tan_x). Confirm the selected one on a **fresh confirmation set** (new seed, identity groups never used) before Codex and any Public use.

## Next variant family (fixed 11:08 JST, before computing): GL-coverage-gated analog weight
- Mechanism: molecules without GL coverage fall back to the fixed list (FP + prior + library priority) with no forward evidence; the analog channel helped most there (E negative-only).
- Variants: anag{wc}_{wu} = registered score + w·z(ap) with w = wc when the molecule's GL coverage passes (learned/blend path) and wu when it falls back: (0.5, 1), (0.5, 2), (0.25, 1), (0.25, 2); plus the submitted anaw0.5 as the reference.
- Same 13-layer selection rule and constraints as above, on the development tables only. A variant replaces anaw0.5 as the next candidate only if it beats anaw0.5's objective by ≥ +0.005 and passes the constraints. Confirmation on unused molecules: fit pool E rows 101-300 (200) + fit_pool_overflow D (first 150) (fold-0), reported for the chosen variant AND anaw0.5 on the same molecules.

## Result 2 (11:27 JST): gated family
- Development tables (13-layer rule): anag0.25_1 (w 0.25 on the learned path, 1.0 on the GL fallback) objective +0.0464 vs anaw0.5 +0.0365 → passes the +0.005 replacement bar (worst layer −0.0195, f0 dev2 C C2).
- Second confirmation set (unused: fit pool E rows 101-300, overflow D 150; fold-0): anag0.25_1 − main: D C2 +0.014 [+0.003, +0.027], E C2 +0.106 [+0.072, +0.142], pooled C2 +0.066 [+0.045, +0.088]. **anag0.25_1 − anaw0.5: D C2 −0.014 [−0.026, −0.004], E C2 +0.013 [−0.004, +0.028], E C1 +0.056 [+0.028, +0.086]** → on unused molecules the gate trades D for E (C2 net ≈ +0.001).
- Decision: anag0.25_1 does **not** replace anaw0.5 (no clear gain on unused data, a significant D loss). It stays an alternative. Side result: the same second set also gives anaw0.5's own effect on unused E/D molecules, recorded with the 035 reading.
