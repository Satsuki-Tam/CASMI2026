# 037 pre-registration: demote train-structure candidates without library support (written 12:15 JST, before computing)

Evidence (computed from existing tables, before this note): Public probes put the largest part of B1's score on COCONUT-only truths (M_B 0.148-0.202). Locally, for C2 COCONUT-truth molecules the main list loses most to TRAIN decoys (dev2 full_eval: main 0.529 → pool-only 0.587 → COCONUT-only candidates 0.721; fresh: 0.556 → 0.593 → 0.763). Of the train decoys whose FP beats the truth's (C2, COCONUT truths), 55% have lib_sim ≤ 0.5 (39% ≤ 0.3), i.e. no reference spectrum of that structure resembles the query: their FP is inflated by FPNet memorisation (every train structure is seen by full_eval) and is not evidence of identity. Class-1 truths rarely lack support (lib_sim_c1 ≤ 0.5: panel clean 6%, G 1%, but dev2 C/E/F 31%, mostly negative-only / uncovered queries).

Variants (label-free: in_train of the view = the candidate is a training structure; lib_sim = its best reference similarity to the query):
- tdem{θ}_{w}: registered score − w · 1[train candidate and lib_sim ≤ θ], θ ∈ {0.3, 0.5}, w ∈ {0.5, 1, 2} (z units), applied to both paths (learned blend and fallback).
- anatdem{θ}_{w}: the same on top of anaw0.5 (analog channel), for the case the analog submission is adopted.

Selection: 11 class-2 layers (fe dev2 C2 ×5, fold-0 dev2 C2 ×5, fold-0 panel C2 clean), objective = equal-weight mean; constraints: every class-2 layer ≥ −0.02, panel C1 clean (fe, seen regime) ≥ −0.01; side table: G C1, C/E/F C1, W7 (inside the ranker's training runs). Then confirmation on the fresh sets (conf3, fit pool, fit pool 2) against the respective base with paired intervals; C1 losses on the fresh C1 views reported. Codex review before any Public use.

## Result (12:17 JST)
- Pre-registered family (development, 11 class-2 layers): best tdem0.5_2 +0.0115 (every layer ≥ 0, panel C1 clean +0.0004, G C1 +0.002, C/E/F C1 −0.026); on top of anaw0.5 the best anatdem0.5_2 adds +0.0097.
- Exploratory (not pre-registered, full_eval tables): even REMOVING unsupported train candidates (lib ≤ 0.5) gives only C/D/E/F/G C2 +0.014/+0.011/+0.035/+0.028/+0.005 and panel C2 +0.008, while C1 costs grow (E −0.062, F −0.118, C −0.054, panel −0.032).
- Reading: most train decoys that outrank COCONUT truths HAVE library support (> 0.5: structurally related compounds with similar spectra) — the inherent class-1 / class-2 ambiguity, not memorisation alone. A small lever (+0.01 on class-2 proxies); not a candidate now.

## Side check (12:31 JST, exploratory): is GLACIER inflated for its own training compounds (MassSpecGym members)?
- dev2 C2 (full_eval tables; dev2 truths are outside MassSpecGym by construction, 0 of 205 truths in MSG): at matched FP-z quintiles, MSG-member decoys have the same GL z as non-members (−0.67 vs −0.59, −0.09 vs −0.08, +0.05 vs +0.02, +0.14 vs +0.14, +0.56 vs +0.44 (n 49)). MSG-member train decoys are weak overall (zfp −1.07, zgl −0.39). Truths: zgl +3.30, zfp +1.36.
- Reading: no material GLACIER memorisation bias against class-2 truths; closed. The train decoys that beat COCONUT truths are library-supported analogs credited through the ranker's library features.
