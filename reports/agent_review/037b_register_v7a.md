# 037b registration: v7a combination as the next Public comparison (written 12:44 JST, BEFORE the anaw0.5 result 57650023 is read)

## Change (frozen)
- full_eval checkpoint (sha 5b8d1c31), candidates / reference conditions / DUP 0.98 / GL budget 14000 / deadline 30000 unchanged; tau 0.9, margin 0.2, min_gl_cover 0.5.
- GL coverage passes → **rank_v7a blend21** (2·z(learned) + z(fixed)); GL fallback → **insurance + 1·z(ap)**.
- Sources: experiments/b1_v7a036 (pipeline b5afcf72, b1_analog 7c9b9973 = 4f471bd1 + an unused drop_libs option, rankfeats f705db7a, rank_v7a f3ffc0f6: 600 trees selected by the same tuning recipe as rank_v4b's 300, so it is a new ranker, not "the pure effect of the analog features"); kernel casmi26-b1-fpnet-v7a (lzma blob 1,037,978 bytes; parity16 PASS in both views with these exact files).

## Local evidence (registered tables; `diag/v7a_registration_tables.md`, `036_prereg_v7a.md`, Codex 036 recomputation)
- vs FE on dev2 (full_eval): every protection layer positive (panel C1 clean +0.010, C C1 +0.045, G C1 +0.133, C2 C/D/E/F/G +0.049/+0.025/+0.181/+0.067/+0.094); vs M2x all positive (the 035 cumulative D shortfall is resolved).
- vs anaw0.5: C2 better (dev +0.035, confirmation +0.023 [+0.014, +0.033]); C1 worse on panel clean (−0.012), dev2 C C1 (−0.032), G C1 (−0.043 dev, −0.082 confirmation).
- COCONUT truths (DB membership outside the list, full denominators): vs main +0.103 (dev) / +0.073 (confirmation); vs anaw0.5 +0.033 / +0.010 [−0.009, +0.030].
- The confirmation sets were already used for 035/034 checks (not fresh for the whole study).

## Framing and reading (fixed now; branch decided by the 035 reading of 57650023)
- **Branch A** (57650023 − 0.370 < +0.008: anaw0.5 not promoted): v7a is compared with **FE 0.370**. Reading: Δ ≥ +0.008 → provisional working baseline (all protection layers vs FE and M2x pass); −0.015 < Δ < +0.008 → FE stays, v7a held as a fixed pending candidate; Δ ≤ −0.015 → not promoted, inspect the analog source / neighbourhood distribution and the run.
- **Branch B** (57650023 − 0.370 ≥ +0.008: anaw0.5 provisionally promoted): v7a is compared with **anaw0.5's Public score S_a** as a replacement. Its C/G unseen-C1 losses vs anaw0.5 (and panel clean −0.012) are recorded as an **operational exception, not a protection pass**; the 035 D exception is not extended. Reading: Δ vs S_a ≥ +0.008 → replace; −0.015 < Δ < +0.008 → keep anaw0.5, v7a held; Δ ≤ −0.015 → keep anaw0.5, inspect.
- No re-weighting / path change after any Public observation; the proxy combination is not mixed in (its path switching needs its own evaluation).

## Kaggle smoke of the frozen kernel (casmi26-b1-fpnet-v7a v1, 12 molecules on the visible dummy)
- rc 0; manifest analog_w 0 / analog_w_fallback 1 / ap / dup 0.98 / ckpt 5b8d1c31; learned model = the embedded 600-tree rank_v7a (27 features); learned path 11, fallback + analog 1; 24.9 s/mol (same as the analog kernel), analog store 981,821 representatives. Ready for submission after the branch decision; not submitted.
