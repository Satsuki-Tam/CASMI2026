# 036 pre-registration: analog-aware ranker rank_v7a (written 11:31 JST, before training finished / any v7a result)

- rank_v7a = rank_v4b recipe (same RUNS run_v3_p1 fit + run_v3_eval + run_v3_c1, v2_noice − lib_nref − in_train, C1 ×3, same params) + analog block (ana_ap, z_ana_ap, ana_mt, ana_gap from analog_probe features of the training tables with the evaluator's masks). Output rule unchanged: blend21 = 2·z(learned) + z(fixed), GL-cover fallback = insurance list. No extra analog term.
- Comparison target: anaw0.5 on rank_v4b (the submitted candidate) and FE main.
- The W7 sets (eval_set) are inside the training RUNS of both rankers → excluded from the selection objective (11 class-2 layers: fe dev2 C/D/E/F/G, f0 dev2 C/D/E/F/G, f0 panel C2 clean; constraints: every layer ≥ −0.02, panel C1 clean (fe) ≥ −0.01).
- v7a becomes the next candidate only if its objective ≥ anaw0.5's + 0.005 and the constraints pass; then it is confirmed against anaw0.5 on ALL fresh sets (conf3 D80, fit pool C/E/F/G, fit pool E 101-300 + overflow D150) with paired intervals, before Codex and any Public use. A trainer regression (rank_v4b re-trained by the patched trainer with the old feature list) must reproduce the feature list and the number of trees.

## Result 1 (11:48 JST) and the next family (fixed before computing)
- v7a alone (11 layers): objective +0.0212 vs anaw0.5 +0.0408 → **not** a replacement. Pattern: v7a > anaw0.5 on the GL-covered layers (fe C/D/G C2 +0.025/+0.032/+0.007 over anaw0.5; f0 C/D/G +0.037/+0.037/+0.025) but 0 on E/F (those molecules fall back to the insurance list, where the learned model is not used), and panel C1 clean −0.0001 (anaw0.5 +0.022).
- Next family (computed only after this note): rank_v7a with an analog term on the fallback path and/or everywhere: v7a_g0_{0.5,1} (w 0 on the learned path, 0.5 / 1 on the fallback), v7a_w{0.25,0.5} (w on both paths). Same 11-layer rule, the +0.005 replacement bar against anaw0.5, then confirmation against anaw0.5 on all fresh sets.

## Result 2 (11:49 JST): combined family
- Development (11 layers): v7a_anag0_1 (rank_v7a on the learned path, analog weight 1 on the GL-fallback path) objective **+0.0745** vs anaw0.5 +0.0408 (min layer −0.0077; panel C1 clean +0.0102 vs anaw0.5 +0.0224) → passes the replacement bar. v7a_anag0_0.5 +0.0619, v7a_anaw0.25 +0.0471, v7a_anaw0.5 fails (f0 panel C2 −0.023).
- **Fresh confirmation vs anaw0.5 (conf3 + fit pool + fit pool 2, fold-0)**: all C2 (686) **+0.023 [+0.013, +0.033]** (C +0.032, D +0.038 [+0.022, +0.056], E +0.010, F +0.039, G +0.015); all C1 (290) +0.012 [−0.012, +0.034], but **G C1 −0.082 [−0.136, −0.028]** and C C1 −0.079 [−0.175, 0.000].
- Reading: a real class-2 gain over anaw0.5 that gives back class-1 accuracy in the G / C (and panel seen, −0.012) layers. Not decided here: needs a review of the class-1 trade-off (Codex) and comes after the Public result of anaw0.5 (57650023); never combined with anaw0.5's result into a new reading silently.

## Family 3 (fixed 12:46 JST, before training finished): fixed-param and seen-regime analog rankers (local only)
- rank_v7a_fx = v7a with rank_v4b's fixed params (300 rounds) → isolates the analog-feature effect from the 600-round selection and fits the zlib notebook.
- rank_rka = rank_rk_fx recipe (full_rk-FPNet tables run_rk_p1/eval/c1, C2 rows of FPNet-seen identities dropped, rank_v4b params) + the analog block (analog features recomputed on the rk tables' shortlists).
- Both evaluated with the registered combination routing (learned blend21 when GL covered, insurance + 1·z(ap) on fallback = column anag0_1 with the model). Same 11-layer rule; a model replaces the registered v7a combination only if its objective is ≥ +0.005 higher AND panel C1 clean / C, G C1 are not lower; otherwise the registered v7a candidate (037b) stays unchanged. Confirmation on the confirmation sets is required before any change of the candidate.
