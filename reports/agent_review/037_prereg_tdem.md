# 037 pre-registration: demote train-structure candidates without library support (written 12:20 JST, before computing)

Evidence (computed from existing tables, before this note): Public probes put the largest part of B1's score on COCONUT-only truths (M_B 0.148-0.202). Locally, for C2 COCONUT-truth molecules the main list loses most to TRAIN decoys (dev2 full_eval: main 0.529 → pool-only 0.587 → COCONUT-only candidates 0.721; fresh: 0.556 → 0.593 → 0.763). Of the train decoys whose FP beats the truth's (C2, COCONUT truths), 55% have lib_sim ≤ 0.5 (39% ≤ 0.3), i.e. no reference spectrum of that structure resembles the query: their FP is inflated by FPNet memorisation (every train structure is seen by full_eval) and is not evidence of identity. Class-1 truths rarely lack support (lib_sim_c1 ≤ 0.5: panel clean 6%, G 1%, but dev2 C/E/F 31%, mostly negative-only / uncovered queries).

Variants (label-free: in_train of the view = the candidate is a training structure; lib_sim = its best reference similarity to the query):
- tdem{θ}_{w}: registered score − w · 1[train candidate and lib_sim ≤ θ], θ ∈ {0.3, 0.5}, w ∈ {0.5, 1, 2} (z units), applied to both paths (learned blend and fallback).
- anatdem{θ}_{w}: the same on top of anaw0.5 (analog channel), for the case the analog submission is adopted.

Selection: 11 class-2 layers (fe dev2 C2 ×5, fold-0 dev2 C2 ×5, fold-0 panel C2 clean), objective = equal-weight mean; constraints: every class-2 layer ≥ −0.02, panel C1 clean (fe, seen regime) ≥ −0.01; side table: G C1, C/E/F C1, W7 (inside the ranker's training runs). Then confirmation on the fresh sets (conf3, fit pool, fit pool 2) against the respective base with paired intervals; C1 losses on the fresh C1 views reported. Codex review before any Public use.
