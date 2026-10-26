# 039 pre-registration: fragmentation as a learned ranker input (written 13:19 JST, before training)

- rank_v7c_fx = rank_v4b recipe (same RUNS, v2_noice − lib_nref − in_train, C1 ×3, rank_v4b's fixed params = 300 rounds) + analog block (ana_ap, z_ana_ap, ana_mt, ana_gap) + fragmentation block (frag, z_frag). Comparator with the same fixed params: rank_v7a_fx (analog only).
- Routing as v7f: learned blend21 when GL covered; GL fallback = insurance + 1·z(ap) + 1·z(frag).
- Rule (fixed now): v7c_fx replaces the v7f candidate only if, on the 036 11-layer objective, it is ≥ +0.005 above v7f (same routing with rank_v7a) AND panel C1 clean, C C1, G C1 are not more than 0.005 below v7f; then confirmation on the reused confirmation sets against v7f and Codex review. Otherwise it is recorded and dropped.

## Result (13:21 JST)
- rank_v7c_fx (analog + frag blocks, 300 fixed rounds) − v7f (registered routing with rank_v7a), 11 class-2 layers: **+0.0047** (fe C −0.005, D +0.009, G +0.012; f0 C +0.011, D +0.014, G +0.013; E/F 0 = fallback path identical; f0 panel C2 −0.003); C1: panel clean +0.001, C +0.008, G +0.010.
- Below the pre-registered +0.005 bar → **not adopted**, recorded and dropped (the difference is within the noise of a single development family; v7f stays the candidate).
