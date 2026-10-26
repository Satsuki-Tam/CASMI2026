# 035 decision (written before the submission and before any 10/26 Public result)

Adopted from Codex 035:
1. One Public comparison today: **FE + anaw0.5**, fixed = full_eval checkpoint (sha 5b8d1c31), DUP setting 0.98, analog_w 0.5, analog_feat ap, frozen sources experiments/b1_ana035 (pipeline ef8f8f96, b1_analog 4f471bd1), kernel casmi26-b1-fpnet-analog. It is not changed after the T/COCONUT/band/DUP results and is never silently combined with dup_sim 1.01 (a combination is a new registered comparison).
2. **Protection record**: the cumulative dev2 D C2 (FE+ana − M2x = −0.0227) fails the default point condition. **This comparison accepts that shortfall as a known risk; it is not treated as a protection pass.** Decided now, before Public: promotion with this exception is allowed only under row 1 of the table below and only if the pre-submission audits below pass. The exception is not extended to later candidates automatically.
3. Reading (fixed now; 0.008 / −0.015 are operating guides, not significance bounds):
| Public − 0.370 | decision |
|---|---|
| ≥ +0.008 (consistent with the local evidence) | provisional working baseline candidate; confirm the frozen version, inputs and a complete run, then promote with the D exception recorded |
| −0.015 < Δ < +0.008 | FE stays the official control; anaw0.5 stays a fixed pending candidate; no weight re-tuning on Public |
| ≤ −0.015 | not promoted; check source / neighbourhood distribution differences, reference self-match, model exposure, GL coverage and time budget (no single-cause conclusion) |
4. Evidence wording: the confirmation C2 set is "unused for the analog selection" (conf3 D80 is entirely new; the fit-pool part was used earlier by other rankers), measured with the fold-0 model. The 86% < 0.9-Tanimoto figure is the share of the net summed RR change. The analog effect also includes self-matches under a different preprocessing/reference choice and is not described as pure "other-structure analogy".
5. The same-library sensitivity in 035_addendum used the development drop_libs, which discards representatives without re-selecting them, so it is approximate. A corrected source-sensitivity table (re-selected representatives, per query library and per analog source) follows as an additional evaluation of the FIXED candidate, not as a search.

Pre-submission checks (Codex 035): (a) identity audit of the returned C2 analogs: intersection with the exclusion set = 0, query rows = 0, official identity of each analog key's SMILES consistent with the key (sample); (b) Kaggle smoke complete, with the added CPU time / memory and its effect on the GL budget under deadline_s estimated from the smoke log.
