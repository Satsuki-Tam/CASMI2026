# E4 (kernel hayatetaf/casmi26-e4-pclist)

Built by `make_e4.py` from `kernels/baseline-v18/casmi26-baseline-v18.ipynb` (= E0, Public LB 0.464) with exact-match replacements.

| version | pushed (JST) | change vs E0 | status |
|---|---|---|---|
| v1 | 2026-10-24 09:00 | K 25->100; GLACIER scores the whole PubChem-only list (same run); list order = z(pc_fz) + 2 z(GL), ICE dropped on that list; GL_BUDGET 5400 | superseded (ICE turned out to be complementary) |
| v2 | 2026-10-24 09:08 | K 25->100; ICE and GL inputs extended in the SAME runs; order = z(pc_fz) + 2 z(GL) + 1 z(ICE); ICE_BUDGET 7200, GL_BUDGET 5400 | visible-test run COMPLETE 09:30; superseded by v3 (no fallback, shared budgets) |
| v3 | 2026-10-24 09:4x | K 25->100; extra PubChem-list structures scored in SEPARATE second ICE/GL runs (own work dirs, budgets 2400 / 1500 s) after the unchanged E0 runs; scores used only for the PubChem-list order; whole-list fusion z(pc_fz) + 2 z(GL) + 1 z(ICE) only when both models cover >= 50% of the list, else the unchanged E0 rule | candidate for today's exploratory submission |

Evidence: `experiments/p1_baseline/run1/results_final/pclist_v2_A_timstof.md` (exact pool condition, real `gl_fuse.rerank_multi`, complete ICE+GL) and `docs/p1_baseline_2026-10-24.md`.
Untouched: class-1 base list and its ICE/GL rerank, gate (LIB_TAU, REL_TH), slots [2,4,6,8,10,24]/[4,8,12,16,20,24], promotion (S_TAU, POP_TAU, rel>150), RRF fusion with the engine list, overlays, N1 proxies, data/weights/Docker image, E0 budgets.
Local self-test (`make_e4.py` build + exec of the fusion block with stubs): full coverage -> fused order, pc_fz[0] preserved; GL cover 30% / no ICE / empty E4 dicts -> E0 rule, list unchanged.
| v4 | 2026-10-24 10:17 | (identical to v3: the coverage patch failed to apply before the push) | ignore |
| v5 | 2026-10-24 10:2x | v3 + E4_MIN_COVER = 1.0: the whole-list fusion is used only when ICE and GL both have finite scores for EVERY structure of the list; otherwise the unchanged E0 rule (Codex 005: partial-coverage fusion was not what P1 measured) | measurement submission candidate |
