# 034 pre-registration: analog channel probe (written 10:05 JST, before any analog result)

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
