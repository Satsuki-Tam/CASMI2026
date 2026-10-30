"""Technical checks of w135_fh_fit (featurize / weights / rank_lists) and w135_fh_read.boot on artificial tables (no real data)."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, r"C:\kaggle\CASMI\experiments\w135"); sys.path.insert(1, r"C:\kaggle\CASMI\experiments\b1_baseline")
import w135_fh_fit as FF
import w135_fh_read as RD

E0 = {k: 0 for k in FF.EDITS}
def row(w, m, key, src, rP, sP, fz, gl, glm, frag, y, **kw):
    d = dict(world=w, molecule=m, key=key, smiles="C" + key, src=src, is_gen=int(src == "B"), in_wwin=int(src == "P"), rP=rP, sP=sP, sP_miss=int(src == "B"),
             fz=fz, gl=gl, gl_miss=glm, frag=frag, apsc=0.0, log_npar=0.0, src_peer=0, src_train=0, n_steps=0, off_mass=0, y=y, **E0)
    d.update(kw); return d
U = pd.DataFrame([
    row("w1", "A", "a1", "P", 1, 3.0, 5.0, 0.5, 0, 0.2, 0), row("w1", "A", "a2", "P", 2, 2.0, 4.0, 0.0, 1, 0.1, 0), row("w1", "A", "a3", "P", 3, 1.0, 3.0, 0.4, 0, 0.0, 0),
    row("w1", "A", "b1", "B", 26, 0.0, 6.0, 0.9, 0, 0.3, 0, apsc=0.5, n_steps=1), row("w1", "A", "b2", "B", 26, 0.0, 2.0, 0.0, 1, 0.0, 1, apsc=0.2, n_steps=2),
    row("w1", "B", "c1", "B", 26, 0.0, 1.0, 0.0, 1, 0.0, 1), row("w1", "B", "c2", "B", 26, 0.0, 2.0, 0.0, 1, 0.0, 0),
    row("w2", "A", "a1", "P", 1, 3.0, 5.0, 0.5, 0, 0.2, 0), row("w2", "C", "d1", "P", 1, 1.0, 1.0, 0.0, 1, 0.0, 0), row("w2", "C", "d2", "P", 2, 1.0, 1.0, 0.0, 1, 0.0, 0),
])
Q = pd.DataFrame([dict(world="w1", molecule="A", n_b=2, n_p=3), dict(world="w1", molecule="B", n_b=2, n_p=0), dict(world="w2", molecule="A", n_b=0, n_p=1),
                  dict(world="w2", molecule="C", n_b=0, n_p=2)])
for k in ("p_gap12", "gl_ok", "lib_max", "log_ncand", "best_analog", "n_peer_struct", "n_train"): Q[k] = 0.5
Rg = FF.featurize(U, Q, "gen"); Rd = FF.featurize(U, Q, "db")
print("gen rows", len(Rg), "db rows", len(Rd), "| db has B rows:", bool((Rd.src == "B").any()), "| db queries:", sorted(set(zip(Rd.world, Rd.molecule))))
a = Rg[(Rg.world == "w1") & (Rg.molecule == "A")].set_index("key")
print(a[["rP_frac", "sP_z", "fz_rf", "gl_rf", "frag_rf", "d_fz_top1", "d_gl_top1", "d_gl_miss", "d_frag_top1", "log_nb", "log_np", "p_empty", "nU"]].round(3).to_string())
assert np.isclose(a.loc["a1", "sP_z"], 1.2247, atol=1e-3) and a.loc["b1", "sP_z"] == 0.0 and a.loc["b1", "d_fz_top1"] == 1.0 and a.loc["b2", "d_gl_miss"] == 1
assert a.loc["b1", "fz_rf"] == 0.0 and np.isclose(a.loc["a1", "fz_rf"], 0.2) and a.loc["a2", "gl_rf"] == 1.0 and np.isclose(a.loc["a1", "gl_rf"], 1 / 3)
b = Rg[(Rg.world == "w1") & (Rg.molecule == "B")]; assert (b.d_fz_top1 == 0).all() and (b.d_gl_miss == 1).all(), "empty P: differences 0 + miss flag"
assert (b.p_empty == 1).all() and (a.p_empty == 0).all(), "p_empty flag"
assert (Rd[(Rd.world == "w1") & (Rd.molecule == "A")].log_nb > 0).all(), "db arm keeps the query summary log_nb (Codex 153)"
# (1) a product with the maximum score goes to rank 1; (2) empty P + products -> the list comes from B; (3) no B -> P can be re-ordered
L1 = FF.rank_lists(Rg, np.where(Rg.key == "b2", 9.0, 0.0)); assert L1[("w1", "A")][0] == "b2"
assert L1[("w1", "B")] == ["c1", "c2"] or L1[("w1", "B")] == ["c2", "c1"]; L2 = FF.rank_lists(Rg, np.where(Rg.key == "d2", 9.0, 0.0)); assert L2[("w2", "C")] == ["d2", "d1"]
print("connection checks (product to rank 1, empty P, re-ordered P) ok")
w = FF.weights(Rg, Q); wa = dict(zip(zip(Rg.world, Rg.molecule, Rg.key), w))
print("weights: w1/A/a1", round(wa[("w1", "A", "a1")], 4), "(1/5 x 1/2) | w1/B/c1", round(wa[("w1", "B", "c1")], 4), "(1/2 x 1/1)")
assert np.isclose(wa[("w1", "A", "a1")], 0.1) and np.isclose(wa[("w1", "B", "c1")], 0.5)
L = FF.rank_lists(Rg, np.where(Rg.key.isin(["a2", "a3"]), 1.0, 0.0))
print("tie order w1/A:", L[("w1", "A")]); assert L[("w1", "A")] == ["a2", "a3", "a1", "b1", "b2"], "ties: rP then key"
D = pd.DataFrame(dict(batch=["x"] * 4, fam=[1, 1, 2, 3], rr_gen=[1.0, 0.5, 0.0, 1.0], rr_P=[0.5, 0.5, 0.0, 1.0]))
est, lo, hi, n = RD.boot(D, "gen", "P", np.ones(4, bool)); print("boot", round(est, 4), round(lo, 4), round(hi, 4), n); assert np.isclose(est, 0.125) and n == 4
print("TECH_CHECK_DONE")
