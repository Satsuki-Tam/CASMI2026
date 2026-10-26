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

## Pre-submission checks (done) and submission
- (a) identity audit (`experiments/b1_baseline/analog_audit.py`, frozen module, 836 C2 molecules, 46,771 unique analog keys): returned keys in the exclusion set **0**; returned keys equal to a query identity **0**; official identity of the key's SMILES == key **1,500 / 1,500** sampled.
- (b) Kaggle smoke (v1, 12 molecules): rc 0, manifest analog_w 0.5 / ap / dup 0.98 / ckpt sha 5b8d1c31; analog store 981,821 representatives built in 85 s; feature stage 25.4 s/mol vs 19.9 s/mol without the channel (+5.5 s/mol ≈ +37 min for 400 molecules). Projected hidden rerun ≈ 3.8-4.4 h; the GL budget under deadline_s 30000 stays at its 14,000 s cap (remaining ≈ 15,700 s), GL needs ≈ 2,300 s.
- Frozen-source parity16: PASS in both views (also re-checked by Codex).
- **Submitted 11:05 JST: ref 57650023** (kernel casmi26-b1-fpnet-analog v1). The reading table above applies unchanged.
